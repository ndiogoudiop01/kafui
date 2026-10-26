# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Nikhil krishnan(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <https://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import fields, models, tools, api


class PayrollReportView(models.Model):
    _name = 'hr.global.report.view'
    _auto = False

    name = fields.Many2one('hr.employee', string='Employé')
    date_from = fields.Date(string='Date du bulletin')
    date_to = fields.Date(string='Date au:')
    state = fields.Selection([('draft', 'Draft'), ('verify', 'Waiting'), ('done', 'Done'), ('cancel', 'Rejected')],string='Status')
    job_id = fields.Many2one('hr.job', string='Job Title')
    company_id = fields.Many2one('res.company', string='Company')
    department_id = fields.Many2one('hr.department', string='Department')
    total = fields.Float(string='Salaire NET')
    number_of_hours = fields.Float(string='Heures travaillées')
    cin = fields.Char(string="Numéro CIN")	
    first_name = fields.Char(string="Prénom", required=False)
    last_name = fields.Char(string="Nom", required=False)	
    matricule_cnss = fields.Char(string="Numéro inps")		
    situation = fields.Selection([('SO', 'SO'), ('DE', 'DE'), ('IT', 'IT'), ('IL', 'IL'), ('AT', 'AT'), ('CS', 'CS'), ('MS', 'MS'), ('MP', 'MP')], 'Situation ')		
    number = fields.Char(string='Reférence') 
    category_id = fields.Many2one('hr.salary.rule.category', string='Catégorie')  
    code = fields.Char(string='code')
    embauche = fields.Date(string="Date d'embauche") 
	

    def _select(self):
        select_str = """
        min(ps.id) as id,
		emp.id as name,
		emp.first_name as first_name,
		emp.last_name as last_name,		
		jb.id as job_id,
        dp.id as department_id,
		cmp.id as company_id,		
        ps.date_from as date_from , 
		ps.date_to as date_to, 
		psl.total as total,
		ps.number as number,		
		ps.state as state,
        emp.cin as cin,
		emp.matricule_cnss,
		wd.number_of_hours as number_of_hours,
        psl.category_id as category_id,
        psl.salary_rule_id as salary_rule_id,
        rc.code as code,
        ct.situation as situation, 		
        ct.date_start as embauche      
	
        """
        return select_str

    def _from(self):
        from_str = """
            hr_payslip_line psl  
			left join hr_payslip ps on (ps.employee_id=psl.employee_id and ps.id=psl.slip_id)
            left join hr_employee emp on (ps.employee_id=emp.id)
			left join hr_department dp on (emp.department_id=dp.id)
            left join hr_job jb on (emp.department_id=jb.id)
			left join hr_payslip_worked_days wd on (psl.slip_id=wd.payslip_id)
			LEFT JOIN hr_salary_rule_category AS rc on (psl.category_id = rc.id)
			left join hr_contract ct on (ps.employee_id=ct.id)
			left join res_company cmp on (cmp.id=ps.company_id) 
	WHERE  rc.code ='NET' 
			
			
         """
        return from_str

    def _group_by(self):
        group_by_str = """
            group by 
			emp.id,
			emp.first_name,
			emp.last_name,
			ps.number,
			psl.total,
			ps.date_from, 
			ps.date_to,
			ps.state,
			jb.id,
			dp.id,cmp.id,
			wd.id,
			wd.number_of_days,emp.cin,
			rc.code,	
			psl.category_id,
			ct.situation,
			ct.date_start,			
			psl.salary_rule_id


		ORDER BY
         emp.last_name 
		 """
	
        return group_by_str


    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as ( SELECT
               %s
               FROM %s
               %s
               )""" % (self._table, self._select(), self._from(), self._group_by()))

