import ast
import os
import shutil
import sys
import tempfile
from functools import partial
from pathlib import Path

import astor

from omg.common.logger import _logger
from omg.common.node import Cleaner, is_model
from omg.common.render import RIGHTS_FULL, ModelAccessHelper, render
from omg.common.tools import fix_indentation, save_code, try_automatic_port
from omg.core.models import Manifest
from omg.core.settings import get_settings
from omg.odoo.model import Model

settings = get_settings()  # pylint: disable=C0413

MANIFESTS = ["__manifest__.py", "__odoo__.py", "__openerp__.py"]
ODOO_MODELS = ["models", "Model", "AbstractModel", "TransientModel"]
EXCLUDE_FOLDERS = ["report", "controller", "controllers", "wizard", "wizards"]


class Module:
    def __init__(self, path: str, version: str = ""):
        self.path = path
        self.name = os.path.basename(path[:-1] if path.endswith("/") else path)
        self.manifest = {}
        self.files = set()
        self.imports = set()
        self.models = {}
        self.classes = {}
        self.files_to_keep = set()
        self.version = version
        self.status = set()

    def __repr__(self) -> str:
        return f"<Module ({self.name}): {self.path}>"

    def _parse_manifest(self, path: str) -> None:
        # odoo_analyse
        with open(path, encoding="utf-8") as fp:
            obj = ast.literal_eval(fp.read())
            if isinstance(obj, dict):
                # self.update(depends=obj.get("depends", []), files=obj.get("data", []))
                self.manifest.update(obj)

    def _load_python(self, path: str, filename: str) -> None:
        # odoo_analyse
        def parse_python(filepath, version=None):
            with open(filepath, encoding="utf-8") as fp:
                data = fp.read()

            # Python 3.8 allows setting the feature level
            if version:
                parsed = ast.parse(data, feature_version=version)
                _logger.warning("Feature version %s %s", version, filepath)
                self.status.add(f"feature-{version[0]}-{version[1]}")
                return parsed
            return ast.parse(data)

        def port_fix_file(filepath):
            with tempfile.NamedTemporaryFile("w+") as tmp:
                with open(filepath, encoding="utf-8") as fp:
                    tmp.file.write(fp.read())
                if try_automatic_port(tmp.name):
                    _logger.warning("Ported %s", filepath)
                    self.status.add("ported")
                if fix_indentation(tmp.name):
                    _logger.warning("Fixed indentation %s", filepath)
                    self.status.add("indent-fix")
                return parse_python(tmp.name)

        versions = [None]
        if sys.version_info >= (3, 8):
            versions.append((3, 6))

        funcs = [partial(parse_python, version=ver) for ver in versions]
        funcs.append(port_fix_file)

        exc = None
        filepath = os.path.join(path, filename)
        for func in funcs:
            try:
                return func(filepath)
            except SyntaxError as e:
                exc = e

        _logger.error(f"Not parsable {filepath}: {exc}")
        raise exc

    def _parse_model(self, obj: ast.ClassDef, content: str) -> None:
        cleaner = Cleaner()
        obj = cleaner.visit(obj)

        model = Model.from_ast(obj, content)

        if model._name in self.models:
            # FIXME: merge
            # self.models[model._name].update(model)
            pass
        else:
            self.models[model._name] = model

    def _parse_python(self, path: str, filename: str) -> None:  # noqa: C901
        # odoo_analyse

        if path + filename in self.files:
            return

        folder = os.path.basename(path)
        if folder in EXCLUDE_FOLDERS:
            return

        obj = self._load_python(path, filename)

        with open(os.path.join(path, filename), encoding="utf-8") as fp:
            content = fp.read()

        self.files.add(os.path.join(path, filename))

        imports = set()
        fmt = "{}.{}".format

        for c in obj.body:
            if isinstance(c, ast.ImportFrom):
                m = c.module
                imports.update(fmt(m or "", name.name) for name in c.names)
            elif isinstance(c, ast.Import):
                imports.update(name.name for name in c.names)

        for child in obj.body:
            if isinstance(child, ast.ClassDef):
                if not is_model(child):
                    # TODO: parse class
                    pass
                else:
                    self._parse_model(child, content)

        patterns = ["odoo.addons.", "openerp.addons."]
        for imp in imports:
            if any(imp.startswith(p) for p in patterns):
                mod = imp.split(".")[2]
                if mod != self.name:
                    self.imports.add(mod)
                continue

            if imp.split(".", 1)[0] in ["odoo", "openerp"]:
                continue

            p = path
            for f in imp.lstrip(".").split("."):
                if os.path.isfile(os.path.join(p, f"{f}.py")):
                    self._parse_python(p, f"{f}.py")
                    continue

                subdir = os.path.join(p, f)
                if os.path.isfile(os.path.join(subdir, "__init__.py")):
                    self._parse_python(subdir, "__init__.py")
                elif os.path.isdir(subdir):
                    p = subdir
                else:
                    break

    @classmethod
    def from_path(cls, path, **config) -> "Module":  # noqa: C901
        # odoo_analyse

        module = cls(path)
        found_init, found_manifest = False, False

        if not path.endswith("/"):
            path += "/"

        # Find the manifest scripts
        for f in MANIFESTS:
            filepath = os.path.join(path, f)
            if os.path.isfile(filepath):
                found_manifest = True
                module._parse_manifest(filepath)

        if not found_manifest:
            return None

        for f in os.listdir(path):
            # Found the init script
            if f == "__init__.py":
                found_init = True
                module._parse_python(path, f)

        if not found_init:
            return None

        _logger.info("Found module %s", module.name)
        return module

    @classmethod
    def _find_modules(cls, path: str):
        blacklist = []
        path = path.strip()

        try:
            module = cls.from_path(path)
        except Exception as e:
            _logger.error(f"Error on {path}")
            _logger.exception(e)
            module = None

        if module is not None:
            name = module.name
            yield (name, module)
        else:
            sub_paths = [
                os.path.join(path, p) for p in os.listdir(path) if p not in blacklist
            ]
            for new_path in filter(os.path.isdir, sub_paths):
                yield from cls._find_modules(new_path)

    @classmethod
    def find_modules(cls, path: str):
        result = {}
        for key, value in cls._find_modules(path):
            result[key] = value

        return result

    def set_version(self, version: str):
        if len(version.split(".")) != 5:
            raise ValueError("Version doesn't match expected format (17.0.x.y.z)")
        self.version = version

    def fields_matrix(self) -> dict:
        res = {}
        for model in self.models.values():
            res[model.sql_name] = model.fields_matrix()

        return res

    def _get_default_imports(self) -> "ast.ImportFrom":
        names = [ast.alias(name=name) for name in ["fields", "models"]]
        return ast.ImportFrom("odoo", names, 0)

    def _get_source(self, model: "Model") -> str:
        imports = self._get_default_imports()
        tree = ast.Module(body=[imports, model._obj])
        return astor.to_source(tree)

    def _generate_init(self, modules: list) -> str:
        imports = [ast.ImportFrom(".", [ast.alias(name=name)], 0) for name in modules]
        tree = ast.Module(body=imports)
        return astor.to_source(tree)

    def clean(self, exclude_files: list = [], exclude_dirs: list = ["models"]) -> None:
        """Clean module"""

        files = {
            str(f.absolute()) for f in Path(self.path).rglob("*") if f.is_file()
        } - set(exclude_files)

        dirs = {
            str(f.absolute())
            for f in Path(self.path).rglob("*")
            if f.is_dir() and f.name not in exclude_dirs
        }

        for filepath in files:
            os.remove(filepath)

        for path in dirs:
            if os.path.exists(path) and len(os.listdir(path)) == 0:
                shutil.rmtree(path)

    def save_init(self, path: str, modules: list) -> str:
        filepath = os.path.join(path, "__init__.py")
        content = self._generate_init(modules)

        save_code(content, filepath)

        return filepath

    def save_manifest(self, data: list = []) -> str:
        filepath = os.path.join(self.path, "__manifest__.py")

        vals = settings.default_manifest.dict()
        vals.update({k: v for k, v in self.manifest.items() if v})

        manifest = Manifest(**vals)
        manifest.set_version(self.version)
        manifest.data = data
        manifest.demo = []
        content = manifest.prepare_to_save()

        save_code(content, filepath)

        return filepath

    def write(self, clean: bool = True) -> None:
        to_keep, modules, data = [], [], []
        models_path = os.path.join(self.path, "models")
        os.makedirs(models_path, exist_ok=True)

        model_access = ModelAccessHelper(self.path)

        for name, model in self.models.items():
            filepath = os.path.join(models_path, model.filename)
            content = self._get_source(model)

            if model.is_new:
                model_access.add(name, "base.group_user", RIGHTS_FULL)

            # Write model
            save_code(content, filepath)
            to_keep.append(filepath)
            modules.append(model.sql_name)

        # Models init
        to_keep.append(self.save_init(models_path, modules))

        # Module init
        to_keep.append(self.save_init(self.path, ["models"]))

        if not model_access.void:
            model_access.save()
            to_keep.append(model_access.filepath)
            data.append(model_access.filename)

        # Manifest
        to_keep.append(self.save_manifest(data))

        # Clean stage
        if clean:
            self.clean(to_keep)

    def rename(self):
        script = "pre-migrate.py"
        migrations_path = os.path.join(self.path, "migrations")
        version_path = os.path.join(migrations_path, self.version)
        filepath = os.path.join(version_path, script)

        os.makedirs(version_path, exist_ok=True)

        template = f"module/{script}.jinja2"
        vals = {"mapping": self.fields_matrix()}
        content = render(template, data=vals)

        save_code(content, filepath)
