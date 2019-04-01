import sys
import pathlib  # for type annotations
from typing import Union
from configparser import ConfigParser
from pathlib import Path

SRC_PATH = Path(__file__).parent


class Config:
    __slots__ = ("config", "port", "app_dir", "ledger_path",)

    def __init__(self, config_path: Union[pathlib.Path, str] = None):
        self.config = ConfigParser()

        config_path = config_path or SRC_PATH.joinpath("../config.ini")
        if isinstance(config_path, pathlib.Path):
            config_path = config_path.resolve()

        self.config.read(config_path)

        self.config = self.config["DEFAULT"]
        self.port = self.config.get("port", "5658")
        self.app_dir = Path(self.config.get("app-dir"))

        # set default app directory for both Windows and Linux
        if sys.platform == "win32" and self.app_dir is None:
            self.app_dir = Path("%appdata%/Bismuth")
        elif sys.platform != "win32" and self.app_dir is None:
            self.app_dir = Path("$HOME/.bismuth")

        # where ledger files (ledger, hyper, etc.) are stored
        self.ledger_path = Path(
            self.config.get("ledger_path", self.app_dir.joinpath("ledger/"))
        )
