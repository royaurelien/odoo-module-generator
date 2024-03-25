import ast
import json
import mimetypes
import os
import pkgutil
import shutil
import subprocess
import tarfile
import tempfile
from collections import namedtuple

import black
import jinja2
import requests
from black.parsing import InvalidInput
from jinja2.exceptions import UndefinedError
from requests.exceptions import HTTPError

from omg.common.exceptions import DownloadError
from omg.common.logger import _logger, logs

DEFAULT_ENCODING = "utf8"
DEFAULT_TIMEOUT = 60
MANIFEST_FILENAME = "__manifest__.py"
TEMPLATE_DIR = os.path.abspath("omg/static/templates/old/")

HEADER = r"""
#
#      ____  __  __  _____
#     / __ \|  \/  |/ ____|
#    | |  | | \  / | |  __
#    | |  | | |\/| | | |_ |
#    | |__| | |  | | |__| |
#     \____/|_|  |_|\_____|
#
#
{}

""".format


File = namedtuple("File", ["name", "path", "content"])


def fix_indentation(filepath):
    """Fixes the indentation of a file"""
    result = False
    with open(filepath, "r+", encoding="utf-8") as fp:
        buf = fp.read()

    with open(filepath, "w+", encoding="utf-8") as fp:
        for line in buf.splitlines():
            left = ""
            for c in line:
                if c == " ":
                    left += c
                elif c == "\t":
                    left += " " * (4 - len(left) % 4)
                    result = True
                else:
                    break
            fp.write(f"{left}{line.strip()}\n")

    return result


def try_automatic_port(filepath):
    """Tries to port a python 2 script to python 3 using 2to3"""
    cmd = shutil.which("2to3")
    if cmd is None:
        return False

    with subprocess.Popen(
        [cmd, "-n", "-w", filepath],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ) as proc:
        proc.communicate()
    return True


def generate(template: str, data: dict, filename: str, functions=None) -> File:
    code = generate_code(template, data, functions)
    file = generate_file(filename, code)

    return file


def generate_code(template: str, data: dict, functions=None) -> str:
    # _logger.error(TEMPLATE_DIR)
    jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATE_DIR))
    jinja_template = jinja_env.get_template(template)

    if functions:
        jinja_template.globals.update(functions)

    try:
        code = jinja_template.render(**data)
        # code = format_str(code, mode=FileMode())
    except UndefinedError as error:
        _logger.error(error)
        code = False
    except InvalidInput as error:
        _logger.error(error)
        exit(1)

    return code


def generate_file(filename: str, content: str) -> File:
    filepath = f"{filename}.py"

    return File(name=filename, path=filepath, content=content)


def get_assign(src):
    def function(obj):
        for child in obj.body:
            if isinstance(child, ast.ClassDef):
                return function(child)
            if isinstance(child, ast.Assign):
                return child

    # src = format_str(src, mode=FileMode())
    src = src.strip('"')
    # print(src)
    obj = ast.parse(src)
    return function(obj)


def get_arg(obj):
    value = obj

    if isinstance(value, ast.Constant):
        value = value.value
    elif isinstance(value, ast.List):
        result = []

        for child in value.elts:
            res = []
            if isinstance(child, ast.Tuple):
                for cc in child.elts:
                    if isinstance(cc, ast.Constant):
                        res.append(cc.value)
                        continue
                    if isinstance(cc, ast.Call):
                        tmp = f"{cc.func.id}({cc.args[0].value})"
                        res.append(tmp)
                        continue
            result.append(res)
        # print(result)
        value = ast.dump(value)

        # value = ast.literal_eval(value)

        # print(value)
        # exit(1)
    # else:
    #     print(type(obj))
    #     exit(1)

    # return f'"{value}"'
    return value


def get_keyword(obj):
    name = obj.arg
    value = obj.value

    if isinstance(value, ast.Constant):
        value = value.value

    return (name, value)


