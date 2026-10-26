# -*- coding: utf-8 -*-
{
    'name': "GVS HR Payroll Multi-Société",

    'summary': """
        Support multi-société pour l'ensemble des modules de paie GVS.
    """,

    'description': """
        Module transversal multi-société pour la paie GVS :
        - Visibilité des bulletins de toutes les sociétés sélectionnées
        - Filtrage des règles salariales et structures par société courante
        - Règles de sécurité multi-société sur hr.payslip, hr.payslip.run
        Ce module s'appuie sur gvs_hr_payroll_base et fonctionne avec tous les
        modules pays GVS (Togo, Sénégal, autres).
    """,

    'author': "KHK Consulting",
    'website': "http://www.khk-consulting.com",
    'license': 'LGPL-3',

    'category': 'Human Resources/Payroll',
    'version': '19.0.1.0.0',

    'depends': ['gvs_hr_payroll_base'],

    'data': [
        'security/security.xml',
    ],
}
