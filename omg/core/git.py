import subprocess

from omg.common.logger import _logger


class Git:
    def __init__(self, path: str) -> None:
        self.path = path

    def _run(self, *args):
        return subprocess.check_call(["git"] + list(args), cwd=self.path)

    def init(self):
        res = self._run(["init", "--quiet", self.path])
        res = self._run(["add", "-A"])
        res = self._run(["commit", "-m", "Initial commit"])

        return res

    def branch(self) -> str:
        try:
            res = self._run(["branch", "--show-current"])
            return res.rstrip().strip()
        except Exception as error:
            _logger.error(error)
            self.init()
            return self.branch()

    def checkout(self, name: str):
        try:
            res = self._run(["checkout", "-b", name])
        except Exception as error:
            _logger.error(error)
            res = self._run(["checkout", name])

        return res

    def revert(self) -> None:
        self._run.checkout(["--"])
        self._run.reset(["--hard"])
        self._run.clean(["-fxd"])
