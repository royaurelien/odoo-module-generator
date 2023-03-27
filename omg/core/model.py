# -*- coding: utf-8 -*-
#!/bin/python3


from collections import namedtuple
import logging

from omg.core.field import Field
from omg.core.tools import generate
from omg.core.models import File

MANIFESTS = ["__manifest__.py", "__odoo__.py", "__openerp__.py"]

_logger = logging.getLogger(__name__)


class Model(object):
    def __init__(self, name, description=None):
        self.name = name
        self.inherit = set()
        self.inherits = {}
        self.description = description or name
        self.fields = {}
        self.functions = {}

    @classmethod
    def from_odoo(cls, obj):
        self = cls(obj.name)
        self.inherit = obj.inherit
        self.inherits = obj.inherits
        # self.functions = obj.functions

        for k, v in obj.fields.items():
            field = Field.from_odoo(v, k)
            self.fields[k] = field

        return self

    @property
    def has_fields(self):
        return bool(self.fields)

    @property
    def filename(self):
        return self.name.replace(".", "_")

    @property
    def classname(self):
        return "".join(map(str.capitalize, self.name.split(".")))

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
