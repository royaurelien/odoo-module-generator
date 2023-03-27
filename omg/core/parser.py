# -*- coding: utf-8 -*-
#!/bin/python3

import os
import logging
import shutil


from omg.core.odoo import Odoo
from omg.core.module import Module
from omg.core.models import File
from omg.core.git import git_branch, git_checkout

MANIFESTS = ["__manifest__.py", "__odoo__.py", "__openerp__.py"]


_logger = logging.getLogger(__name__)


class Parser(object):
    def __init__(self, path):
        self.path = path
        self.modules = {}

    @classmethod
    def from_path(cls, path, modules=None):
        self = cls(path)

        if not isinstance(modules, list):
            modules = list(set(map(str.strip, modules.split(","))))

        # module = Module.from_path(path)
        odoo = Odoo.from_path(path)

        for k, v in odoo.modules.items():
            if v.name not in modules:
                continue
            module = Module.from_odoo(v)
            module.path = path
            self.modules[k] = module

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
