# -*- coding: utf-8 -*-
# from odoo import http


# class SecadoExterno(http.Controller):
#     @http.route('/secado_externo/secado_externo', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/secado_externo/secado_externo/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('secado_externo.listing', {
#             'root': '/secado_externo/secado_externo',
#             'objects': http.request.env['secado_externo.secado_externo'].search([]),
#         })

#     @http.route('/secado_externo/secado_externo/objects/<model("secado_externo.secado_externo"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('secado_externo.object', {
#             'object': obj
#         })
