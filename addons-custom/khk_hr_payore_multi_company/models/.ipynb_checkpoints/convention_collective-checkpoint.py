# -*- coding: utf-8 -*-
from odoo import fields, models, _

class ConventionCollectiveInherit(models.Model):
    """inherit model for adding company_id field"""
    _inherit = "convention.collective"

    company_id = fields.Many2one('res.company', 'Company', copy=False, readonly=True,
                                 default=lambda self: self.env.user.company_id)
    
    
class ConventionCollectiveLine(models.Model):
    """inherit model for adding company_id field"""
    _inherit = "convention.collective.line"

    company_id = fields.Many2one('res.company', 'Company', copy=False, readonly=True,
                                 default=lambda self: self.env.user.company_id)