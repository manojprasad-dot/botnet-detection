"""
KOVIRX — Logging service.

Provides helpers to write and query system logs and audit logs.
"""

import logging
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.log import AuditLog, LogLevel, SystemLog

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
    log = SystemLog(
        level=LogLevel(level) if level in LogLevel.__members__ else LogLevel.info,
        module=module,
        message=message,
        details=details,
    )
    db.add(log)
    await db.flush()


async def query_system_logs(
    db: AsyncSession,
    level: str | None = None,
    module: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> tuple[int, list]:
    """Query system logs with optional filters."""
    query = select(SystemLog)
    count_query = select(func.count(SystemLog.id))

    if level:
        query = query.where(SystemLog.level == level)
        count_query = count_query.where(SystemLog.level == level)
    if module:
        query = query.where(SystemLog.module == module)
        count_query = count_query.where(SystemLog.module == module)

    total = (await db.execute(count_query)).scalar() or 0
    result = await db.execute(
        query.order_by(SystemLog.created_at.desc()).offset(skip).limit(limit)
    )
    return total, list(result.scalars().all())


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
    log = AuditLog(
        user_id=user_id,
        action=action,
        resource=resource,
        resource_id=resource_id,
        ip_address=ip_address,
        user_agent=user_agent,
        details=details,
    )
    db.add(log)
    await db.flush()


async def query_audit_logs(
    db: AsyncSession,
    user_id: UUID | None = None,
    action: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> tuple[int, list]:
    """Query audit logs with optional filters."""
    query = select(AuditLog)
    count_query = select(func.count(AuditLog.id))

    if user_id:
        query = query.where(AuditLog.user_id == user_id)
        count_query = count_query.where(AuditLog.user_id == user_id)
    if action:
        query = query.where(AuditLog.action == action)
        count_query = count_query.where(AuditLog.action == action)

    total = (await db.execute(count_query)).scalar() or 0
    result = await db.execute(
        query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)
    )
    return total, list(result.scalars().all())
