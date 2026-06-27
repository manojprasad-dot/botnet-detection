"""
KOVIRX — Threat intelligence schemas.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


# ── IOCs ───────────────────────────────────────────────────────────
class IOCCreateRequest(BaseModel):
    ioc_type: str   # ip, domain, hash, url
    ioc_value: str
    threat_type: str = "botnet"
    reputation_score: float = 0.0
    source: str | None = None
    botnet_family_id: UUID | None = None


class IOCCheckRequest(BaseModel):
    """Check a list of IPs / domains against the threat intel database."""
    values: list[str]


class IOCResponse(BaseModel):
    id: UUID
    ioc_type: str
    ioc_value: str
    threat_type: str
    reputation_score: float
    source: str | None = None
    botnet_family_id: UUID | None = None
    is_active: bool
    first_seen: datetime | None = None
    last_seen: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class IOCCheckResult(BaseModel):
    value: str
    found: bool
    ioc: IOCResponse | None = None


class IOCListResponse(BaseModel):
    total: int
    iocs: list[IOCResponse]


# ── Botnet Families ────────────────────────────────────────────────
class BotnetFamilyCreateRequest(BaseModel):
    name: str
    description: str | None = None
    indicators: dict | None = None
    ttps: dict | None = None


class BotnetFamilyResponse(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    first_seen: datetime | None = None
    last_seen: datetime | None = None
    indicators: dict | None = None
    ttps: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class BotnetFamilyListResponse(BaseModel):
    total: int
    families: list[BotnetFamilyResponse]
