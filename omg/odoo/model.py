# -*- coding: utf-8 -*-
#!/bin/python3

import ast
from collections import namedtuple
import logging

from omg.odoo import OdooModel, get_ast_source_segment
from omg.odoo.field import Field
from omg.core.tools import generate, get_arg, get_keyword, get_assign
from omg.core.models import File

MANIFESTS = ["__manifest__.py", "__odoo__.py", "__openerp__.py"]

_logger = logging.getLogger(__name__)


class Model(OdooModel):
    @property
    def has_fields(self):
        return bool(self.fields)

    @property
    def filename(self):
        return self.name.replace(".", "_")

    @property
    def classname(self):
        return "".join(map(str.capitalize, self.name.split(".")))

    @classmethod
    def field_from_string(cls, content):
        obj = get_assign(content)
        model = Model("test.test")
        model._parse_assign(obj, content)

        return model.fields[next(iter(model.fields))]

    def generate(self) -> File:
        filepath = f"models/{self.filename}"
        inherit = self.name if self.inherit and self.name in self.inherit else False

        vals = {
            "name": self.name,
            "classname": self.classname,
            "fields": list(
                map(
                    lambda field: field.get_definition(keywords=False),
                    self.fields.values(),
                )
            ),
        }

        if inherit:
            vals["inherit"] = inherit

        return generate("model.jinja2", vals, filepath)

    def _parse_assign(self, obj: ast.Assign, content: str) -> None:
        """Overrided to replace Field"""

        assignments = [k.id for k in obj.targets if isinstance(k, ast.Name)]
        if len(assignments) != 1:
            return

        assign, value = assignments[0], obj.value
        if assign == "_name":
            if not isinstance(value, ast.Constant):
                return

            self.name = ast.literal_eval(value)
        elif assign == "_inherit":
            if isinstance(value, ast.Name) and value.id == "_name":
                self.inherit.add(self.name)
            elif not isinstance(value, ast.Name):
                value = ast.literal_eval(value)
                if isinstance(value, list):
                    self.inherit.update(value)
                else:
                    self.inherit.add(value)
        elif assign == "_inherits":
            inhs = ast.literal_eval(value)
            if isinstance(inhs, dict):
                print(inhs)
                self.inherits.update(inhs)
                self.fields.update({k: Field(k, "Many2one") for k in inhs.values()})
        elif isinstance(value, ast.Call):
            f = value.func
            if not isinstance(f, ast.Attribute) or not isinstance(f.value, ast.Name):
                return

            if f.value.id == "fields":
                ttype = f.attr
                definition = get_ast_source_segment(content, value)

                # Store args and keywords
                args = list(map(get_arg, value.args))
                keywords = dict(map(get_keyword, value.keywords))

                if args:
                    if ttype in ["Many2one"]:
                        if len(args) == 1:
                            keywords["comodel_name"] = args[0]
                            args = []
                        elif len(args) == 2:
                            keywords["comodel_name"], keywords["string"] = args
                            args = []

                self.fields[assign] = Field(
                    assign,
                    ttype,
                    definition,
                    args=args,
                    keywords=keywords,
                )
