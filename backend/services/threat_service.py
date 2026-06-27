"""
KOVIRX — Threat intelligence service.
"""

import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import ConflictException, NotFoundException
from database.models.threat import BotnetFamily, ThreatIntelligence
from backend.schemas.threat import (
    BotnetFamilyCreateRequest,
    BotnetFamilyListResponse,
    BotnetFamilyResponse,
    IOCCheckRequest,
    IOCCheckResult,
    IOCCreateRequest,
    IOCListResponse,
    IOCResponse,
)

logger = logging.getLogger("kovirx.threats")


# ── IOC Operations ─────────────────────────────────────────────────
async def create_ioc(db: AsyncSession, data: IOCCreateRequest) -> IOCResponse:
    """Add a new Indicator of Compromise."""
    existing = await db.execute(
        select(ThreatIntelligence).where(ThreatIntelligence.ioc_value == data.ioc_value)
    )
    if existing.scalar_one_or_none():
        raise ConflictException("IOC with this value already exists")

    ioc = ThreatIntelligence(
        ioc_type=data.ioc_type,
        ioc_value=data.ioc_value,
        threat_type=data.threat_type,
        reputation_score=data.reputation_score,
        source=data.source,
        botnet_family_id=data.botnet_family_id,
        first_seen=datetime.now(timezone.utc),
        last_seen=datetime.now(timezone.utc),
    )
    db.add(ioc)
    await db.flush()
    await db.refresh(ioc)
    logger.info("IOC created: %s=%s", data.ioc_type, data.ioc_value)
    return IOCResponse.model_validate(ioc)


async def list_iocs(
    db: AsyncSession,
    ioc_type: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> IOCListResponse:
    """List IOCs with optional type filter."""
    query = select(ThreatIntelligence)
    count_query = select(func.count(ThreatIntelligence.id))

    if ioc_type:
        query = query.where(ThreatIntelligence.ioc_type == ioc_type)
        count_query = count_query.where(ThreatIntelligence.ioc_type == ioc_type)

    total = (await db.execute(count_query)).scalar() or 0
    result = await db.execute(
        query.order_by(ThreatIntelligence.created_at.desc()).offset(skip).limit(limit)
    )
    iocs = [IOCResponse.model_validate(i) for i in result.scalars().all()]
    return IOCListResponse(total=total, iocs=iocs)


async def delete_ioc(db: AsyncSession, ioc_id: UUID) -> None:
    """Delete an IOC."""
    result = await db.execute(
        select(ThreatIntelligence).where(ThreatIntelligence.id == ioc_id)
    )
    ioc = result.scalar_one_or_none()
    if not ioc:
        raise NotFoundException("IOC")
    await db.delete(ioc)
    await db.flush()
    logger.info("IOC deleted: %s", ioc_id)


async def check_iocs(db: AsyncSession, data: IOCCheckRequest) -> list[IOCCheckResult]:
    """Check a list of values against the threat intel database."""
    results: list[IOCCheckResult] = []
    for value in data.values:
        result = await db.execute(
            select(ThreatIntelligence).where(
                ThreatIntelligence.ioc_value == value,
                ThreatIntelligence.is_active == True,
            )
        )
        ioc = result.scalar_one_or_none()
        results.append(IOCCheckResult(
            value=value,
            found=ioc is not None,
            ioc=IOCResponse.model_validate(ioc) if ioc else None,
        ))
    return results


# ── Botnet Family Operations ──────────────────────────────────────
async def create_botnet_family(
    db: AsyncSession, data: BotnetFamilyCreateRequest
) -> BotnetFamilyResponse:
    """Create a new botnet family record."""
    family = BotnetFamily(
        name=data.name,
        description=data.description,
        indicators=data.indicators,
        ttps=data.ttps,
        first_seen=datetime.now(timezone.utc),
    )
    db.add(family)
    await db.flush()
    await db.refresh(family)
    logger.info("Botnet family created: %s", data.name)
    return BotnetFamilyResponse.model_validate(family)


async def list_botnet_families(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 50,
) -> BotnetFamilyListResponse:
    """List all botnet families."""
    total = (await db.execute(select(func.count(BotnetFamily.id)))).scalar() or 0
    result = await db.execute(
        select(BotnetFamily).order_by(BotnetFamily.created_at.desc()).offset(skip).limit(limit)
    )
    families = [BotnetFamilyResponse.model_validate(f) for f in result.scalars().all()]
    return BotnetFamilyListResponse(total=total, families=families)


async def get_botnet_family(db: AsyncSession, family_id: UUID) -> BotnetFamilyResponse:
    """Get a single botnet family with details."""
    result = await db.execute(
        select(BotnetFamily).where(BotnetFamily.id == family_id)
    )
    family = result.scalar_one_or_none()
    if not family:
        raise NotFoundException("Botnet family")
    return BotnetFamilyResponse.model_validate(family)
