# -*- coding: utf-8 -*-
# from odoo import http


# class KhkHrPayoreMultiCompany(http.Controller):
#     @http.route('/khk_hr_payore_multi_company/khk_hr_payore_multi_company/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/khk_hr_payore_multi_company/khk_hr_payore_multi_company/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('khk_hr_payore_multi_company.listing', {
#             'root': '/khk_hr_payore_multi_company/khk_hr_payore_multi_company',
#             'objects': http.request.env['khk_hr_payore_multi_company.khk_hr_payore_multi_company'].search([]),
#         })

#     @http.route('/khk_hr_payore_multi_company/khk_hr_payore_multi_company/objects/<model("khk_hr_payore_multi_company.khk_hr_payore_multi_company"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('khk_hr_payore_multi_company.object', {
#             'object': obj
#         })
