#!/bin/python3

import os

from omg.odoo import Module


def get_module():
    modules = Module.find_modules(os.path.abspath("tests/"))
    return modules["testing_module"]


def test_module():
    mod = get_module()

    assert repr(mod) == "<Module: testing_module>"


def test_models():
    module = get_module()
    models = module.models

    names = {
        "test.wizard",
        "test.wizard.line",
        "test.abstract",
        "test.model",
        "res.users",
        "res.partner",
        "product.template",
    }

    assert set(models.keys()) == names

    assert models["test.abstract"].ttype == "AbstractModel"
    assert models["test.wizard"].ttype == "TransientModel"
    assert models["test.model"].ttype == "Model"
    assert models["res.users"].ttype == "Model"

    assert set(filter(lambda x: models[x].is_stored, models.keys())) == {
        "test.model",
        "res.users",
        "res.partner",
        "product.template",
    }
