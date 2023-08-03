import os
import sys

import click

from omg.common.exceptions import ExternalCommandFailed
from omg.core.models import DefaultQuestion, YesNoQuestion
from omg.core.repository import Repository
from omg.core.scaffold import ScaffoldModule, ScaffoldRepository, prompt_manifest
from omg.core.settings import get_settings

settings = get_settings()  # pylint: disable=C0413


@click.command()
@click.argument("path")
def repo(path):
    """Update repository."""

    repository = Repository(path)

    scaffold = ScaffoldRepository.load()
    files = scaffold.extract_to(repository.path)

    if settings.repo_tmpl.commit_enable:
        repository.add(files)
        repository.commit(settings.repo_tmpl.commit_message)

    try:
        scaffold.post_install_hook(path)
    except ExternalCommandFailed as error:
        click.echo(error)
        sys.exit(1)


@click.command()
@click.argument("path")
def module(path):
    """Generate module."""

    scaffold = ScaffoldModule(path)

    # Validate module name and path
    module_name = os.path.basename(path)
    scaffold.name = DefaultQuestion(
        question="Module name: ",
        default=module_name,
    ).prompt()

    if scaffold.name == module_name:
        scaffold.module_path = path
    else:
        scaffold.module_path = os.path.join(path, module_name)

    manifest = prompt_manifest()

    # Custom model
    scaffold.add_model = YesNoQuestion(
        question="Would you like to add a custom model ?", default=False
    ).prompt()

    if scaffold.add_model:
        scaffold.model_name = DefaultQuestion(
            question="Model name: ", default="custom.model"
        ).prompt()

    # Generate
    scaffold.generate(manifest)
