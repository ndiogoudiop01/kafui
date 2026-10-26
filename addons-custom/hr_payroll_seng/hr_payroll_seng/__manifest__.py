#-*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Paie Sénégal V17',
    'version': '17.0.1.0.0',
    'category': 'Payroll',
    'sequence': 38,
    'author': 'Paiesoft',
	'website': 'https://paieafricaine.online',
	'live_test_url': 'https://paiesoft.casa',
	'support': 'contact@paieafricaine.online',	
    'summary': """
Le module qu'il vaut faut pour traiter la paie du Sénégal en toute tranquillité sous odoo 17-nouveaux palfonds CSS IPRESS et Tranches IR
""",
	'license': 'OPL-1',
	'currency': 'EUR',
	'price': 899.00,	
	
	'description': """
        Paie sénégalaise : Odoo entreprise V17 conforme ** 2024**,
        Paie,
        Payroll,
        Senegal payroll,
        Odoo apps,
        Déclarations CSS IPRES,
        HR ,
        Paie africaine,
        Sénégal,
        Odoo payroll,

 
""",
    'depends': ['hr_payroll','hr_attendance','hr_payroll_attendance','hr_holidays'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_contract_views.xml',
        'views/hr_employee_views.xml',
        'views/hr_company_view.xml',		
        'data/hr_payroll_sequence.xml',
        'data/hr_payroll_categ_data.xml',
        'data/hr_payroll_data.xml',			
        'data/hr_employee_sequence.xml', 
        'data/hr_contract_sequence.xml', 		
        'data/css_sequence.xml',	
        'data/report_paperformat.xml',
		
        'report/menu_report.xml',
        'views/l10n_ma_hr_payroll_report.xml',
        'views/cnss_view.xml',	
        'report/paie_report_pat.xml',	
        'report/cert_stage.xml',	
        'report/cert_travail.xml',	
        'report/certificate_report.xml',	
        'report/certificate_template.xml',	
        'report/report_l10n_ma_fiche_paye.xml',	
        'report/cnss_report.xml',
        'views/paie_view.xml',	
        'report/paie_report_decompte.xml',	
        'report/selon_mode_paie.xml',	
		
],
	
    'images': ['static/description/banner.png'],
    'installable': True,	
}
