"""
KOVIRX Endpoint Agent — Feature Extractor.

Extracts a 46-dimensional feature vector from flow telemetry data for ML models.
Maintains backward compatibility by placing legacy features first.
"""

import math
import logging
from collections import Counter
import psutil

logger = logging.getLogger("kovirx.agent.ml.feature_extractor")

FEATURE_NAMES = [
    # ── Legacy 22 features (Must remain first/same order) ──
    "event_count", "network_event_count", "dns_query_count", "max_dns_entropy",
    "avg_dns_entropy", "flow_duration", "packet_rate", "connection_count",
    "bytes_sent", "bytes_recv", "packets_sent", "packets_recv", "unique_remote_ips",
    "public_remote_ips", "listening_ports", "top_remote_port_count",
    "failed_connection_ratio", "tcp_flag_score", "beacon_interval_score",
    "outbound_frequency", "cpu_percent", "process_count",
    # ── Enterprise EDR 24 new features (Total 46) ──
    "min_packet_size", "max_packet_size", "mean_packet_size", "std_packet_size",
    "variance_packet_size", "byte_rate", "direction_ratio", "tcp_flags_syn_count",
    "tcp_flags_ack_count", "tcp_flags_fin_count", "tcp_flags_rst_count", "tcp_flags_psh_count",
    "tls_sni_entropy", "http_methods_get_count", "http_methods_post_count", "port_diversity",
    "session_duration", "payload_entropy", "connection_frequency", "beacon_interval_variance",
    "burst_count", "ram_percent", "disk_percent", "unique_dest_count"
]


def extract_features(
    flow: dict,
    batch_size: int = 1,
    unique_ips: int = 1,
    public_ips: int = 1,
) -> dict[str, float]:
    """
    Extract 46-dimensional feature vector from a compiled flow dict.
    """
    dns_entropy = flow.get("dns_entropy", 0.0)
    flow_duration = max(0.001, flow.get("flow_duration", 0.001))
    packet_count = flow.get("packet_count", 1)
    beacon_interval = flow.get("beacon_interval", 0.0)
    packets_sent = flow.get("packets_sent", 0)
    packets_recv = flow.get("packets_recv", 0)
    bytes_sent = flow.get("bytes_sent", 0)
    bytes_recv = flow.get("bytes_recv", 0)

    # Beacon score: low variance = high regularity = suspicious
    beacon_score = 0.0
    if beacon_interval > 0.0:
        beacon_score = max(0.0, min(1.0, 1.0 - (beacon_interval / 10.0)))

    # TCP flag score
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

    # Packet size list calculations
    sizes = flow.get("packet_sizes", []) or [flow.get("avg_packet_size", 0)]
    min_size = float(min(sizes)) if sizes else 0.0
    max_size = float(max(sizes)) if sizes else 0.0
    mean_size = float(sum(sizes) / len(sizes)) if sizes else 0.0
    variance_size = float(sum((x - mean_size) ** 2 for x in sizes) / len(sizes)) if sizes else 0.0
    std_size = float(math.sqrt(variance_size))

    # TCP flag specific counts
    syn_count = 1.0 if "S" in tcp_flags else 0.0
    ack_count = 1.0 if "A" in tcp_flags else 0.0
    fin_count = 1.0 if "F" in tcp_flags else 0.0
    rst_count = 1.0 if "R" in tcp_flags else 0.0
    psh_count = 1.0 if "P" in tcp_flags else 0.0

    # TLS SNI & DNS query info
    tls_sni = flow.get("tls_sni", "") or ""
    tls_entropy = shannon_entropy(tls_sni)

    # HTTP Methods
    http_method = flow.get("http_method", "") or ""
    get_count = 1.0 if http_method.upper() == "GET" else 0.0
    post_count = 1.0 if http_method.upper() == "POST" else 0.0

    # Burst count (timestamps with IAT < 10ms)
    timestamps = flow.get("packet_timestamps", []) or []
    bursts = 0
    if len(timestamps) >= 2:
        intervals = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
        bursts = sum(1 for i in intervals if i < 0.01)

    features = {
        "event_count": float(batch_size),
        "network_event_count": float(batch_size),
        "dns_query_count": 1.0 if flow.get("dns_query") else 0.0,
        "max_dns_entropy": dns_entropy,
        "avg_dns_entropy": dns_entropy,
        "flow_duration": flow_duration,
        "packet_rate": packet_count / flow_duration,
        "connection_count": float(batch_size),
        "bytes_sent": float(bytes_sent),
        "bytes_recv": float(bytes_recv),
        "packets_sent": float(packets_sent),
        "packets_recv": float(packets_recv),
        "unique_remote_ips": float(unique_ips),
        "public_remote_ips": float(public_ips) if is_public else 0.0,
        "listening_ports": 0.0,
        "top_remote_port_count": float(packet_count),
        "failed_connection_ratio": failed_ratio,
        "tcp_flag_score": tcp_flag_score,
        "beacon_interval_score": beacon_score,
        "outbound_frequency": float(packets_sent) / flow_duration,
        "cpu_percent": float(psutil.cpu_percent(interval=0)),
        "process_count": float(len(psutil.pids())),
        # ── Enterprise EDR features ──
        "min_packet_size": min_size,
        "max_packet_size": max_size,
        "mean_packet_size": mean_size,
        "std_packet_size": std_size,
        "variance_packet_size": variance_size,
        "byte_rate": (bytes_sent + bytes_recv) / flow_duration,
        "direction_ratio": packets_sent / max(1, packets_recv),
        "tcp_flags_syn_count": syn_count,
        "tcp_flags_ack_count": ack_count,
        "tcp_flags_fin_count": fin_count,
        "tcp_flags_rst_count": rst_count,
        "tcp_flags_psh_count": psh_count,
        "tls_sni_entropy": tls_entropy,
        "http_methods_get_count": get_count,
        "http_methods_post_count": post_count,
        "port_diversity": 1.0 / max(1, packet_count),
        "session_duration": flow_duration,
        "payload_entropy": shannon_entropy(flow.get("payload", "")),
        "connection_frequency": packet_count / flow_duration,
        "beacon_interval_variance": beacon_interval,
        "burst_count": float(bursts),
        "ram_percent": float(psutil.virtual_memory().percent),
        "disk_percent": float(psutil.disk_usage('/').percent),
        "unique_dest_count": float(unique_ips)
    }

    return features


def shannon_entropy(value: str) -> float:
    """Compute Shannon entropy."""
    if not value:
        return 0.0
    counts = Counter(value)
    length = len(value)
    return -sum((c / length) * math.log2(c / length) for c in counts.values())
