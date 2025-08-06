from odoo import http
from odoo.http import request

class FbrStaticImage(http.Controller):

    @http.route('/fbr', type='http', auth='user', website=False)
    def show_image(self):
        return request.render('fbr_integration_fields.fbr_template')