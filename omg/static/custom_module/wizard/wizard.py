from odoo import fields, models


class CustomWizard(models.TransientModel):
    _name = "custom.wizard"
    _description = "Custom Wizard"

    new_model_id = fields.Many2one(
        comodel_name="new.model",
        required=True,
    )
    partner_ids = fields.One2many(
        comodel_name="res.partner",
        related="new_model_id.partner_ids",
    )
    partner_count = fields.Integer(
        related="new_model_id.partner_count",
    )
    is_checked = fields.Boolean(default=False)

    def validate(self):
        return True
