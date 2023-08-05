# pylint: disable=C0411

import click

from omg.core.settings import get_settings

settings = get_settings()  # pylint: disable=C0413

from omg.cli.scaffold import module, repo  # noqa: E402
from omg.cli.update import manifest  # noqa: E402

if not settings.is_ready and settings.ask_to_user:
    click.echo("Please fill configuration to continue :")
    settings.user_prompt()


@click.group()
def cli():
    """OMG! Odoo Module Generator"""


@click.group()
def scaffold():
    """Scaffold module or repository."""


@click.group()
def update():
    """Update commands."""


scaffold.add_command(repo)
scaffold.add_command(module)

update.add_command(manifest)

cli.add_command(scaffold)
cli.add_command(update)
