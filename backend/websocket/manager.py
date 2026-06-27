"""
KOVIRX — WebSocket connection manager.

Manages authenticated WebSocket connections and broadcasts
real-time events (threats, alerts, traffic, device status).
"""

import json
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger("kovirx.websocket")


class ConnectionManager:
    """
    Manages active WebSocket connections.

    Supports broadcasting JSON messages to all connected clients.
    """

    def __init__(self):
        self._connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        self._connections.append(websocket)
        logger.info(
            "WebSocket connected: %s (total: %d)",
            websocket.client, len(self._connections),
        )

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection."""
        if websocket in self._connections:
            self._connections.remove(websocket)
            logger.info(
                "WebSocket disconnected: %s (total: %d)",
                websocket.client, len(self._connections),
            )

    async def broadcast(self, message: dict[str, Any]) -> None:
        """
        Send a JSON message to all connected clients.

        Silently removes any broken connections.
        """
        if not self._connections:
            return

        payload = json.dumps(message, default=str)
        disconnected: list[WebSocket] = []

        for ws in self._connections:
            try:
                await ws.send_text(payload)
            except Exception:
                disconnected.append(ws)

        # Clean up broken connections
        for ws in disconnected:
            self.disconnect(ws)

    async def send_to(self, websocket: WebSocket, message: dict[str, Any]) -> None:
        """Send a message to a specific client."""
        try:
            await websocket.send_json(message)
        except Exception:
            self.disconnect(websocket)

    @property
    def active_count(self) -> int:
        """Number of active connections."""
        return len(self._connections)


# Singleton instance
ws_manager = ConnectionManager()
