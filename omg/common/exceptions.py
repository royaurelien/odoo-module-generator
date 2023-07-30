class ExternalDependenciesMissing(Exception):
    """Exception raised for system package missing ."""

    def __init__(self, name):
        self.name = name
        self.message = f"System package missing, please install {name} first."
        super().__init__(self.message)


class CommandNotImplemented(NotImplementedError):
    """Exception raised for CLI command not implemented."""

    def __init__(self, name):
        self.name = name
        self.message = f"The {name} command is not yet implemented."
        super().__init__(self.message)


class DownloadError(Exception):
    """Exception raised for download errors."""

    def __init__(self, filename, url, http_code):
        self.filename = filename
        self.url = url
        self.http_code = http_code
        self.message = (
            f"Error while trying to download {filename} from {url} (HTTP {http_code})."
        )
        super().__init__(self.message)


class ExternalCommandFailed(Exception):
    """Exception raised for external command failed."""

    def __init__(self, name):
        self.name = name
        self.message = f"Command {name} failed."
        super().__init__(self.message)
