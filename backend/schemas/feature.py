"""
KOVIRX — Feature extraction schemas.
"""

from uuid import UUID

from pydantic import BaseModel


class FeatureVector(BaseModel):
    """Computed feature vector for a single flow or device window."""
    packet_rate: float = 0.0
    beacon_interval: float = 0.0
    dns_entropy: float = 0.0
    flow_duration: float = 0.0
    tcp_flags_encoded: int = 0
    avg_packet_size: float = 0.0
    failed_connections: int = 0
    outbound_ratio: float = 0.0


class FeatureExtractRequest(BaseModel):
    flow_ids: list[UUID]


class DeviceFeatureResponse(BaseModel):
    device_id: UUID
    features: FeatureVector
    flow_count: int
