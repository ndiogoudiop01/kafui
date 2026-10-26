# -*- coding: utf-8 -*-
{
    'name': "GVS HR Payroll Burkina Faso",
    'version': '19.0.1.0.0',
    'category': 'Human Resources/Payroll',
    'summary': "Paie Burkina Faso — IUTS, CNSS, FSP, charges patronales",
    'description': """
Module de paie pour le Burkina Faso.

Dépend de gvs_hr_payroll_base pour les éléments variables du contrat.

Structure salariale unique BF_PAIE :
  - Salaire de base + sursalaire + heures supplémentaires (20 %, 40 %)
  - Prime d'ancienneté calculée automatiquement : 1 % par année de service,
    plafonnée à 25 % (Convention Collective Interprofessionnelle BF)
  - Rémunération brute = gains imposables + indemnités exonérées
  - CNSS salarié : 5,5 % plafonné à 66 667 FCFA/mois (800 000 FCFA/an)
  - Abattement forfaitaire : 20 % des gains imposables
  - IUTS barème progressif annuel (base annualisée × 12, calcul, ÷ 12) :
      0 %   → 0 – 415 000 FCFA
      12 %  → 415 001 – 700 000 FCFA
      20 %  → 700 001 – 1 400 000 FCFA
      27 %  → 1 400 001 – 1 900 000 FCFA
      33 %  → 1 900 001 – 2 650 000 FCFA
      38 %  → 2 650 001 – 3 300 000 FCFA
      40 %  → > 3 300 000 FCFA
  - FSP : 1 % du Net Fiscal (Brut − CNSS − IUTS)
  - Charges patronales : CNSS retraite 16 %, CNSS PF 5,5 % (total 21,5 %)
    sur base plafonnée 66 667 FCFA/mois
  - Indemnités exonérées : logement, transport, fonction

Isolation pays : toutes les règles ont country_id = BF — invisibles des
sociétés CI, TG et autres pays (via ir.rule dans gvs_hr_payroll_base).
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
        'report/report_bulletin_paie_bf.xml',
    ],
    'application': False,
    'installable': True,
    'auto_install': False,
}
