# -*- coding: utf-8 -*-
from odoo.exceptions import AccessError, UserError
from odoo import api, fields, models, _


class ResConfigSettings(models.Model):
    _inherit = 'res.config.settings'
    
    payroll_chart_template = fields.Many2one(related='company_id.payroll_chart_template', string='Payroll Template', readonly=False)
    
    @api.multi
    def set_values(self):
        """ install a chart of accounts for the given company (if required) """
        if self.payroll_chart_template:
            self.payroll_chart_template.load_for_current_company()
        super(ResConfigSettingsInherit, self).set_values()