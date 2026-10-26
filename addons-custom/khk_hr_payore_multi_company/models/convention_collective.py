# -*- coding: utf-8 -*-
from odoo import fields, models, _

class ConventionCollectiveInherit(models.Model):
    """inherit model for adding company_id field"""
    _inherit = "convention.collective"
    _check_company_auto = True

    company_id = fields.Many2one('res.company', 'Company', copy=False,
                                 default=lambda self: self.env.company.id)
    
    
class ConventionCollectiveLine(models.Model):
    """inherit model for adding company_id field"""
    _inherit = "convention.collective.line"
    _check_company_auto = True

    company_id = fields.Many2one('res.company', 'Company', copy=False, readonly=True, related="conv_id.company_id")