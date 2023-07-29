#!/bin/python3

import os

from omg.core.parser import Parser


def get_module():
    parser = Parser.from_path(os.path.abspath("tests/"), "testing_module")
    return parser.modules["testing_module"]


def test_module():
    mod = get_module()

    assert repr(mod) == "<Module: testing_module>"

    files = mod.skeleton()

    assert files["__manifest__"].name == "__manifest__"
    assert (
        files["__manifest__"].content
        == """# -*- coding: utf-8 -*-
{
    "name": "test module",
    "version": "x.0.1.0.0",
    "category": "Hidden",
    "author": "Odoo S.A.",
    "website": "https://example.org",
    "license": "license",
    "summary": "summary",
    "description": "description",
    "depends": ["base"],
    "data": [],
    "installable": True,
    "demo": [],
    "auto_install": False,
    "application": False,
    "external_dependencies": {},
}

"""
    )
