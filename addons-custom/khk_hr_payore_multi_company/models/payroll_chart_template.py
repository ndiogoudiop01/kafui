# -*- coding: utf-8 -*-
from odoo.exceptions import AccessError, UserError
from odoo import fields, models, _


class PayrollChartTemplate(models.Model):
    _name = "payroll.chart.template"
    _description = "Payroll Chart Template"

    name = fields.Char('Name')

    def load_for_current_company(self):
        """
        Installs payroll salary rules on the current company, replacing
        the existing one if it had already one defined.

        Only administrators can run this. The first company (id=1) is protected.
        """
        self.ensure_one()
        company = self.env.company
        # Work in the company's language
        self = self.with_context(lang=company.partner_id.lang)
        if not self.env.user._is_admin():
            raise AccessError(_("Only administrators can load a payroll chart template"))

        if company.id == 1:
            raise UserError(_('Cannot change salary rules for the first/main company'))

        # Delete existing salary rule inputs then rules for this company
        for rule in self.env['hr.salary.rule'].search([('company_id', '=', company.id)]):
            rule_inputs = self.env['hr.rule.input'].search([('input_id', '=', rule.id)])
            rule_inputs.unlink()
        self.env['hr.salary.rule'].search([('company_id', '=', company.id)]).unlink()

        # Delete existing salary rule categories for this company
        self.env['hr.salary.rule.category'].sudo().search(
            [('company_id', '=', company.id)]
        ).unlink()

        # Create salary rule categories then rules for the company
        self._create_salary_rule_category(company)
        self._create_salary_rule(company)

        return {}

    def _create_salary_rule_category(self, company):
        self.ensure_one()
        rules_category = self.env['hr.salary.rule.category']
        for src_cat in self.env['hr.salary.rule.category'].sudo().search([('company_id', '=', 1)]):
            # Find matching category in target company (by code)
            existing = self.env['hr.salary.rule.category'].sudo().search([
                ('company_id', '=', company.id),
                ('code', '=', src_cat.code),
            ], limit=1)

            rules_category += self.env['hr.salary.rule.category'].create({
                'name': src_cat.name,
                'code': src_cat.code,
                'parent_id': existing.id if existing else False,
                'company_id': company.id,
            })
        return rules_category

    def _create_salary_rule(self, company):
        self.ensure_one()
        salary_rules = self.env['hr.salary.rule']

        for src_rule in self.env['hr.salary.rule'].sudo().search([('company_id', '=', 1)]):
            # Resolve category in target company
            category = self.env['hr.salary.rule.category'].search([
                ('company_id', '=', company.id),
                ('code', '=', src_rule.category_id.code),
            ], limit=1)

            new_rule = self.env['hr.salary.rule'].create({
                'name': src_rule.name,
                'sequence': src_rule.sequence,
                'code': src_rule.code,
                'category_id': category.id if category else False,
                'condition_select': src_rule.condition_select or False,
                'amount_select': src_rule.amount_select or False,
                'amount_python_compute': src_rule.amount_python_compute or False,
                'note': src_rule.note or False,
                'appears_on_payslip': src_rule.appears_on_payslip,
                'register_id': src_rule.register_id.id or False,
                'parent_rule_id': src_rule.parent_rule_id.id or False,
                'quantity': src_rule.quantity,
                'amount_fix': src_rule.amount_fix,
                'amount_percentage_base': src_rule.amount_percentage_base or False,
                'condition_python': src_rule.condition_python or False,
                'company_id': company.id,
            })

            # Duplicate rule inputs
            for rule_input in self.env['hr.rule.input'].sudo().search([('input_id', '=', src_rule.id)]):
                self.env['hr.rule.input'].create({
                    'name': rule_input.name,
                    'code': rule_input.code,
                    'input_id': new_rule.id,
                })

            salary_rules += new_rule

        # Create a base payroll structure linked to these rules
        self.env['hr.payroll.structure'].create({
            'name': 'Base for new structures',
            'code': 'BASE_%s' % company.id,
            'company_id': company.id,
            'rule_ids': [(6, 0, salary_rules.ids)],
            'parent_id': False,
        })

        company.write({'payroll_chart_template': self.id})
        return salary_rules
