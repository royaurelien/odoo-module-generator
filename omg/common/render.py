import csv
import os
from collections import namedtuple

from jinja2 import Environment, FileSystemLoader
from jinja2.exceptions import UndefinedError

# from omg.common.exceptions import DownloadError
from omg.common.logger import _logger
from omg.common.path import apppath
from omg.common.tools import (
    DEFAULT_ENCODING,
    dot_name_to_camel_case,
    dot_name_to_human,
    dot_name_to_snake_case,
    get_python_filenames,
    get_xml_files,
    save_to,
)
from omg.core.models import IrModelAccess, IrModelAccessLine

INIT_FILENAME = "__init__.py"
IR_MODEL_ACCESS_FILENAME = "ir.model.access.csv"
CRUD_FIELDS = [
    "perm_read",
    "perm_write",
    "perm_create",
    "perm_unlink",
]


CrudLevel = namedtuple("CrudLevel", CRUD_FIELDS)

RIGHTS_FULL = CrudLevel(True, True, True, True)
RIGHTS_NO_UNLINK = CrudLevel(True, True, True, False)
RIGHTS_READONLY = CrudLevel(True, False, False, False)


def render(template: str, data: dict = None, functions: dict = None) -> str:
    """Render template."""

    filename = os.path.basename(template)
    part = template.replace(filename, "")
    complete_path = os.path.join(apppath.template_dir, part)

    jinja_env = Environment(loader=FileSystemLoader(complete_path))
    jinja_template = jinja_env.get_template(filename)

    if functions:
        jinja_template.globals.update(functions)

    try:
        content = jinja_template.render(**data)
    except UndefinedError as error:
        _logger.error(error)
        content = False

    return content


class ModelHelper:
    def __init__(self, module_name, model_name, path):
        self.model_name = model_name
        self.root_path = path
        self.module_name = module_name
        self._files = {}

    @property
    def model_slugified(self):
        """Slugified model name."""
        return dot_name_to_snake_case(self.model_name)

    @property
    def class_name(self):
        """Class name."""
        return dot_name_to_camel_case(self.model_name)

    @property
    def model_description(self):
        """Model description."""
        return dot_name_to_human(self.model_name)

    def _get_context(self):
        return {
            "module_name": self.module_name,
            "class_name": self.class_name,
            "model_name": self.model_name,
            "model_description": self.model_description,
            "model_slugified": self.model_slugified,
        }


class ModelAccessHelper:
    def __init__(self, path):
        self.path = path
        self.ir_model_access = IrModelAccess()

    @property
    def void(self):
        return not bool(self.ir_model_access)

    @property
    def filename(self):
        """Model access filename."""
        return os.path.join("security", IR_MODEL_ACCESS_FILENAME)

    @property
    def filepath(self):
        """Model access filepath."""
        return os.path.join(self.path, self.filename)

    def add(self, model, group, crud, suffix=None):
        """Add ir.model.access line."""
        model = dot_name_to_snake_case(model)

        name = f"access_{model}"
        if suffix:
            name = f"{name}_{suffix}"

        vals = {
            "id": name,
            "name": name,
            "model_id": f"model_{model}",
            "group_id": group,
            "perm_read": int(crud.perm_read),
            "perm_write": int(crud.perm_write),
            "perm_create": int(crud.perm_create),
            "perm_unlink": int(crud.perm_unlink),
        }

        line = IrModelAccessLine(**vals)
        self.ir_model_access.lines.append(line)

    def save(self):
        """Save to ir.model.access.csv"""

        fieldnames = IrModelAccess.header()

        path = os.path.dirname(self.filepath)
        os.makedirs(path, exist_ok=True)

        with open(self.filepath, "w", encoding=DEFAULT_ENCODING, newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()

            for line in self.ir_model_access.lines:
                writer.writerow(line.to_csv())


class Helper(ModelHelper):
    def _add_to_files(self, dest, filename):
        self._files.setdefault(dest, [])
        self._files[dest].append(filename)

    def _render(self, template, **kwargs):
        context = self._get_context()
        new_context = kwargs.get("ctx", {})
        context.update(new_context)

        content = render(template, context)

        return content

    def _render_to(self, template, dest, extension, filename=None, **kwargs):
        if not filename:
            filename = f"{self.model_slugified}.{extension}"
        filepath = os.path.join(self.root_path, dest, filename)

        content = self._render(template, **kwargs)

        save_to(content, filepath)

        self._add_to_files(dest, filename)

    def render_python(self, template, dest, filename=None, **kwargs):
        """Render Python file."""
        self._render_to(template, dest, "py", filename, **kwargs)

    def render_xml(self, template, dest, filename=None, **kwargs):
        """Render XML file."""
        self._render_to(template, dest, "xml", filename, **kwargs)

    def reset(self, module_name, model_name, path):
        """Reset Helper."""
        self.model_name = model_name
        self.root_path = path
        self.module_name = module_name

    def get_python_files(self, dir_name):
        """Get Python files."""
        return get_python_filenames(self._files.get(dir_name, []))

    def get_views(self):
        """Get XML files."""
        keys = ["views", "wizard", "demo", "data", "report", "security"]
        files = {}

        _logger.debug(self._files)

        for key in keys:
            files.setdefault(key, [])
            items = get_xml_files(self._files.get(key, []))
            # pylint: disable=W0640
            files[key] += list(map(lambda item: os.path.join(key, item), items))

        # Reorder and merge most of views in data entry.
        new_data = files.pop("security")
        new_data += files["data"]
        new_data += files.pop("views")
        new_data += files.pop("wizard")
        new_data += files.pop("report")
        files["data"] = new_data

        _logger.debug(files)
        return files


class InitHelper:
    def __init__(self, path):
        self.root_path = path

    def render(self, dest, modules):
        """Render Python __init__ file."""
        filepath = os.path.join(self.root_path, dest, INIT_FILENAME)
        context = {"modules": modules}

        content = render("module/init.jinja2", context)
        save_to(content, filepath)
