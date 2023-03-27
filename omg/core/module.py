# -*- coding: utf-8 -*-
#!/bin/python3

import ast
import os
import logging
from collections import namedtuple


from omg.core.model import Model
from omg.core.tools import generate
from omg.core.models import File

MANIFESTS = ["__manifest__.py", "__odoo__.py", "__openerp__.py"]

_logger = logging.getLogger(__name__)


class Module(object):
    def __init__(self):
        self.models = set()
        self.path = ""
        self.name = ""
        self.manifest = dict()
        self.models = dict()
        self.files = set()
        self.status = set()
        self.imports = set()

    @classmethod
    def from_odoo(cls, obj):
        self = cls()

        self.name = obj.name
        self.manifest = obj.manifest

        for k, v in obj.models.items():
            model = Model.from_odoo(v)
            self.models[k] = model

        return self

    def sanitize_manifest(self):
        DEFAULT_MANIFEST = {
            "data": [],
            "demo": [],
            "auto_install": False,
            "installable": True,
            "application": False,
            "external_dependencies": {},
        }
        self.manifest.update(DEFAULT_MANIFEST)

        to_remove = ["certificate", "complexity", "images", "sequence"]
        for key in to_remove:
            if key in self.manifest:
                self.manifest.pop(key)

        if "qweb" in self.manifest:
            self.manifest["qweb"] = []

    def generate_init(self, modules, name="__init__"):
        vals = {"modules": modules}
        code = generate("init.jinja2", vals)

        return File(name=name, path=f"{name}.py", content=code)

    def skeleton(self):
        self.sanitize_manifest()

        files = {}
        models = []
        for name, model in self.models.items():
            if not model.has_fields:
                continue
            file = model.generate()
            files[name] = file

            models.append(model.filename)

            # print(file.content)

        f = generate("init.jinja2", dict(modules=models), "models/__init__")
        files[f.name] = f
        # print(f.content)

        f = generate("init.jinja2", dict(modules=["models"]), "__init__")
        files[f.name] = f
        # print(f.content)

        f = generate("manifest.jinja2", dict(manifest=self.manifest), "__manifest__")
        files[f.name] = f
        print(f.content)

        return files

    def __repr__(self) -> str:
        return f"<Module: {self.name}>"
