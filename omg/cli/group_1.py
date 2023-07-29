import click

from omg.common.exceptions import CommandNotImplemented
from omg.common.tools import abort_if_false
from omg.core.settings import get_settings

settings = get_settings()  # pylint: disable=C0413


@click.command()
@click.argument("name")
def command_1(name):
    """Command 1."""

    click.echo(f"Command 1: {name}")


@click.command()
@click.option(
    "--yes",
    is_flag=True,
    callback=abort_if_false,
    expose_value=False,
    prompt="Are you sure ?",
)
def command_2():
    """Command 2."""

    raise CommandNotImplemented("command_2")
