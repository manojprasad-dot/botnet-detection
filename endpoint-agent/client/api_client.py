"""
KOVIRX Endpoint Agent — Platform API Client.

Handles JWT authentication, device registration, telemetry upload,
heartbeat delivery, IOC feed retrieval, and version checking.
Supports gzip compression and offline queue fallback.
"""

import json
import logging
from typing import Any

import requests

logger = logging.getLogger("kovirx.agent.client")


class PlatformApiClient:
    """
    HTTP client for agent-to-backend communication.

    Features:
        - JWT authentication with token persistence
        - Device registration
        - Telemetry batch upload with compression
        - Heartbeat delivery
        - IOC feed retrieval
        - Agent version checking
        - Connection pooling via requests.Session
    """

    def __init__(self, server_url: str, timeout: int = 15):
        self.server_url = server_url.rstrip("/")
        self.timeout = timeout
        self.token: str | None = None
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "KOVIRX-Agent/1.0.0",
            "Content-Type": "application/json",
        })

    def _auth_headers(self) -> dict[str, str]:
        """Build authorization headers with JWT token."""
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    def login(self, email: str, password: str) -> bool:
        """Authenticate and store JWT token."""
        try:
            response = self._session.post(
                f"{self.server_url}/api/v1/auth/login",
                json={"email": email, "password": password},
                timeout=self.timeout,
            )
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self._session.headers.update(self._auth_headers())
                logger.info("Agent authenticated successfully.")
                return True
            else:
                logger.error("Authentication failed: HTTP %d", response.status_code)
                return False
        except Exception as e:
            logger.error("Login error: %s", e)
            return False

    def register_device(self, payload: dict) -> dict | None:
        """Register the endpoint device with the backend."""
        try:
            response = self._session.post(
                f"{self.server_url}/api/v1/devices/register",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            logger.info("Device registered successfully.")
            return response.json()
        except Exception as e:
            logger.error("Device registration failed: %s", e)
            return None

    def send_telemetry(
        self,
        payload: dict,
        compressed_data: bytes | None = None,
        is_compressed: bool = False,
    ) -> dict | None:
        """
        Send a telemetry batch to the backend.

        Args:
            payload: Telemetry payload dict (used if not compressed)
            compressed_data: Pre-compressed payload bytes
            is_compressed: Whether compressed_data is gzip-compressed

        Returns:
            Response dict on success, None on failure
        """
        try:
            url = f"{self.server_url}/api/v1/telemetry/ingest"

            if is_compressed and compressed_data:
                headers = {**self._auth_headers(), "Content-Encoding": "gzip"}
                response = self._session.post(
                    url,
                    data=compressed_data,
                    headers=headers,
                    timeout=self.timeout,
                )
            else:
                response = self._session.post(
                    url,
                    json=payload,
                    timeout=self.timeout,
                )

            response.raise_for_status()
            logger.info("Telemetry batch uploaded successfully.")
            return response.json()
        except Exception as e:
            logger.warning("Telemetry upload failed: %s", e)
            return None

    def send_heartbeat(self, payload: dict) -> bool:
        """Send heartbeat payload to backend."""
        try:
            response = self._session.post(
                f"{self.server_url}/api/v1/devices/heartbeat",
                json=payload,
                timeout=self.timeout,
            )
            return response.status_code in (200, 201)
        except Exception as e:
            logger.debug("Heartbeat delivery failed: %s", e)
            return False

    def get_ioc_feed(self) -> list[dict] | None:
        """Retrieve latest IOC feed from backend."""
        try:
            response = self._session.get(
                f"{self.server_url}/api/v1/threats/ioc/feed",
                timeout=self.timeout,
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.debug("IOC feed retrieval failed: %s", e)
            return None

    def check_agent_version(self) -> dict | None:
        """Check backend for latest agent version info."""
        try:
            response = self._session.get(
                f"{self.server_url}/api/v1/agent/version",
                timeout=self.timeout,
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.debug("Version check failed: %s", e)
            return None

    def download_update(self, url: str) -> bytes | None:
        """Download an update package from the given URL."""
        try:
            response = self._session.get(url, timeout=60)
            response.raise_for_status()
            return response.content
        except Exception as e:
            logger.error("Update download failed: %s", e)
            return None
