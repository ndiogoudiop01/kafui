# -*- coding: utf-8 -*-
{
    'name': "GVS HR Payroll Sénégal",

    'summary': "Paie Sénégal — IPRES, CSS, TRIMF, IR",

    'description': """
Module de paie pour le Sénégal.
Convention collective, IPRES, CSS, TRIMF, IR sur salaires.
Dépend de gvs_hr_payroll_base pour les mécaniques communes
(éléments variables sur contrat, famille, filtrage multi-pays).
    """,

    'author': "GVS",
    'website': "",

    'category': 'Human Resources/Payroll',
    'version': '19.0.2.0',
    'license': 'LGPL-3',

    'depends': ['om_hr_payroll', 'gvs_hr_payroll_base'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/convention_collective_data.xml',
        'data/salary_rule_data.xml',
        'data/custom_format_paper.xml',
        'static/src/css/my_css.xml',
        'views/convention_collective_views.xml',
        'views/employee_bonus_views.xml',
        'views/hr_employee_inherit_views.xml',
        'views/hr_salary_rule_inherit.xml',
        'views/res_company_inherit_views.xml',
        'views/report_bulletin_paie.xml',
        'views/custom_external_layout_bulletin.xml',
        'wizard/cotisation_ipres.xml',
        'views/report_cotisation_ipres.xml',
        'wizard/securite_sociale.xml',
        'views/report_securite_sociale.xml',
        'wizard/declaration_retenues.xml',
        'views/report_declaration_retenues.xml',
        'wizard/transfer_order.xml',
        'views/report_transfer_order.xml',
        'views/menu_reports.xml',
        'views/res_config_settings_inherit_view.xml',
        'views/hr_leave_type_inherit.xml',
        'views/hr_payslip_inherit.xml',
        'views/hr_payslip_run_inherit.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
