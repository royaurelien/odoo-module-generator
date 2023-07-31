import sys

import click

from omg.common.exceptions import ExternalCommandFailed
from omg.core.repository import Repository
from omg.core.scaffold import RepositoryTemplate, ScaffoldModule
from omg.core.settings import get_settings

settings = get_settings()  # pylint: disable=C0413


@click.command()
@click.argument("path")
def repo(path):
    """Update repository."""

    repository = Repository(path)

    scaffold = RepositoryTemplate.load()
    files = scaffold.extract_to(repository.path)
    arg = " ".join(files)

    try:
        scaffold.post_install_hook(path, arg)
    except ExternalCommandFailed as error:
        click.echo(error)
        sys.exit(1)


@click.command()
@click.argument("path")
def module(path):
    """Generate module."""

    scaffold = ScaffoldModule(path)
    scaffold.user_prompt()
    scaffold.complete_manifest()

    scaffold.generate()
