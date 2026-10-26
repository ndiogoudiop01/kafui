# -*- coding: utf-8 -*-
from odoo.exceptions import AccessError, UserError
from odoo import api, fields, models, _


class ResCompany(models.Model):
    _inherit = "res.company"

    payroll_chart_template = fields.Many2one('payroll.chart.template')