import logging
import sys

py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


def get_logger(
    name: str, level: str = "debug", file: bool = True, stream: bool = True
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

    if level.lower() == "debug":
        level = logging.DEBUG
    elif level.lower() == "info":
        level = logging.INFO
    elif level.lower() == "warning":
        level = logging.WARNING
    elif level.lower() == "error":
        level = logging.ERROR
    else:
        level = logging.DEBUG

    logger.setLevel(level)
    formatter = logging.Formatter(
        "[%(asctime)-15s][%(levelname)s][%(name)s]: %(message)s", "%Y-%m-%d][%H:%M:%S"
    )

    if file:
        file_handler = logging.FileHandler(f"{name}.log")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    if stream:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    return logger
