# -*- coding: utf-8 -*-
#!/bin/python3

import click

from omg.core.config import Config
from omg.core.parser import Parser
from omg.core.git import git_revert

settings = Config()


@click.group()
def cli():
    """Odoo Module Generator"""


@click.command()
@click.argument("path")
def parse(path, **kwargs):
    parser = Parser.from_path(path)
    for module in parser.get_modules():
        module.skeleton()


@click.command()
@click.argument("path")
@click.option("--modules", "-m", required=True, type=str, help="Modules")
@click.option("--branch", "-b", required=True, type=str, help="Branch")
@click.option(
    "--revert", "-r", is_flag=True, default=False, type=bool, help="Revert changes"
)
def skeleton(path, modules, branch, revert, **kwargs):
    if revert:
        git_revert(path)
        exit(0)

    parser = Parser.from_path(path, modules)
    parser.skeleton(branch)


@click.command()
@click.argument("name")
@click.argument("value")
def set(name, value, **kwargs):
    settings.set_value(name, value)


@click.command()
def get(**kwargs):
    for k, v in settings.options._asdict().items():
        print(f"{k}: {v}".format(k, v))


@click.group()
def config():
    """Configuration"""


config.add_command(set)
config.add_command(get)

cli.add_command(config)
cli.add_command(parse)
cli.add_command(skeleton)
