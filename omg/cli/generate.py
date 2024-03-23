import click

# import numpy as np
# import pandas as pd
# from tabulate import tabulate


# from omg.core.git import git_revert
from omg.core.parser import Parser

# from omg.core.xml import generate_model, parse_xml_from_path

from omg.core.settings import get_settings

settings = get_settings()  # pylint: disable=C0413


@click.command()
@click.argument("path")
@click.argument("output")
def generate(path, output):
    """Generate level-1 base code from source."""

    parser = Parser.from_path(path)
    parser.write(output)
