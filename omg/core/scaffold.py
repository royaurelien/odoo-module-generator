import os
import shutil

from omg.common.exceptions import ExternalCommandFailed
from omg.common.logger import _logger
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
from omg.core.models import DefaultListQuestion, DefaultQuestion, Manifest
from omg.core.repository import Repository
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


class Scaffold:
    source: str = ""

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
        files = extract_to(self.source, path)

        _logger.debug("files: %s", files)

        return files


class ScaffoldRepository(Scaffold):
    @classmethod
    def load(cls):
        """Return RepositoryTemplate object from settings url."""
        url = get_github_archive(settings.repo_tmpl.name, settings.repo_tmpl.branch)
        return cls.from_url(url)

    def post_install_hook(self, path, *args):  # pylint: disable=R0201
        """Execute post install hook."""

        for i, cmd in enumerate(settings.repo_tmpl.post_hook, 1):
            _logger.debug("Run %s/%s: %s", i, len(settings.repo_tmpl.post_hook), cmd)

            res = run_external_command(cmd, cwd=path)
            if not res:
                raise ExternalCommandFailed(cmd)

    def get_repository(self):
        """Return Repository object from source path."""

        return Repository(self.source)


def prompt_manifest():
    """Ask user to complete Manifest values."""

    default_values = settings.default_manifest.dict()

    vals = {}
    for key, value in default_values.items():
        if isinstance(value, list):
            question = DefaultListQuestion
        else:
            question = DefaultQuestion

        vals[key] = question(
            question=convert_string_to_human_readable(key),
            default=value,
        ).prompt()

    return Manifest(**vals)


class ScaffoldModule(Scaffold):
    name: str = None
    path: str = None
    module_path: str = None
    values: dict = {}

    add_model: bool = False
    model_name: str = None

    def __init__(self, path):
        super().__init__(None)
        self.path = path

    def _copy_icon(self):
        src = settings.get_default_icon_path()
        dest = os.path.join(self.module_path, "static/description", "icon.png")
        shutil.copyfile(src, dest)

    def generate(self, manifest: Manifest):
        """Create module folders."""

        root = self.module_path

        create_dirs(root, MODULE_DIRECTORIES)
        self._copy_icon()

        model_access = ModelAccessHelper(root)

        # res.partner
        helper = Helper(self.name, "res.partner", root)
        helper.render_python("module/res_partner.py.jinja2", "models")
        helper.render_xml("module/res_partner.xml.jinja2", "views")

        # custom controller
        helper.reset(self.name, "main", root)
        helper.render_python("module/main.py.jinja2", "controllers")

        # custom model
        if self.add_model and self.model_name:
            helper.reset(self.name, self.model_name, root)
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
            manifest.add_items(key, items)

        # Save manifest
        filepath = os.path.join(root, MANIFEST_FILENAME)

        # content = manifest.dict()
        content = manifest.prepare_to_save()
        _logger.debug(content)

        save_to(content, filepath, code=True, delete=True)
