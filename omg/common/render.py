import os

from jinja2 import Environment, FileSystemLoader
from jinja2.exceptions import UndefinedError

# from omg.common.exceptions import DownloadError
from omg.common.logger import _logger
from omg.common.path import path
from omg.common.tools import (
    DEFAULT_ENCODING,
    MANIFEST_FILENAME,
    dot_name_to_camel_case,
    dot_name_to_human,
    format_code,
    save_to,
    slugify,
)


def generate_manifest(content: dict, path: str) -> bool:
    content = format_code(content)

    filepath = os.path.join(path, MANIFEST_FILENAME)

    if os.path.exists(filepath):
        os.remove(filepath)

    with open(filepath, "w+", encoding=DEFAULT_ENCODING) as file:
        file.write(content)

    return True


def render(template: str, data: dict = {}, functions: dict = {}) -> str:
    filename = os.path.basename(template)
    part = template.replace(filename, "")
    complete_path = os.path.join(path.template_dir, part)

    _logger.warning(complete_path)

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


class Helper:
    def __init__(self, module_name, model_name, path):
        self.model_name = model_name
        self.root_path = path
        self.module_name = module_name
        self._files = {}

    @property
    def model_slugified(self):
        return slugify(self.model_name)

    @property
    def class_name(self):
        return dot_name_to_camel_case(self.model_name)

    @property
    def model_description(self):
        return dot_name_to_human(self.model_name)

    def _get_context(self):
        return {
            "module_name": self.module_name,
            "class_name": self.class_name,
            "model_name": self.model_name,
            "model_description": self.model_description,
            "model_slugified": self.model_slugified,
        }

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
        self._render_to(template, dest, "py", filename, **kwargs)

    def render_xml(self, template, dest, filename=None, **kwargs):
        self._render_to(template, dest, "xml", filename, **kwargs)

    def reset(self, module_name, model_name, path):
        self.model_name = model_name
        self.root_path = path
        self.module_name = module_name
