#!/bin/python3

import json
import os
from collections import namedtuple
from pathlib import Path

Options = namedtuple("Options", ["url", "authenable", "authmethod"])

DEFAULT_OPTIONS = {
    "author": "Aurelien ROY",
    "website": "https://odoo.com",
}
CONFIG_FILE = "odoo-module-generator.json"


def get_config_filepath():
    parts = [Path.home(), ".config", CONFIG_FILE]
    return os.path.join(*parts)


def read_from_json(path):
    with open(path) as file:
        data = json.loads(file.read())

    return data


def save_to_json(path, data):
    with open(path, "w") as file:
        file.write(json.dumps(data))


class Config:
    options: Options = None

    def __init__(self, **kwargs):
        self._path = get_config_filepath()

        if not os.path.exists(self._path):
            self.create_default()
        else:
            self.load()

    def create_default(self):
        self.options = Options(**DEFAULT_OPTIONS)
        data = self.options._asdict()

        save_to_json(self._path, data)

    def save(self):
        data = read_from_json(self._path)
        data.update(self.options._asdict())

        save_to_json(self._path, data)

    def load(self):
        if not os.path.exists(self._path):
            raise FileNotFoundError

        data = read_from_json(self._path)

        self.options = Options(**data)

    def set_value(self, name, value):
        self.options[name] = value
