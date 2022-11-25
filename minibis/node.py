import glob
import json
import os
import socket
import sqlite3
import tarfile
import threading
import time
from pathlib import Path
from time import perf_counter
from typing import Set, Tuple

import requests

from config import Config
from logger import get_logger, py_ver
from mempool import Mempool

__version__ = "4.2.9.3"  # node version

# path to project root
SRC_PATH = Path(__file__).parent.parent.resolve()

logger = get_logger("node", "debug")


def download_file(url, fn):
    """Download a file from URL to filename

    :param url: URL to download file from
    :param filename: Filename to save downloaded data as

    returns `filename`
    """
    try:
        r = requests.get(url, stream=True)
        total_size = int(r.headers.get("content-length")) / 1024

        with open(fn, "wb") as f:
            chunkno = 0
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    chunkno += 1
                    if chunkno % 10000 == 0:  # every x chunks
                        print(
                            f"Downloaded {int(100 * (chunkno / total_size))}%", end="\r"
                        )

                    f.write(chunk)
                    f.flush()
            print("Downloaded 100%", end="\r")

        logger.info("Bootstrap downloaded")
        return f
    except:  # TODO : make bare except strict
        raise


def bootstrap(ledger_path):
    path = SRC_PATH.joinpath('./ledger/ledger.db').resolve()
    logger.info(f"Extracting ledger archive to {path}")

    if not path.parent.exists():
        path.parent.mkdir()

    try:
        types = ["static/*.db-wal", "static/*.db-shm"]
        for t in types:
            for f in glob.glob(t):
                os.remove(f)
                logger.debug(f"File {f} was deleted")

        archive_path = SRC_PATH.joinpath(f"{ledger_path}").resolve()
        download_file("https://bismuth.cz/ledger.tar.gz", archive_path)

        with tarfile.open(archive_path) as tar:
            def is_within_directory(directory, target):
                
                abs_directory = os.path.abspath(directory)
                abs_target = os.path.abspath(target)
            
                prefix = os.path.commonprefix([abs_directory, abs_target])
                
                return prefix == abs_directory
            
            def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
            
                for member in tar.getmembers():
                    member_path = os.path.join(path, member.name)
                    if not is_within_directory(path, member_path):
                        raise Exception("Attempted Path Traversal in Tar File")
            
                tar.extractall(path, members, numeric_owner=numeric_owner) 
                
            
            safe_extract(tar, SRC_PATH.joinpath("ledger/").resolve())

        logger.info(f"Bootstrap extracted to {path}")

    except:  # TODO : make bare except strict
        raise


def check_ledger_integrity(ledger_path):
    redownload = False
    try:
        with sqlite3.connect(ledger_path.joinpath("ledger.db").resolve()) as db:
            cursor = db.cursor()

            cursor.execute("PRAGMA table_info('transactions');")
            r = cursor.fetchall()

            if len(r) != 12:
                logger.debug(f"{r}")
                redownload = True

    except sqlite3.OperationalError:
        logger.warning(f"Unable to open database file {ledger_path}")
        redownload = True
    except sqlite3.DatabaseError:
        logger.error(f"Unable to open non-database file {ledger_path}")
        redownload = True

    if redownload:
        logger.warning(
            f"Ledger integrity check failed for database '{ledger_path}', "
            "bootstrapping from official website..."
        )
        bootstrap(ledger_path)


class Node:
    def __init__(self, config):
        self.config = config
        self.port = config.port
        self.lock = threading.Lock()

        self.startup_time = None
        self.peers = []

    def start(self):
        logger.info(f"Starting node version {__version__}")
        self.startup_time = perf_counter()

        # create mempool ram file
        self.mempool = Mempool(self.config, self.lock)
        check_ledger_integrity(self.config.ledger_path)

    def connect(self):
        """Connect to the Bismuth network"""

        # set up peers
        peers_file = SRC_PATH.joinpath("peers.json").resolve()
        with open(peers_file) as f:
            peers = set(json.load(f).items())  # remove duplicate peers

        return self.connect_to_peers(peers)

    def connect_to_peers(self, peers: Set[Tuple[str, str]]):
        logger.info(f"Checking {len(peers)} peers are alive")

        # attempt first to connect to peers with `statusjson` command
        # this command may not be free-for-all
        closed_peers = []
        new_peers = 0
        for peer in peers:
            host, port = peer
            logger.debug(f"Attempting to connect to '{host}:{port}'...")
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(5)
                try:
                    sock.connect((host, int(port)))
                    sock.sendall(b'0000000012"statusjson"')

                    while True:
                        data = sock.recv(1024)
                        if not data:
                            break
                        else:
                            logger.debug(
                                f"Connection to '{host}:{port}' was successful"
                            )
                            self.peers.append(peer)
                            new_peers += 1
                            break

                except socket.timeout:
                    logger.debug(f"Connection to '{host}:{port}' timed out")
                except ConnectionRefusedError:
                    logger.debug(f"Connection to '{host}:{port}' was refused")
                except ConnectionResetError:
                    logger.debug(f"Connection to '{host}:{port}' was closed")
                    closed_peers.append(peer)

        logger.debug(f"Connected to {new_peers} peers on the first try")
        logger.info(
            f"Done! Trying to connect to {len(closed_peers)} closed peers in 5 seconds"
        )
        time.sleep(5)

        # Last, try `hello` command which is more likely to receive a response
        new_peers = 0
        for peer in closed_peers:
            host, port = peer
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(5)
                try:
                    sock.connect((host, int(port)))
                    sock.sendall(b'0000000007"hello"')

                    while True:
                        data = sock.recv(1024)
                        if not data:
                            break
                        else:
                            logger.debug(
                                f"Connection to '{host}:{port}' was successful"
                            )
                            self.peers.append(peer)
                            new_peers += 1
                            break

                except socket.timeout:
                    logger.debug(f"Connection to '{host}:{port}' timed out")
                except ConnectionRefusedError:
                    logger.debug(f"Connection to '{host}:{port}' was refused")
                except ConnectionResetError:
                    logger.debug(f"Connection to '{host}:{port}' was closed")

        logger.debug(f"Connected to {new_peers} peers on the second try")
        logger.info(f"Successfully connected to {len(self.peers)} peers")


if __name__ == "__main__":
    config = Config()
    node = Node(config)

    logger.info("Loaded configuration settings")
    logger.debug(f"Python version {py_ver}")

    node.start()
    node.connect()

    # set up api handeling

    # set up mempool

    # set up database/ledger

    # set up tor?

    # set up connection manager
