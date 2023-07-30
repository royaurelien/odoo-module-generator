from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    is_gold = fields.Boolean(default=False, string="Gold Partner")
