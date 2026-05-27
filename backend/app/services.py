import math
from collections import Counter
from uuid import uuid4

from .config import settings
from .schemas import Alert, PlatformSummary, RegisteredDevice, Severity, TelemetryBatch, TelemetryRecord
from .store import store


def register_device(device: RegisteredDevice) -> RegisteredDevice:
    return store.register_device(device)


def get_device(device_id: str) -> RegisteredDevice | None:
    return store.get_device(device_id)


def list_devices() -> list[RegisteredDevice]:
    return store.list_devices()


def list_alerts(limit: int = 100, device_id: str | None = None) -> list[Alert]:
    return store.list_alerts(limit=limit, device_id=device_id)


def list_telemetry(
    limit: int = 100, device_id: str | None = None
) -> list[TelemetryRecord]:
    return store.list_telemetry(limit=limit, device_id=device_id)


def get_platform_summary() -> PlatformSummary:
    return store.get_summary()


def ingest_telemetry(batch: TelemetryBatch) -> list[Alert]:
    alerts = detect_suspicious_activity(batch)
    store.ingest_telemetry(batch, alerts)
    return alerts


def detect_suspicious_activity(batch: TelemetryBatch) -> list[Alert]:
    alerts: list[Alert] = []

    for event in batch.events:
        if event.event_type == "dns_query":
            query = str(event.payload.get("query", ""))
            entropy = shannon_entropy(query)
            if entropy >= settings.alert_dns_entropy_threshold:
                alerts.append(
                    Alert(
                        alert_id=str(uuid4()),
                        device_id=batch.device_id,
                        severity=Severity.medium,
                        title="High-entropy DNS query detected",
                        description=(
                            "A DNS query with unusually high entropy may indicate "
                            "algorithmically generated domains or C2 beaconing."
                        ),
                        confidence_score=min(0.95, entropy / 6.0),
                        evidence={"query": query, "entropy": round(entropy, 3)},
                    )
                )

        if event.event_type == "network_summary":
            connection_count = int(event.payload.get("connection_count", 0))
            if connection_count >= settings.alert_connection_threshold:
                alerts.append(
                    Alert(
                        alert_id=str(uuid4()),
                        device_id=batch.device_id,
                        severity=Severity.high,
                        title="Abnormal connection volume",
                        description=(
                            "The endpoint reported a connection count above the current "
                            "baseline threshold, which may suggest scanning, beaconing, "
                            "or botnet fan-out behavior."
                        ),
                        confidence_score=0.81,
                        evidence={"connection_count": connection_count},
                    )
                )

        if event.event_type == "socket_snapshot":
            unique_remote_ips = int(event.payload.get("unique_remote_ips", 0))
            public_remote_ips = int(event.payload.get("public_remote_ips", 0))
            if unique_remote_ips >= 25 or public_remote_ips >= 20:
                alerts.append(
                    Alert(
                        alert_id=str(uuid4()),
                        device_id=batch.device_id,
                        severity=Severity.high,
                        title="Suspicious remote endpoint fan-out",
                        description=(
                            "The endpoint is communicating with an unusually large "
                            "number of remote addresses, which may indicate scanning "
                            "activity, proxying, or botnet coordination."
                        ),
                        confidence_score=0.86,
                        evidence={
                            "unique_remote_ips": unique_remote_ips,
                            "public_remote_ips": public_remote_ips,
                        },
                    )
                )

    return alerts


def shannon_entropy(value: str) -> float:
    if not value:
        return 0.0

    counts = Counter(value)
    length = len(value)
    return -sum((count / length) * math.log2(count / length) for count in counts.values())
