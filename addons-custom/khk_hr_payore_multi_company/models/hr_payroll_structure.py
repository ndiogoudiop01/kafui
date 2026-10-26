# -*- coding: utf-8 -*-
from odoo import fields, models, _

class HRPayrollStructureMulticompany(models.Model):
    """inherit model for removing required=True for company field """
    _inherit = "hr.payroll.structure"
    _check_company_auto = True

    company_id = fields.Many2one('res.company', required=False)