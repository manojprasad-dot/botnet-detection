import math
from collections import Counter

from backend.schemas.telemetry import TelemetryBatch, TelemetryEvent
from ml.feature_schema import FEATURE_NAMES


def extract_feature_vector(batch: TelemetryBatch) -> dict[str, float]:
    dns_entropies: list[float] = []
    network_events = 0
    values: dict[str, float] = {name: 0.0 for name in FEATURE_NAMES}
    values["event_count"] = float(len(batch.events))

    for event in batch.events:
        if event.event_type in {"network_summary", "socket_snapshot", "dns_query"}:
            network_events += 1

        if event.event_type == "dns_query":
            query = str(event.payload.get("query", ""))
            entropy = shannon_entropy(query)
            dns_entropies.append(entropy)
            values["dns_query_count"] += 1

        if event.event_type == "network_summary":
            values["flow_duration"] = max(
                values["flow_duration"], float(event.payload.get("flow_duration", 0))
            )
            values["connection_count"] = max(
                values["connection_count"], float(event.payload.get("connection_count", 0))
            )
            values["bytes_sent"] = max(values["bytes_sent"], float(event.payload.get("bytes_sent", 0)))
            values["bytes_recv"] = max(values["bytes_recv"], float(event.payload.get("bytes_recv", 0)))
            values["packets_sent"] = max(values["packets_sent"], float(event.payload.get("packets_sent", 0)))
            values["packets_recv"] = max(values["packets_recv"], float(event.payload.get("packets_recv", 0)))
            values["failed_connection_ratio"] = max(
                values["failed_connection_ratio"],
                float(event.payload.get("failed_connection_ratio", 0)),
            )
            values["tcp_flag_score"] = max(
                values["tcp_flag_score"], float(event.payload.get("tcp_flag_score", 0))
            )
            values["beacon_interval_score"] = max(
                values["beacon_interval_score"],
                infer_beacon_score(event),
            )
            values["outbound_frequency"] = max(
                values["outbound_frequency"], float(event.payload.get("outbound_frequency", 0))
            )
            values["packet_rate"] = max(
                values["packet_rate"], float(event.payload.get("packet_rate", 0))
            )
            # ── Enterprise EDR features ──
            values["min_packet_size"] = max(values["min_packet_size"], float(event.payload.get("min_packet_size", 0.0)))
            values["max_packet_size"] = max(values["max_packet_size"], float(event.payload.get("max_packet_size", 0.0)))
            values["mean_packet_size"] = max(values["mean_packet_size"], float(event.payload.get("mean_packet_size", 0.0)))
            values["std_packet_size"] = max(values["std_packet_size"], float(event.payload.get("std_packet_size", 0.0)))
            values["variance_packet_size"] = max(values["variance_packet_size"], float(event.payload.get("variance_packet_size", 0.0)))
            values["byte_rate"] = max(values["byte_rate"], float(event.payload.get("byte_rate", 0.0)))
            values["direction_ratio"] = max(values["direction_ratio"], float(event.payload.get("direction_ratio", 0.0)))
            values["tcp_flags_syn_count"] = max(values["tcp_flags_syn_count"], float(event.payload.get("tcp_flags_syn_count", 0.0)))
            values["tcp_flags_ack_count"] = max(values["tcp_flags_ack_count"], float(event.payload.get("tcp_flags_ack_count", 0.0)))
            values["tcp_flags_fin_count"] = max(values["tcp_flags_fin_count"], float(event.payload.get("tcp_flags_fin_count", 0.0)))
            values["tcp_flags_rst_count"] = max(values["tcp_flags_rst_count"], float(event.payload.get("tcp_flags_rst_count", 0.0)))
            values["tcp_flags_psh_count"] = max(values["tcp_flags_psh_count"], float(event.payload.get("tcp_flags_psh_count", 0.0)))
            values["tls_sni_entropy"] = max(values["tls_sni_entropy"], float(event.payload.get("tls_sni_entropy", 0.0)))
            values["http_methods_get_count"] = max(values["http_methods_get_count"], float(event.payload.get("http_methods_get_count", 0.0)))
            values["http_methods_post_count"] = max(values["http_methods_post_count"], float(event.payload.get("http_methods_post_count", 0.0)))
            values["port_diversity"] = max(values["port_diversity"], float(event.payload.get("port_diversity", 0.0)))
            values["session_duration"] = max(values["session_duration"], float(event.payload.get("session_duration", 0.0)))
            values["payload_entropy"] = max(values["payload_entropy"], float(event.payload.get("payload_entropy", 0.0)))
            values["connection_frequency"] = max(values["connection_frequency"], float(event.payload.get("connection_frequency", 0.0)))
            values["beacon_interval_variance"] = max(values["beacon_interval_variance"], float(event.payload.get("beacon_interval_variance", 0.0)))
            values["burst_count"] = max(values["burst_count"], float(event.payload.get("burst_count", 0.0)))

        if event.event_type == "socket_snapshot":
            values["unique_remote_ips"] = max(
                values["unique_remote_ips"], float(event.payload.get("unique_remote_ips", 0))
            )
            values["public_remote_ips"] = max(
                values["public_remote_ips"], float(event.payload.get("public_remote_ips", 0))
            )
            values["listening_ports"] = max(
                values["listening_ports"], float(event.payload.get("listening_ports", 0))
            )
            values["top_remote_port_count"] = max(
                values["top_remote_port_count"],
                extract_top_remote_port_count(event),
            )
            # EDR unique dest count
            values["unique_dest_count"] = max(
                values["unique_dest_count"], float(event.payload.get("unique_dest_count", 0.0))
            )

        if event.event_type == "system_profile":
            values["cpu_percent"] = max(values["cpu_percent"], float(event.payload.get("cpu_percent", 0)))
            values["process_count"] = max(
                values["process_count"], float(event.payload.get("process_count", 0))
            )
            values["ram_percent"] = max(values["ram_percent"], float(event.payload.get("ram_percent", 0.0)))
            values["disk_percent"] = max(values["disk_percent"], float(event.payload.get("disk_percent", 0.0)))

    values["network_event_count"] = float(network_events)
    if dns_entropies:
        values["max_dns_entropy"] = max(dns_entropies)
        values["avg_dns_entropy"] = sum(dns_entropies) / len(dns_entropies)

    if values["outbound_frequency"] == 0 and values["connection_count"] > 0:
        values["outbound_frequency"] = values["connection_count"] / max(1, values["event_count"])

    if values["packet_rate"] == 0 and values["flow_duration"] > 0:
        values["packet_rate"] = (
            values["packets_sent"] + values["packets_recv"]
        ) / values["flow_duration"]

    return values


