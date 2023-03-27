# -*- coding: utf-8 -*-
#!/bin/python3

import logging

from omg.core.tools import get_field_from_source, dict_to_list

_logger = logging.getLogger(__name__)


class Field(object):
    def __init__(self, name, ttype):
        self.name = name
        self.ttype = ttype
        self.src = None
        self.args = []
        self.keywords = {}

    def __repr__(self) -> str:
        return f"<Field ({self.ttype}): {self.name}>"

    @classmethod
    def from_odoo(cls, obj, name):
        self = cls(name, obj.ttype)

        self.args = obj.args
        self.keywords = obj.keywords

        assert hasattr(obj, "definition"), "No definition"

        return self

    @classmethod
    def from_string(cls, content):
        obj = get_field_from_source(content)

        return Field.from_odoo(obj, obj.name)

    def get_definition(self, keywords=True):
        # if keywords:
        #     parts += [*self.keywords]

        keys = ["selection", "comodel_name", "inverse_name", "related"]

        if self.ttype in ["Char", "Text", "Html"]:
            pass
        elif self.ttype in ["Many2one", "One2many", "Many2many"]:
            pass
        elif self.ttype in ["Many2one", "One2many", "Many2many"]:
            pass
        else:
            pass

        parts = dict_to_list(self.keywords, keys)
        chain = ", ".join(parts)

        return f"{self.name} = fields.{self.ttype}({chain})"
