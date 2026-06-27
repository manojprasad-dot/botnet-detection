"""
KOVIRX — Feature extraction service.

Computes 8-dimensional feature vectors from raw network flows.
"""

import logging
import math
from collections import Counter
from uuid import UUID

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.traffic import NetworkFlow
from backend.schemas.feature import DeviceFeatureResponse, FeatureVector

logger = logging.getLogger("kovirx.features")

# TCP flag mapping for bitmap encoding
TCP_FLAG_MAP = {"SYN": 1, "ACK": 2, "FIN": 4, "RST": 8, "PSH": 16, "URG": 32}


def _encode_tcp_flags(flags_str: str | None) -> int:
    """Encode a comma-separated TCP flags string into a bitmap integer."""
    if not flags_str:
        return 0
    encoded = 0
    for flag in flags_str.upper().replace(",", " ").split():
        encoded |= TCP_FLAG_MAP.get(flag.strip(), 0)
    return encoded


def _shannon_entropy(value: str) -> float:
    if not value:
        return 0.0
    counts = Counter(value)
    length = len(value)
    return -sum((c / length) * math.log2(c / length) for c in counts.values())


def compute_features_from_flows(flows: list[NetworkFlow]) -> FeatureVector:
    """
    Compute an aggregated 8-feature vector from a list of network flows.

    Features:
        1. packet_rate       — avg packets/sec across flows
        2. beacon_interval   — std deviation of inter-flow timing
        3. dns_entropy       — mean Shannon entropy of DNS queries
        4. flow_duration     — mean flow duration
        5. tcp_flags_encoded — OR-combined TCP flag bitmap
        6. avg_packet_size   — total bytes / total packets
        7. failed_connections— count of flows with RST flag
        8. outbound_ratio    — fraction of total bytes from outbound flows
    """
    if not flows:
        return FeatureVector()

    # 1. Packet rate
    packet_rates = []
    for f in flows:
        dur = f.flow_duration if f.flow_duration and f.flow_duration > 0 else 1.0
        packet_rates.append(f.packet_count / dur)
    packet_rate = float(np.mean(packet_rates))

    # 2. Beacon interval (std dev of start times)
    start_times = sorted(
        [f.start_time.timestamp() for f in flows if f.start_time]
    )
    if len(start_times) >= 2:
        intervals = np.diff(start_times)
        beacon_interval = float(np.std(intervals))
    else:
        beacon_interval = 0.0

    # 3. DNS entropy
    dns_entropies = [
        f.dns_entropy if f.dns_entropy is not None else _shannon_entropy(f.dns_query or "")
        for f in flows
        if f.dns_query
    ]
    dns_entropy = float(np.mean(dns_entropies)) if dns_entropies else 0.0

    # 4. Flow duration
    durations = [f.flow_duration for f in flows if f.flow_duration]
    flow_duration = float(np.mean(durations)) if durations else 0.0

    # 5. TCP flags
    combined_flags = 0
    for f in flows:
        combined_flags |= _encode_tcp_flags(f.tcp_flags)

    # 6. Avg packet size
    total_bytes = sum(f.byte_count for f in flows)
    total_packets = sum(f.packet_count for f in flows)
    avg_packet_size = total_bytes / total_packets if total_packets > 0 else 0.0

    # 7. Failed connections (RST flag)
    failed = sum(1 for f in flows if f.tcp_flags and "RST" in (f.tcp_flags or "").upper())

    # 8. Outbound ratio (simplified: fraction of flows going to external IPs)
    outbound_bytes = sum(
        f.byte_count for f in flows
        if not f.dest_ip.startswith(("10.", "172.16.", "192.168.", "127."))
    )
    outbound_ratio = outbound_bytes / total_bytes if total_bytes > 0 else 0.0

    return FeatureVector(
        packet_rate=round(packet_rate, 4),
        beacon_interval=round(beacon_interval, 4),
        dns_entropy=round(dns_entropy, 4),
        flow_duration=round(flow_duration, 4),
        tcp_flags_encoded=combined_flags,
        avg_packet_size=round(avg_packet_size, 4),
        failed_connections=failed,
        outbound_ratio=round(outbound_ratio, 4),
    )


async def extract_features_for_flows(
    db: AsyncSession,
    flow_ids: list[UUID],
) -> FeatureVector:
    """Load flows by ID and compute feature vector."""
    result = await db.execute(
        select(NetworkFlow).where(NetworkFlow.id.in_(flow_ids))
    )
    flows = list(result.scalars().all())
    return compute_features_from_flows(flows)


async def get_device_features(
    db: AsyncSession,
    device_id: UUID,
    window_size: int = 100,
) -> DeviceFeatureResponse:
    """Compute features from the latest N flows for a device."""
    result = await db.execute(
        select(NetworkFlow)
        .where(NetworkFlow.device_id == device_id)
        .order_by(NetworkFlow.created_at.desc())
        .limit(window_size)
    )
    flows = list(result.scalars().all())
    features = compute_features_from_flows(flows)
    return DeviceFeatureResponse(
        device_id=device_id,
        features=features,
        flow_count=len(flows),
    )
