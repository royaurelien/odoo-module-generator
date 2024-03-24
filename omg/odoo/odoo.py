from io import StringIO
import json
import sys
import asyncio
import ast

from omg.odoo.module import Module

from omg.common.logger import _logger


class Odoo:
    def __init__(self):
        self.modules = {}

    @classmethod
    def load_path(cls, path, **config):
        odoo = cls()
        odoo.modules = Module.find_modules(path)

        return odoo
