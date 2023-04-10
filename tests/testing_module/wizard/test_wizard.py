# © 2020 initOS GmbH
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import fields, models


class TestWizard(models.TransientModel):
    _name = "test.wizard"

    a = fields.Char()
    b = fields.Text()
    c = fields.Integer()
    line_ids = fields.One2many("test.wizard.line", inverse_name="wizard_id")


class TestWizardLine(models.TransientModel):
    _name = "test.wizard.line"

    e = fields.Char()
    wizard_id = fields.Many2one("test.wizard", istring="Parent")
