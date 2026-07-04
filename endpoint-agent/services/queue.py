"""
KOVIRX Endpoint Agent — Priority Queue.

SQLite-backed persistent queue for telemetry batches.
Supports priority levels for IOC-match flows vs normal traffic.
Provides offline caching when the backend is unreachable.
"""

import json
import logging
import sqlite3
import threading
from enum import IntEnum

logger = logging.getLogger("kovirx.agent.queue")


class Priority(IntEnum):
    """Telemetry batch priority levels."""
    CRITICAL = 0   # IOC match — upload immediately
    HIGH = 1       # ML threat detected
    NORMAL = 2     # Standard telemetry


class TelemetryQueue:
    """
    Thread-safe, SQLite-backed persistent priority queue for telemetry batches.

    Items survive agent restarts. Oldest items are evicted when the queue
    exceeds max_size.
    """

    def __init__(self, db_path: str = "agent_queue.db", max_size: int = 10000):
        self.db_path = db_path
        self.max_size = max_size
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self) -> None:
        """Initialize the SQLite queue table."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS telemetry_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    priority INTEGER NOT NULL DEFAULT 2,
                    payload TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_queue_priority
                ON telemetry_queue (priority ASC, id ASC)
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error("Failed to initialize queue database: %s", e)

    def enqueue(self, payload: dict, priority: Priority = Priority.NORMAL) -> bool:
        """Add a telemetry batch to the queue."""
        with self._lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                # Evict oldest entries if over capacity
                cursor.execute("SELECT COUNT(*) FROM telemetry_queue")
                count = cursor.fetchone()[0]
                if count >= self.max_size:
                    evict_count = count - self.max_size + 1
                    cursor.execute("""
                        DELETE FROM telemetry_queue
                        WHERE id IN (
                            SELECT id FROM telemetry_queue
                            ORDER BY priority DESC, id ASC
                            LIMIT ?
                        )
                    """, (evict_count,))
                    logger.warning("Queue at capacity. Evicted %d oldest entries.", evict_count)

                cursor.execute(
                    "INSERT INTO telemetry_queue (priority, payload) VALUES (?, ?)",
                    (int(priority), json.dumps(payload, default=str)),
                )
                conn.commit()
                conn.close()
                return True
            except Exception as e:
                logger.error("Failed to enqueue telemetry: %s", e)
                return False

    def dequeue(self, batch_size: int = 10) -> list[tuple[int, dict]]:
        """
        Dequeue up to batch_size items, ordered by priority then FIFO.

        Returns:
            List of (row_id, payload_dict) tuples.
        """
        with self._lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, payload FROM telemetry_queue ORDER BY priority ASC, id ASC LIMIT ?",
                    (batch_size,),
                )
                rows = cursor.fetchall()
                conn.close()
                return [(row_id, json.loads(payload)) for row_id, payload in rows]
            except Exception as e:
                logger.error("Failed to dequeue telemetry: %s", e)
                return []

    def remove(self, row_ids: list[int]) -> None:
        """Remove successfully uploaded items from the queue."""
        if not row_ids:
            return
        with self._lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                placeholders = ",".join("?" for _ in row_ids)
                cursor.execute(
                    f"DELETE FROM telemetry_queue WHERE id IN ({placeholders})",
                    row_ids,
                )
                conn.commit()
                conn.close()
            except Exception as e:
                logger.error("Failed to remove queue items: %s", e)

    @property
    def depth(self) -> int:
        """Current number of items in the queue."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM telemetry_queue")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception:
            return 0

    def clear(self) -> None:
        """Clear all items from the queue."""
        with self._lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM telemetry_queue")
                conn.commit()
                conn.close()
                logger.info("Queue cleared.")
            except Exception as e:
                logger.error("Failed to clear queue: %s", e)
