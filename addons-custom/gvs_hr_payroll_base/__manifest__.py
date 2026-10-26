# -*- coding: utf-8 -*-
{
    'name': 'GVS HR Payroll Base',
    'version': '19.0.1.2.0',
    'category': 'Human Resources/Payroll',
    'summary': 'Socle commun pour les modules de paie GVS multi-pays',
    'description': """
Module socle partagé par tous les modules de paie GVS (Togo, Sénégal, etc.).

Fournit :
  • Modèle hr.employee.bonus — éléments variables saisis sur le contrat
  • Modèle relation.famille — famille de l'employé (conjoint, enfants)
  • Champ is_prorata sur hr.salary.rule
  • Champ company_id sur hr.payroll.structure (filtrage multi-société/pays)
  • Onglet "Éléments variables" sur le contrat (hr.version)
  • Onglet "Famille" sur la fiche employé
  • Override _get_payslip_lines : lecture des bonus → injection amount_fix
  • Champs dateAnciennete, typeContract, motif sur hr.version
    """,
    'author': 'GVS',
    'license': 'LGPL-3',
    'depends': ['om_hr_payroll'],
    'data': [
        'security/ir.model.access.csv',
        'data/hr_payroll_category_shared.xml',
        'views/employee_bonus_views.xml',
        'views/hr_employee_views.xml',
        'views/hr_payroll_structure_views.xml',
    ],
    'application': False,
    'installable': True,
    'auto_install': False,
}