def feature_vector_to_ordered_list(features: dict[str, float]) -> list[float]:
    return [float(features.get(name, 0.0)) for name in FEATURE_NAMES]


def shannon_entropy(value: str) -> float:
    if not value:
        return 0.0

    counts = Counter(value)
    length = len(value)
    return -sum((count / length) * math.log2(count / length) for count in counts.values())


def extract_top_remote_port_count(event: TelemetryEvent) -> float:
    ports = event.payload.get("top_remote_ports", [])
    if not isinstance(ports, list):
        return 0.0

    counts = []
    for item in ports:
        if isinstance(item, dict):
            counts.append(float(item.get("count", 0)))
    return max(counts, default=0.0)


def infer_beacon_score(event: TelemetryEvent) -> float:
    explicit_score = event.payload.get("beacon_interval_score")
    if explicit_score is not None:
        return float(explicit_score)

    connection_count = float(event.payload.get("connection_count", 0))
    packets_sent = float(event.payload.get("packets_sent", 0))
    packets_recv = float(event.payload.get("packets_recv", 0))
    if connection_count < 50:
        return 0.0

    packet_ratio = packets_sent / max(1.0, packets_recv)
    if 1.5 <= packet_ratio <= 4.0:
        return min(1.0, connection_count / 250)
    return min(0.7, connection_count / 350)
