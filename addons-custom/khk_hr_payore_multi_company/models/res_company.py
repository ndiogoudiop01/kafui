# -*- coding: utf-8 -*-
from odoo.exceptions import AccessError, UserError
from odoo import fields, models, _


class ResCompany(models.Model):
    _inherit = "res.company"
    _check_company_auto = True

    payroll_chart_template = fields.Many2one('payroll.chart.template')