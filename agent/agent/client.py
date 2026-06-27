import json
import logging
import sqlite3
from typing import Any
import requests

logger = logging.getLogger("kovirx.agent.client")


class PlatformApiClient:
    """
    Robust HTTP Client for Agent-to-Backend secure communication.
    Handles JWT authentication, endpoint sensor enrollment, and offline packet queuing.
    """

    def __init__(self, server_url: str, db_path: str = "agent_queue.db", timeout: int = 15) -> None:
        self.server_url = server_url.rstrip("/")
        self.timeout = timeout
        self.db_path = db_path
        self.token: str | None = None
        self._init_db()

    def _init_db(self) -> None:
        """Initialize local SQLite DB for offline queue storage."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS telemetry_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    payload TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error("Failed to initialize offline agent DB cache: %s", e)

    def login(self, email: str, password: str) -> bool:
        """Authenticate agent credentials and store JWT token."""
        try:
            url = f"{self.server_url}/api/v1/auth/login"
            response = requests.post(
                url,
                json={"email": email, "password": password},
                timeout=self.timeout
            )
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                logger.info("Agent authenticated successfully.")
                return True
            else:
                logger.error("Authentication failed: Status %d", response.status_code)
                return False
        except Exception as e:
            logger.error("Network error during agent login: %s", e)
            return False

    def register_device(self, payload: dict) -> dict | None:
        """Register the endpoint device with the backend."""
        try:
            headers = {}
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"

            response = requests.post(
                f"{self.server_url}/api/v1/devices/register",
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            logger.info("Sensor successfully registered on backend.")
            return response.json()
        except Exception as e:
            logger.error("Failed to register device: %s", e)
            return None

    def send_telemetry(self, payload: dict) -> dict | None:
        """
        Send a real-time telemetry batch to the backend.
        Queues data locally if the backend is offline.
        """
        try:
            headers = {}
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"

            url = f"{self.server_url}/api/v1/telemetry/ingest"
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            logger.info("Telemetry batch uploaded successfully.")
            return response.json()
        except Exception as e:
            logger.warning("Backend offline or unreachable. Queueing telemetry locally. Details: %s", e)
            self._queue_telemetry(payload)
            return None

    def flush_queue(self) -> None:
        """Attempts to flush stored offline telemetry queue to the backend."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id, payload FROM telemetry_queue ORDER BY id ASC")
            rows = cursor.fetchall()
            if not rows:
                conn.close()
                return

            logger.info("Attempting to flush %d queued telemetry items...", len(rows))
            headers = {}
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"

            flushed_ids = []
            for row_id, payload_str in rows:
                payload = json.loads(payload_str)
                try:
                    url = f"{self.server_url}/api/v1/telemetry/ingest"
                    response = requests.post(
                        url,
                        json=payload,
                        headers=headers,
                        timeout=self.timeout
                    )
                    response.raise_for_status()
                    flushed_ids.append(row_id)
                except Exception as ex:
                    logger.error("Failed to flush queue row %d: %s. Aborting queue flush.", row_id, ex)
                    break

            # Delete successfully flushed rows
            if flushed_ids:
                cursor.execute(
                    f"DELETE FROM telemetry_queue WHERE id IN ({','.join(map(str, flushed_ids))})"
                )
                conn.commit()
                logger.info("Flushed and deleted %d queued telemetry batches.", len(flushed_ids))

            conn.close()
        except Exception as e:
            logger.error("Error during queue flushing: %s", e)

    def _queue_telemetry(self, payload: dict) -> None:
        """Insert payload into local SQLite db queue."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO telemetry_queue (payload) VALUES (?)",
                (json.dumps(payload),)
            )
            conn.commit()
            conn.close()
            logger.info("Telemetry batch saved to offline queue cache.")
        except Exception as e:
            logger.critical("Local offline queue insertion failed: %s", e)
