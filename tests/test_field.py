import ast
from unittest import mock
import logging

from black import format_str, FileMode

from omg.core.field import Field

_logger = logging.getLogger(__name__)


def run_test_field(src, name, ttype, args, keywords):
    # assert isinstance(parsed, ast.Assign)

    field = Field.from_string(src)

    assert repr(field) == f"<Field ({ttype}): {name}>"

    assert field.ttype == ttype
    assert len(field.args) == len(args)
    assert len(field.keywords) == len(keywords)

    for key, key2 in zip(field.keywords.keys(), keywords.keys()):
        assert key == key2

    for value, value2 in zip(field.keywords.values(), keywords.values()):
        assert value == value2

    return field


def test_field_char_1():
    src = """var = fields.Char(string="Link supplier", groups="hr.group_hr_user")"""
    run_test_field(
        src, "var", "Char", [], dict(string="Link supplier", groups="hr.group_hr_user")
    )


def test_field_monetary_1():
    src = """var = fields.Monetary(string="Amount untaxed tjm2", related="address_home_id.amount_untaxed_tjm2", readonly=False, store=True, groups="hr.group_hr_user")"""
    run_test_field(
        src,
        "var",
        "Monetary",
        [],
        dict(
            string="Amount untaxed tjm2",
            related="address_home_id.amount_untaxed_tjm2",
            readonly=False,
            store=True,
            groups="hr.group_hr_user",
        ),
    )


def test_field_many2one_1():
    src = """var = fields.Many2one('code.establishment', string="Establishment code", groups="hr.group_hr_user")"""

    run_test_field(
        src,
        "var",
        "Many2one",
        [],
        dict(
            string="Establishment code",
            groups="hr.group_hr_user",
            comodel_name="code.establishment",
        ),
    )


def test_field_many2one_2():
    src = """var = fields.Many2one('res.users', "Responsable Congé NV2", compute="_compue_leave_manager_fields", store=True)"""

    field = run_test_field(
        src,
        "var",
        "Many2one",
        [],
        dict(
            compute="_compue_leave_manager_fields",
            store=True,
            comodel_name="res.users",
            string="Responsable Congé NV2",
        ),
    )

    assert (
        field.get_definition() == """var = fields.Many2one(comodel_name="res.users")"""
    )


def test_field_selection_1():
    src = """var = fields.Selection(string="Contract type", selection='CONTRACT_TYPE_SELECTION', readonly=False, related="address_home_id.contract_type", store=True, groups="hr.group_hr_user")"""

    field = run_test_field(
        src,
        "var",
        "Selection",
        [],
        dict(
            string="Contract type",
            selection="CONTRACT_TYPE_SELECTION",
            readonly=False,
            related="address_home_id.contract_type",
            store=True,
            groups="hr.group_hr_user",
        ),
    )

    assert (
        field.get_definition()
        == """var = fields.Selection(selection="CONTRACT_TYPE_SELECTION", related="address_home_id.contract_type")"""
    )


def test_field_one2many_1():
    src = """
room_ids = fields.One2many(
    string="Rooms",
    help="Rooms that a property has.",
    comodel_name="pms.room",
    inverse_name="pms_property_id")
    """

    field = run_test_field(
        src,
        "room_ids",
        "One2many",
        [],
        dict(
            string="Rooms",
            help="Rooms that a property has.",
            comodel_name="pms.room",
            inverse_name="pms_property_id",
        ),
    )

    assert (
        field.get_definition()
        == """room_ids = fields.One2many(comodel_name="pms.room", inverse_name="pms_property_id")"""
    )
