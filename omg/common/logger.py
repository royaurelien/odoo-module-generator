import logging
import os
import time
from functools import wraps
from logging.config import dictConfig

from pydantic import BaseModel


class LogConfig(BaseModel):
    """Logging configuration to be set for the server"""

    LOGGER_NAME: str = "app"
    # LOG_FORMAT: str = "%(levelprefix)s | %(asctime)s | %(message)s"
    LOG_FORMAT: str = "%(levelprefix)s | %(message)s"
    LOG_LEVEL: str = os.getenv("OMG_LOG_LEVEL", "INFO")

    # Logging config
    version: int = 1
    disable_existing_loggers: bool = False
    formatters: dict = {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": LOG_FORMAT,
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    }
    handlers: dict = {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
    }
    loggers: dict = {
        LOGGER_NAME: {"handlers": ["default"], "level": LOG_LEVEL},
    }


dictConfig(LogConfig().model_dump())

_logger = logger = logging.getLogger("app")


def logs(function):
    """Specialized decorator for logging and measuring execution time."""

    @wraps(function)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        logger.debug("%s: start", function.__qualname__)
        output = function(*args, **kwargs)

        end = time.perf_counter()
        message = f"{function.__qualname__}: end ({end - start:.6f})"  # noqa: F841, pylint: disable=W0612
        logger.debug(message)

        return output

    return wrapper


__all__ = ["_logger", "logger", "logs"]
