import click

from omg.core.scaffold import RepositoryTemplate
from omg.core.settings import get_settings

settings = get_settings()  # pylint: disable=C0413


@click.command()
@click.argument("path")
def install(path):
    """Command 1."""

    # scaffold = Scaffold.from_url(settings.odoo_repository_url)
    # scaffold.extract_to(path)

    scaffold = RepositoryTemplate.load()
    scaffold.extract_to(path)
    scaffold.install(path)
