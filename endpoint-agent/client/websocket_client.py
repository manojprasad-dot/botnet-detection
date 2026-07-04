"""
KOVIRX Endpoint Agent — WebSocket Client.

Connects to backend WebSocket endpoint for real-time command reception.
Handles policy updates, block commands, IOC sync pushes, and config changes.
Reconnects automatically with exponential backoff.
"""

import json
import logging
import threading
import time
from typing import Callable

logger = logging.getLogger("kovirx.agent.websocket_client")


class WebSocketClient:
    """
    WebSocket listener for agent-to-backend bidirectional communication.

    Receives commands from backend:
        - block_ip: Block an IP via local firewall
        - update_config: Update agent configuration
        - sync_ioc: Add IOC to local cache
        - restart_capture: Restart packet capture
        - shutdown: Graceful agent shutdown
    """

    def __init__(
        self,
        ws_url: str,
        token: str | None = None,
        on_command: Callable[[dict], None] | None = None,
        reconnect_max_delay: float = 60.0,
    ):
        self.ws_url = ws_url
        self.token = token
        self.on_command = on_command
        self.reconnect_max_delay = reconnect_max_delay
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._connected = False

    def start(self) -> None:
        """Start WebSocket listener in a daemon thread."""
        if self._thread and self._thread.is_alive():
            logger.warning("WebSocket client is already running.")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._connect_loop,
            name="WSClientThread",
            daemon=True,
        )
        self._thread.start()
        logger.info("WebSocket client started. Target: %s", self.ws_url)

    def stop(self) -> None:
        """Stop WebSocket client."""
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)
        logger.info("WebSocket client stopped.")

    @property
    def is_connected(self) -> bool:
        return self._connected

    def _connect_loop(self) -> None:
        """Main reconnection loop with exponential backoff."""
        attempt = 0

        while not self._stop_event.is_set():
            try:
                self._run_connection()
                attempt = 0  # Reset on successful connection
            except Exception as e:
                attempt += 1
                delay = min(2 ** attempt, self.reconnect_max_delay)
                logger.warning(
                    "WebSocket disconnected: %s. Reconnecting in %.1fs (attempt %d)...",
                    e, delay, attempt,
                )
                self._connected = False
                self._stop_event.wait(delay)

    def _run_connection(self) -> None:
        """Establish and maintain a single WebSocket connection."""
        try:
            import websocket as ws_lib
        except ImportError:
            logger.error(
                "websocket-client library not installed. "
                "Install with: pip install websocket-client"
            )
            self._stop_event.wait(30)
            return

        url = self.ws_url
        if self.token:
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}token={self.token}"

        ws = ws_lib.WebSocket()
        try:
            ws.connect(url, timeout=10)
            self._connected = True
            logger.info("WebSocket connected to backend.")

            ws.settimeout(5.0)

            while not self._stop_event.is_set():
                try:
                    message = ws.recv()
                    if message:
                        self._handle_message(message)
                except ws_lib.WebSocketTimeoutException:
                    continue
                except ws_lib.WebSocketConnectionClosedException:
                    logger.info("WebSocket connection closed by server.")
                    break

        except Exception as e:
            raise
        finally:
            try:
                ws.close()
            except Exception:
                pass
            self._connected = False

    def _handle_message(self, raw_message: str) -> None:
        """Parse and dispatch a received WebSocket message."""
        try:
            data = json.loads(raw_message)
            command = data.get("command")
            logger.info("Received WS command: %s", command)

            if self.on_command:
                self.on_command(data)
            else:
                logger.warning("No command handler registered for: %s", command)

        except json.JSONDecodeError:
            logger.error("Invalid JSON in WebSocket message: %s", raw_message[:100])
        except Exception as e:
            logger.error("Error handling WebSocket message: %s", e)
