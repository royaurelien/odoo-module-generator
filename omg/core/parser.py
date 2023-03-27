# -*- coding: utf-8 -*-
#!/bin/python3

import os
import logging
import shutil


from omg.odoo import Odoo
from omg.core.git import git_branch, git_checkout

MANIFESTS = ["__manifest__.py", "__odoo__.py", "__openerp__.py"]


_logger = logging.getLogger(__name__)


class Parser(object):
    def __init__(self, path):
        self.path = path
        self.modules = {}

        self._odoo = None

    @classmethod
    def from_path(cls, path, modules=None):
        self = cls(path)

        if not isinstance(modules, list):
            modules = list(set(map(str.strip, modules.split(","))))

        odoo = Odoo.from_path(path)

        for k, v in odoo.modules.items():
            if v.name not in modules:
                continue
            self.modules[k] = v

        self._odoo = odoo

        return self

    def skeleton(self, branch):
        current_branch = git_branch(self.path)

        assert current_branch, "no repository"

        if current_branch != branch:
            git_checkout(self.path, branch)

        for name, module in self.modules.items():
            module_path = os.path.join(self.path, name)
            files = module.skeleton()

            shutil.rmtree(module_path)
            os.makedirs(module_path)

            for file in files.values():
                filepath = os.path.join(module_path, file.path)
                parts, filename = os.path.split(file.path)

                if parts:
                    dirs = os.path.join(module_path, parts)
                    os.makedirs(dirs, exist_ok=True)

                with open(filepath, "w") as f:
                    f.write(file.content)
