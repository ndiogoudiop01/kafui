# -*- coding: utf-8 -*-
from dateutil import relativedelta
from odoo import models, fields, api


class ProvisionRetraiteRuleInput(models.Model):
    _inherit = 'hr.payslip'

    def compute_provision_retraite(self, brut_of_current_payslip):
        """
        Calcule la provision de retraite sénégalaise.
        brut_of_current_payslip: valeur du brut du bulletin courant.
        """
        for payslip in self:
            # Get last 12 payslips of employee
            payslip_ids = self.env['hr.payslip'].search(
                [('employee_id', '=', payslip.employee_id.id)],
                order='id desc',
                limit=12,
            )
            if len(payslip_ids) >= 11:
                cumul_brut = 0.0
                for prev_slip in payslip_ids:
                    cumul_brut += sum(
                        line.total for line in prev_slip.line_ids if line.code == 'C1148'
                    )

                # Add current payslip brut
                cumul_brut += brut_of_current_payslip
                moy_brut = cumul_brut / len(payslip_ids)

                # Use version_id (hr.version) instead of contract_id (hr.contract)
                version = payslip.version_id
                if not version or not version.dateAnciennete:
                    return 0.0

                diff = relativedelta.relativedelta(version.dateAnciennete, payslip.date_to)
                years = -diff.years
                months = -diff.months
                days = -diff.days

                if years <= 5:
                    provision_retraite = self.compute_pr_moin_cinq(
                        moy_brut, years, months, days
                    )
                elif 5 < years <= 10:
                    provision_retraite = self.compute_pr_moin_cinq(moy_brut, 5, 0, 0)
                    provision_retraite += self.compute_pr_plus_cinq(
                        moy_brut, years - 5, months, days
                    )
                else:
                    provision_retraite = self.compute_pr_moin_cinq(moy_brut, 5, 0, 0)
                    provision_retraite += self.compute_pr_plus_cinq(moy_brut, years - 5, 0, 0)
                    provision_retraite += self.compute_pr_plus_dix(
                        moy_brut, years - 10, months, days
                    )

                return round(provision_retraite)
            return 0.0

    def compute_pr_moin_cinq(self, moyb, years, months, days):
        amount_for_year = moyb * 0.25 * float(years)
        amount_for_month = moyb * 0.25 * (float(months) / 12)
        amount_for_days = moyb * 0.25 * (float(days) / 365)
        return round(amount_for_year + amount_for_month + amount_for_days)

    def compute_pr_plus_cinq(self, moyb, years, months, days):
        amount_for_year = moyb * 0.3 * float(years)
        amount_for_month = moyb * 0.3 * (float(months) / 12)
        amount_for_days = moyb * 0.3 * (float(days) / 365)
        return round(amount_for_year + amount_for_month + amount_for_days)

    def compute_pr_plus_dix(self, moyb, years, months, days):
        amount_for_year = moyb * 0.4 * float(years)
        amount_for_month = moyb * 0.4 * (float(months) / 12)
        amount_for_days = moyb * 0.4 * (float(days) / 365)
        return round(amount_for_year + amount_for_month + amount_for_days)

    def compute_retirement_balance(self, brut_of_current_payslip):
        for payslip in self:
            # In v19, version_id replaces contract_id
            if payslip.version_id and payslip.version_id.motif:
                return self.compute_provision_retraite(brut_of_current_payslip)
        return 0.0

    def loan_balance(self):
        """
        Returns the outstanding loan balance for the employee.
        Requires the hr.loan module to be installed.
        """
        for payslip in self:
            amount = 0.0
            if 'hr.loan.line' not in self.env:
                return 0.0
            loan_lines = self.env['hr.loan.line'].search([
                ('employee_id', '=', payslip.employee_id.id),
                ('paid', '=', False),
            ])
            for loan_line in loan_lines:
                # Exclude loan lines for current payslip period
                if not (payslip.date_from <= loan_line.paid_date <= payslip.date_to):
                    amount += loan_line.paid_amount
            return round(amount)
