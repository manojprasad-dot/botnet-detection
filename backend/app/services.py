from datetime import datetime, timezone
import math
from collections import Counter
from uuid import uuid4

from .config import settings
from .schemas import (
    AIBrainSummary,
    Alert,
    CommandCenterSnapshot,
    DeviceCommandNode,
    PlatformSummary,
    RegisteredDevice,
    Severity,
    TelemetryBatch,
    TelemetryRecord,
    ThreatTimelineEntry,
    TrafficFeedEntry,
)
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


def get_command_center_snapshot() -> CommandCenterSnapshot:
    summary = get_platform_summary()
    devices = list_devices()
    alerts = list_alerts(limit=20)
    telemetry = list_telemetry(limit=60)

    alerts_by_device: dict[str, list[Alert]] = {}
    for alert in alerts:
        alerts_by_device.setdefault(alert.device_id, []).append(alert)

    telemetry_by_device: dict[str, list[TelemetryRecord]] = {}
    for event in telemetry:
        telemetry_by_device.setdefault(event.device_id, []).append(event)

    nodes = [
        build_device_node(device, alerts_by_device.get(device.device_id, []), telemetry_by_device.get(device.device_id, []))
        for device in devices
    ]
    nodes.sort(key=lambda node: node.risk_score, reverse=True)

    ai_brain = build_ai_brain(summary, alerts, nodes)
    timeline = build_timeline(alerts, telemetry)
    traffic_feed = build_traffic_feed(telemetry)

    return CommandCenterSnapshot(
        summary=summary,
        ai_brain=ai_brain,
        nodes=nodes,
        alerts=alerts,
        timeline=timeline,
        traffic_feed=traffic_feed,
    )


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


def build_device_node(
    device: RegisteredDevice,
    device_alerts: list[Alert],
    device_telemetry: list[TelemetryRecord],
) -> DeviceCommandNode:
    severity_weights = {"low": 18, "medium": 42, "high": 68, "critical": 92}
    base_risk = max((severity_weights.get(alert.severity, 0) for alert in device_alerts), default=8)
    alert_pressure = min(24, len(device_alerts) * 6)
    staleness_penalty = compute_staleness_penalty(device.last_seen_at)
    telemetry_penalty = compute_telemetry_penalty(device_telemetry)
    risk_score = min(100, base_risk + alert_pressure + staleness_penalty + telemetry_penalty)
    health_score = max(0, 100 - risk_score)
    confidence_score = min(
        100,
        max(
            40,
            int(
                (
                    max((alert.confidence_score for alert in device_alerts), default=0.48) * 100
                )
            ),
        ),
    )
    reasons = build_reasons(device_alerts, device_telemetry)
    latest_alert_title = device_alerts[0].title if device_alerts else None

    if risk_score >= 85:
        status = "critical"
    elif risk_score >= 60:
        status = "threat"
    elif risk_score >= 32:
        status = "warning"
    else:
        status = "safe"

    return DeviceCommandNode(
        device_id=device.device_id,
        label=device.hostname,
        operating_system=device.operating_system,
        status=status,
        risk_score=risk_score,
        health_score=health_score,
        confidence_score=confidence_score,
        last_seen_at=device.last_seen_at,
        tags=device.tags,
        reasons=reasons,
        latest_alert_title=latest_alert_title,
    )


def compute_staleness_penalty(last_seen_at: datetime) -> int:
    if last_seen_at.tzinfo is None:
        last_seen_at = last_seen_at.replace(tzinfo=timezone.utc)

    age_minutes = (datetime.now(timezone.utc) - last_seen_at).total_seconds() / 60
    if age_minutes > 240:
        return 20
    if age_minutes > 60:
        return 12
    if age_minutes > 15:
        return 6
    return 0


