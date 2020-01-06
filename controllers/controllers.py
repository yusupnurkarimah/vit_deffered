# -*- coding: utf-8 -*-
from odoo import http

# class VitDeffered(http.Controller):
#     @http.route('/vit_deffered/vit_deffered/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/vit_deffered/vit_deffered/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('vit_deffered.listing', {
#             'root': '/vit_deffered/vit_deffered',
#             'objects': http.request.env['vit_deffered.vit_deffered'].search([]),
#         })

#     @http.route('/vit_deffered/vit_deffered/objects/<model("vit_deffered.vit_deffered"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('vit_deffered.object', {
#             'object': obj
#         })