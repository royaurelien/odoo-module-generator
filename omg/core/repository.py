import os

from git import InvalidGitRepositoryError, Repo

from omg.common.tools import get_absolute_path


class Repository:
    def __init__(self, path):
        self.path = get_absolute_path(path)

        os.makedirs(path, exist_ok=True)

        try:
            self.git = Repo(path)
        except InvalidGitRepositoryError:
            self.git = Repo.init(path)
