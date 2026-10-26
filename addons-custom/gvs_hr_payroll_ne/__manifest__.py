{
    'name': 'GVS Payroll Niger',
    'version': '19.0.1.0.0',
    'category': 'Payroll',
    'summary': 'Règles de paie conformes à la législation nigérienne',
    'author': 'Groupe La Visibilité SAS',
    'depends': ['om_hr_payroll', 'gvs_hr_payroll_base'],
    'data': [
        'security/ir.model.access.csv',
        'data/hr_payroll_category_data.xml',
        'data/hr_salary_rule_data.xml',
        'data/hr_rule_input_data.xml',
        'data/hr_payroll_structure_data.xml',
        'report/report_bulletin_paie_ne.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
}
