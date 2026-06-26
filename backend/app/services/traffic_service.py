"""
KOVIRX — Traffic collection service.

Stores incoming network flows and triggers the ML detection pipeline.
"""

import logging
import math
from collections import Counter
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.traffic import NetworkFlow
from app.schemas.traffic import FlowBatchIngestRequest, FlowIngestRequest, FlowListResponse, FlowResponse

logger = logging.getLogger("kovirx.traffic")


def _shannon_entropy(value: str) -> float:
    """Compute Shannon entropy of a string."""
    if not value:
        return 0.0
    counts = Counter(value)
    length = len(value)
    return -sum((c / length) * math.log2(c / length) for c in counts.values())


async def ingest_flows(
    db: AsyncSession,
    batch: FlowBatchIngestRequest,
) -> list[NetworkFlow]:
    """Store a batch of network flows from an endpoint agent."""
    flow_records: list[NetworkFlow] = []

    for flow_data in batch.flows:
        dns_entropy = None
        if flow_data.dns_query:
            dns_entropy = round(_shannon_entropy(flow_data.dns_query), 4)

        flow = NetworkFlow(
            device_id=batch.device_id,
            source_ip=flow_data.source_ip,
            source_port=flow_data.source_port,
            dest_ip=flow_data.dest_ip,
            dest_port=flow_data.dest_port,
            protocol=flow_data.protocol,
            packet_count=flow_data.packet_count,
            byte_count=flow_data.byte_count,
            flow_duration=flow_data.flow_duration,
            tcp_flags=flow_data.tcp_flags,
            dns_query=flow_data.dns_query,
            dns_entropy=dns_entropy,
            start_time=flow_data.start_time or datetime.now(timezone.utc),
            end_time=flow_data.end_time,
        )
        db.add(flow)
        flow_records.append(flow)

    # Handle legacy event format for backwards compatibility
    for event in batch.events:
        flow = NetworkFlow(
            device_id=batch.device_id,
            source_ip=event.get("source_ip", "0.0.0.0"),
            dest_ip=event.get("destination_ip", event.get("dest_ip", "0.0.0.0")),
            protocol=event.get("protocol", "TCP"),
            packet_count=int(event.get("packet_count", 0)),
            byte_count=int(event.get("bytes", event.get("byte_count", 0))),
            flow_duration=float(event.get("flow_duration", 0)),
            dns_query=event.get("dns_query", event.get("query")),
            dns_entropy=round(_shannon_entropy(str(event.get("dns_query", ""))), 4) if event.get("dns_query") else None,
            start_time=datetime.now(timezone.utc),
        )
        db.add(flow)
        flow_records.append(flow)

    await db.flush()
    for f in flow_records:
        await db.refresh(f)

    logger.info("Ingested %d flows for device %s", len(flow_records), batch.device_id)
    return flow_records


async def list_flows(
    db: AsyncSession,
    device_id: UUID | None = None,
    skip: int = 0,
    limit: int = 50,
) -> FlowListResponse:
    """Return paginated list of network flows."""
    from sqlalchemy import func

    query = select(NetworkFlow)
    count_query = select(func.count(NetworkFlow.id))

    if device_id:
        query = query.where(NetworkFlow.device_id == device_id)
        count_query = count_query.where(NetworkFlow.device_id == device_id)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    result = await db.execute(
        query.order_by(NetworkFlow.created_at.desc()).offset(skip).limit(limit)
    )
    flows = [FlowResponse.model_validate(f) for f in result.scalars().all()]
    return FlowListResponse(total=total, flows=flows)


async def get_flow(db: AsyncSession, flow_id: UUID) -> FlowResponse:
    """Get a single flow by ID."""
    from app.core.exceptions import NotFoundException

    result = await db.execute(select(NetworkFlow).where(NetworkFlow.id == flow_id))
    flow = result.scalar_one_or_none()
    if not flow:
        raise NotFoundException("Flow")
    return FlowResponse.model_validate(flow)
