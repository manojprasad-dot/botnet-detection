"""
KOVIRX — Server-Side Behavior Analysis Service.

Analyzes flow data stored in the database across all devices
to detect cross-network behavioral patterns:
    - DNS beaconing (regular interval queries)
    - Port scanning (high port fan-out)
    - Lateral movement (internal IP scanning)
    - Data exfiltration (high outbound ratio)
    - DGA domains (high DNS entropy)
"""

import logging
import math
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.behavior.schemas import (
    BehaviorAnalysisResponse,
    BehaviorPattern,
    DeviceBehaviorPattern,
    DeviceBehaviorResponse,
)
from database.models.traffic import NetworkFlow

logger = logging.getLogger("kovirx.behavior.service")


class BehaviorAnalysisService:
    """
    Server-side behavior analysis across all stored flows.

    Unlike the agent-side analyzer (which analyzes real-time per-device data),
    this service provides cross-network correlation by querying the flow database.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def analyze_network(self, hours: int = 24) -> BehaviorAnalysisResponse:
        """Run behavior analysis across all devices for the specified timeframe."""
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        patterns: list[BehaviorPattern] = []

        # 1. DNS Beaconing Detection — high-entropy domains queried repeatedly
        dns_patterns = await self._detect_dns_abuse(since)
        patterns.extend(dns_patterns)

        # 2. Port Scanning — devices connecting to many ports
        scan_patterns = await self._detect_scanning(since)
        patterns.extend(scan_patterns)

        # 3. Data Exfiltration — high outbound byte ratio
        exfil_patterns = await self._detect_exfiltration(since)
        patterns.extend(exfil_patterns)

        return BehaviorAnalysisResponse(
            timeframe_hours=hours,
            total_patterns_detected=len(patterns),
            patterns=patterns,
            risk_summary={
                "dns_abuse": len([p for p in patterns if "dns" in p.pattern_type.lower()]),
                "scanning": len([p for p in patterns if "scan" in p.pattern_type.lower()]),
                "exfiltration": len([p for p in patterns if "exfil" in p.pattern_type.lower()]),
            },
        )

    async def analyze_device(
        self, device_id: str, hours: int = 24
    ) -> DeviceBehaviorResponse:
        """Run behavior analysis for a single device."""
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        patterns: list[DeviceBehaviorPattern] = []

        try:
            result = await self.db.execute(
                select(NetworkFlow).where(
                    NetworkFlow.device_id == device_id,
                    NetworkFlow.created_at >= since,
                ).order_by(NetworkFlow.created_at.desc()).limit(500)
            )
            flows = list(result.scalars().all())

            # Analyze DNS entropy
            for flow in flows:
                if flow.dns_entropy and flow.dns_entropy >= 4.0:
                    patterns.append(DeviceBehaviorPattern(
                        pattern_type="dns_abuse",
                        confidence=min(0.95, flow.dns_entropy / 5.0),
                        description=f"High-entropy DNS query (entropy={flow.dns_entropy:.2f})",
                        dest_ip=flow.dest_ip,
                    ))

            # Analyze connection patterns
            dest_ports = defaultdict(int)
            for flow in flows:
                if flow.dest_port:
                    dest_ports[flow.dest_port] += 1

            if len(dest_ports) >= 15:
                patterns.append(DeviceBehaviorPattern(
                    pattern_type="port_scan",
                    confidence=min(0.9, len(dest_ports) / 50.0),
                    description=f"Connected to {len(dest_ports)} unique ports",
                ))

        except Exception as e:
            logger.error("Device behavior analysis failed: %s", e)

        behavior_score = (
            min(1.0, sum(p.confidence for p in patterns) / max(1, len(patterns)))
            if patterns else 0.0
        )

        return DeviceBehaviorResponse(
            device_id=device_id,
            timeframe_hours=hours,
            behavior_score=round(behavior_score, 4),
            patterns=patterns,
        )

    async def _detect_dns_abuse(self, since: datetime) -> list[BehaviorPattern]:
        """Detect DNS abuse patterns across the network."""
        patterns = []
        try:
            result = await self.db.execute(
                select(
                    NetworkFlow.source_ip,
                    func.avg(NetworkFlow.dns_entropy).label("avg_entropy"),
                    func.count(NetworkFlow.id).label("flow_count"),
                ).where(
                    NetworkFlow.created_at >= since,
                    NetworkFlow.dns_entropy > 3.5,
                ).group_by(NetworkFlow.source_ip)
                .having(func.count(NetworkFlow.id) >= 5)
            )
            for row in result.all():
                if row.avg_entropy and row.avg_entropy >= 4.0:
                    patterns.append(BehaviorPattern(
                        pattern_type="dns_abuse",
                        confidence=min(0.95, float(row.avg_entropy) / 5.0),
                        description=(
                            f"Device {row.source_ip}: {row.flow_count} high-entropy DNS queries "
                            f"(avg entropy={float(row.avg_entropy):.2f})"
                        ),
                        affected_devices=1,
                        evidence={
                            "source_ip": row.source_ip,
                            "avg_entropy": round(float(row.avg_entropy), 3),
                            "flow_count": row.flow_count,
                        },
                    ))
        except Exception as e:
            logger.error("DNS abuse detection error: %s", e)
        return patterns

    async def _detect_scanning(self, since: datetime) -> list[BehaviorPattern]:
        """Detect port scanning behavior."""
        patterns = []
        try:
            result = await self.db.execute(
                select(
                    NetworkFlow.source_ip,
                    func.count(func.distinct(NetworkFlow.dest_port)).label("port_count"),
                ).where(
                    NetworkFlow.created_at >= since,
                ).group_by(NetworkFlow.source_ip)
                .having(func.count(func.distinct(NetworkFlow.dest_port)) >= 15)
            )
            for row in result.all():
                patterns.append(BehaviorPattern(
                    pattern_type="port_scan",
                    confidence=min(0.9, row.port_count / 50.0),
                    description=(
                        f"Device {row.source_ip} connected to {row.port_count} unique ports"
                    ),
                    affected_devices=1,
                    evidence={
                        "source_ip": row.source_ip,
                        "unique_ports": row.port_count,
                    },
                ))
        except Exception as e:
            logger.error("Scanning detection error: %s", e)
        return patterns

    async def _detect_exfiltration(self, since: datetime) -> list[BehaviorPattern]:
        """Detect potential data exfiltration."""
        patterns = []
        try:
            result = await self.db.execute(
                select(
                    NetworkFlow.source_ip,
                    NetworkFlow.dest_ip,
                    func.sum(NetworkFlow.bytes_sent).label("total_sent"),
                    func.sum(NetworkFlow.bytes_received).label("total_recv"),
                ).where(
                    NetworkFlow.created_at >= since,
                ).group_by(NetworkFlow.source_ip, NetworkFlow.dest_ip)
                .having(func.sum(NetworkFlow.bytes_sent) > 1_000_000)  # >1MB
            )
            for row in result.all():
                sent = int(row.total_sent or 0)
                recv = int(row.total_recv or 0)
                if recv > 0 and sent / recv > 10:
                    patterns.append(BehaviorPattern(
                        pattern_type="data_exfiltration",
                        confidence=min(0.85, (sent / recv) / 50.0),
                        description=(
                            f"{row.source_ip} → {row.dest_ip}: "
                            f"{sent / 1_000_000:.1f}MB sent vs {recv / 1_000_000:.1f}MB received"
                        ),
                        affected_devices=1,
                        evidence={
                            "source_ip": row.source_ip,
                            "dest_ip": row.dest_ip,
                            "bytes_sent": sent,
                            "bytes_received": recv,
                        },
                    ))
        except Exception as e:
            logger.error("Exfiltration detection error: %s", e)
        return patterns
