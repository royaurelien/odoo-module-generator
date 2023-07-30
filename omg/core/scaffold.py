import os
import shutil

from omg.common.exceptions import ExternalCommandFailed
from omg.common.logger import _logger
from omg.common.path import path
from omg.common.tools import (
    download_to_tempfile,
    extract_to,
    get_github_archive,
    run_external_command,
)
from omg.core.models import Manifest
from omg.core.security import Security
from omg.core.settings import get_settings

settings = get_settings()  # pylint: disable=C0413


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
        self.source = None
        self.name = None
        self.path = path
        self.module_path = None
        self.values = {}

    # def _get_missing_values(self):
    #     return {
    #         k: v for k, v in self.__fields__.items() if not self.values.get(k)
    #     }.items()

    # @property
    # def is_ready(self):
    #     return len(self._get_missing_values()) == 0

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

    def get_manifest(self, prompt_user=True):
        manifest = Manifest(technical_name=self.name)

        if not prompt_user:
            return manifest

        vals = {}
        for key in manifest.__prompt__:

            def format_key(item):
                return item.replace("_", " ").capitalize()

            default_value = getattr(manifest, key)
            res = input(f"{format_key(key)} '{default_value}' ? [Y/n] : ")

            if not res:
                continue

            vals[key] = res

        return manifest.copy(update=vals)

    def create_dirs(self):
        """Create module folders."""

        root = self.module_path
        dirs = [
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

        for name in dirs:
            os.makedirs(os.path.join(root, name), exist_ok=True)

        if settings.logo_filepath and os.path.exists(settings.logo_filepath):
            src = settings.logo_filepath
        else:
            src = os.path.join(path.images_dir, "icon.png")

        dest = os.path.join(root, "static/description", "icon.png")
        _logger.warning(src)

        shutil.copyfile(src, dest)

        model_access = [
            {
                "id": "access_new_model",
                "name": "access_new_model",
                "model_id": "model_new_model",
                "group_id": "custom_module.group_user",
                "perm_read": True,
                "perm_write": True,
                "perm_create": True,
                "perm_unlink": False,
            },
            {
                "id": "access_new_model_manager",
                "name": "access_new_model_manager",
                "model_id": "model_new_model",
                "group_id": "custom_module.group_manager",
                "perm_read": True,
                "perm_write": True,
                "perm_create": True,
                "perm_unlink": True,
            },
        ]

        security = Security()
        security.new_model_access(model_access)
        security.generate_ir_model_access(root)
