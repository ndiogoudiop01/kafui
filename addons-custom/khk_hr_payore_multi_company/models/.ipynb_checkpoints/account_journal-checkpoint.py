# -*- coding: utf-8 -*-
from odoo import fields, models, _

class HRAccountJournal(models.Model):
    """inherit model for removing required=True for company field """
    _inherit = "account.journal"

    company_id = fields.Many2one('res.company', required=False)