"""
KOVIRX — Agent WebSocket Routes.

Provides REST endpoints for managing agent WebSocket connections
and sending commands (block_ip, sync_ioc, restart_capture, etc.)
to connected endpoint agents.

The actual WebSocket endpoint is in backend/main.py alongside the
existing /ws/live dashboard WebSocket.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from backend.api.deps import get_current_user, require_role
from database.models.user import User
from backend.api.agent_ws.handler import agent_ws_manager

logger = logging.getLogger("kovirx.api.agent_ws")

router = APIRouter(prefix="/agent", tags=["Agent Management"])


class AgentCommandRequest(BaseModel):
    device_id: str | None = None  # None = broadcast to all agents
    command: str  # block_ip, unblock_ip, sync_ioc, restart_capture, shutdown
    target: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class AgentCommandResponse(BaseModel):
    status: str
    message: str
    agents_notified: int


class AgentVersionResponse(BaseModel):
    latest_version: str = "1.0.0"
    download_url: str | None = None
    checksum: str | None = None
    release_notes: str | None = None


@router.post("/command", response_model=AgentCommandResponse)
async def send_agent_command(
    request: AgentCommandRequest,
    current_user: User = Depends(require_role("super_admin", "security_analyst")),
):
    """
    Send a command to one or all connected endpoint agents.

    Commands: block_ip, unblock_ip, sync_ioc, restart_capture, shutdown
    """
    command_data = {
        "command": request.command,
        "target": request.target,
        "payload": request.payload,
    }

    if request.device_id:
        sent = await agent_ws_manager.send_to_device(request.device_id, command_data)
    else:
        sent = await agent_ws_manager.broadcast_to_agents(command_data)

    return AgentCommandResponse(
        status="ok",
        message=f"Command '{request.command}' dispatched.",
        agents_notified=sent,
    )


@router.get("/version", response_model=AgentVersionResponse)
async def get_latest_agent_version():
    """Return latest agent version info for self-update checks."""
    return AgentVersionResponse(
        latest_version="1.0.0",
        release_notes="Initial release of the KOVIRX endpoint agent.",
    )


@router.get("/connections")
async def list_agent_connections(
    current_user: User = Depends(require_role("super_admin")),
):
    """List all currently connected agent WebSocket connections."""
    return {
        "total": agent_ws_manager.active_count,
        "agents": agent_ws_manager.list_agents(),
    }
