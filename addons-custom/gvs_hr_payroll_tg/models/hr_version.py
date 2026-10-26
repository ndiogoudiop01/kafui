# -*- coding: utf-8 -*-
"""
Extension de hr.version (contrat) pour la paie Togo.
Ajoute :
  - forfait_km  : forfait kilométrique mensuel non imposable (FCFA)
  - nb_jours_anciennete_tg : nombre de jours d'ancienneté depuis la date
    d'embauche, utilisé pour le calcul automatique de la prime d'ancienneté.
    Lit dateAnciennete depuis khk_hr_payor si disponible, sinon contract_date_start.

ATTENTION : ne pas utiliser version.date_start comme fallback !
date_start est un champ calculé Odoo 19 qui retourne
max(date_version, contract_date_start). Si la version a été créée ou migrée
APRÈS la date de début du contrat (cas typique pour les employés importés),
date_start renvoie la date de migration au lieu de la date d'embauche réelle,
ce qui donne une ancienneté = 0 et donc une prime nulle.
"""
from odoo import models, fields, api
from datetime import date


class HrVersion(models.Model):
    _inherit = 'hr.version'

    forfait_km = fields.Integer(
        string="Forfait kilométrique non imposable (FCFA/mois)",
        default=0,
        help=(
            "Montant mensuel de l'indemnité kilométrique NON IMPOSABLE.\n"
            "Alimente automatiquement la règle IND_KM_NI du bulletin.\n"
            "Non soumis à CNSS/INAM ni à l'IRPP.\n"
            "Peut être surchargé mois par mois via l'onglet Éléments variables du contrat.\n\n"
            "Pour l'indemnité kilométrique IMPOSABLE (IND_KM, soumise CNSS+IRPP),\n"
            "utiliser l'onglet Éléments variables."
        ),
    )

    nb_jours_anciennete_tg = fields.Float(
        string="Jours d'ancienneté (Togo)",
        compute='_compute_anciennete_tg',
        help=(
            "Nombre de jours écoulés depuis la date d'ancienneté.\n"
            "Utilise « dateAnciennete » (khk_hr_payor) si disponible, "
            "sinon contract_date_start (date de début du contrat stockée)."
        ),
    )

    @api.depends('contract_date_start')
    def _compute_anciennete_tg(self):
        """Calcule le nombre de jours d'ancienneté de façon portable.

        Ordre de priorité pour la date de référence :
        1. dateAnciennete (champ khk_hr_payor) si présent et renseigné
           — vérifié dynamiquement car khk_hr_payor est optionnel
        2. contract_date_start (champ stocké en base, toujours = date réelle)

        NE PAS utiliser date_start : c'est max(date_version, contract_date_start)
        ce qui renvoie la date de migration pour les employés importés, donnant
        une ancienneté nulle même si le contrat remonte à plusieurs années.
        """
        today = date.today()
        for version in self:
            ref = None
            # 1. Préférer dateAnciennete de khk_hr_payor si présente et renseignée
            #    Vérification dynamique : khk_hr_payor est une dépendance optionnelle.
            if 'dateAnciennete' in version._fields and version.dateAnciennete:
                ref = version.dateAnciennete
            # 2. Fallback : contract_date_start (champ stocké, jamais altéré par date_version)
            elif version.contract_date_start:
                ref = version.contract_date_start
            version.nb_jours_anciennete_tg = (today - ref).days if ref else 0.0
