# -*- coding: utf-8 -*-
#!/bin/python3

import ast
import os
import logging
import sys
import tempfile
from functools import partial

import odoo_analyse
from odoo_analyse import Odoo
from odoo_analyse import Model
from odoo_analyse.field import Field
from odoo_analyse.utils import try_automatic_port, get_ast_source_segment


parse_assign = Model._parse_assign


def get_keyword(obj):
    name = obj.arg
    value = obj.value

    if isinstance(value, ast.Constant):
        value = value.value

    return (name, value)


def get_arg(obj):
    # List(
    #     elts=[
    #         Tuple(
    #             elts=[
    #                 Constant(value="0", kind=None),
    #                 Call(
    #                     func=Name(id="_", ctx=Load()),
    #                     args=[Constant(value="Pas de tickets restaurant", kind=None)],
    #                     keywords=[],
    #                 ),
    #             ],
    #             ctx=Load(),
    #         ),
    #         Tuple(
    #             elts=[
    #                 Constant(value="1", kind=None),
    #                 Call(
    #                     func=Name(id="_", ctx=Load()),
    #                     args=[
    #                         Constant(
    #                             value="Nombre de tickets restaurant automatique",
    #                             kind=None,
    #                         )
    #                     ],
    #                     keywords=[],
    #                 ),
    #             ],
    #             ctx=Load(),
    #         ),
    #         Tuple(
    #             elts=[
    #                 Constant(value="2", kind=None),
    #                 Call(
    #                     func=Name(id="_", ctx=Load()),
    #                     args=[
    #                         Constant(
    #                             value="Nombre de tickets restaurant saisi", kind=None
    #                         )
    #                     ],
    #                     keywords=[],
    #                 ),
    #             ],
    #             ctx=Load(),
    #         ),
    #         Tuple(
    #             elts=[
    #                 Constant(value="3", kind=None),
    #                 Call(
    #                     func=Name(id="_", ctx=Load()),
    #                     args=[
    #                         Constant(
    #                             value="Nombre de tickets restaurant saisi, repris du mois précedent",
    #                             kind=None,
    #                         )
    #                     ],
    #                     keywords=[],
    #                 ),
    #             ],
    #             ctx=Load(),
    #         ),
    #     ],
    #     ctx=Load(),
    # )

    value = obj

    if isinstance(value, ast.Constant):
        value = value.value
    elif isinstance(value, ast.List):
        result = []

        for child in value.elts:
            res = []
            if isinstance(child, ast.Tuple):
                for cc in child.elts:
                    if isinstance(cc, ast.Constant):
                        res.append(cc.value)
                        continue
                    if isinstance(cc, ast.Call):
                        tmp = f"{cc.func.id}({cc.args[0].value})"
                        res.append(tmp)
                        continue
            result.append(res)
        print(result)
        value = ast.dump(value)

        # value = ast.literal_eval(value)

        # print(value)
        # exit(1)
    # else:
    #     print(type(obj))
    #     exit(1)

    # return f'"{value}"'
    return value


class CustomField(Field):
    def __init__(self, name: str, ttype: str, definition: str = None, **kwargs: dict):
        self.name = name
        self.ttype = ttype
        self.definition = definition
        self.args = []
        self.keywords = {}

        # args, keywords
        self.__dict__.update(kwargs)


def _parse_assign(self, obj: ast.Assign, content: str) -> None:
    """Overloaded method"""
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


Field.__init__ = CustomField.__init__
odoo_analyse.Model._parse_assign = _parse_assign


_logger = logging.getLogger(__name__)
