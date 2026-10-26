# -*- coding: utf-8 -*-
{
    'name': "GVS HR Payroll Côte d'Ivoire",
    'version': '19.0.1.0.0',
    'category': 'Human Resources/Payroll',
    'summary': "Paie Côte d'Ivoire — ITS, CNPS, CMU, charges patronales",
    'description': """
Module de paie pour la Côte d'Ivoire.

Dépend de gvs_hr_payroll_base pour les éléments variables du contrat.

Deux structures salariales (CI_CADRE / CI_NC) :
  - Salaire de base + sursalaire + heures supplémentaires (15 %, 50 %, 100 %)
  - Prime d'ancienneté (taux saisi manuellement via ANC_TX)
  - Brut imposable = BASIC + ALW
  - ITS barème progressif 2024 (75k/240k/800k/2,4M/8M) — RICF déduit de la fiche employé
  - CNPS retraite : 6,3 % salarié / 7,7 % employeur — plafond 3 375 000 FCFA
  - CMU : 500 FCFA/personne/côté — effectif automatique depuis fiche employé
  - Charges patronales : IS 1,2 %, Taxe apprentissage 0,4 %, FPC 0,6 %,
    PF 5,75 %, AT 3 % (plafond 75 000 FCFA)
  - Primes non imposables : transport (30 000), fonction (saisie)
  - Arrondi net à la centaine la plus proche

Isolation pays : toutes les règles ont country_id = CI — invisibles des
sociétés Togo et autres pays (via ir.rule dans gvs_hr_payroll_base).
    """,
    'author': 'GVS',
    'website': '',
    'license': 'LGPL-3',
    'depends': [
        'om_hr_payroll',
        'gvs_hr_payroll_base',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/hr_payroll_category_data.xml',
        'data/hr_salary_rule_data.xml',
        'data/hr_rule_input_data.xml',
        'data/hr_payroll_structure_data.xml',
        'report/report_bulletin_paie_ci.xml',
    ],
    'application': False,
    'installable': True,
    'auto_install': False,
}
