import json
import os
import shutil
import sys
from io import StringIO

from omg.common.logger import _logger
from omg.core.git import Git
from omg.odoo import Odoo

MANIFESTS = ["__manifest__.py", "__odoo__.py", "__openerp__.py"]


class Parser:
    def __init__(self, path):
        self.path = path
        self.modules = {}

        self._odoo = None

    @classmethod
    def from_path(cls, path, modules=None):
        self = cls(path)

        if modules and not isinstance(modules, list):
            modules = list(set(map(str.strip, modules.split(","))))

        odoo = Odoo.from_path(path)

        for k, v in odoo.modules.items():
            if modules and v.name not in modules:
                continue
            self.modules[k] = v

        self._odoo = odoo

        return self

    def skeleton(self, branch):
        git = Git(self.path)
        current_branch = git.branch()

        assert current_branch, "no repository"

        if current_branch != branch:
            git.checkout(branch)

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

    def write(self, root_path):
        os.makedirs(root_path, exist_ok=True)

        for name, module in self.modules.items():
            module_path = os.path.join(root_path, name)
            os.makedirs(module_path, exist_ok=True)

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

    def analyze(self):
        output = StringIO()

        # Capture stdout to buffer
        sys.stdout = output
        self._odoo.analyse("-")
        sys.stdout = sys.__stdout__

        data = json.loads(output.getvalue())

        _logger.warning(data)

        return data
