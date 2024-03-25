# pylint: disable=C0301

import getpass
import os
from functools import lru_cache

from pydantic import ValidationError
from pydantic_settings import BaseSettings

from omg.common.logger import _logger
from omg.common.path import apppath
from omg.common.tools import DEFAULT_ENCODING, save_to
from omg.core.models import DefaultManifest, RepositoryTemplate


class Settings(BaseSettings):
    __MANDATORY_VALUES__ = []
    __prompt__ = True

    log_level: str = ""
    repo_tmpl: RepositoryTemplate = RepositoryTemplate()

    default_manifest: DefaultManifest = DefaultManifest(
        author="Aurélien ROY",
        website="https://github.com/royaurelien",
        mainteners=["Aurelien ROY"],
        category="Technical",
        license="LGPL-3",
    )

    logo_filepath: str = ""

    @property
    def ask_to_user(self):
        """Ask to user."""
        return bool(self.__prompt__)

    @property
    def is_ready(self):
        """IS Ready property."""
        return bool(len(self._get_missing_values()) == 0)

    def _get_missing_values(self):
        missing_values = {
            key: False
            for key in self.__MANDATORY_VALUES__
            if not self.__dict__.get(key)
        }

        return list(missing_values.items())

    def user_prompt(self):
        """Prepare configuration and ask user to complete if necessary."""

        vals = {}
        while not self.is_ready:
            for key, _ in self._get_missing_values():
                if "password" in key:
                    vals[key] = getpass.getpass(f"{key.capitalize()}: ")
                else:
                    vals[key] = input(f"{key.capitalize()}: ")

            _logger.debug(vals)

            self.__dict__.update(vals)
            self.save()

    @staticmethod
    def _get_default_values():
        return {k: "" for k in Settings.__MANDATORY_VALUES__}

    @classmethod
    def new_file(cls, save=True):
        """Get defaults settings and save"""

        _logger.debug("Create new file.")

        self = cls(**Settings._get_default_values())
        if save:
            self.save()

        return self

    @classmethod
    def load_from_json(cls):
        """Load settings from JSON file"""

        _logger.debug("Root dir: %s", apppath.root_dir)
        _logger.debug("Load settings from '%s'.", apppath.config_filepath)

        if not os.path.exists(apppath.config_filepath):
            return cls.new_file()

        with open(apppath.config_filepath, encoding=DEFAULT_ENCODING) as file:
            data = file.read()

        if not data:
            _logger.debug("No data, create file.")
            return cls.new_file()

        try:
            self = cls.parse_raw(data)
        except ValidationError as error:
            _logger.error(error)
            _logger.debug(error.errors())
            # for item in error.errors():
            #     for key in item.get("loc"):
            #         if key in data:
            #             data.pop(key)
            #     self = cls.parse_raw(data)

        self.save()
        _logger.debug("Missing values: %s", self._get_missing_values())
        return self

    def save(self, clear=False):
        """Save settings to JSON file"""

        data = self.json()
        # _logger.debug(data)

        filepath = apppath.config_filepath

        if clear and os.path.exists(filepath):
            os.remove(filepath)

        save_to(data, filepath)

    def set_value(self, name, value, auto_save=True):
        """Set value"""

        self.__dict__[name] = value

        if auto_save:
            self.save()

    def get_value(self, name):
        """Get value"""

        try:
            value = getattr(self, name)
        except AttributeError:
            value = f"<Unknown variable '{name}'>"
        return value

    def get_default_icon_path(self):
        """Return module icon filepath."""
        if self.logo_filepath and os.path.exists(self.logo_filepath):
            return self.logo_filepath

        return os.path.join(apppath.images_dir, "icon.png")


@lru_cache()
def get_settings():
    """Return cached settings object."""

    return Settings.load_from_json()
