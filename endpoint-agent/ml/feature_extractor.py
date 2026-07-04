"""
KOVIRX Endpoint Agent — Feature Extractor.

Extracts the 22-dimensional feature vector from flow telemetry data
for ML model consumption. Handles rolling window calculations for
aggregate features like unique_remote_ips and connection_count.
"""

import logging
import psutil

logger = logging.getLogger("kovirx.agent.ml.feature_extractor")


# ── Feature Schema (matches ML training pipeline) ────────────────
FEATURE_NAMES = [
    "event_count", "network_event_count", "dns_query_count", "max_dns_entropy",
    "avg_dns_entropy", "flow_duration", "packet_rate", "connection_count",
    "bytes_sent", "bytes_recv", "packets_sent", "packets_recv", "unique_remote_ips",
    "public_remote_ips", "listening_ports", "top_remote_port_count",
    "failed_connection_ratio", "tcp_flag_score", "beacon_interval_score",
    "outbound_frequency", "cpu_percent", "process_count",
]


def extract_features(
    flow: dict,
    batch_size: int = 1,
    unique_ips: int = 1,
    public_ips: int = 1,
) -> dict[str, float]:
    """
    Extract 22-dimensional feature vector from a compiled flow dict.

    Args:
        flow: Compiled flow dict from FlowEngine._compile_flow()
        batch_size: Number of flows in the current batch (for event_count)
        unique_ips: Number of unique remote IPs seen (rolling window)
        public_ips: Number of public remote IPs seen (rolling window)

    Returns:
        Dict mapping feature names to float values
    """
    dns_entropy = flow.get("dns_entropy", 0.0)
    flow_duration = max(0.001, flow.get("flow_duration", 0.001))
    packet_count = flow.get("packet_count", 0)
    beacon_interval = flow.get("beacon_interval", 0.0)

    # Beacon score: low variance = high regularity = suspicious
    beacon_score = 0.0
    if beacon_interval > 0.0:
        # Inverse relationship: lower variance = more regular = higher score
        beacon_score = max(0.0, min(1.0, 1.0 - (beacon_interval / 10.0)))

    # TCP flag score: presence of RST or SYN-only indicates scanning
    tcp_flags = flow.get("tcp_flags", "") or ""
    tcp_flag_score = 0.0
    if "R" in tcp_flags:
        tcp_flag_score = max(tcp_flag_score, 0.7)
    if "S" in tcp_flags and "A" not in tcp_flags:
        tcp_flag_score = max(tcp_flag_score, 0.5)

    # Determine if destination is public IP
    dest_ip = flow.get("dest_ip", "")
    is_public = not dest_ip.startswith(("10.", "192.168.", "172.16.", "127.", "0."))

    # Failed connection ratio
    failed = flow.get("failed_connections", 0)
    failed_ratio = min(1.0, failed / max(1, packet_count))

    features = {
        "event_count": float(batch_size),
        "network_event_count": float(batch_size),
        "dns_query_count": 1.0 if flow.get("dns_query") else 0.0,
        "max_dns_entropy": dns_entropy,
        "avg_dns_entropy": dns_entropy,
        "flow_duration": flow_duration,
        "packet_rate": packet_count / flow_duration,
        "connection_count": float(batch_size),
        "bytes_sent": float(flow.get("bytes_sent", 0)),
        "bytes_recv": float(flow.get("bytes_recv", 0)),
        "packets_sent": float(flow.get("packets_sent", 0)),
        "packets_recv": float(flow.get("packets_recv", 0)),
        "unique_remote_ips": float(unique_ips),
        "public_remote_ips": float(public_ips) if is_public else 0.0,
        "listening_ports": 0.0,
        "top_remote_port_count": float(packet_count),
        "failed_connection_ratio": failed_ratio,
        "tcp_flag_score": tcp_flag_score,
        "beacon_interval_score": beacon_score,
        "outbound_frequency": float(flow.get("packets_sent", 0)) / flow_duration,
        "cpu_percent": float(psutil.cpu_percent(interval=0)),
        "process_count": float(len(psutil.pids())),
    }

    return features
