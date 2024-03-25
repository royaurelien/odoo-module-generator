# pylint: disable=C0411
import ast
import os
import sys

import click

from omg.common.exceptions import ExternalCommandFailed
from omg.common.logger import _logger
from omg.common.tools import copy_file, find_modules, get_absolute_path, save_to
from omg.core.git import Git
from omg.core.models import DefaultQuestion, YesNoQuestion
from omg.core.repository import Repository
from omg.core.scaffold import ScaffoldModule, ScaffoldRepository, prompt_manifest
from omg.core.settings import get_settings
from omg.odoo import Odoo  # noqa: E402

# from omg.common.exceptions import ExternalCommandFailed

settings = get_settings()  # pylint: disable=C0413

if not settings.is_ready and settings.ask_to_user:
    click.echo("Please fill configuration to continue :")
    settings.user_prompt()


@click.group()
def cli():
    """OMG! Odoo Module Generator"""


@click.group()
def scaffold():
    """Scaffold module or repository."""


@click.command("repo")
@click.argument("path")
def scaffold_repository(path):
    """Scaffold repository."""

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


@click.command("module")
@click.argument("path")
def scaffold_module(path):
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


@click.command("manifest")
@click.argument("path")
@click.option("--icon", "-i", is_flag=True, help="Copy default icon")
def update_manifest(path, **kwargs):
    """Update manifest."""

    copy_icon = kwargs.get("icon", False)
    path = get_absolute_path(path)
    modules = find_modules(path)

    default_icon = settings.get_default_icon_path()

    manifest = prompt_manifest()

    for name in modules:
        if os.path.basename(path) == name:
            module_path = path
        else:
            module_path = os.path.join(path, name)
        manifest_filepath = os.path.join(module_path, "__manifest__.py")
        desc_path = os.path.join(module_path, "static/description")
        icon_filepath = os.path.join(desc_path, "icon.png")

        _logger.warning("manifest: %s", manifest_filepath)

        if not os.path.exists(manifest_filepath):
            click.echo("Module '{name}' has no manifest.")
            continue

        with open(manifest_filepath, encoding="utf8") as file:
            data = ast.literal_eval(file.read())
            manifest = manifest.update(data)

        _logger.debug("manifest updated: %s", manifest)

        content = manifest.prepare_to_save()
        save_to(content, manifest_filepath, code=True)

        if copy_icon:
            os.makedirs(desc_path, exist_ok=True)
            copy_file(default_icon, icon_filepath)

        # _logger.debug(content)


@click.command()
@click.argument("path")
@click.argument("version")
@click.option("--no-clean", "-n", is_flag=True, help="Preserve files")
@click.option("--commit", "-c", is_flag=True, help="Auto-commit")
@click.option("--rename", "-r", is_flag=True, help="Rename fields")
def codebase(
    path: str,
    version: str,
    no_clean: bool = False,
    commit: bool = False,
    rename: bool = False,
):
    """Generate code base from source."""

    if commit:
        git = Git(path)
        branch = "codebase"
        current_branch = git.branch()

        if current_branch != branch:
            git.checkout(branch)

    odoo = Odoo.load_path(path)

    for name, module in odoo.modules.items():
        module.set_version(version)
        module.write(clean=not no_clean)

        if rename:
            module.rename()

        if commit:
            git.commit(f"[IMP] {name}: codebase")


@click.command()
@click.argument("path")
def skeleton(path):
    """Transform to skeleton module."""

    Odoo.load_path(path)


scaffold.add_command(scaffold_repository)
scaffold.add_command(scaffold_module)
cli.add_command(update_manifest)
cli.add_command(scaffold)
cli.add_command(codebase)
cli.add_command(skeleton)
