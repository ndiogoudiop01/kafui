# -*- coding: utf-8 -*-
from odoo import models, fields, api


class HrSalaryRuleBase(models.Model):
    """Ajoute is_prorata et country_id sur hr.salary.rule.

    - is_prorata : contrôle la proratisation des éléments variables
    - country_id : pays d'appartenance de la règle (champ direct, non calculé)

    Le country_id est défini EXPLICITEMENT dans les fichiers data de chaque
    module pays (ex. gvs_hr_payroll_tg définit country_id=Togo sur ses règles).
    On n'utilise plus un champ calculé depuis company_id car les règles sont
    globales (company_id=False) : country_id calculé serait toujours False,
    rendant toutes les règles visibles partout.

    Ir.rule (hr_payroll_structure_views.xml) :
      ['|', ('country_id', '=', False),              ← règles universelles
            ('country_id', '=', user.company_id.country_id.id)]  ← règles pays
    """
    _inherit = 'hr.salary.rule'

    is_prorata = fields.Boolean(
        string='Prorata',
        default=True,
        help="Si coché, le montant de l'élément variable est proratisé par "
             "les jours WORK100 / 30 lors du calcul du bulletin.",
    )

    country_id = fields.Many2one(
        'res.country',
        string='Pays',
        help="Pays auquel appartient la règle salariale. "
             "Laisser vide pour une règle universelle (visible partout). "
             "Définir explicitement dans le fichier data du module pays.",
    )


class HrSalaryRuleCategoryBase(models.Model):
    """Ajoute country_id direct sur hr.salary.rule.category pour filtrage par pays."""

    _inherit = 'hr.salary.rule.category'

    country_id = fields.Many2one(
        'res.country',
        string='Pays',
        help="Pays auquel appartient la catégorie de règle salariale. "
             "Laisser vide pour une catégorie universelle (visible partout). "
             "Définir explicitement dans le fichier data du module pays.",
    )


class HrPayrollStructureBase(models.Model):
    """Ajoute country_id sur hr.payroll.structure et rend company_id optionnel.

    company_id devient required=False pour permettre des structures globales
    (multi-pays, company_id=False). La visibilité par société est gérée via
    ir.rule sur country_id.
    """

    _inherit = 'hr.payroll.structure'

    # Override pour permettre les structures globales (company_id=False)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=False,
        default=lambda self: self.env.company,
    )

    country_id = fields.Many2one(
        'res.country',
        string='Pays',
        help="Pays auquel appartient la structure de paie. "
             "Laisser vide pour une structure universelle (visible partout). "
             "Définir explicitement dans le fichier data du module pays.",
    )
