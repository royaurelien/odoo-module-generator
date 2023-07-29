import os
import sys

from omg.common.logger import _logger
from omg.common.tools import download_to_tempfile, extract_to, run_external_command
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

        return cls.from_url(settings.odoo_repository_url)

    def install(self, path):  # pylint: disable=R0201
        """Install pre-commit."""

        cmd = "pre-commit install"
        # cmd = "pre-commit run --all-files"

        res = run_external_command(cmd, cwd=path)
        _logger.warning(res)

        if not res:
            sys.exit(1)

        cmd = "pre-commit run --all-files"
        res = run_external_command(cmd, result=False, cwd=path)
