# -*- coding: utf-8 -*-
# Champs communs (bonus, total_bonus, dateAnciennete, typeContract, motif)
# sont maintenant dans gvs_hr_payroll_base.models.hr_version.
# Ce fichier conserve uniquement les champs et méthodes spécifiques Sénégal.

import math
from datetime import datetime, time as t
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class HrVersionSenegal(models.Model):
    """Champs Sénégal sur hr.version : congés, convention collective, ancienneté."""
    _inherit = 'hr.version'

    nb_days = fields.Float(string="Ancienneté (jours)", compute="_get_duration")
    cumul_jour = fields.Float("Cumul jours antérieur")
    cumul_conges = fields.Float("Cumul congés antérieur")
    nbj_aquis = fields.Float("Jours acquis", default=0.0)
    convention_id = fields.Many2one('convention.collective.line', 'Catégorie convention')
    nbj_pris = fields.Float("Jours pris", default=0.0, store=True)
    cumul_mensuel = fields.Float("Cumul mensuel congés")
    last_date = fields.Date("Dernière date")
    alloc_conges = fields.Float(
        "Allocation congés",
        compute="_get_alloc",
        default=0.0,
        store=True,
    )
    nbj_sup = fields.Float("Jours supplémentaires")
    year_extra_day_anciennete = fields.Integer()
    cumul_provision_fin_contrat = fields.Float("Cumul provision fin de contrat")

    def reinit(self):
        for record in self:
            record.cumul_mensuel = record.cumul_mensuel - record.alloc_conges
            record.alloc_conges = 0
            record.nbj_aquis = record.nbj_aquis - record.nbj_pris
            record.nbj_pris = 0

    @api.onchange("convention_id")
    def onchange_categ(self):
        if self.convention_id:
            self.wage = self.convention_id.wage

    def _get_droit(self, provision_conges, provision_fin_contrat):
        for record in self:
            record.cumul_mensuel += provision_conges
            record.cumul_provision_fin_contrat += provision_fin_contrat
            record.nbj_aquis += record.company_id.nbj_alloue

    @api.depends('cumul_mensuel', 'nbj_pris', 'nbj_aquis')
    def _get_alloc(self):
        for record in self:
            if record.nbj_pris != 0 and record.cumul_mensuel != 0 and record.nbj_aquis != 0:
                record.alloc_conges = (
                    record.cumul_mensuel * record.nbj_pris
                ) / record.nbj_aquis
            else:
                record.alloc_conges = 0

    def _get_duration(self):
        for record in self:
            today = datetime.now()
            if record.dateAnciennete:
                dateanciennete = datetime.combine(record.dateAnciennete, t.min)
                dur = today - dateanciennete
                record.nb_days = dur.days
                if dur.days >= 3653:
                    if record.year_extra_day_anciennete:
                        if record.year_extra_day_anciennete != today.year:
                            record.year_extra_day_anciennete = today.year
                            record.write({'nbj_aquis': record.nbj_aquis + 1})
                            record.create_allocation(1, 'Congé ancienneté')
                    else:
                        record.year_extra_day_anciennete = today.year
                        record.write({'nbj_aquis': record.nbj_aquis + 1})
                        record.create_allocation(1, 'Congé ancienneté')
            else:
                record.nb_days = 0

    def create_allocation(self, nb_jour, lib):
        for record in self:
            leave_type = self.env['hr.leave.type'].search(
                [('paid_legal_leave', '=', True)], order="id desc", limit=1,
            )
            self.env['hr.leave.allocation'].create({
                'name': lib,
                'holiday_status_id': leave_type.id,
                'number_of_days': nb_jour,
                'employee_id': record.employee_id.id,
            })
