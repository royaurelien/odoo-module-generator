# -*- coding: utf-8 -*-
#!/bin/python3

import json

message = """
Please install git package first.
"""

try:
    from sh import git
    from sh import ErrorReturnCode_128
except ImportError as error:
    print(message)
    exit(1)


def git_init(path):
    res = git(["init", "--quiet"], _cwd=path)
    res = git(["add", "-A"], _cwd=path)
    res = git(["commit", "-m", "Initial commit"], _cwd=path)


def git_branch(path):
    res = False
    # print(path)

    try:
        res = git(["branch", "--show-current"], _cwd=path)
        res = res.rstrip().strip()
    except ErrorReturnCode_128:
        # print("pas de depot")
        git_init(path)
        return git_branch(path)

    return res


def git_checkout(path, name):
    try:
        res = git(["checkout", "-b", name], _cwd=path)
    except ErrorReturnCode_128:
        res = git(["checkout", name], _cwd=path)


def git_revert(path):
    git.checkout(["--"], _cwd=path)
    git.reset(["--hard"], _cwd=path)
    git.clean(["-fxd"], _cwd=path)
