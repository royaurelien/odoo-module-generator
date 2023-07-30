import os
import shutil

from omg.common.exceptions import ExternalCommandFailed
from omg.common.path import apppath
from omg.common.render import (
    RIGHTS_FULL,
    RIGHTS_NO_UNLINK,
    Helper,
    InitHelper,
    ModelAccessHelper,
)
from omg.common.tools import (
    MANIFEST_FILENAME,
    convert_string_to_human_readable,
    create_dirs,
    download_to_tempfile,
    extract_to,
    get_github_archive,
    run_external_command,
    save_to,
)
from omg.core.models import Manifest
from omg.core.settings import get_settings

settings = get_settings()  # pylint: disable=C0413

MODULE_DIRECTORIES = [
    "controllers",
    "data",
    "demo",
    "i18n",
    "models",
    "report",
    "security",
    "static",
    "static/description",
    "views",
    "wizard",
]


def get_icon_filepath():
    """Return module icon filepath."""
    if settings.logo_filepath and os.path.exists(settings.logo_filepath):
        return settings.logo_filepath

    return os.path.join(apppath.images_dir, "icon.png")


class Scaffold:
    def __init__(self, source):
        self.source = source

    @classmethod
    def from_url(cls, url):
        """Return Scaffold object from url."""

        filepath = download_to_tempfile(url)

        return cls(filepath)

    def extract_to(self, path):
        """Extract archive to path."""

        os.makedirs(path, exist_ok=True)
        extract_to(self.source, path)


class RepositoryTemplate(Scaffold):
    @classmethod
    def load(cls):
        """Return RepositoryTemplate object from settings url."""
        url = get_github_archive(
            settings.odoo_repo_tmpl_name, settings.odoo_repo_tmpl_branch
        )
        return cls.from_url(url)

    def post_install_hook(self, path):  # pylint: disable=R0201
        """Execute post install hook."""

        for cmd in settings.odoo_repo_tmpl_commands:
            res = run_external_command(cmd, cwd=path)
            if not res:
                raise ExternalCommandFailed(cmd)


class ScaffoldModule(Scaffold):
    __fields__ = {
        "name": "Name (technical name)",
        "mod_name": "Module name (Human readable)",
        "mod_description": "Description",
    }

    def __init__(self, path):
        super().__init__(None)

        self.name = None
        self.path = path
        self.module_path = None
        self.values = {}
        self.manifest = None

    def _get_manifest(self, prompt_user=True):
        manifest = Manifest(technical_name=self.name)

        if not prompt_user:
            return manifest

        vals = {}
        for key in manifest.__prompt__:
            default_value = getattr(manifest, key)
            res = input(
                f"{convert_string_to_human_readable(key)} '{default_value}' ? [Y/n] : "
            )

            if not res:
                continue

            vals[key] = res

        return manifest.copy(update=vals)

    def _copy_logo(self):
        src = get_icon_filepath()
        dest = os.path.join(self.module_path, "static/description", "icon.png")
        shutil.copyfile(src, dest)

    def generate(self):
        """Create module folders."""

        root = self.module_path

        create_dirs(root, MODULE_DIRECTORIES)
        self._copy_logo()

        model_access = ModelAccessHelper(root)

        # res.partner
        helper = Helper(self.name, "res.partner", root)
        helper.render_python("module/res_partner.py.jinja2", "models")
        helper.render_xml("module/res_partner.xml.jinja2", "views")

        # custom controller
        helper = Helper(self.name, "main", root)
        helper.render_python("module/main.py.jinja2", "controllers")

        # custom model
        helper.reset(self.name, "cust.om", root)
        helper.render_python("module/new_model.py.jinja2", "models")
        helper.render_xml("module/new_model.xml.jinja2", "views")
        helper.render_xml("module/menu.xml.jinja2", "views", "menu.xml")
        helper.render_xml("module/demo.xml.jinja2", "demo", "demo.xml")
        helper.render_xml("module/security.xml.jinja2", "security", "security.xml")

        model_access.add(
            helper.model_name,
            f"{helper.module_name}.group_user",
            RIGHTS_NO_UNLINK,
        )
        model_access.add(
            helper.model_name,
            f"{helper.module_name}.group_manager",
            RIGHTS_FULL,
            "manager",
        )

        # custom wizard
        ctx = {
            "related_model_name": helper.model_name,
            "related_model_slugified": helper.model_slugified,
        }

        helper.reset(self.name, "custom.wizard", root)
        helper.render_python("module/wizard.py.jinja2", "wizard", ctx=ctx)
        helper.render_xml("module/wizard.xml.jinja2", "wizard", ctx=ctx)

        model_access.add(helper.model_name, "base.group_user", RIGHTS_FULL)

        # Save ir.model.access.csv
        model_access.save()

        # Make init files
        init_helper = InitHelper(root)
        python_dirs = ["models", "wizard", "controllers"]
        for dir_name in python_dirs:
            init_helper.render(dir_name, helper.get_python_files(dir_name))
        init_helper.render(".", python_dirs)

        # Update manifest with XML files
        views = helper.get_views()
        views["data"].insert(1, model_access.filename)

        for key, items in views.items():
            self.manifest.add_items(key, items)

        # Save manifest
        filepath = os.path.join(root, MANIFEST_FILENAME)
        content = self.manifest.dict()
        save_to(content, filepath, code=True, delete=True)

    def user_prompt(self):
        """Prepare configuration and ask user to complete if necessary."""

        technical_name = os.path.basename(self.path)
        check_name = False

        while not check_name or not technical_name:
            res = input(f"Module name: {technical_name} ? [Y/n] : ")

            if not res:
                check_name = True
                self.module_path = self.path
            else:
                technical_name = res
                check_name = True
                self.module_path = os.path.join(self.path, technical_name)

        self.name = technical_name

        # _logger.debug("Technical name: %s", technical_name)
        # _logger.debug("Module path: %s", module_path)

    def complete_manifest(self):
        """Ask user to complete manifest fields."""
        self.manifest = self._get_manifest()
