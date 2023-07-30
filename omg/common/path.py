import os

from platformdirs import PlatformDirs

from omg.common.logger import _logger
from omg.common.meta import SingletonMeta

APP_NAME = "omg"
AUTHOR = "Aurelien ROY"
CONFIG_FILENAME = "config.json"
ROOT_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__), ".."))
TEMPLATE_DIR = False


class Path(metaclass=SingletonMeta):
    def __init__(self, app_name, author, config_filename):
        self._dirs = PlatformDirs(app_name, author)
        self.config_filename = config_filename

        self._make_dirs()

    @property
    def root_dir(self):
        """Root directory."""
        return os.path.realpath(os.path.join(os.path.dirname(__file__), ".."))

    @property
    def static_dir(self):
        """Static directory."""
        return os.path.join(self.root_dir, "static")

    @property
    def template_dir(self):
        """Templates directory."""
        return os.path.join(self.root_dir, "static/templates")

    @property
    def images_dir(self):
        """Images directory."""
        return os.path.join(self.root_dir, "static/img")

    @property
    def config_dir(self):
        """Configuration directory."""

        return self._dirs.user_data_dir

    @property
    def config_filepath(self):
        """Configuration filepath."""

        return os.path.join(self.config_dir, self.config_filename)

    def _make_dirs(self):
        os.makedirs(self.config_dir, exist_ok=True)
        _logger.debug("Config dir: %s", self.config_dir)


apppath = Path(APP_NAME, AUTHOR, CONFIG_FILENAME)
