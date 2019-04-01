import sqlite3
import threading

from logger import get_logger

logger = get_logger("mempool", "debug")

# Create mempool table
SQL_CREATE = (
    "CREATE TABLE IF NOT EXISTS transactions ("
    "timestamp TEXT, address TEXT, recipient TEXT, amount TEXT, signature TEXT, "
    "public_key TEXT, operation TEXT, openfield TEXT, mergedts INTEGER)"
)


class Mempool:
    """The mempool manager. This object is thread-safe"""

    def __init__(self, config, lock=None):
        self.config = config
        self.lock = lock or threading.Lock()

        self.mempool_file = "file:mempool?mode=memory&cache=shared"
        self.db = None

        self.check_exists()

    def check_exists(self):
        """Checks if mempool file exists, create it if not."""
        with self.lock:
            self.db = sqlite3.connect(
                self.mempool_file,
                uri=True,
                timeout=1,
                isolation_level=None,
                check_same_thread=False,
            )

            self.db.execute("PRAGMA journal_mode = WAL;")
            self.db.execute("PRAGMA page_size = 4096;")

            cursor = self.db.cursor()
            cursor.execute(SQL_CREATE)
            self.db.commit()
            logger.debug("In-memory mempool created")
