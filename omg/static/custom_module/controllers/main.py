from odoo import http
from odoo.http import request


class WebsiteCustomController(http.Controller):
    @http.route(
        ["/custom", "/custom/page/<int:page>"], type="http", auth="public", website=True
    )
    def custom(self, page=1, **searches):
        values = {}

        return request.render("custom.index", values)
