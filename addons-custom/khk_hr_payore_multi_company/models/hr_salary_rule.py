# -*- coding: utf-8 -*-
from odoo import fields, models, _


class HrSalaryCategoryMultiCompany(models.Model):
    """inherit model for removing required=True for company field """
    _inherit = 'hr.salary.rule.category'
    _check_company_auto = True

    company_id = fields.Many2one('res.company', 'Company', copy=False,
                                 default=lambda self: self.env.company.id)
    
    