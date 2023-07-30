# pylint: disable=C0103

from odoo import _, api, fields, models


class NewModel(models.Model):
    _name = "new.model"
    _description = "New Model"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    description = fields.Text()
    country_id = fields.Many2one(
        comodel_name="res.country",
        required=True,
    )
    partner_ids = fields.One2many(
        comodel_name="res.partner",
        compute="_compute_partners",
        compute_sudo=True,
    )
    partner_count = fields.Integer(
        compute="_compute_partners",
        string="# Partners",
        compute_sudo=True,
    )

    @api.depends("country_id")
    def _compute_partners(self):
        Partner = self.env["res.partner"].sudo()
        for record in self:
            partners = Partner.search([("country_id", "=", record.country_id.id)])
            record.partner_ids = partners
            record.partner_count = len(partners)

    def action_view_partners(self):
        self.ensure_one()

        action = self.env.ref("contacts.action_contacts").read()[0]
        action["context"] = {}

        if self.partner_count != 1:
            action["domain"] = [("id", "in", self.partner_ids.ids)]
        else:
            res = self.env.ref("base.view_partner_form", False)
            action["views"] = [(res and res.id or False, "form")]
            action["res_id"] = self.partner_ids.id

        return action

    def action_custom_wizard(self):
        self.ensure_one()

        view_id = self.env.ref("custom_module.custom_wizard_view_form").id
        wizard = self.env["custom.wizard"].create(
            {
                "new_model_id": self.id,
            }
        )

        return {
            "name": _("Custom Wizard"),
            "view_mode": "form",
            "res_model": wizard._name,
            "view_id": view_id,
            "views": [(view_id, "form")],
            "type": "ir.actions.act_window",
            "res_id": wizard.id,
            "target": "new",
        }
