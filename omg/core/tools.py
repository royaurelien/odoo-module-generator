# -*- coding: utf-8 -*-
#!/bin/python3

import ast
import os
import logging
import sys
import tempfile
from functools import partial
from collections import namedtuple
import subprocess

from black import format_str, FileMode
from black.parsing import InvalidInput
import jinja2
from jinja2.exceptions import UndefinedError

from omg.core.models import FakeModel
from omg.core.odoo import _parse_assign


_logger = logging.getLogger(__name__)

File = namedtuple("File", ["name", "path", "content"])
TEMPLATE_DIR = os.path.abspath("omg/static/")


def generate(template: str, data: dict, filename: str, functions=None) -> File:
    code = generate_code(template, data, functions)
    file = generate_file(filename, code)

    return file


def generate_code(template: str, data: dict, functions=None) -> str:
    jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATE_DIR))
    jinja_template = jinja_env.get_template(template)

    if functions:
        jinja_template.globals.update(functions)

    try:
        code = jinja_template.render(**data)
        code = format_str(code, mode=FileMode())
    except UndefinedError as error:
        _logger.error(error)
        code = False
    except InvalidInput as error:
        _logger.error(error)
        exit(1)

    return code


def generate_file(filename: str, content: str) -> File:
    filepath = f"{filename}.py"

    return File(name=filename, path=filepath, content=content)


def get_assign(src):
    def function(obj):
        for child in obj.body:
            if isinstance(child, ast.ClassDef):
                return function(child)
            if isinstance(child, ast.Assign):
                return child

    # src = format_str(src, mode=FileMode())
    src = src.strip('"')
    print(src)
    obj = ast.parse(src)
    return function(obj)


def get_field_from_source(content):
    parsed = get_assign(content)
    model = FakeModel()
    _parse_assign(model, parsed, content)

    return model.field


def dict_to_list(data, keys=None):
    def function(item):
        return f'{item}="{data[item]}"'

    if keys:
        items = filter(lambda x: x in keys, data)
    else:
        items = data

    return list(map(function, items))
