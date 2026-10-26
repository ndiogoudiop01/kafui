# -*- coding: utf-8 -*-
# hr.employee.bonus et relation.famille sont maintenant dans gvs_hr_payroll_base.
# Ce fichier conserve uniquement HrPayslipRunInherit et SaveAllocMensuel
# qui sont spécifiques à la paie Sénégal (comptabilité SYSCOHADA).

from odoo.tools import float_compare, float_is_zero
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class HrPayslipRunInherit(models.Model):
    _inherit = 'hr.payslip.run'

    journal_id = fields.Many2one('account.journal', 'Journal de salaires', readonly=False)

    def done_payslip_run(self):
        """
        Génère les écritures comptables SYSCOHADA pour le lot de bulletins,
        puis valide les bulletins.
        """
        precision = self.env['decimal.precision'].precision_get('Payroll')

        line_ids = []
        entries = {}
        index_deb = 0
        index_cred = 0

        last_slip = self.slip_ids and self.slip_ids[-1]
        batch_date = last_slip.date_to if last_slip else fields.Date.today()

        for slip in self.slip_ids.filtered(lambda s: s.state != 'done'):
            debit_sum = 0.0
            credit_sum = 0.0
            slip_date = slip.date_to

            employee_partner_id = (
                slip.employee_id.address_home_id.id
                if slip.employee_id.address_home_id
                else False
            )

            for line in slip.line_ids:
                amount = -line.total if slip.credit_note else line.total
                if float_is_zero(amount, precision_digits=precision):
                    continue

                debit_account_id = line.salary_rule_id.account_debit.id
                credit_account_id = line.salary_rule_id.account_credit.id
                journal_id = self.journal_id.id

                # Débit
                if debit_account_id and line.total > 0:
                    if line.salary_rule_id.account_debit.code[:3] == "421":
                        index_deb += 1
                        key = str(debit_account_id) + '_d_' + str(index_deb)
                        entries[key] = {
                            'name': line.name, 'partner_id': employee_partner_id,
                            'account_id': debit_account_id, 'journal_id': journal_id,
                            'date': slip_date,
                            'debit': round(amount > 0.0 and amount or 0.0), 'credit': 0.0,
                        }
                    else:
                        grp_key = str(debit_account_id) + '_d'
                        if grp_key in entries:
                            entries[grp_key]['debit'] += round(amount > 0.0 and amount or 0.0)
                        else:
                            entries[grp_key] = {
                                'name': line.name, 'partner_id': False,
                                'account_id': debit_account_id, 'journal_id': journal_id,
                                'date': slip_date,
                                'debit': round(amount > 0.0 and amount or 0.0), 'credit': 0.0,
                            }
                    debit_sum += round(amount > 0.0 and amount or 0.0)

                elif debit_account_id and line.total < 0:
                    amt = abs(amount)
                    if line.salary_rule_id.account_debit.code[:3] == "421":
                        index_cred += 1
                        key = str(debit_account_id) + '_dc_' + str(index_cred)
                        entries[key] = {
                            'name': line.name, 'partner_id': employee_partner_id,
                            'account_id': debit_account_id, 'journal_id': journal_id,
                            'date': slip_date, 'debit': 0.0,
                            'credit': round(amt > 0.0 and amt or 0.0),
                        }
                    else:
                        grp_key = str(debit_account_id) + '_neg_d'
                        if grp_key in entries:
                            entries[grp_key]['credit'] += round(amt > 0.0 and amt or 0.0)
                        else:
                            entries[grp_key] = {
                                'name': line.name, 'partner_id': False,
                                'account_id': debit_account_id, 'journal_id': journal_id,
                                'date': slip_date, 'debit': 0.0,
                                'credit': round(amt > 0.0 and amt or 0.0),
                            }
                    credit_sum += round(amt > 0.0 and amt or 0.0)

                # Crédit
                if credit_account_id and line.total > 0:
                    if line.salary_rule_id.account_credit.code[:3] == "421":
                        index_cred += 1
                        key = str(credit_account_id) + '_c_' + str(index_cred)
                        entries[key] = {
                            'name': line.name, 'partner_id': employee_partner_id,
                            'account_id': credit_account_id, 'journal_id': journal_id,
                            'date': slip_date, 'debit': 0.0,
                            'credit': round(amount > 0.0 and amount or 0.0),
                        }
                    else:
                        grp_key = str(credit_account_id) + '_c'
                        if grp_key in entries:
                            entries[grp_key]['credit'] += round(amount > 0.0 and amount or 0.0)
                        else:
                            entries[grp_key] = {
                                'name': line.name, 'partner_id': False,
                                'account_id': credit_account_id, 'journal_id': journal_id,
                                'date': slip_date, 'debit': 0.0,
                                'credit': round(amount > 0.0 and amount or 0.0),
                            }
                    credit_sum += round(amount > 0.0 and amount or 0.0)

                elif credit_account_id and line.total < 0:
                    amt = abs(amount)
                    if line.salary_rule_id.account_credit.code[:3] == "421":
                        index_deb += 1
                        key = str(credit_account_id) + '_cd_' + str(index_deb)
                        entries[key] = {
                            'name': line.name, 'partner_id': employee_partner_id,
                            'account_id': credit_account_id, 'journal_id': journal_id,
                            'date': slip_date,
                            'debit': round(amt > 0.0 and amt or 0.0), 'credit': 0.0,
                        }
                    else:
                        grp_key = str(credit_account_id) + '_neg_c'
                        if grp_key in entries:
                            entries[grp_key]['debit'] += round(amt > 0.0 and amt or 0.0)
                        else:
                            entries[grp_key] = {
                                'name': line.name, 'partner_id': False,
                                'account_id': credit_account_id, 'journal_id': journal_id,
                                'date': slip_date,
                                'debit': round(amt > 0.0 and amt or 0.0), 'credit': 0.0,
                            }
                    debit_sum += round(amt > 0.0 and amt or 0.0)

            if float_compare(credit_sum, debit_sum, precision_digits=precision) == -1:
                acc_id = self.journal_id.default_account_id.id
                if not acc_id:
                    raise UserError(
                        _('Le journal "%s" n\'a pas de compte de crédit configuré.')
                        % self.journal_id.name
                    )
                line_ids.append((0, 0, {
                    'name': _('Écriture d\'équilibrage'),
                    'partner_id': False, 'account_id': acc_id,
                    'journal_id': self.journal_id.id, 'date': slip_date,
                    'debit': 0.0, 'credit': debit_sum - credit_sum,
                }))
            elif float_compare(debit_sum, credit_sum, precision_digits=precision) == -1:
                acc_id = self.journal_id.default_account_id.id
                if not acc_id:
                    raise UserError(
                        _('Le journal "%s" n\'a pas de compte de débit configuré.')
                        % self.journal_id.name
                    )
                line_ids.append((0, 0, {
                    'name': _('Écriture d\'équilibrage'),
                    'partner_id': False, 'account_id': acc_id,
                    'journal_id': self.journal_id.id, 'date': slip_date,
                    'debit': credit_sum - debit_sum, 'credit': 0.0,
                }))

        for key, value in entries.items():
            line_ids.append((0, 0, {
                'name': value['name'], 'partner_id': value['partner_id'],
                'account_id': value['account_id'], 'journal_id': value['journal_id'],
                'date': value['date'], 'debit': value['debit'], 'credit': value['credit'],
            }))

        if line_ids and self.journal_id:
            name = _('Bulletins du lot %s') % self.name
            self.env['account.move'].create({
                'narration': name, 'ref': self.name,
                'journal_id': self.journal_id.id, 'date': batch_date,
                'line_ids': line_ids,
            })

        for slip in self.slip_ids.filtered(lambda s: s.state != 'done'):
            provision_amount = sum(l.total for l in slip.line_ids if l.code == 'C1150')
            provision_fin_contrat = sum(l.total for l in slip.line_ids if l.code == 'C1160')
            if slip.version_id:
                slip.version_id._get_droit(provision_amount, provision_fin_contrat)
            slip.action_payslip_done()

        self.write({'state': 'done'})


class SaveAllocMensual(models.Model):
    _name = "save.alloc.mensuel"
    _description = "Cumul mensuel allocation congés"

    slip_id = fields.Many2one('hr.payslip')
    cumul_mensuel = fields.Float()
    nbj_alloue = fields.Float()
