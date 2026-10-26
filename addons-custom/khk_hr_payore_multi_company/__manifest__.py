# -*- coding: utf-8 -*-
{
    'name': "SN PAYORE MULTI COMPANY",

    'summary': """
        Multi-company support for Senegalese payroll module (khk_hr_payor)
    """,

    'description': """
        Adds multi-company support to the khk_hr_payor Senegalese payroll module:
        - Payroll chart template system to duplicate salary rules per company
        - Company filtering on payslip batches, structures, salary rules
        - Multi-company security rules
    """,

    'author': "KHK Consulting",
    'website': "http://www.khk-consulting.com",
    'license': 'LGPL-3',

    'category': 'Payroll',
    'version': '19.0.1.0',

    'depends': ['base', 'khk_hr_payor'],

    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/payroll_chart_data.xml',
        'views/res_config_settings_views.xml',
        'views/hr_payslip_run_views.xml',
        'views/res_company_views.xml',
        'views/salary_rule_category.xml',
        'views/convention_collective.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
}