def dict_to_list(data, keys=None):
    def function(item):
        return f'{item}="{data[item]}"'

    if keys:
        items = filter(lambda x: x in keys, data)
    else:
        items = data

    return list(map(function, items))


def copy_file(source, destination):
    """Copy file from source to destination."""
    shutil.copyfile(source, destination)


def find_modules(path):
    """Search for Odoo modules at path"""
    # path = get_absolute_path(path)
    modules = list(pkgutil.walk_packages([path]))

    # _logger.warning(modules)

    # Is path a package?
    res = [
        os.path.basename(item.module_finder.path)
        for item in filter(lambda item: item.name == "__manifest__", modules)
    ]

    if not res:
        res = [item.name for item in filter(lambda item: item.ispkg, modules)]

    return list(set(res))


def get_absolute_path(path):
    """Return absolute path."""
    new_path = os.path.abspath(path)
    _logger.debug("Absolute path: %s", new_path)

    return new_path


def format_code(data):
    """Apply Black formatting on code."""
    data = str(data)

    return black.format_str(data, mode=black.Mode())


def save_to(content, filepath, **kwargs):
    """Save content to filepath."""

    code = bool(kwargs.get("code", False))
    delete = bool(kwargs.get("delete", False))
    header = bool(kwargs.get("header", False))
    mode = kwargs.get("mode", "w+")

    if header:
        content = HEADER(content)

    if code:
        content = format_code(content)

    if delete and os.path.exists(filepath):
        os.remove(filepath)

    with open(filepath, mode, encoding=DEFAULT_ENCODING) as file:
        file.write(content)


def save_code(content, filepath):
    return save_to(content, filepath, mode="w", header=True, code=True)


def abort_if_false(ctx, _, value):
    """Confirm: Abort if false."""

    if not value:
        ctx.abort()


@logs
def run_external_command(cmd, **kwargs):
    """Run system command and return result."""

    result = kwargs.pop("result", True)

    if isinstance(cmd, str):
        cmd = cmd.split(" ")

    try:
        if result:
            res = subprocess.check_output(cmd, **kwargs)
        else:
            subprocess.call(cmd, **kwargs)
            res = True
    except FileNotFoundError as error:
        _logger.error(error)
        return False
    except subprocess.CalledProcessError as error:
        _logger.error(error)
        return False

    if isinstance(res, bytes):
        res = res.decode("utf8")

    if isinstance(res, str) and len(res) == 0:
        res = True

    _logger.debug("Result: '%s'", res)

    return res


def nested_set(dic, keys, value):
    """Update nested dict."""
    for key in keys[:-1]:
        dic = dic.setdefault(key, {})
    dic[keys[-1]] = value


def dict_merge(dct, merge_dct):
    """Recursive dict merge. Inspired by :meth:``dict.update()``, instead of
    updating only top-level keys, dict_merge recurses down into dicts nested
    to an arbitrary depth, updating keys. The ``merge_dct`` is merged into
    ``dct``.
    :param dct: dict onto which the merge is executed
    :param merge_dct: dct merged into dct
    :return: None
    """
    for key, _ in merge_dct.items():
        if (
            key in dct
            and isinstance(dct[key], dict)
            and isinstance(merge_dct[key], dict)
        ):  # noqa
            dict_merge(dct[key], merge_dct[key])
        else:
            dct[key] = merge_dct[key]


def convert_stdout_to_json(content):
    """Convert stdout bytes to json array."""

    try:
        data = json.loads(content)
    except json.decoder.JSONDecodeError:
        content = content.decode("utf8")
        content = content.strip().rstrip().lstrip()
        content = f"[{content}]"
        content = content.replace("}", "},").replace("},]", "}]")

        data = json.loads(content)

    return data


# def download_file(url, filepath, force=False, **kwargs):
#     """Generic method to download file."""

#     filename = os.path.basename(filepath)
#     headers = kwargs.get("headers", {})

