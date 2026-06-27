"""
KOVIRX — Logging service.

Provides helpers to write and query system logs and audit logs.
"""

import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from database.models.log import LogLevel
from database.repositories.log import system_log_repository, audit_log_repository

logger = logging.getLogger("kovirx.logs")


# ── System Logs ────────────────────────────────────────────────────
async def write_system_log(
    db: AsyncSession,
    level: str,
    module: str,
    message: str,
    details: dict | None = None,
) -> None:
    """Write a system-level log entry to the database."""
    log_in = {
        "level": LogLevel(level) if level in LogLevel.__members__ else LogLevel.info,
        "module": module,
        "message": message,
        "details": details,
    }
    await system_log_repository.create(db, obj_in=log_in)


async def query_system_logs(
    db: AsyncSession,
    level: str | None = None,
    module: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> tuple[int, list]:
    """Query system logs with optional filters."""
    return await system_log_repository.list_system_logs(
        db, level=level, module=module, skip=skip, limit=limit
    )


# ── Audit Logs ─────────────────────────────────────────────────────
async def write_audit_log(
    db: AsyncSession,
    user_id: UUID | None,
    action: str,
    resource: str,
    resource_id: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    details: dict | None = None,
) -> None:
    """Write a security audit log entry."""
    log_in = {
        "user_id": user_id,
        "action": action,
        "resource": resource,
        "resource_id": resource_id,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "details": details,
    }
    await audit_log_repository.create(db, obj_in=log_in)


async def query_audit_logs(
    db: AsyncSession,
    user_id: UUID | None = None,
    action: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> tuple[int, list]:
    """Query audit logs with optional filters."""
    return await audit_log_repository.list_audit_logs(
        db, user_id=user_id, action=action, skip=skip, limit=limit
    )
