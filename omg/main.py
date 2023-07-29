# -*- coding: utf-8 -*-
#!/bin/python3

import click
from tabulate import tabulate
import pandas as pd
import numpy as np

from omg.core.config import Config
from omg.core.parser import Parser
from omg.core.git import git_revert
from omg.core.xml import parse_xml_from_path, generate_model

settings = Config()


@click.group()
def cli():
    """Odoo Module Generator"""


def extract(items):
    res = []
    for item in items:
        if isinstance(item, list):
            # line = ", ".join(map(str, item))
            line = len(item)
        elif isinstance(item, dict):
            line = ", ".join([f"{k}: {v}" for k, v in item.items()])
        else:
            line = item
        res.append(line)
    return res


@click.command()
@click.argument("path")
@click.argument("output")
def xml_to_fields(path, output, **kwargs):
    res = parse_xml_from_path(path)
    for model, fields in res.items():
        file = generate_model(output, model, fields)
        with open(file.path, "w") as f:
            f.write(file.content)


@click.command()
@click.argument("path")
@click.option("--modules", "-m", required=False, type=str, help="Modules")
def stats(path, modules=None, **kwargs):
    parser = Parser.from_path(path, modules)

    # data = parser.analyze()

    data = parser._odoo.export()

    columns = {
        "index": "name",
        # "model_count": "models",
        # "record_count": "records",
    }

    df = pd.DataFrame(data).transpose()
    df.reset_index(inplace=True)
    df.rename(columns=columns, inplace=True)

    df["missing"] = np.where(df["missing_dependency"].isnull(), False, True)
    df["missing_dependency"] = df["missing_dependency"].apply(
        lambda row: ", ".join(row) if isinstance(row, list) else row
    )
    df["depends"] = df["depends"].apply(
        lambda row: ", ".join(sorted(row)) if isinstance(row, list) else row
    )
    df["language"] = df["language"].apply(
        lambda row: ", ".join([f"{k}: {v}" for k, v in row.items()])
    )
    df["missing_dependency"] = df["missing_dependency"].fillna("")
    df = df.replace([0], "-")

    selection = [
        "name",
        "author",
        "version",
        "models_count",
        "fields",
        # "record_count",
        "records_count",
        "views_count",
        "class_count",
        # "depends_count",
        "PY",
        "XML",
        "JS",
        # "missing",
        # "missing_dependency",
        # "language",
        # "duration",
        "depends",
    ]
    df = df[selection]

    def rename_columns(df):
        def transform(columns):
            def clean(name):
                name = name.replace("count", "")
                name = name.replace("_", " ")
                name = name.strip()
                name = name.capitalize()

                return name

            new_columns = map(clean, columns)
            return dict(zip(columns, new_columns))

        return df.rename(columns=transform(list(df.columns)))

    df = rename_columns(df)
    results = df.to_dict(orient="list")

    print(tabulate(results, headers="keys"))


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
cli.add_command(stats)
cli.add_command(xml_to_fields)
cli.add_command(skeleton)
