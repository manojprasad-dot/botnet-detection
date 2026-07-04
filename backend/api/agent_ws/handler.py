"""
KOVIRX — Agent WebSocket Handler.

Manages authenticated WebSocket connections from endpoint agents.
Supports:
    - Per-device connections indexed by device_id
    - Targeted command delivery to specific agents
    - Broadcast commands to all agents
    - IOC sync pushes
"""

import json
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger("kovirx.websocket.agent_handler")


class AgentWebSocketManager:
    """
    Manages WebSocket connections from endpoint agents.

    Each agent registers with its device_id. Commands can be sent
    to individual agents or broadcast to all connected agents.
    """

    def __init__(self):
        # device_id → WebSocket
        self._agents: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, device_id: str) -> None:
        """Register an agent WebSocket connection."""
        await websocket.accept()
        self._agents[device_id] = websocket
        logger.info(
            "Agent connected: %s (total: %d)",
            device_id, len(self._agents),
        )

    def disconnect(self, device_id: str) -> None:
        """Remove an agent connection."""
        if device_id in self._agents:
            del self._agents[device_id]
            logger.info(
                "Agent disconnected: %s (total: %d)",
                device_id, len(self._agents),
            )

    async def send_to_device(self, device_id: str, data: dict[str, Any]) -> int:
        """Send a command to a specific agent by device_id."""
        ws = self._agents.get(device_id)
        if not ws:
            logger.warning("Agent %s not connected.", device_id)
            return 0

        try:
            await ws.send_text(json.dumps(data, default=str))
            return 1
        except Exception as e:
            logger.error("Failed to send to agent %s: %s", device_id, e)
            self.disconnect(device_id)
            return 0

    async def broadcast_to_agents(self, data: dict[str, Any]) -> int:
        """Broadcast a command to all connected agents."""
        payload = json.dumps(data, default=str)
        disconnected = []
        sent = 0

        for device_id, ws in self._agents.items():
            try:
                await ws.send_text(payload)
                sent += 1
            except Exception:
                disconnected.append(device_id)

        for device_id in disconnected:
            self.disconnect(device_id)

        logger.info("Broadcast to %d agents. %d disconnected.", sent, len(disconnected))
        return sent

    def list_agents(self) -> list[dict[str, str]]:
        """List all connected agent device IDs."""
        return [{"device_id": did} for did in self._agents.keys()]

    @property
    def active_count(self) -> int:
        return len(self._agents)


# Singleton instance
agent_ws_manager = AgentWebSocketManager()
