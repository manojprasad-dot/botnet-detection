import logging
import math
import threading
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from scapy.layers.inet import IP, TCP, UDP
from scapy.layers.dns import DNS, DNSQR

logger = logging.getLogger("kovirx.agent.capture.flow_engine")


@dataclass
class FlowStats:
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


class FlowEngine:
    """
    Tracks and aggregates raw packet events into directional network flows.
    Computes statistical network properties to build model-ready features.
    """

    def __init__(self, active_timeout: float = 60.0, idle_timeout: float = 15.0):
        self.active_timeout = active_timeout
        self.idle_timeout = idle_timeout
        self.flows: dict[tuple, FlowStats] = {}
        self.lock = threading.Lock()

    def process_packet(self, pkt: IP, local_ips: set[str]) -> None:
        """Process a sniffed packet and update flow tracking statistics."""
        if not IP in pkt:
            return

        ip_layer = pkt[IP]
        src_ip = ip_layer.src
        dest_ip = ip_layer.dst
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

        # Flow Key is directional but grouped: normalized by (Client, Server) IP and ports
        # We define flow direction relative to local node
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

            if is_outbound:
                flow.packets_sent += 1
                flow.bytes_sent += pkt_len
            else:
                flow.packets_recv += 1
                flow.bytes_recv += pkt_len

            if tcp_flags:
                for char in tcp_flags:
                    flow.tcp_flags.add(char)
                if "R" in tcp_flags or "S" in tcp_flags and "A" not in tcp_flags and is_outbound:
                    # Possible failed or reset attempt
                    if "R" in tcp_flags:
                        flow.failed_connections += 1

            # Extract DNS Query Name
            if DNS in pkt and pkt[DNS].qr == 0:  # DNS query request
                dns_layer = pkt[DNS]
                if dns_layer.qd:
                    qname = dns_layer.qd.qname.decode("utf-8", errors="ignore").rstrip(".")
                    flow.dns_queries.append(qname)

    def flush_expired(self) -> list[dict]:
        """Flushes flows that exceeded idle or active timeout thresholds."""
        now = time.time()
        flushed_flows = []
        expired_keys = []

        with self.lock:
            for key, flow in self.flows.items():
                idle_dur = now - flow.last_seen
                active_dur = now - flow.start_time

                if idle_dur >= self.idle_timeout or active_dur >= self.active_timeout:
                    flushed_flows.append(self._compile_flow(flow))
                    expired_keys.append(key)

            for key in expired_keys:
                del self.flows[key]

        return flushed_flows

    def _compile_flow(self, flow: FlowStats) -> dict:
        """Translates aggregated flow metrics into a backend-ready JSON telemetry format."""
        duration = flow.last_seen - flow.start_time
        if duration <= 0:
            duration = 0.001

        # DNS Entropy calculations
        dns_query = flow.dns_queries[0] if flow.dns_queries else None
        dns_entropy = self._shannon_entropy(dns_query) if dns_query else 0.0

        # Beacon timing analysis
        beacon_interval = 0.0
        if len(flow.packet_timestamps) >= 3:
            intervals = []
            for i in range(len(flow.packet_timestamps) - 1):
                intervals.append(flow.packet_timestamps[i+1] - flow.packet_timestamps[i])
            # standard deviation of timing intervals
            beacon_interval = float(math.nan if len(intervals) < 2 else sum((x - sum(intervals)/len(intervals))**2 for x in intervals)/(len(intervals)-1))
            if math.isnan(beacon_interval):
                beacon_interval = 0.0

        tcp_flags_str = ",".join(flow.tcp_flags) if flow.tcp_flags else None

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
            "tcp_flags": tcp_flags_str,
            "dns_query": dns_query,
            "dns_entropy": round(dns_entropy, 4),
            "beacon_interval": round(beacon_interval, 4),
            "failed_connections": flow.failed_connections,
            "start_time": datetime.fromtimestamp(flow.start_time, tz=timezone.utc).isoformat(),
            "end_time": datetime.fromtimestamp(flow.last_seen, tz=timezone.utc).isoformat(),
        }

    @staticmethod
    def _shannon_entropy(value: str) -> float:
        """Compute the Shannon entropy score for a query domain string."""
        if not value:
            return 0.0
        counts = Counter(value)
        length = len(value)
        return -sum((c / length) * math.log2(c / length) for c in counts.values())
