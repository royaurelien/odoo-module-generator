import logging
from io import StringIO
import json
import sys
import asyncio
import ast

# import odoo_analyse
from odoo_analyse import Odoo as OOdoo
from odoo_analyse import Module as OdooModule
from odoo_analyse import Model as OdooModel
from odoo_analyse.field import Field as OdooField

# from odoo_analyse.utils import get_ast_source_segment

from omg.odoo.module import Module
from omg.odoo.model import Model
from omg.odoo.field import Field

_logger = logging.getLogger(__name__)

__all__ = [
    "OdooModule",
    "OdooModel",
    "OdooField",
    "Module",
    "Model",
    "Field",
    # "get_ast_source_segment",
]


class Odoo(OOdoo):
    def load_path(self, paths, *, max_depth=None, **config):
        """Overrided to replace Module"""
        if isinstance(paths, str):
            paths = [paths]

        result = asyncio.run(Module.find_modules(paths, max_depth=max_depth, **config))

        self.full.update(result.copy())
        self.modules.update(result.copy())

    def export(self):
        output = StringIO()

        # Capture stdout to buffer
        sys.stdout = output
        self.analyse("-")
        sys.stdout = sys.__stdout__

        data = json.loads(output.getvalue())

        for name in data.keys():
            vals = self.modules[name].to_json()
            data[name].update(vals)

            data[name].setdefault("missing_dependency", {})
            # data[name]["missing_dependency"] = x

        return data
