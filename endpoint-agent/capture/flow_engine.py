"""
KOVIRX Endpoint Agent — Flow Engine.

Tracks and aggregates raw packet events into directional network flows.
Computes statistical network properties for ML feature extraction.
Supports immediate flush for high-priority IOC-matching destinations.
"""

import logging
import math
import threading
import time
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone

from scapy.layers.inet import IP, TCP, UDP
from scapy.layers.inet6 import IPv6
from scapy.layers.dns import DNS, DNSQR

logger = logging.getLogger("kovirx.agent.capture.flow_engine")


@dataclass
class FlowStats:
    """Aggregated statistics for a single network flow."""
    src_ip: str
    dest_ip: str
    src_port: int | None
    dest_port: int | None
    protocol: str
    start_time: float
    last_seen: float
    packet_count: int = 0
    byte_count: int = 0
    packets_sent: int = 0
    packets_recv: int = 0
    bytes_sent: int = 0
    bytes_recv: int = 0
    tcp_flags: set[str] = field(default_factory=set)
    dns_queries: list[str] = field(default_factory=list)
    failed_connections: int = 0
    packet_timestamps: list[float] = field(default_factory=list)
    packet_sizes: list[int] = field(default_factory=list)


class FlowEngine:
    """
    Tracks and aggregates raw packets into directional network flows.

    Features:
        - 5-tuple flow keying (src_ip, dst_ip, src_port, dst_port, protocol)
        - Bidirectional flow tracking with sent/recv counters
        - DNS query extraction and entropy calculation
        - Beacon interval analysis via timing statistics
        - Immediate flush for IOC-matching destinations
        - Configurable active/idle timeouts
    """

    def __init__(self, active_timeout: float = 60.0, idle_timeout: float = 5.0):
        self.active_timeout = active_timeout
        self.idle_timeout = idle_timeout
        self.flows: dict[tuple, FlowStats] = {}
        self.lock = threading.Lock()
        self.total_flows_completed: int = 0

    def process_packet(self, pkt, local_ips: set[str]) -> None:
        """Process a sniffed packet and update flow tracking statistics."""
        if IP in pkt:
            ip_layer = pkt[IP]
            src_ip = ip_layer.src
            dest_ip = ip_layer.dst
        elif IPv6 in pkt:
            ip_layer = pkt[IPv6]
            src_ip = ip_layer.src
            dest_ip = ip_layer.dst
        else:
            return

        protocol = "OTHER"
        src_port = None
        dest_port = None
        tcp_flags = ""

        if TCP in pkt:
            protocol = "TCP"
            src_port = pkt[TCP].sport
            dest_port = pkt[TCP].dport
            tcp_flags = str(pkt[TCP].flags)
        elif UDP in pkt:
            protocol = "UDP"
            src_port = pkt[UDP].sport
            dest_port = pkt[UDP].dport

        # Directional flow key: normalize by local/remote
        is_outbound = src_ip in local_ips or (dest_ip not in local_ips and src_ip < dest_ip)
        if is_outbound:
            key = (src_ip, dest_ip, src_port, dest_port, protocol)
        else:
            key = (dest_ip, src_ip, dest_port, src_port, protocol)

        now = time.time()
        pkt_len = len(pkt)

        with self.lock:
            if key not in self.flows:
                self.flows[key] = FlowStats(
                    src_ip=key[0],
                    dest_ip=key[1],
                    src_port=key[2],
                    dest_port=key[3],
                    protocol=protocol,
                    start_time=now,
                    last_seen=now,
                )

            flow = self.flows[key]
            flow.last_seen = now
            flow.packet_count += 1
            flow.byte_count += pkt_len
            flow.packet_timestamps.append(now)
            flow.packet_sizes.append(pkt_len)

            if is_outbound:
                flow.packets_sent += 1
                flow.bytes_sent += pkt_len
            else:
                flow.packets_recv += 1
                flow.bytes_recv += pkt_len

            # TCP flag tracking
            if tcp_flags:
                for char in tcp_flags:
                    flow.tcp_flags.add(char)
                if "R" in tcp_flags:
                    flow.failed_connections += 1

            # DNS query extraction
            if DNS in pkt and pkt[DNS].qr == 0:
                dns_layer = pkt[DNS]
                if dns_layer.qd:
                    qname = dns_layer.qd.qname.decode("utf-8", errors="ignore").rstrip(".")
                    flow.dns_queries.append(qname)

    def flush_expired(self) -> list[dict]:
        """Flush flows that exceeded idle or active timeout."""
        now = time.time()
        flushed = []
        expired_keys = []

        with self.lock:
            for key, flow in self.flows.items():
                idle_dur = now - flow.last_seen
                active_dur = now - flow.start_time

                if idle_dur >= self.idle_timeout or active_dur >= self.active_timeout:
                    flushed.append(self._compile_flow(flow))
                    expired_keys.append(key)

            for key in expired_keys:
                del self.flows[key]

            self.total_flows_completed += len(flushed)

        return flushed

    def flush_immediate(self, dest_ip: str) -> list[dict]:
        """Immediately flush all flows matching a destination IP (IOC match)."""
        flushed = []
        matching_keys = []

        with self.lock:
            for key, flow in self.flows.items():
                if flow.dest_ip == dest_ip:
                    flushed.append(self._compile_flow(flow))
                    matching_keys.append(key)

            for key in matching_keys:
                del self.flows[key]

            self.total_flows_completed += len(flushed)

        if flushed:
            logger.info("Immediate flush: %d flows for IOC IP %s", len(flushed), dest_ip)

        return flushed

    def flush_all(self) -> list[dict]:
        """Flush all active flows (used during shutdown)."""
        with self.lock:
            flushed = [self._compile_flow(flow) for flow in self.flows.values()]
            self.total_flows_completed += len(flushed)
            self.flows.clear()
        return flushed

    def _compile_flow(self, flow: FlowStats) -> dict:
        """Compile aggregated flow metrics into a telemetry-ready dict."""
        duration = flow.last_seen - flow.start_time
        if duration <= 0:
            duration = 0.001

        # DNS entropy
        dns_query = flow.dns_queries[0] if flow.dns_queries else None
        dns_entropy = self._shannon_entropy(dns_query) if dns_query else 0.0

        # Beacon interval analysis (variance of inter-packet times)
        beacon_interval = 0.0
        if len(flow.packet_timestamps) >= 3:
            intervals = [
                flow.packet_timestamps[i + 1] - flow.packet_timestamps[i]
                for i in range(len(flow.packet_timestamps) - 1)
            ]
            mean_interval = sum(intervals) / len(intervals)
            if len(intervals) >= 2:
                variance = sum((x - mean_interval) ** 2 for x in intervals) / (len(intervals) - 1)
                beacon_interval = variance if not math.isnan(variance) else 0.0

        # Average packet size
        avg_packet_size = sum(flow.packet_sizes) / len(flow.packet_sizes) if flow.packet_sizes else 0.0

        tcp_flags_str = ",".join(sorted(flow.tcp_flags)) if flow.tcp_flags else None

        return {
            "source_ip": flow.src_ip,
            "source_port": flow.src_port,
            "dest_ip": flow.dest_ip,
            "dest_port": flow.dest_port,
            "protocol": flow.protocol,
            "packet_count": flow.packet_count,
            "byte_count": flow.byte_count,
            "packets_sent": flow.packets_sent,
            "packets_recv": flow.packets_recv,
            "bytes_sent": flow.bytes_sent,
            "bytes_recv": flow.bytes_recv,
            "flow_duration": round(duration, 4),
            "avg_packet_size": round(avg_packet_size, 2),
            "tcp_flags": tcp_flags_str,
            "dns_query": dns_query,
            "dns_entropy": round(dns_entropy, 4),
            "beacon_interval": round(beacon_interval, 4),
            "failed_connections": flow.failed_connections,
            "start_time": datetime.fromtimestamp(flow.start_time, tz=timezone.utc).isoformat(),
            "end_time": datetime.fromtimestamp(flow.last_seen, tz=timezone.utc).isoformat(),
            "packet_sizes": flow.packet_sizes,
            "packet_timestamps": flow.packet_timestamps,
        }

    @staticmethod
    def _shannon_entropy(value: str) -> float:
        """Compute Shannon entropy for a domain string (DGA detection)."""
        if not value:
            return 0.0
        counts = Counter(value)
        length = len(value)
        return -sum((c / length) * math.log2(c / length) for c in counts.values())
