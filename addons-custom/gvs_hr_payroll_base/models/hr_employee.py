# -*- coding: utf-8 -*-
from datetime import date
from odoo import models, fields, api, _


class HrEmployeeBase(models.Model):
    """Extension partagée de hr.employee.

    Ajoute :
    - relation_ids : relations familiales détaillées (utilisées par khk_hr_payor
      pour le calcul IR/TRIMF Sénégal).
    - nb_charge : nombre de personnes à charge calculé depuis les champs natifs
      Odoo (état civil + enfants à charge). Utilisable par tous les modules pays.
    - action_open_contract : ouvre le contrat (hr.version) depuis la fiche employé.
    """
    _inherit = 'hr.employee'

    relation_ids = fields.One2many(
        'relation.famille', 'employee_id',
        string='Famille',
    )

    nb_charge = fields.Integer(
        string="Personnes à charge",
        compute='_compute_nb_charge',
        store=True,
        help=(
            "Calculé depuis les relations familiales (onglet Famille) :\n"
            "• Conjoint non salarié : +1\n"
            "• Enfant de moins de 18 ans : +1 (date de naissance obligatoire)\n"
            "Plafonné à 6 personnes.\n"
            "Utilisé par les règles IRPP Togo (abattement 10 000 FCFA/mois/personne)."
        ),
    )

    @api.depends(
        'relation_ids',
        'relation_ids.type',
        'relation_ids.birth',
        'relation_ids.salari',
    )
    def _compute_nb_charge(self):
        """Calcul des personnes à charge depuis la table relation.famille.

        Règles communes à tous les modules pays :
          • Conjoint non salarié  → +1
          • Enfant < 18 ans       → +1  (date de naissance obligatoire)
          • Plafonné à 6

        Pour Togo  : nb_charge → abattement IRPP 10 000 FCFA/mois par personne.
        Pour Sénégal : nb_charge est informatif (IR/TRIMF utilisent les champs ir/trimf).
        """
        today = date.today()
        for emp in self:
            count = 0
            for rel in emp.relation_ids:
                if rel.type == 'conjoint' and not rel.salari:
                    count += 1
                elif rel.type == 'enfant' and rel.birth:
                    age_days = (today - rel.birth).days
                    if age_days < 6570:  # 18 années × 365 jours
                        count += 1
            emp.nb_charge = min(count, 6)

    def action_open_contract(self):
        """Ouvre le(s) contrat(s) de l'employé (hr.version) depuis sa fiche.

        - 1 contrat  → ouvre directement en vue formulaire
        - N contrats → ouvre la liste filtrée par employé
        """
        self.ensure_one()
        form_view = self.env.ref(
            'hr.hr_contract_template_form_view',
            raise_if_not_found=False,
        )
        versions = self.version_ids

        action = {
            'type': 'ir.actions.act_window',
            'name': _('Contrat(s) — %s') % self.name,
            'res_model': 'hr.version',
            'domain': [('employee_id', '=', self.id)],
            'context': {'default_employee_id': self.id},
        }

        if len(versions) == 1:
            action['view_mode'] = 'form'
            action['res_id'] = versions.id
            action['views'] = [(form_view.id if form_view else False, 'form')]
        else:
            action['view_mode'] = 'list,form'
            action['views'] = [
                (False, 'list'),
                (form_view.id if form_view else False, 'form'),
            ]

        return action
