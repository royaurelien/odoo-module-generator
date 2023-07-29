import json
import mimetypes
import os
import shutil
import subprocess
import tarfile
import tempfile

import requests
from requests.exceptions import HTTPError

from omg.common.exceptions import DownloadError
from omg.common.logger import _logger

DEFAULT_ENCODING = "utf8"
DEFAULT_TIMEOUT = 60


def save_to(data, filepath):
    """Save content to filepath."""

    with open(filepath, "w+", encoding=DEFAULT_ENCODING) as file:
        file.write(data)


def abort_if_false(ctx, _, value):
    """Confirm: Abort if false."""

    if not value:
        ctx.abort()


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
    options = {"timeout": DEFAULT_TIMEOUT}

    if headers:
        options["headers"] = headers

    # allow_redirects=False

    try:
        response = requests.get(
            url,
            **options,
        )
        response.raise_for_status()
    except HTTPError as error:
        code = error.response.status_code
        _logger.error(error)
        if raise_if_error:
            raise DownloadError("n/c", url, code) from error
        return False

    # _logger.warning(response.content)

    with tempfile.NamedTemporaryFile("wb", delete=False) as tmp:
        zipfile = tmp.name
        tmp.write(response.content)

    return zipfile


def extract_to(filepath, destination, exclude=[]):  # pylint: disable=W0102
    """Extract zio or tar archive to destination."""

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

            _logger.debug([os.path.basename(member.name) for member in members])

            dir_name = archive.getmembers()[0].name
            archive.extractall(path, members=members)

        shutil.copytree(os.path.join(path, dir_name), destination, dirs_exist_ok=True)
