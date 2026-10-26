# -*- coding: utf-8 -*-
from odoo import fields, models, _


class HrPayslipRunInherit(models.Model):
    """inherit model for adding company_id field"""
    _inherit = "hr.payslip.run"
    _check_company_auto = True

    company_id = fields.Many2one('res.company', 'Company', copy=False, readonly=True,
                                 default=lambda self: self.env.company.id)