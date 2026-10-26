# -*- coding: utf-8 -*-
from datetime import datetime, time as t
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class HrVersionBase(models.Model):
    """Extension partagée de hr.version (contrat) pour tous les pays GVS.

    Fournit :
      • bonus        : liste des éléments variables du contrat
      • total_bonus  : somme des éléments variables actifs
      • dateAnciennete, typeContract, motif : champs communs tous pays
    """
    _inherit = 'hr.version'

    # ── Éléments variables ──────────────────────────────────────────────────
    bonus = fields.One2many(
        'hr.employee.bonus', 'version_id',
        string='Éléments variables',
        domain=[('state', '=', 'active')],
    )
    total_bonus = fields.Float(
        string='Total éléments variables',
        compute='_compute_total_bonus',
        store=True,
    )

    @api.depends('bonus.amount')
    def _compute_total_bonus(self):
        now = datetime.now()
        for version in self:
            total = 0.0
            for b in version.bonus:
                if b.date_from and b.date_to:
                    if (datetime.combine(b.date_from, t.min)
                            <= now
                            <= datetime.combine(b.date_to, t.max)):
                        total += b.amount
            version.total_bonus = total

    # ── Champs communs tous pays ─────────────────────────────────────────────
    dateAnciennete = fields.Date(
        string="Date d'ancienneté",
        default=lambda self: fields.Date.today(),
        help="Date de référence pour le calcul de l'ancienneté (prime, congés).",
    )
    typeContract = fields.Selection([
        ('cdi', 'CDI'),
        ('cdd', 'CDD'),
        ('others', 'Autres'),
    ], string='Type de contrat')
    motif = fields.Selection([
        ('demission', 'Démission'),
        ('fin', 'Fin de contrat'),
        ('retraite', 'Retraite'),
        ('licenciement', 'Licenciement'),
        ('deces', 'Décès'),
        ('depart_negocie', 'Départ négocié'),
    ], string='Motif de sortie')
