# -*- coding: utf-8 -*-
from odoo import models, fields


class HrPayslipInheritIr(models.Model):
    _inherit = 'hr.payslip'

    brut_of_current_payslip = fields.Float(default=0.0)

    def get_brut_annual(self):
        self.ensure_one()
        year = self.date_from.year
        cumul_brut = 0.0
        for line in self.env['hr.payslip'].search(
            [('employee_id', '=', self.employee_id.id), ('year', '=', str(year))],
            limit=11,
        ):
            cumul_brut += sum(
                pl.total for pl in line.line_ids if pl.code == "C1200"
            )
        return cumul_brut + self.brut_of_current_payslip

    def get_base_fiscal_apres_abattement_annuel(self):
        self.ensure_one()
        brut = self.get_brut_annual()
        abbatement = min(brut * 0.3, 900000)
        return brut - abbatement

    def get_second_tranch(self):
        self.ensure_one()
        base_fisc = self.get_base_fiscal_apres_abattement_annuel()
        if 630000 < base_fisc <= 1500000:
            return round((base_fisc - 630000) * 0.2)
        elif base_fisc > 1500000:
            return 174000
        return 0

    def get_third_tranch(self):
        self.ensure_one()
        base_fisc = self.get_base_fiscal_apres_abattement_annuel()
        if 1500000 < base_fisc <= 4000000:
            return round((base_fisc - 1500000) * 0.3)
        elif base_fisc > 4000000:
            return 750000
        return 0

    def get_fourth_tranch(self):
        self.ensure_one()
        base_fisc = self.get_base_fiscal_apres_abattement_annuel()
        if 4000000 < base_fisc <= 8000000:
            return round((base_fisc - 4000000) * 0.35)
        elif base_fisc > 8000000:
            return 1400004
        return 0

    def get_fifth_tranch(self):
        self.ensure_one()
        base_fisc = self.get_base_fiscal_apres_abattement_annuel()
        if 8000000 < base_fisc <= 13500000:
            return round((base_fisc - 8000000) * 0.37)
        elif base_fisc > 13500000:
            return 2034996
        return 0

    def get_sixth_tranch(self):
        self.ensure_one()
        base_fisc = self.get_base_fiscal_apres_abattement_annuel()
        if 13500000 < base_fisc <= 50000000:
            return round((base_fisc - 13500000) * 0.4)
        elif base_fisc > 50000000:
            return 14600000
        return 0

    def get_seven_tranch(self):
        self.ensure_one()
        base_fisc = self.get_base_fiscal_apres_abattement_annuel()
        if base_fisc > 50000000:
            return round((base_fisc - 50000000) * 0.43)
        return 0

    def get_cumul_tranche(self):
        self.ensure_one()
        return round(
            self.get_second_tranch()
            + self.get_third_tranch()
            + self.get_fourth_tranch()
            + self.get_fifth_tranch()
            + self.get_sixth_tranch()
            + self.get_seven_tranch()
        )

    def get_one_part(self):
        self.ensure_one()
        if self.employee_id.ir == 1.5:
            raw = self.get_cumul_tranche() * 0.1
            return max(100000, min(raw, 300000))
        return 0

    def get_two_part(self):
        self.ensure_one()
        ir = self.employee_id.ir
        ct = self.get_cumul_tranche()
        if ir == 2:
            return round(max(200000, min(ct * 0.15, 650000)))
        if ir == 2.5:
            return round(max(300000, min(ct * 0.2, 1100000)))
        return 0

    def get_third_part(self):
        self.ensure_one()
        ir = self.employee_id.ir
        ct = self.get_cumul_tranche()
        if ir == 3:
            return round(max(400000, min(ct * 0.25, 1650000)))
        if ir == 3.5:
            return round(max(500000, min(ct * 0.3, 2030000)))
        return 0

    def get_fourth_part(self):
        self.ensure_one()
        ir = self.employee_id.ir
        ct = self.get_cumul_tranche()
        if ir == 4:
            return round(max(600000, min(ct * 0.35, 2490000)))
        if ir == 4.5:
            return round(max(700000, min(ct * 0.4, 2755000)))
        return 0

    def get_fifth_part(self):
        self.ensure_one()
        if self.employee_id.ir == 5:
            ct = self.get_cumul_tranche()
            return round(max(800000, min(ct * 0.45, 3180000)))
        return 0

    def get_ir_annuel(self, brut_imposable):
        self.brut_of_current_payslip = brut_imposable
        self.ensure_one()
        deduction = (
            self.get_one_part()
            + self.get_two_part()
            + self.get_third_part()
            + self.get_fourth_part()
            + self.get_fifth_part()
        )
        result = self.get_cumul_tranche() - deduction
        return round(result) if result > 0 else 0

    def get_cumul_ir(self, ir_of_current_payslip):
        self.ensure_one()
        year = self.date_from.year
        cumul_ir = 0.0
        for line in self.env['hr.payslip'].search(
            [('employee_id', '=', self.employee_id.id), ('year', '=', str(year))],
            limit=12,
        ):
            cumul_ir += sum(
                pl.total for pl in line.line_ids if pl.code == "C2170"
            )
        return cumul_ir
