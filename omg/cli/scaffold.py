import sys

import click

from omg.common.exceptions import ExternalCommandFailed
from omg.common.logger import _logger
from omg.common.render import generate_manifest
from omg.core.scaffold import RepositoryTemplate, ScaffoldModule
from omg.core.settings import get_settings

settings = get_settings()  # pylint: disable=C0413


@click.command()
@click.argument("path")
def repo(path):
    """Command 1."""

    scaffold = RepositoryTemplate.load()
    scaffold.extract_to(path)

    try:
        scaffold.post_install_hook(path)
    except ExternalCommandFailed as error:
        click.echo(error)
        sys.exit(1)


@click.command()
@click.argument("path")
def module(path):
    """Command 1."""

    scaffold = ScaffoldModule(path)
    scaffold.user_prompt()
    manifest = scaffold.get_manifest()

    _logger.debug(manifest.model_dump())

    print(manifest.model_dump())

    scaffold.create_dirs()
    generate_manifest(manifest.dict(), scaffold.module_path)
