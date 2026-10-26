# -*- coding: utf-8 -*-
import time
from datetime import datetime, date, time as t
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from pytz import timezone
import logging

_logger = logging.getLogger(__name__)


class BonusRuleInput(models.Model):
    _inherit = 'hr.payslip'

    nb_part_of_payslip = fields.Float(
        string="Nb part",
        compute="_get_nb_part_of_payslip",
        store=True,
    )
    payslip_count_yearly = fields.Integer(
        'Nb payslip yearly',
        compute="_get_payslip_count_yearly",
    )
    year = fields.Char(string="year", compute='_get_year', store=True)
    holiday_of_payslip = fields.Float(default=0)
    marital = fields.Selection([
        ('single', 'Single'),
        ('married', 'Married'),
        ('cohabitant', 'Legal Cohabitant'),
        ('widower', 'Widower'),
        ('divorced', 'Divorced')
    ], string='Marital Status', related="employee_id.marital")

    @api.depends('date_from')
    def _get_year(self):
        """for recovering easily the year of payslip"""
        for payslip in self:
            if payslip.date_from:
                payslip.year = str(payslip.date_from.year)
            else:
                payslip.year = False

    @api.depends('employee_id', 'date_from')
    def _get_payslip_count_yearly(self):
        for payslip in self:
            if payslip.date_from:
                year = str(payslip.date_from.year)
                count = self.env['hr.payslip'].search([
                    ('employee_id', '=', payslip.employee_id.id),
                    ('year', '=', year),
                ])
                payslip.payslip_count_yearly = len(count)
            else:
                payslip.payslip_count_yearly = 0

    @api.depends('employee_id')
    def _get_nb_part_of_payslip(self):
        for payslip in self:
            if payslip.employee_id:
                payslip.nb_part_of_payslip = payslip.employee_id.ir
            else:
                payslip.nb_part_of_payslip = 0.0

    @api.model
    def create(self, vals):
        res = super(BonusRuleInput, self).create(vals)
        if not res.credit_note and res.version_id:
            self.env.cr.execute(
                "SELECT date_from, date_to FROM hr_payslip WHERE employee_id = %s AND year = %s AND id != %s",
                (res.employee_id.id, res.year, res.id)
            )
            date_from_to = self.env.cr.fetchall()
            exist = [item for item in date_from_to if item[0] and item[0].month == res.date_from.month]
            if exist:
                raise ValidationError(_(str(res.name) + " existe déjà"))
        return res

    def get_worked_days_per_year(self, employee_id, year):
        worked_days_obj = self.env['employee.worked.days'].search([
            ('employee_id', '=', employee_id),
            ('year', '=', year),
        ])
        if worked_days_obj.exists():
            return worked_days_obj[0].worked_days
        else:
            return 0

    def action_payslip_done(self):
        val = super(BonusRuleInput, self).action_payslip_done()
        for payslip in self:
            work_line = payslip.worked_days_line_ids.filtered(lambda l: l.code == 'WORK100')
            if work_line and work_line[0].number_of_days != 0:
                # update or create the worked days in this year
                worked_days_obj = payslip.env['employee.worked.days'].search([
                    ('employee_id', '=', payslip.employee_id.id),
                    ('year', '=', payslip.date_from.year),
                ])
                if worked_days_obj.exists():
                    worked_days_obj[0].write({
                        'worked_days': worked_days_obj[0].worked_days + work_line[0].number_of_days
                    })
                else:
                    self.env['employee.worked.days'].create({
                        'year': payslip.date_from.year,
                        'worked_days': work_line[0].number_of_days,
                        'employee_id': payslip.employee_id.id,
                    })
                provision_conges = sum(
                    line.total for line in payslip.line_ids if line.code == 'C1150'
                )
                provision_fin_contrat = sum(
                    line.total for line in payslip.line_ids if line.code == 'C1160'
                )
                if payslip.version_id:
                    payslip.version_id._get_droit(provision_conges, provision_fin_contrat)

                for line in payslip.line_ids:
                    if line.code == "C1060":
                        if payslip.version_id:
                            payslip.version_id.reinit()
                        break
        return val

    def update_recompute_ir(self):
        for payslip in self:
            year = payslip.date_from.year

            ir_changed = 0
            two_last_payslip = self.env['hr.payslip'].search(
                [('employee_id', '=', payslip.employee_id.id)],
                order="id desc",
                limit=2,
            )
            # compute ir recal monthly
            if len(two_last_payslip) > 1:
                if two_last_payslip[1].nb_part_of_payslip != payslip.employee_id.ir:
                    ir_changed = 1
                    for line in self.env['hr.payslip'].search(
                        [('employee_id', '=', payslip.employee_id.id)],
                        order="id desc",
                        limit=12,
                    ):
                        if line.date_from and line.date_from.year == year:
                            cumul_tranche_ipm = 0.0
                            deduction = 0.0
                            payslip_line_ids = self.env['hr.payslip.line'].search(
                                [('slip_id', '=', line.id)]
                            )
                            cumul_tranche_ipm += sum(
                                pl.total for pl in payslip_line_ids if pl.code == "C2110"
                            )

                            for payslip_line in payslip_line_ids:
                                if payslip_line.code == "C2150":
                                    obj_empl = self.env['hr.employee'].browse(payslip.employee_id.id)
                                    if obj_empl:
                                        ir_val = payslip.employee_id.ir
                                        if ir_val == 1:
                                            deduction = 0.0
                                        elif ir_val == 1.5:
                                            raw = cumul_tranche_ipm * 0.1
                                            deduction = max(8333, min(raw, 25000))
                                        elif ir_val == 2:
                                            raw = cumul_tranche_ipm * 0.15
                                            deduction = max(16666.66666666667, min(raw, 54166.66666666667))
                                        elif ir_val == 2.5:
                                            raw = cumul_tranche_ipm * 0.2
                                            deduction = max(25000, min(raw, 91666.66666666667))
                                        elif ir_val == 3:
                                            raw = cumul_tranche_ipm * 0.25
                                            deduction = max(33333.33333333333, min(raw, 137500))
                                        elif ir_val == 3.5:
                                            raw = cumul_tranche_ipm * 0.3
                                            deduction = max(41666.66666666667, min(raw, 169166.6666666667))
                                        elif ir_val == 4:
                                            raw = cumul_tranche_ipm * 0.35
                                            deduction = max(50000, min(raw, 207500))
                                        elif ir_val == 4.5:
                                            raw = cumul_tranche_ipm * 0.4
                                            deduction = max(58333.33333, min(raw, 229583.3333))
                                        elif ir_val == 5:
                                            raw = cumul_tranche_ipm * 0.45
                                            deduction = max(66666.66667, min(raw, 265000))

                                        ir_val_recal = max(cumul_tranche_ipm - deduction, 0.0)
                                        obj = self.env['hr.payslip.line'].search(
                                            [('code', '=', payslip_line.code),
                                             ('slip_id', '=', line.id)],
                                            limit=1,
                                        )
                                        if obj:
                                            obj.write({'amount': round(ir_val_recal)})
            # end compute ir_recal

            ir_payslip = sum(
                pl.total for pl in payslip.line_ids if pl.code == "C2140"
            )
            net_payslip = sum(
                pl.total for pl in payslip.line_ids if pl.code == "C5000"
            )

            # update the ir_regul of current payslip
            if ir_changed == 1:
                cumul_ir = 0.0
                cumul_ir_recal = 0.0
                for line in self.env['hr.payslip'].search(
                    [('employee_id', '=', payslip.employee_id.id)]
                ):
                    if line.date_from and line.date_from.year == year:
                        cumul_ir += sum(
                            pl.total for pl in line.line_ids if pl.code == "C2140"
                        )
                        cumul_ir_recal += sum(
                            pl.total for pl in line.line_ids if pl.code == "C2150"
                        )
                        for obj in payslip.line_ids:
                            if obj.code == "C2160":
                                obj.write({'amount': round(cumul_ir - cumul_ir_recal)})
                for obj in payslip.line_ids:
                    if obj.code == "C2170":
                        obj.write({'amount': round(ir_payslip - (cumul_ir - cumul_ir_recal))})
            else:
                for obj in payslip.line_ids:
                    if obj.code == "C2170":
                        obj.write({'amount': round(ir_payslip)})

            # in case of regul yearly
            regul_annuel = [obj for obj in payslip.line_ids if obj.code == 'C2163']
            if regul_annuel:
                for obj in payslip.line_ids:
                    if obj.code == "C2170":
                        obj.write({'amount': round(regul_annuel[0].total)})

            # défalquer ir_fin du net
            ir_fin = sum(pl.total for pl in payslip.line_ids if pl.code == "C2170")
            for obj in payslip.line_ids:
                if obj.code == "C5000":
                    obj.write({'amount': round(net_payslip - ir_fin)})

            # compute_loan_balance (only if motif is set and hr.loan.line model exists)
            version = payslip.version_id
            if version and version.motif:
                try:
                    val_loan_balance = payslip.loan_balance()
                    if val_loan_balance != 0:
                        for payslip_line in payslip.line_ids:
                            if payslip_line.code == "C5000":
                                payslip_line.write({'amount': round(net_payslip - val_loan_balance)})
                except Exception:
                    pass

    def compute_sheet(self):
        """Override: call super() then set holiday_of_payslip and update IR recalculation."""
        for payslip in self:
            if payslip.state == "draft":
                # Check version end date
                if (payslip.version_id and payslip.version_id.contract_date_end
                        and payslip.date_from > payslip.version_id.contract_date_end):
                    raise ValidationError(
                        _("La date du bulletin ne peut pas être supérieur à la date de sortie du contrat"))
        # Call base compute_sheet (which calls _get_payslip_lines)
        result = super(BonusRuleInput, self).compute_sheet()
        # Post-process: set holiday and recompute IR
        for payslip in self:
            if payslip.state == "draft":
                payslip.write({
                    'holiday_of_payslip': payslip.version_id.nbj_pris if payslip.version_id else 0,
                })
                payslip.update_recompute_ir()
        return result

    @api.model
    def _get_payslip_lines(self, version_ids, payslip_id):
        """
        Override to inject Senegalese bonus rules and custom rule amount computations.
        """

        def _sum_salary_rule_category(localdict, category, amount):
            if category.parent_id:
                localdict = _sum_salary_rule_category(localdict, category.parent_id, amount)
            if category.code in localdict['categories'].dict:
                amount += localdict['categories'].dict[category.code]
            localdict['categories'].dict[category.code] = amount
            return localdict

        class BrowsableObject(object):
            def __init__(self, employee_id, dict, env):
                self.employee_id = employee_id
                self.dict = dict
                self.env = env

            def __getattr__(self, attr):
                return attr in self.dict and self.dict.__getitem__(attr) or 0.0

        class InputLine(BrowsableObject):
            def sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = fields.Date.today()
                self.env.cr.execute("""
                    SELECT sum(amount) as sum
                    FROM hr_payslip as hp, hr_payslip_input as pi
                    WHERE hp.employee_id = %s AND hp.state = 'done'
                    AND hp.date_from >= %s AND hp.date_to <= %s
                    AND hp.id = pi.payslip_id AND pi.code = %s""",
                    (self.employee_id, from_date, to_date, code))
                return self.env.cr.fetchone()[0] or 0.0

        class WorkedDays(BrowsableObject):
            def _sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = fields.Date.today()
                self.env.cr.execute("""
                    SELECT sum(number_of_days) as number_of_days,
                           sum(number_of_hours) as number_of_hours
                    FROM hr_payslip as hp, hr_payslip_worked_days as pi
                    WHERE hp.employee_id = %s AND hp.state = 'done'
                    AND hp.date_from >= %s AND hp.date_to <= %s
                    AND hp.id = pi.payslip_id AND pi.code = %s""",
                    (self.employee_id, from_date, to_date, code))
                return self.env.cr.fetchone()

            def sum(self, code, from_date, to_date=None):
                res = self._sum(code, from_date, to_date)
                return res and res[0] or 0.0

            def sum_hours(self, code, from_date, to_date=None):
                res = self._sum(code, from_date, to_date)
                return res and res[1] or 0.0

        class Payslips(BrowsableObject):
            def sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = fields.Date.today()
                self.env.cr.execute("""
                    SELECT sum(case when hp.credit_note = False then (pl.total) else (-pl.total) end)
                    FROM hr_payslip as hp, hr_payslip_line as pl
                    WHERE hp.employee_id = %s AND hp.state = 'done'
                    AND hp.date_from >= %s AND hp.date_to <= %s
                    AND hp.id = pl.slip_id AND pl.code = %s""",
                    (self.employee_id, from_date, to_date, code))
                res = self.env.cr.fetchone()
                return res and res[0] or 0.0

        result_dict = {}
        rules_dict = {}
        worked_days_dict = {}
        inputs_dict = {}
        blacklist = []

        payslip = self.env['hr.payslip'].browse(payslip_id)
        for worked_days_line in payslip.worked_days_line_ids:
            worked_days_dict[worked_days_line.code] = worked_days_line
        for input_line in payslip.input_line_ids:
            inputs_dict[input_line.code] = input_line

        categories = BrowsableObject(payslip.employee_id.id, {}, self.env)
        inputs = InputLine(payslip.employee_id.id, inputs_dict, self.env)
        worked_days = WorkedDays(payslip.employee_id.id, worked_days_dict, self.env)
        payslips = Payslips(payslip.employee_id.id, payslip, self.env)
        rules = BrowsableObject(payslip.employee_id.id, rules_dict, self.env)

        baselocaldict = {
            'categories': categories,
            'rules': rules,
            'payslip': payslips,
            'worked_days': worked_days,
            'inputs': inputs,
        }

        # Browse hr.version instead of hr.contract
        versions = self.env['hr.version'].browse(version_ids)

        if len(versions) == 1 and payslip.struct_id:
            structure_ids = list(set(payslip.struct_id._get_parent_structure().ids))
        else:
            structure_ids = (
                versions.mapped('struct_id').ids
                or versions.mapped('employee_id.struct_id').ids
            )

        # sudo() pour contourner les ir.rule multi-société sur hr.payroll.structure
        # et hr.salary.rule : le calcul du bulletin doit pouvoir accéder aux règles
        # de la structure, quelle que soit la société active de l'utilisateur.
        rule_ids = self.env['hr.payroll.structure'].sudo().browse(structure_ids).get_all_rules()

        # ── Injection des éléments variables depuis le contrat ───────────────
        # IMPORTANT : ne JAMAIS écrire amount_fix sur l'enregistrement partagé
        # hr.salary.rule — cela contaminerait tous les bulletins suivants.
        # On construit un dictionnaire d'écrasements par version (par employé) :
        #   {version_id: {rule_id: montant}}
        bonus_overrides = {}  # {version.id: {rule_id: montant}}
        for version in versions:
            version_overrides = {}
            for bonus in version.bonus:
                # Calcul de la période active selon le type de durée :
                # - one_time / limited : date_to est renseignée
                # - unlimited          : date_to est False → actif si date_from ≤ fin bulletin
                if bonus.date_to:
                    in_period = not (
                        bonus.date_to < payslip.date_from
                        or bonus.date_from > payslip.date_to
                    )
                else:
                    # Illimité : actif si date_from ≤ date_to du bulletin
                    in_period = bonus.date_from <= payslip.date_to
                if in_period:
                    work100 = worked_days_dict.get('WORK100')
                    nb_days = work100.number_of_days if work100 else 30
                    rule_sudo = bonus.salary_rule.sudo()
                    if rule_sudo.is_prorata:
                        amt = round(bonus.amount * nb_days / 30)
                    else:
                        amt = round(bonus.amount)
                    _logger.debug(
                        'Bonus override [%s] %.0f FCFA → version %s',
                        rule_sudo.code, amt, version.id,
                    )
                    version_overrides[rule_sudo.id] = amt
                    rule_ids.append((rule_sudo.id, rule_sudo.sequence))
            bonus_overrides[version.id] = version_overrides
        # ────────────────────────────────────────────────────────────────────

        sorted_rule_ids = [r_id for r_id, sequence in sorted(rule_ids, key=lambda x: x[1])]
        # sudo() pour accéder aux règles salariales sans filtre multi-société
        sorted_rules = self.env['hr.salary.rule'].sudo().browse(sorted_rule_ids)

        for version in versions:
            employee = version.employee_id
            # Pass version as 'contract' so salary rules using contract.wage etc. still work
            localdict = dict(baselocaldict, employee=employee, contract=version)
            version_overrides = bonus_overrides.get(version.id, {})

            brut_of_current_payslip = 0.0
            brut_imposable_of_current_payslip = 0.0
            ir_of_current_payslip = 0.0

            for rule in sorted_rules:
                key = rule.code + '-' + str(version.id)
                localdict['result'] = None
                localdict['result_qty'] = 1.0
                localdict['result_rate'] = 100

                if rule._satisfy_condition(localdict) and rule.id not in blacklist:
                    amount, qty, rate = rule._compute_rule(localdict)

                    # Écrasement par le montant de l'élément variable de CET employé.
                    # Évite la contamination inter-employés : chaque version a ses
                    # propres overrides, indépendants de l'enregistrement partagé.
                    if rule.id in version_overrides:
                        amount = version_overrides[rule.id]

                    # Accumulate totals for Senegalese tax computations
                    if rule.category_id.code in ['INDM', 'BASE', 'NOIMP', 'HS']:
                        brut_of_current_payslip += amount
                    if rule.code == 'C1200':
                        brut_imposable_of_current_payslip = amount
                    if rule.code == 'C2140':
                        ir_of_current_payslip += amount

                    # Special Senegalese rule overrides
                    if rule.code == 'C1120':      # indemnité de retraite
                        amount = payslip.compute_retirement_balance(brut_of_current_payslip)
                    elif rule.code == 'C1145':    # indemnité de licenciement
                        amount = payslip.compute_retirement_balance(brut_of_current_payslip)
                    elif rule.code == 'C1146':    # indemnité de décès
                        amount = payslip.compute_retirement_balance(brut_of_current_payslip)
                    elif rule.code == 'C1147':    # provision de retraite
                        amount = payslip.compute_provision_retraite(brut_of_current_payslip)
                    elif rule.code == 'C2161':    # IR annuel
                        amount = payslip.get_ir_annuel(brut_imposable_of_current_payslip)
                    elif rule.code == 'C2162':    # cumul IR
                        amount = payslip.get_cumul_ir(ir_of_current_payslip)
                    elif rule.code == 'C2048':    # TRIMF annuel
                        amount = payslip.get_annual_trimf()
                    elif rule.code == 'C2047':    # cumul TRIMF
                        amount = payslip.get_cumul_trimf(brut_imposable_of_current_payslip)

                    previous_amount = rule.code in localdict and localdict[rule.code] or 0.0
                    company = employee.company_id
                    tot_rule = company.currency_id.round(amount * qty * rate / 100.0)
                    localdict[rule.code] = tot_rule
                    rules_dict[rule.code] = rule
                    localdict = _sum_salary_rule_category(
                        localdict, rule.category_id, tot_rule - previous_amount
                    )

                    result_dict[key] = {
                        'salary_rule_id': rule.id,
                        'version_id': version.id,
                        'name': rule.name,
                        'code': rule.code,
                        'category_id': rule.category_id.id,
                        'sequence': rule.sequence,
                        'appears_on_payslip': rule.appears_on_payslip,
                        'condition_select': rule.condition_select,
                        'condition_python': rule.condition_python,
                        'condition_range': rule.condition_range,
                        'condition_range_min': rule.condition_range_min,
                        'condition_range_max': rule.condition_range_max,
                        'amount_select': rule.amount_select,
                        'amount_fix': rule.amount_fix,
                        'amount_python_compute': rule.amount_python_compute,
                        'amount_percentage': rule.amount_percentage,
                        'amount_percentage_base': rule.amount_percentage_base,
                        'register_id': rule.register_id.id,
                        'amount': amount,
                        'employee_id': employee.id,
                        'quantity': qty,
                        'rate': rate,
                    }
                else:
                    blacklist += [r_id for r_id, seq in rule._recursive_search_of_rules()]

            # Trigger duration calculation for the version
            if hasattr(version, '_get_duration'):
                version._get_duration()

        return list(result_dict.values())

    @api.model
    def get_worked_day_lines(self, versions, date_from, date_to):
        """
        Custom Senegalese 30-day month calculation.
        Uses fixed 30 days per month minus leave days.
        """
        res = []
        for version in versions.filtered(lambda v: v.resource_calendar_id):
            day_from = datetime.combine(fields.Date.from_string(date_from), t.min)
            day_to = datetime.combine(fields.Date.from_string(date_to), t.max)

            # compute leave days
            leaves = {}
            calendar = version.resource_calendar_id
            tz = timezone(calendar.tz)
            day_leave_intervals = version.employee_id.list_leaves(
                day_from, day_to, calendar=calendar
            )
            nb_day_leave = 0.0
            nb_hour_leave = 0.0

            for day, hours, leave in day_leave_intervals:
                holiday = leave.holiday_id
                if not holiday:
                    continue
                current_leave_struct = leaves.setdefault(holiday.holiday_status_id, {
                    'name': holiday.holiday_status_id.name or _('Global Leaves'),
                    'sequence': 5,
                    'code': holiday.holiday_status_id.code or holiday.holiday_status_id.name or 'GLOBAL',
                    'number_of_days': 0.0,
                    'number_of_hours': 0.0,
                    'version_id': version.id,
                })
                current_leave_struct['number_of_hours'] += hours
                work_hours = calendar.get_work_hours_count(
                    tz.localize(datetime.combine(day, t.min)),
                    tz.localize(datetime.combine(day, t.max)),
                    compute_leaves=False,
                )
                if work_hours:
                    current_leave_struct['number_of_days'] += hours / work_hours
                    nb_day_leave = current_leave_struct['number_of_days']
                    nb_hour_leave = current_leave_struct['number_of_hours']

            # Senegalese fixed 30-day month
            attendances = {
                'name': _("Normal Working Days paid at 100%"),
                'sequence': 1,
                'code': 'WORK100',
                'number_of_days': 30 - nb_day_leave,
                'number_of_hours': 173.33 - nb_hour_leave,
                'version_id': version.id,
            }

            res.append(attendances)
            res.extend(leaves.values())
        return res