def compute_telemetry_penalty(device_telemetry: list[TelemetryRecord]) -> int:
    penalty = 0
    for event in device_telemetry[:8]:
        if event.event_type == "socket_snapshot":
            public_remote_ips = int(event.payload.get("public_remote_ips", 0))
            penalty += min(10, public_remote_ips // 8)
        if event.event_type == "network_summary":
            connection_count = int(event.payload.get("connection_count", 0))
            penalty += min(10, connection_count // 80)
    return min(18, penalty)


def build_reasons(device_alerts: list[Alert], device_telemetry: list[TelemetryRecord]) -> list[str]:
    reasons: list[str] = []

    for alert in device_alerts[:3]:
        reasons.append(alert.title)

    for event in device_telemetry[:4]:
        if event.event_type == "dns_query":
            reasons.append("Abnormal DNS request pattern observed")
        elif event.event_type == "network_summary":
            connection_count = int(event.payload.get("connection_count", 0))
            reasons.append(f"Outbound connection count reached {connection_count}")
        elif event.event_type == "socket_snapshot":
            public_remote_ips = int(event.payload.get("public_remote_ips", 0))
            reasons.append(f"Connected to {public_remote_ips} public remote IPs")

    if not reasons:
        reasons.append("Telemetry is within the current lightweight baseline")

    unique_reasons: list[str] = []
    for reason in reasons:
        if reason not in unique_reasons:
            unique_reasons.append(reason)

    return unique_reasons[:4]


def build_ai_brain(
    summary: PlatformSummary, alerts: list[Alert], nodes: list[DeviceCommandNode]
) -> AIBrainSummary:
    global_risk = min(
        100,
        (
            summary.total_alerts * 12
            + sum(node.risk_score for node in nodes[:5]) // max(1, min(5, len(nodes)))
        ),
    )
    confidence = min(
        99,
        max(
            46,
            int(sum(alert.confidence_score for alert in alerts[:6]) * 100 / max(1, min(6, len(alerts)))),
        ),
    )

    if global_risk >= 85:
        threat_level = "Critical threat spread"
        headline = "Multiple high-risk signals suggest active compromise paths."
    elif global_risk >= 60:
        threat_level = "Elevated botnet pressure"
        headline = "The AI engine sees coordinated suspicious behavior across the fleet."
    elif global_risk >= 30:
        threat_level = "Anomalous activity detected"
        headline = "The command center sees weak but meaningful attack indicators."
    else:
        threat_level = "Baseline holding"
        headline = "No strong botnet campaign indicators are dominating the network."

    top_reasons = []
    if summary.alerts_by_severity:
        top_reasons.append(
            "Alert severity mix: "
            + ", ".join(f"{key}={value}" for key, value in summary.alerts_by_severity.items())
        )
    if summary.events_by_type:
        top_reasons.append(
            "Telemetry mix: "
            + ", ".join(f"{key}={value}" for key, value in summary.events_by_type.items())
        )
    if nodes:
        highest = nodes[0]
        top_reasons.append(
            f"Highest-risk endpoint: {highest.label} at {highest.risk_score}% risk."
        )
    if alerts:
        top_reasons.append(
            f"Latest alert: {alerts[0].title} on device {alerts[0].device_id[:8]}."
        )

    return AIBrainSummary(
        threat_level=threat_level,
        confidence_score=confidence,
        global_risk_score=global_risk,
        headline=headline,
        explanations=top_reasons[:4],
    )


def build_timeline(
    alerts: list[Alert], telemetry: list[TelemetryRecord]
) -> list[ThreatTimelineEntry]:
    combined: list[ThreatTimelineEntry] = []

    for event in telemetry[:12]:
        stage, title, description, severity = map_event_to_timeline(event)
        combined.append(
            ThreatTimelineEntry(
                stage=stage,
                title=title,
                device_id=event.device_id,
                occurred_at=event.collected_at,
                severity=severity,
                description=description,
            )
        )

    for alert in alerts[:12]:
        combined.append(
            ThreatTimelineEntry(
                stage="Escalation",
                title=alert.title,
                device_id=alert.device_id,
                occurred_at=alert.created_at,
                severity=alert.severity,
                description=alert.description,
            )
        )

    combined.sort(key=lambda item: item.occurred_at, reverse=True)
    return combined[:10]


def map_event_to_timeline(
    event: TelemetryRecord,
) -> tuple[str, str, str, str]:
    if event.event_type == "dns_query":
        query = str(event.payload.get("query", "unknown domain"))
        return (
            "Recon",
            "Suspicious DNS pattern",
            f"Endpoint requested {query}, which may align with beacon staging or DGA behavior.",
            "medium",
        )
    if event.event_type == "network_summary":
        connections = int(event.payload.get("connection_count", 0))
        return (
            "Beaconing",
            "Outbound traffic surge",
            f"Connection volume reached {connections}, consistent with scanning or call-home activity.",
            "high" if connections >= settings.alert_connection_threshold else "low",
        )
    if event.event_type == "socket_snapshot":
        remotes = int(event.payload.get("public_remote_ips", 0))
        return (
            "Propagation",
            "Remote endpoint fan-out",
            f"Device communicated with {remotes} public destinations during the latest snapshot.",
            "high" if remotes >= 20 else "medium",
        )
    return (
        "Observation",
        event.event_type.replace("_", " ").title(),
        "Baseline telemetry captured for ongoing analysis.",
        "low",
    )


def build_traffic_feed(telemetry: list[TelemetryRecord]) -> list[TrafficFeedEntry]:
    feed = []
    for event in telemetry[:12]:
        feed.append(
            TrafficFeedEntry(
                device_id=event.device_id,
                event_type=event.event_type,
                source=event.source,
                observed_at=event.collected_at,
                summary=describe_telemetry_event(event),
            )
        )
    return feed


def describe_telemetry_event(event: TelemetryRecord) -> str:
    if event.event_type == "dns_query":
        return f"DNS lookup: {event.payload.get('query', 'unknown')}"
    if event.event_type == "network_summary":
        return (
            "Traffic snapshot with "
            f"{event.payload.get('connection_count', 0)} outbound connections"
        )
    if event.event_type == "socket_snapshot":
        return (
            "Socket map shows "
            f"{event.payload.get('public_remote_ips', 0)} public remote endpoints"
        )
    if event.event_type == "system_profile":
        return (
            "Endpoint profile reports "
            f"CPU {event.payload.get('cpu_percent', 0)}% and "
            f"{event.payload.get('process_count', 0)} processes"
        )
    return "Telemetry event captured for model context"
