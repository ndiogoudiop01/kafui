from odoo import models, fields


class ResConfigSettingsInherit(models.TransientModel):
    _inherit = "res.config.settings"

    nbj_alloue = fields.Float(related='company_id.nbj_alloue', string="Nombre de jour alloue",
                              readonly=False)
    nbj_travail = fields.Float(related='company_id.nbj_travail', string="Nombre de jour de travail",
                               readonly=False)
