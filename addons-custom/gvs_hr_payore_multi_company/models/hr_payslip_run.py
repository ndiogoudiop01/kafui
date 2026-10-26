# -*- coding: utf-8 -*-
from odoo import fields, models


class HrPayslipRunGvs(models.Model):
    """Ajoute company_id sur hr.payslip.run pour le filtrage multi-société."""
    _inherit = 'hr.payslip.run'
    _check_company_auto = True

    company_id = fields.Many2one(
        'res.company',
        string='Société',
        copy=False,
        readonly=True,
        default=lambda self: self.env.company,
    )
