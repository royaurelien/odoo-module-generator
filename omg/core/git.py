import shlex
import subprocess

from omg.common.logger import _logger


class Git:
    def __init__(self, path: str) -> None:
        self.path = path

    def _run(self, cmd):
        args = shlex.split(cmd)
        _logger.error(args)
        return subprocess.check_output(args, cwd=self.path)

    def init(self):
        res = self._run(f"git init --quiet {self.path}")
        res = self._run("git add -A")
        res = self._run("git commit -m Initial commit")

        return res

    def branch(self) -> str:
        try:
            res = self._run("git branch --show-current")
            return res.rstrip().strip()
        except Exception as error:
            _logger.error(error)
            raise FileNotFoundError from error

    def checkout(self, name: str):
        try:
            res = self._run(f"git checkout -b {name}")
        except Exception as error:
            _logger.error(error)
            res = self._run(f"git checkout {name}")

        return res

    def commit(self, message: str) -> None:
        self._run("git add -A")
        self._run(f"git commit -m '{message}'")

    def revert(self) -> None:
        self._run("git checkout --")
        self._run("git reset --hard")
        self._run("git clean -fxd")
