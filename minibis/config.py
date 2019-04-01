from configparser import ConfigParser
from pathlib import Path

SRC_PATH = Path(__file__).parent.resolve()


class Config:
    def __init__(self, conf_file="../config.ini"):
        self.config = ConfigParser()
        self.config.read(SRC_PATH.joinpath(conf_file).resolve())

        self.config = self.config["DEFAULT"]
        self.port = self.config.get("port", "5658")
        self.ledger_path = self.config.get(
            "ledger_path", SRC_PATH.joinpath("ledger/").resolve()
        )