#     if force and os.path.exists(filepath):
#         _logger.debug("Remove %s file", filepath)
#         os.remove(filepath)

#     try:
#         response = requests.get(
#             url,
#             headers=headers,
#             allow_redirects=False,
#             timeout=DEFAULT_TIMEOUT,
#         )
#         response.raise_for_status()
#     except HTTPError as error:
#         code = error.response.status_code
#         raise DownloadError(filename, url, code) from error

#     with open(filepath, "wb") as file:
#         file.write(response.content)

#     return True


def download_to_tempfile(url, raise_if_error=False, **kwargs):
    """Generic method to download file."""

    mimetype = mimetypes.guess_type(url)
    _logger.debug("Guess mimetype: %s", mimetype)

    headers = kwargs.get("headers", {})
    options = {}

    if headers:
        options["headers"] = headers

    # allow_redirects=False

    try:
        response = requests.get(
            url,
            timeout=DEFAULT_TIMEOUT,
            **options,
        )
        response.raise_for_status()
    except HTTPError as error:
        code = error.response.status_code
        _logger.error(error)
        if raise_if_error:
            raise DownloadError("n/c", url, code) from error
        return False

    with tempfile.NamedTemporaryFile("wb", delete=False) as tmp:
        zipfile = tmp.name
        tmp.write(response.content)

    return zipfile


def extract_to(filepath, destination, exclude=[]):  # pylint: disable=W0102
    """Extract zio or tar archive to destination."""

    files = []
    with tempfile.TemporaryDirectory("wb") as path:
        _logger.debug("Tempdir: %s", path)

        # with ZipFile(filepath, "r") as archive:
        #     members = list(filter(lambda x: x not in exclude, archive.namelist()))
        #     # module_name = os.path.basename(os.path.dirname(members[0]))
        #     archive.extractall("./", members)

        with tarfile.open(filepath, "r") as archive:
            members = list(
                filter(
                    lambda x: os.path.basename(x.name) not in exclude,
                    archive.getmembers(),
                )
            )

            files = [os.path.basename(member.name) for member in members]
            dir_name = files.pop(0)
            # dir_name = archive.getmembers()[0].name

            _logger.debug("files: %s", files)

            archive.extractall(path, members=members)

        shutil.copytree(os.path.join(path, dir_name), destination, dirs_exist_ok=True)

    return files


def get_github_archive(repository, branch="master"):
    """Get archive from Github repository."""

    url = f"https://github.com/{repository}/archive/refs/heads/{branch}.tar.gz"
    _logger.debug(url)
    return url


def dot_name_to_camel_case(content):
    """Convert dot name to camel case.

    eg: res.partner => ResPartner
    """
    return "".join(map(str.capitalize, content.split(".")))


def dot_name_to_human(content):
    """Convert dot name to Human readable format.

    eg: res.partner => Res Partner
    """
    return " ".join(map(str.capitalize, content.split(".")))


def dot_name_to_snake_case(content):
    """Convert dot name to snake case.

    eg: res.partner => res_partner
    """
    return "_".join(content.split("."))


def filter_by_extensions(items, extensions):
    """Filter items by files extensions."""
    return list(filter(lambda item: item.split(".")[-1] in extensions, items))


def get_filenames(items):
    """Split filenames and return it w/o extension."""
    return list(map(lambda item: item.split(".")[0], items))


def get_python_filenames(items):
    """Return Python filenames only."""
    return get_filenames(filter_by_extensions(items, ["py"]))


def get_xml_files(items):
    """Return XML files only."""
    return filter_by_extensions(items, ["xml"])


def create_dirs(root, directories):
    """Create directories."""
    for name in directories:
        os.makedirs(os.path.join(root, name), exist_ok=True)


def convert_string_to_human_readable(string):
    """Convert string to most Human readable format."""
    return string.replace("_", " ").capitalize()
