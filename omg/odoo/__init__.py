# -*- coding: utf-8 -*-
#!/bin/python3

import logging

# import odoo_analyse
from odoo_analyse import Odoo as OOdoo
from odoo_analyse import Module as OdooModule
from odoo_analyse import Model as OdooModel
from odoo_analyse.field import Field as OdooField
from odoo_analyse.utils import get_ast_source_segment

from omg.odoo.module import Module
from omg.odoo.model import Model
from omg.odoo.field import Field

_logger = logging.getLogger(__name__)


class Odoo(OOdoo):
    def load_path(self, paths, depth=None):
        """Overrided to replace Module"""

        if isinstance(paths, str):
            paths = [paths]

        result = Module.find_modules(paths, depth=depth)

        self.full.update(result.copy())
        self.modules.update(result.copy())
