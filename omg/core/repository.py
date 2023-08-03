import os

from git import GitCommandError, InvalidGitRepositoryError, Repo

from omg.common.logger import _logger
from omg.common.tools import get_absolute_path


class Repository:
    def __init__(self, path):
        self.path = get_absolute_path(path)

        os.makedirs(path, exist_ok=True)

        try:
            self.repo = Repo(path)
        except InvalidGitRepositoryError:
            self.repo = Repo.init(path)

    @property
    def git(self):
        return self.repo.git

    def add(self, files):
        self.git.add(files)

    def commit(self, message):
        try:
            self.git.commit(f"-m {message}")
        except GitCommandError as error:
            _logger.error(error)
