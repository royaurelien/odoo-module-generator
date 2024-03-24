import ast
import astor
import time
import tempfile
import sys
import os
from pathlib import Path
from functools import partial

from omg.common.logger import _logger
from omg.odoo.model import Model
from omg.common.tools import fix_indentation, try_automatic_port

from omg.common.node import Cleaner

MANIFESTS = ["__manifest__.py", "__odoo__.py", "__openerp__.py"]
ODOO_MODELS = ["models", "Model", "AbstractModel", "TransientModel"]


def is_model(obj):
    if not obj.bases:
        return False

    base = obj.bases[0]

    if isinstance(base, ast.Name):
        if base.id in ODOO_MODELS:
            return True

    if isinstance(base, ast.Attribute):
        # bases=[Attribute(value=Name(id='models'), attr='Model')],
        if base.value.id in ODOO_MODELS or base.attr in ODOO_MODELS[1:]:
            return True

    return False


class Module:

    def __init__(self, path):
        self.path = path
        self.name = os.path.basename(path)
        self.manifest = {}
        self.files = set()
        self.imports = set()
        self.models = {}
        self.classes = {}

    def __repr__(self) -> str:
        return f"<Module ({self.name}): {self.path}>"

    def _parse_manifest(self, path):
        with open(path, encoding="utf-8") as fp:
            obj = ast.literal_eval(fp.read())
            if isinstance(obj, dict):
                # self.update(depends=obj.get("depends", []), files=obj.get("data", []))
                self.manifest.update(obj)

    def _load_python(self, path, filename):
        filepath = os.path.join(path, filename)
        return astor.code_to_ast.parse_file(filepath)

    def _load_python_old(self, path, filename):
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
                with open(filepath, "r", encoding="utf-8") as fp:
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

    # def _parse_class_def(self, obj: ast.ClassDef, content: str) -> None:
    #     model = Model.from_ast(obj, content)
    #     if not model.is_model():
    #         self.classes[model.name] = model
    #         return

    #     if model._name in self.models:
    #         self.models[model._name].update(model)
    #     else:
    #         self.models[model._name] = model

    def _parse_model(self, obj: ast.ClassDef, content: str) -> None:

        cleaner = Cleaner()
        obj = cleaner.visit(obj)

        model = Model.from_ast(obj, content)

        if model._name in self.models:
            self.models[model._name].update(model)
        else:
            self.models[model._name] = model

    def _parse_python(self, path, filename):
        exclude = ["report", "controller", "controllers", "wizard", "wizards"]

        if path + filename in self.files:
            return

        folder = os.path.basename(path)
        if folder in exclude:
            return

        obj = self._load_python(path, filename)
        _logger.warning(obj)

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
                name = child.name
                # print(name)
                # print(child.bases)
                if not is_model(child):
                    print(f"class {name}")
                else:
                    print(f"model {name}")
                    self._parse_model(child, content)

                # self._parse_class_def(child, content)

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
    def from_path(cls, path, **config):  # noqa: C901
        parent_path = str(Path(path).parent.absolute())
        _logger.warning("parent path: %s", parent_path)
        # files_list = []
        # analyse_start = time.time()
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

                # imports = module._parse_init(path, f)
                # _logger.error("Imports: %s", imports)

                # for name in imports:
                #     tmp = module._parse_init(path, name)
                #     _logger.error("Imports from %s: %s", name, tmp)

        if not found_init:
            return None

        return module

    @classmethod
    def _find_modules(cls, path):
        blacklist = []
        path = path.strip()
        _logger.warning("path: %s", path)

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
            _logger.warning("path: %s", sub_paths)
            for new_path in filter(os.path.isdir, sub_paths):
                yield from cls._find_modules(new_path)

    @classmethod
    def find_modules(cls, path):
        result = {}
        for key, value in cls._find_modules(path):
            result[key] = value

        return result

    def write(self):
        for name, model in self.models.items():
            print(name)
            model.export(self.path)
