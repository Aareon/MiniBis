import logging
import pathlib  # for type annotations
import sys
from pathlib import Path
from typing import Union

py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
SRC_PATH = Path(__file__).parent.parent


def get_logger(
    name: str,
    level: str = "debug",
    file: bool = True,
    file_path: Union[pathlib.Path, str] = None,
    stream: bool = True
) -> logging.Logger:
    """Create a new logger with a given name and logging level

    :param name: str
        The name of the logger object.
    :param level: str
        The logging level to be used.
    :param file: bool
        Whether to create a file handler for this logger. Saves the log to a `{name}.log`.
    :param stream: bool
        Whether to create a stream handler for this logger. Prints log entries to STDOUT.

    :returns: logging.Logger
    """
    logger = logging.getLogger(f"{name}")
    level = logging._nameToLevel.get(level.lower(), logging.DEBUG))

    logger.setLevel(level)
    formatter = logging.Formatter(
        "[%(asctime)-15s][%(levelname)s][%(name)s]: %(message)s", "%Y-%m-%d][%H:%M:%S"
    )

    if file:
        # properly handle file storage
        if file_path is None:
            SRC_PATH.joinpath(f"logs/{name}.log")  # MiniBis/logs/
        elif isinstance(file_path, str):
            file_path = Path(file_path)

        if not file_path.is_absolute():
            # we need to decide what directory to store the file in
            file_path = SRC_path.joinpath(file_path)
        if file_path.name == "":
            # no filename, we'll need to provide one
            file_path = file_path.joinpath(f"{name}.log")

        file_handler = logging.FileHandler(file_path.resolve())
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    if stream:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    return logger
