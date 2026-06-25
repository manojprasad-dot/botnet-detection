import math
from collections import Counter
from datetime import datetime, timezone
from uuid import uuid4

from .config import settings
from .schemas import Alert, RegisteredDevice, Severity, TelemetryBatch
from .store import store


def register_device(device: RegisteredDevice) -> RegisteredDevice:
    store.devices[device.device_id] = device
    return device


def list_devices() -> list[RegisteredDevice]:
    return list(store.devices.values())


def list_alerts() -> list[Alert]:
    return sorted(store.alerts, key=lambda alert: alert.created_at, reverse=True)


def update_last_seen(device_id: str) -> None:
    device = store.devices.get(device_id)
    if device:
        device.last_seen_at = datetime.now(timezone.utc)


def ingest_telemetry(batch: TelemetryBatch) -> list[Alert]:
    store.telemetry[batch.device_id].extend(batch.events)
    update_last_seen(batch.device_id)
    alerts = detect_suspicious_activity(batch)
    store.alerts.extend(alerts)
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

    return alerts


def shannon_entropy(value: str) -> float:
    if not value:
        return 0.0

    counts = Counter(value)
    length = len(value)
    return -sum((count / length) * math.log2(count / length) for count in counts.values())
