import ast
import os

import click

from omg.common.logger import _logger
from omg.common.tools import find_modules, get_absolute_path, save_to

# from omg.common.exceptions import ExternalCommandFailed
from omg.core.scaffold import prompt_manifest
from omg.core.settings import get_settings

settings = get_settings()  # pylint: disable=C0413


@click.command()
@click.argument("path")
def manifest(path):
    """Update repository."""

    path = get_absolute_path(path)
    modules = find_modules(path)
    # click.echo(modules)

    manifest = prompt_manifest()

    for name in modules:
        module_path = os.path.join(path, name)
        manifest_filepath = os.path.join(module_path, "__manifest__.py")

        with open(manifest_filepath, encoding="utf8") as file:
            data = ast.literal_eval(file.read())
            manifest.update(data)

        _logger.debug(manifest)

        content = manifest.prepare_to_save()
        save_to(content, manifest_filepath, code=True)

        _logger.debug(content)