class HrPayslipLine(models.Model):
    _inherit = 'hr.payslip.line'

    total = fields.Float(compute='_compute_total', string='Total', store=True)
    fonction_employee = fields.Char(
        string='Fonction Employe',
        related='employee_id.job_id.name',
        store=True,
    )
    # In v19, employee inherits version fields via _inherits,
    # so employee_id.convention_id.name works directly
    categorie_employee = fields.Char(
        string="Categorie Employe",
        related='employee_id.convention_id.name',
        store=True,
    )
    payslip_date_from = fields.Date(
        string="Date de debut",
        related="slip_id.date_from",
        store=True,
    )
    payslip_date_to = fields.Date(
        string="Date de fin",
        related="slip_id.date_to",
        store=True,
    )
    year = fields.Char(string="year", compute='_get_year', store=True)

    @api.depends('quantity', 'amount', 'rate')
    def _compute_total(self):
        for line in self:
            line.total = float(line.quantity) * line.amount * line.rate / 100

    @api.depends('payslip_date_to')
    def _get_year(self):
        """for recovering easily the year of payslip line in DADS report"""
        for line in self:
            if line.payslip_date_to:
                line.year = str(line.payslip_date_to.year)
            else:
                line.year = False


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    def action_send_email(self):
        try:
            template_id = self.env.ref('om_hr_payroll.mail_template_payslip').id
        except ValueError:
            _logger.warning("Mail template 'om_hr_payroll.mail_template_payslip' not found")
            return
        for batch in self:
            for payslip in batch.slip_ids:
                self.env['mail.template'].browse(template_id).send_mail(
                    payslip.id, force_send=True
                )
