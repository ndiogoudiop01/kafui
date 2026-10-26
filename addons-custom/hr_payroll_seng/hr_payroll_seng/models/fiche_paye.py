# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields
from datetime import date
from dateutil.relativedelta import relativedelta
from datetime import timedelta


class FichePayeParser(models.AbstractModel):
    _name = 'report.hr_payroll_seng.report_l10n_ma_fiche_paye'

    def get_payslip_lines(self, objs):
        res = []
        ids = []
        for item in objs:
            if item.appears_on_payslip is True and not item.salary_rule_id.parent_rule_id:
                ids.append(item.id)
        if ids:
            res = self.env['hr.payslip.line'].browse(ids)
        return res
    @api.model
    def get_total_by_rule_category(self, obj, code):
        category_total = 0
        category_id = self.env['hr.salary.rule.category'].search([('code', '=', code)], limit=1).id
        if category_id:
            line_ids = self.env['hr.payslip.line'].search([('slip_id', '=', obj.id), ('category_id', 'child_of', category_id)])
            for line in line_ids:
                category_total += line.total
        return category_total
		
    @api.model
    def get_annual_total_by_rule_category(self, obj, code):
        category_total = 0
        category_id = self.env['hr.salary.rule.category'].search([('code', '=', code)], limit=1).id
        if category_id:
            line_ids = self.env['hr.payslip.line'].search([('slip_id', '=', obj.id), ('category_id', 'child_of', category_id)])
            for line in line_ids:
                category_total += line.total_ytd
        return category_total

    date_payment = fields.Date(default=fields.Date.today)	

    @api.model
    def compute_sheets(self):
        self.ensure_one()	
        res = super(HrPayslip, self).compute_sheets()
        self.compute_total_ytds()
        return res

    @api.model
    def compute_total_ytds(self):
        if not self.line_ids:
            return

        query = (
            """SELECT pl_1.id, sum(
                case when p.credit_note then -pl_2.amount else pl_2.amount end)
            FROM hr_payslip_line pl_1, hr_payslip_line pl_2, hr_payslip p
            WHERE pl_1.id IN %(payslip_line_ids)s
            AND pl_1.salary_rule_id = pl_2.salary_rule_id
            AND pl_2.slip_id = p.id
            AND p.employee_id = %(employee_id)s
            AND p.company_id = %(company_id)s
            AND (p.state = 'draft' OR p.state = 'done' OR p.id = %(payslip_id)s)

            GROUP BY pl_1.id
            """)

        date_payment = fields.Date.from_string(self.datepaiem)
        date_from = fields.Date.to_string(datetime(date_payment.year, 1, 1))

        cr = self.env.cr

        cr.execute(query, {
            'date_from': date_from,
            'date_to': self.date_payment,
            'payslip_line_ids': tuple(self.line_ids.ids),
            'employee_id': self.employee_id.id,
            'company_id': self.company_id.id,
            'payslip_id': self.id,
        })

        res = cr.fetchall()

        line_model = self.env['hr.payslip.line']

        for (line_id, total_ytd) in res:
            line = line_model.browse(line_id)
            line.total_ytd = total_ytd

    @api.model
    def total_ytd(self, total):
        """
        Get the total amount since the beginning of the year
        of a given salary rule code.

        :param code: salary rule code
        :return: float
        """
        self.ensure_one()

        date_slip = fields.Date.from_string(self.date_to)
        date_from = to_string(datetime(date_slip.year, 1, 1))

        query = (
            """SELECT sum(
                case when p.credit_note then -pl.total else pl.total end)
            FROM hr_payslip_line as pl, hr_payslip as p
            WHERE pl.slip_id = p.id
            AND pl.total = %(total)s
            AND p.employee_id = %(employee_id)s
            AND p.company_id = %(company_id)s
      
            """
        )

        cr = self.env.cr

        cr.execute(query, {
            'date_from': date_from,
            'date_to': self.date_payment,
            'company_id': self.company_id.id,
            'employee_id': self.employee_id.id,
            'total': total,
        })

        return cr.fetchone()[0] or 0





		
    def get_employe_line(self, obj, parent_line):
        return self.env['hr.payslip.line'].search([('slip_id', '=', obj.id), ('salary_rule_id.parent_rule_id.id', '=', parent_line.salary_rule_id.id)], limit=1)
    
    def get_employer_line(self, obj, parent_line):
        return self.env['hr.payslip.line'].search([('slip_id', '=', obj.id), ('salary_rule_id.parent_rule_id.id', '=', parent_line.salary_rule_id.id)], limit=1)
		                                  
    @api.model
    def _get_report_values(self, docids, data=None):
        payslip = self.env['hr.payslip'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'hr.payslip',
            'data': data,
            'docs': payslip,
            'lang': "fr_FR",
            'get_payslip_lines': self.get_payslip_lines,			
            'get_total_by_rule_category': self.get_total_by_rule_category,
            'get_annual_total_by_rule_category': self.get_annual_total_by_rule_category,			
            'get_employe_line': self.get_employe_line,
            'get_employer_line': self.get_employer_line,	
        }
