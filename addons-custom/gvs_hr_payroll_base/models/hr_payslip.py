# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class HrPayslipBase(models.Model):
    """Override de _get_payslip_lines pour injecter les éléments variables.

    Lit les enregistrements hr.employee.bonus du contrat (hr.version) et
    écrit amount_fix sur chaque règle salariale correspondante avant le
    calcul du bulletin.  Compatible avec tous les modules pays GVS.
    """
    _inherit = 'hr.payslip'

    @api.model
    def _get_payslip_lines(self, version_ids, payslip_id):
        """Calcul des lignes de bulletin avec injection des éléments variables."""

        def _sum_salary_rule_category(localdict, category, amount):
            if category.parent_id:
                localdict = _sum_salary_rule_category(
                    localdict, category.parent_id, amount
                )
            if category.code in localdict['categories'].dict:
                amount += localdict['categories'].dict[category.code]
            localdict['categories'].dict[category.code] = amount
            return localdict

        class BrowsableObject:
            def __init__(self, employee_id, dict_, env):
                self.employee_id = employee_id
                self.dict = dict_
                self.env = env

            def __getattr__(self, attr):
                return attr in self.dict and self.dict[attr] or 0.0

        class InputLine(BrowsableObject):
            def sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = fields.Date.today()
                self.env.cr.execute(
                    """SELECT sum(amount) FROM hr_payslip hp
                       JOIN hr_payslip_input pi ON hp.id = pi.payslip_id
                       WHERE hp.employee_id = %s AND hp.state = 'done'
                         AND hp.date_from >= %s AND hp.date_to <= %s
                         AND pi.code = %s""",
                    (self.employee_id, from_date, to_date, code),
                )
                return self.env.cr.fetchone()[0] or 0.0

        class WorkedDays(BrowsableObject):
            def _sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = fields.Date.today()
                self.env.cr.execute(
                    """SELECT sum(number_of_days), sum(number_of_hours)
                       FROM hr_payslip hp
                       JOIN hr_payslip_worked_days pi ON hp.id = pi.payslip_id
                       WHERE hp.employee_id = %s AND hp.state = 'done'
                         AND hp.date_from >= %s AND hp.date_to <= %s
                         AND pi.code = %s""",
                    (self.employee_id, from_date, to_date, code),
                )
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
                self.env.cr.execute(
                    """SELECT sum(CASE WHEN hp.credit_note = False
                                      THEN pl.total ELSE -pl.total END)
                       FROM hr_payslip hp
                       JOIN hr_payslip_line pl ON hp.id = pl.slip_id
                       WHERE hp.employee_id = %s AND hp.state = 'done'
                         AND hp.date_from >= %s AND hp.date_to <= %s
                         AND pl.code = %s""",
                    (self.employee_id, from_date, to_date, code),
                )
                res = self.env.cr.fetchone()
                return res and res[0] or 0.0

        result_dict = {}
        rules_dict = {}
        worked_days_dict = {}
        inputs_dict = {}
        blacklist = []

        payslip = self.env['hr.payslip'].browse(payslip_id)
        for wd in payslip.worked_days_line_ids:
            worked_days_dict[wd.code] = wd
        for inp in payslip.input_line_ids:
            inputs_dict[inp.code] = inp

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

        versions = self.env['hr.version'].browse(version_ids)

        if len(versions) == 1 and payslip.struct_id:
            structure_ids = list(set(payslip.struct_id._get_parent_structure().ids))
        else:
            structure_ids = (
                versions.mapped('struct_id').ids
                or versions.mapped('employee_id.struct_id').ids
            )

        # sudo() pour contourner les ir.rule multi-société sur hr.payroll.structure
        # et hr.salary.rule : le calcul du bulletin doit accéder aux règles de la
        # structure du bulletin, indépendamment de la société active de l'utilisateur.
        if not structure_ids:
            # Auto-détection : cherche la structure par défaut du pays de la société
            # de l'employé.  Couvre le cas des contrats créés AVANT l'installation du
            # module pays (struct_id non configuré sur hr.version / hr.employee).
            company = (
                versions.mapped('employee_id.company_id')[:1]
                or self.env.company
            )
            if company.country_id:
                default_struct = self.env['hr.payroll.structure'].sudo().search(
                    [
                        ('country_id', '=', company.country_id.id),
                        ('parent_id', '=', False),   # structure racine (top-level)
                    ],
                    limit=1,
                )
                if default_struct:
                    structure_ids = list(
                        set(default_struct._get_parent_structure().ids)
                    )
                    _logger.info(
                        '_get_payslip_lines: auto-detected structure "%s" (id=%s) '
                        'from company country %s for employee(s) %s',
                        default_struct.name,
                        default_struct.id,
                        company.country_id.code,
                        versions.mapped('employee_id.name'),
                    )

        if not structure_ids:
            employee_names = ', '.join(versions.mapped('employee_id.name')) or '?'
            company_country = (
                versions.mapped('employee_id.company_id.country_id.name')[:1]
                or ['(pays non défini)']
            )[0]
            raise ValidationError(_(
                "Aucune structure de paie trouvée pour le bulletin de %s.\n\n"
                "Veuillez :\n"
                "  1. Sélectionner une structure de paie sur le bulletin (champ « Structure »), ou\n"
                "  2. Configurer la structure sur le contrat de l'employé "
                "(Paie → Employés → Contrats → champ « Structure de paie »), ou\n"
                "  3. Vérifier qu'une structure de paie est définie pour le pays « %s » "
                "(Paie → Configuration → Structures de paie)."
            ) % (employee_names, company_country))

        structures = self.env['hr.payroll.structure'].sudo().browse(structure_ids)
        rule_ids = structures.get_all_rules()

        _logger.debug(
            '_get_payslip_lines: structure_ids=%s, rule_ids count=%d',
            structure_ids, len(rule_ids),
        )

        if not rule_ids:
            struct_names = ', '.join(structures.mapped('name')) or '?'
            raise ValidationError(_(
                "La structure de paie « %s » ne contient aucune règle salariale.\n\n"
                "Vérifiez que les règles salariales sont bien associées à cette structure "
                "(Paie → Configuration → Structures de paie → onglet Règles salariales)."
            ) % struct_names)

        # ── Injection des éléments variables depuis le contrat ───────────────
        # IMPORTANT : ne JAMAIS écrire amount_fix sur l'enregistrement partagé
        # hr.salary.rule — cela contaminerait tous les bulletins suivants pour tous
        # les employés utilisant la même règle.
        # On construit à la place un dictionnaire d'écrasements par version
        # (par employé) : {version_id: {rule_id: montant}}.
        bonus_overrides = {}  # {version.id: {rule_id: montant}}
        existing_rule_ids = {r_id for r_id, _ in rule_ids}
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
                    # Priorité NB_JOURS (convention pays BF=26, CI=30) sur WORK100
                    # (jours calendrier 5j/semaine ≈ 21-22) pour le prorata.
                    # NB_JOURS est dans inputs_dict si l'employé l'a renseigné.
                    nb_jours_inp = inputs_dict.get('NB_JOURS')
                    if nb_jours_inp and nb_jours_inp.amount:
                        nb_days = nb_jours_inp.amount
                    else:
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
                    # N'ajouter la règle que si elle n'est pas déjà dans la structure
                    # (évite le double traitement et la duplication de lignes)
                    if rule_sudo.id not in existing_rule_ids:
                        rule_ids.append((rule_sudo.id, rule_sudo.sequence))
                        existing_rule_ids.add(rule_sudo.id)
            bonus_overrides[version.id] = version_overrides
        # ────────────────────────────────────────────────────────────────────

        sorted_rule_ids = [
            r_id for r_id, _seq in sorted(rule_ids, key=lambda x: x[1])
        ]
        # sudo() pour accéder aux règles salariales sans filtre multi-société
        sorted_rules = self.env['hr.salary.rule'].sudo().browse(sorted_rule_ids)

        for version in versions:
            employee = version.employee_id
            localdict = dict(baselocaldict, employee=employee, contract=version)
            version_overrides = bonus_overrides.get(version.id, {})

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

                    previous_amount = localdict.get(rule.code, 0.0)
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
                    blacklist += [
                        r_id for r_id, _seq in rule._recursive_search_of_rules()
                    ]

        return list(result_dict.values())

    # ── Valeur par défaut WORK100 = 30 jours / 173,33 h ──────────────────────
    # Convention forfaitaire commune à tous les pays GVS (BF/BJ/CI/NE/TG) : un
    # mois plein correspond à 30 jours, indépendamment du calendrier hebdo de
    # l'employé (qui donnerait sinon ~22 jours ouvrés en semaine de 5 jours).
    # Ce n'est qu'une VALEUR PAR DÉFAUT : le champ "Nombre de jours" de
    # l'onglet "Jours travaillés et entrées" (ligne WORK100) reste ensuite
    # librement modifiable par l'utilisateur, ce qui fait varier le salaire
    # de base au prorata (cf. les règles NB_JOURS / TECH_JOURS de chaque
    # module pays).
    #
    # Appliqué à la fois sur :
    #  - onchange_employee (formulaire bulletin, saisie interactive) ;
    #  - onchange_employee_id (utilisé par l'assistant "Bulletins par
    #    employés" om_hr_payroll pour la génération en lot).
    # Ne touche PAS get_worked_day_lines()/_get_payslip_lines() directement,
    # afin de rester compatible quel que soit le module qui fournit ces deux
    # méthodes (om_hr_payroll ou une éventuelle surcharge additionnelle).

    _GVS_DEFAULT_WORK100_DAYS = 30.0
    _GVS_DEFAULT_WORK100_HOURS = 173.33

    @api.onchange('employee_id', 'date_from', 'date_to')
    def onchange_employee(self):
        res = super().onchange_employee()
        for line in self.worked_days_line_ids:
            if line.code == 'WORK100':
                line.number_of_days = self._GVS_DEFAULT_WORK100_DAYS
                line.number_of_hours = self._GVS_DEFAULT_WORK100_HOURS
        return res

    def onchange_employee_id(self, date_from, date_to, employee_id=False, contract_id=False):
        res = super().onchange_employee_id(
            date_from, date_to, employee_id=employee_id, contract_id=contract_id,
        )
        for line in (res.get('value') or {}).get('worked_days_line_ids') or []:
            # Ligne au format (0, 0, {...}) renvoyée par get_worked_day_lines(),
            # ou dict brut selon le point d'appel : on gère les deux formes.
            vals = line[2] if isinstance(line, (list, tuple)) and len(line) == 3 else line
            if isinstance(vals, dict) and vals.get('code') == 'WORK100':
                vals['number_of_days'] = self._GVS_DEFAULT_WORK100_DAYS
                vals['number_of_hours'] = self._GVS_DEFAULT_WORK100_HOURS
        return res
