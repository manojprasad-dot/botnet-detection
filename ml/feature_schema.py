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

MODEL_LAYERS = [
    "Random Forest fast screen",
    "XGBoost known-threat classifier",
    "Isolation Forest unknown-threat verifier",
    "Threat confidence voting layer",
]
