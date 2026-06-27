"""
KOVIRX — Threat intelligence models.

BotnetFamily      — known botnet family catalogue.
ThreatIntelligence — Indicators of Compromise (IOCs) with reputation scoring.
"""

import enum

from sqlalchemy import Boolean, DateTime, Enum, Float, JSON, String, Text, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base, TimestampMixin, UUIDMixin


class IOCType(str, enum.Enum):
    ip = "ip"
    domain = "domain"
    hash = "hash"
    url = "url"


class BotnetFamily(Base, UUIDMixin, TimestampMixin):
    """Known botnet family with indicators and TTPs."""

    __tablename__ = "botnet_families"

    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    first_seen: Mapped[None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_seen: Mapped[None] = mapped_column(DateTime(timezone=True), nullable=True)
    indicators: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ttps: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # MITRE ATT&CK TTPs

    def __repr__(self) -> str:
        return f"<BotnetFamily {self.name}>"


class ThreatIntelligence(Base, UUIDMixin, TimestampMixin):
    """Indicator of Compromise (IOC) entry with reputation scoring."""

    __tablename__ = "threat_intelligence"

    ioc_type: Mapped[IOCType] = mapped_column(
        Enum(IOCType, name="ioc_type"),
        nullable=False,
        index=True,
    )
    ioc_value: Mapped[str] = mapped_column(String(512), unique=True, nullable=False, index=True)
    threat_type: Mapped[str] = mapped_column(String(128), nullable=False, default="botnet")
    reputation_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    source: Mapped[str | None] = mapped_column(String(256), nullable=True)
    botnet_family_id: Mapped[None] = mapped_column(UUID(as_uuid=True), nullable=True)
    first_seen: Mapped[None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_seen: Mapped[None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<ThreatIntel {self.ioc_type.value}={self.ioc_value}>"
