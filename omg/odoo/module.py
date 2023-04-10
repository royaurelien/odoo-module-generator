# -*- coding: utf-8 -*-
#!/bin/python3

import ast
import os
import logging
from collections import namedtuple


from omg.odoo import OdooModule
from omg.odoo.model import Model
from omg.core.tools import generate
from omg.core.models import File

MANIFESTS = ["__manifest__.py", "__odoo__.py", "__openerp__.py"]

_logger = logging.getLogger(__name__)


class Module(OdooModule):
    def _parse_class_def(self, obj: ast.ClassDef, content: str) -> None:
        """Overrided to replace Model"""

        model = Model.from_ast(obj, content)

        if not model.is_model():
            self.classes[model.name] = model
            return

        if model.name in self.models:
            self.models[model.name].update(model)
        else:
            self.models[model.name] = model

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
        # print(f.content)

        return files

    def to_json(self):
        languages = {k: v["lines"] for k, v in self.language.items()}

        data = {
            "path": self.path,
            "name": self.name,
            "duration": self.duration,
            "manifest": self.manifest,
            "models": {n: m.to_json() for n, m in self.models.items()},
            "classes": {n: c.to_json() for n, c in self.classes.items()},
            "views": {n: v.to_json() for n, v in self.views.items()},
            "records": {n: d.to_json() for n, d in self.records.items()},
            "depends": list(self.depends),
            "imports": list(self.imports),
            "refers": list(self.refers),
            "files": list(self.files),
            "status": list(self.status),
            "language": self.language,
            "words": list(self.words),
            "hashsum": self.hashsum,
            "readme": bool(self.readme),
            "readme_type": self.readme_type,
            "author": self.author,
            "category": self.category,
            "license": self.license,
            "version": self.version,
            "info": self.info,
            "models_count": self.info.get("model_count", 0),
            "class_count": self.info.get("class_count", 0),
            "records_count": self.info.get("record_count", 0),
            "views_count": self.info.get("view_count", 0),
            "depends_count": self.info.get("depends", 0),
            "PY": languages.get("Python", 0),
            "XML": languages.get("XML", 0),
            "JS": languages.get("JavaScript", 0),
            # "fields_count": len(self.fields),
            # "python": self.language.get("Python", 0),
            # "xml": self.language.get("Xml", 0),
        }
        if self.manifest and "data" in self.manifest:
            data["manifest"]["data"] = list(data["manifest"]["data"])

        return data
