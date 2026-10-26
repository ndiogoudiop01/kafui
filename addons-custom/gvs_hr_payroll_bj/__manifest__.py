# -*- coding: utf-8 -*-
{
    'name': "GVS HR Payroll Bénin",
    'version': '19.0.1.0.0',
    'category': 'Human Resources/Payroll',
    'summary': "Paie Bénin — ITS, CNSS, VPS, charges patronales",
    'description': """
Module de paie pour le Bénin.

Dépend de gvs_hr_payroll_base pour les éléments variables du contrat.

Structure salariale unique BJ_PAIE :
  - Salaire de base proraté NB_JOURS / 30 (défaut 30 jours)
  - Prime d'ancienneté automatique depuis date_start (1 %/an, plafond 25 %)
    — Source : Code du Travail Bénin (Loi 98-004)
  - Éléments imposables : sursalaire, frais de communication, congés
  - Éléments non imposables : indemnité de fonction, indemnité de transport
  - Brut imposable = BASIC + ALW
  - ITS barème mensuel progressif (CGI Bénin — à confirmer) :
      10 % → 0 – 50 000 FCFA
      13 % → 50 001 – 130 000 FCFA
      15 % → 130 001 – 280 000 FCFA
      19 % → 280 001 – 530 000 FCFA
      28 % → > 530 000 FCFA
  - CNSS Assurance vieillesse : 3,6 % salarié / 6,4 % patronal
  - CNSS Risques professionnels : 0 % salarié / 1 % patronal
  - CNSS Prestations familiales : 0 % salarié / 9 % patronal
  - VPS (Versement Patronal de Solidarité) : 4 % patronal
  - SRTB : optionnel (saisi via Autres entrées)

Isolation pays : toutes les règles ont country_id = BJ — invisibles des
sociétés CI, BF, TG et autres pays (via ir.rule dans gvs_hr_payroll_base).
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
        'report/report_bulletin_paie_bj.xml',
    ],
    'application': False,
    'installable': True,
    'auto_install': False,
}
