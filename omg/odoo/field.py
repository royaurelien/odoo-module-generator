# -*- coding: utf-8 -*-
#!/bin/python3

import logging

from omg.odoo import OdooField
from omg.core.tools import dict_to_list

_logger = logging.getLogger(__name__)


class Field(OdooField):
    def __init__(self, name: str, ttype: str, definition: str = None, **kwargs: dict):
        self.name = name
        self.ttype = ttype
        self.definition = definition
        self.args = []
        self.keywords = {}

        # args, keywords
        self.__dict__.update(kwargs)
        self.sanitize()

    def __repr__(self) -> str:
        return f"<Field ({self.ttype}): {self.name}>"

    def sanitize(self):
        if not self.args:
            return

        ttype, args = self.ttype, self.args
        vals = None

        if ttype in ["Many2one"]:
            if len(args) == 1:
                vals = dict(comodel_name=args[0])
            elif len(args) == 2:
                vals = dict(comodel_name=args[0], string=args[1])
        elif ttype in ["Selection"]:
            if len(args) == 1:
                vals = dict(selection=args[0])

        if vals:
            self.keywords.update(vals)
            self.args = []

    def get_definition(self, keywords=True):
        # if keywords:
        #     parts += [*self.keywords]

        keys = ["selection", "comodel_name", "inverse_name", "related"]

        # if self.ttype in ["Char", "Text", "Html"]:
        #     pass
        # elif self.ttype in ["Many2one", "One2many", "Many2many"]:
        #     pass
        # elif self.ttype in ["Many2one", "One2many", "Many2many"]:
        #     pass
        # else:
        #     pass

        parts = dict_to_list(self.keywords, keys)
        chain = ", ".join(parts)

        return f"{self.name} = fields.{self.ttype}({chain})"
