import ast
import os

import click

from omg.common.logger import _logger
from omg.common.tools import copy_file, find_modules, get_absolute_path, save_to

# from omg.common.exceptions import ExternalCommandFailed
from omg.core.scaffold import prompt_manifest
from omg.core.settings import get_settings

settings = get_settings()  # pylint: disable=C0413


@click.command("manifest")
@click.argument("path")
@click.option("--icon", "-i", is_flag=True, help="Copy default icon")
def cmd_manifest(path, **kwargs):
    """Update repository."""

    copy_icon = kwargs.get("icon", False)
    path = get_absolute_path(path)
    modules = find_modules(path)

    default_icon = settings.get_default_icon_path()

    manifest = prompt_manifest()

    for name in modules:
        if os.path.basename(path) == name:
            module_path = path
        else:
            module_path = os.path.join(path, name)
        manifest_filepath = os.path.join(module_path, "__manifest__.py")
        desc_path = os.path.join(module_path, "static/description")
        icon_filepath = os.path.join(desc_path, "icon.png")

        _logger.warning("manifest: %s", manifest_filepath)

        if not os.path.exists(manifest_filepath):
            click.echo("Module '{name}' has no manifest.")
            continue

        with open(manifest_filepath, encoding="utf8") as file:
            data = ast.literal_eval(file.read())
            _logger.error(data)
            manifest = manifest.update(data)

        _logger.debug("manifest updated: %s", manifest)

        content = manifest.prepare_to_save()
        save_to(content, manifest_filepath, code=True)

        if copy_icon:
            os.makedirs(desc_path, exist_ok=True)
            copy_file(default_icon, icon_filepath)

        _logger.debug(content)
