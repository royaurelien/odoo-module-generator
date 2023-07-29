#!/bin/python3

import ast
import logging
import os
from collections import namedtuple

import jinja2
from black.parsing import InvalidInput
from jinja2.exceptions import UndefinedError

_logger = logging.getLogger(__name__)

File = namedtuple("File", ["name", "path", "content"])
TEMPLATE_DIR = os.path.abspath("static/")


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
        # code = format_str(code, mode=FileMode())
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
    # print(src)
    obj = ast.parse(src)
    return function(obj)


def dict_to_list(data, keys=None):
    def function(item):
        return f'{item}="{data[item]}"'

    if keys:
        items = filter(lambda x: x in keys, data)
    else:
        items = data

    return list(map(function, items))


def get_keyword(obj):
    name = obj.arg
    value = obj.value

    if isinstance(value, ast.Constant):
        value = value.value

    return (name, value)


def get_arg(obj):
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
        # print(result)
        value = ast.dump(value)

        # value = ast.literal_eval(value)

        # print(value)
        # exit(1)
    # else:
    #     print(type(obj))
    #     exit(1)

    # return f'"{value}"'
    return value
