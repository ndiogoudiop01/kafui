# -*- coding: utf-8 -*-
{
    'name': 'GVS HR Payroll Togo',
    'version': '19.0.2.5.0',
    'category': 'Human Resources/Payroll',
    'summary': 'Paie Togo — CNSS/INAM, IRPP, charges patronales',
    'description': """
Module de paie pour le Togo (Afrique de l'Ouest).

Dépend de gvs_hr_payroll_base pour :
  - Les éléments variables sur le contrat (hr.employee.bonus)
  - L'onglet Famille (relation.famille)

Règles spécifiques Togo (structure unique TG_MENS) :
  - Salaire de base = contract.wage × TECH_JOURS / 30
  - Indemnité kilométrique : allocation imposable (ALW), saisie mensuelle
    via les éléments variables du contrat
  - Prime d'ancienneté :
      0% avant 2 ans | 2% de 2 à 3 ans
      ≥ 4 ans : 2% + 1%/an au-delà de 3 ans, plafonné à 35%
  - CNSS + INAM 9 % salarié, 17,5 % patronal (sans plafond)
  - IRPP barème progressif 2023 (annualisé, abattement 28 %)
  - Personnes à charge : 10 000 FCFA/mois, max 6

Règles/structures/catégories globales (company_id=False) : visibles par
toutes les sociétés, s'appliquent aux contrats avec structure TG_MENS.
Bulletins et employés restent liés à leur société.
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
        'views/hr_payslip_views.xml',
        'views/hr_employee_views.xml',
        'report/report_bulletin_paie_tg.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'application': False,
    'installable': True,
    'auto_install': False,
}
