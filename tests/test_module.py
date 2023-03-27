# -*- coding: utf-8 -*-
#!/bin/python3

import os
from unittest import mock

from omg.odoo import Module


def get_module():
    modules = Module.find_modules(os.path.abspath("tests/"))
    return modules["testing_module"]


def test_module():
    mod = get_module()

    assert repr(mod) == "<Module: testing_module>"
