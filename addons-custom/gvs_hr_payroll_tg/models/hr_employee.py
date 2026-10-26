# -*- coding: utf-8 -*-
"""
Extension de hr.employee pour la paie Togo.

Ajoute :
  - is_tg_payroll : booléen calculé si la société de l'employé est au Togo
                    (code pays 'TG'). Utilisé pour la visibilité conditionnelle
                    dans l'onglet Famille et le groupe Paramètres RH.

Le calcul de nb_charge (personnes à charge) est désormais géré dans
gvs_hr_payroll_base et s'applique à tous les modules pays :
  • Conjoint non salarié → +1
  • Enfant < 18 ans      → +1
  • Plafonné à 6
"""
from odoo import models, fields


class HrEmployeeTogo(models.Model):
    _inherit = 'hr.employee'

    # ── Indicateur pays Togo ─────────────────────────────────────────────────
    is_tg_payroll = fields.Boolean(
        compute='_compute_is_tg_payroll',
        help="Vrai si la société de l'employé est au Togo (code pays 'TG')."
             " Utilisé pour la visibilité de l'onglet Famille et du groupe Paie Togo.",
    )

    def _compute_is_tg_payroll(self):
        for emp in self:
            emp.is_tg_payroll = (
                emp.company_id.country_id.code == 'TG'
                if emp.company_id and emp.company_id.country_id
                else False
            )
