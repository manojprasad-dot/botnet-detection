"""
KOVIRX Endpoint Agent — Behavior Analyzer.

Detects suspicious behavioral patterns from network flow data:
    - DNS Beaconing: Regular interval DNS queries to same domain
    - Periodic Callbacks: Fixed-interval outbound connections
    - Fast-Flux Domains: Rapid DNS A-record rotation
    - DGA Domains: High-entropy domain names
    - Data Exfiltration: High outbound/inbound byte ratio
    - Long-Lived Encrypted Sessions: TLS connections with low packet rate
"""

import logging
import math
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field

logger = logging.getLogger("kovirx.agent.behavior.analyzer")


@dataclass
class BehaviorSignal:
    """A detected behavioral pattern with confidence score."""
    pattern_type: str
    confidence: float
    description: str
    evidence: dict = field(default_factory=dict)


class BehaviorAnalyzer:
    """
    Analyzes network flow patterns for behavioral indicators of compromise.

    Maintains rolling windows of flow data to detect temporal patterns
    that single-flow analysis would miss.
    """

    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        # Rolling state
        self._dns_history: dict[str, list[float]] = defaultdict(list)  # domain → [timestamps]
        self._dest_history: dict[str, list[float]] = defaultdict(list)  # dest_ip → [timestamps]
        self._dns_responses: dict[str, set[str]] = defaultdict(set)     # domain → {resolved IPs}
        self._flow_history: list[dict] = []

    def analyze(self, flow: dict) -> list[BehaviorSignal]:
        """
        Analyze a flow for behavioral indicators.

        Args:
            flow: Compiled flow dict from FlowEngine

        Returns:
            List of detected behavior signals
        """
        signals: list[BehaviorSignal] = []
        now = time.time()

        # Record flow for history
        self._record_flow(flow, now)

        # Run detectors
        dns_signal = self._detect_dns_beaconing(flow, now)
        if dns_signal:
            signals.append(dns_signal)

        callback_signal = self._detect_periodic_callbacks(flow, now)
        if callback_signal:
            signals.append(callback_signal)

        dga_signal = self._detect_dga_domain(flow)
        if dga_signal:
            signals.append(dga_signal)

        exfil_signal = self._detect_data_exfiltration(flow)
        if exfil_signal:
            signals.append(exfil_signal)

        encrypted_signal = self._detect_long_encrypted_session(flow)
        if encrypted_signal:
            signals.append(encrypted_signal)

        return signals

    def get_behavior_score(self, signals: list[BehaviorSignal]) -> float:
        """Compute aggregate behavior score from detected signals."""
        if not signals:
            return 0.0
        return min(1.0, sum(s.confidence for s in signals) / len(signals))

    def _record_flow(self, flow: dict, timestamp: float) -> None:
        """Record flow data for rolling window analysis."""
        self._flow_history.append(flow)
        if len(self._flow_history) > self.window_size:
            self._flow_history = self._flow_history[-self.window_size:]

        dest_ip = flow.get("dest_ip", "")
        self._dest_history[dest_ip].append(timestamp)
        self._dest_history[dest_ip] = self._dest_history[dest_ip][-50:]

        dns_query = flow.get("dns_query")
        if dns_query:
            self._dns_history[dns_query].append(timestamp)
            self._dns_history[dns_query] = self._dns_history[dns_query][-50:]

    def _detect_dns_beaconing(self, flow: dict, now: float) -> BehaviorSignal | None:
        """Detect regular-interval DNS queries to the same domain."""
        dns_query = flow.get("dns_query")
        if not dns_query:
            return None

        timestamps = self._dns_history.get(dns_query, [])
        if len(timestamps) < 5:
            return None

        # Calculate inter-query intervals
        intervals = [timestamps[i + 1] - timestamps[i] for i in range(len(timestamps) - 1)]
        if not intervals:
            return None

        mean = sum(intervals) / len(intervals)
        if mean <= 0:
            return None

        # Standard deviation relative to mean (coefficient of variation)
        variance = sum((x - mean) ** 2 for x in intervals) / len(intervals)
        std_dev = math.sqrt(variance)
        cv = std_dev / mean  # Coefficient of variation

        # Low CV = very regular intervals = likely beaconing
        if cv < 0.3 and mean < 300:  # Regular and frequent
            confidence = max(0.6, 1.0 - cv)
            return BehaviorSignal(
                pattern_type="dns_beaconing",
                confidence=confidence,
                description=f"Regular DNS queries to {dns_query} every {mean:.0f}s (CV={cv:.2f})",
                evidence={
                    "domain": dns_query,
                    "mean_interval": round(mean, 1),
                    "coefficient_of_variation": round(cv, 3),
                    "query_count": len(timestamps),
                },
            )
        return None

    def _detect_periodic_callbacks(self, flow: dict, now: float) -> BehaviorSignal | None:
        """Detect fixed-interval outbound connections to the same IP."""
        dest_ip = flow.get("dest_ip", "")
        if not dest_ip or dest_ip.startswith(("10.", "192.168.", "127.")):
            return None

        timestamps = self._dest_history.get(dest_ip, [])
        if len(timestamps) < 5:
            return None

        intervals = [timestamps[i + 1] - timestamps[i] for i in range(len(timestamps) - 1)]
        if not intervals:
            return None

        mean = sum(intervals) / len(intervals)
        if mean <= 0 or mean > 600:
            return None

        variance = sum((x - mean) ** 2 for x in intervals) / len(intervals)
        std_dev = math.sqrt(variance)
        cv = std_dev / mean

        if cv < 0.25:
            confidence = max(0.65, 1.0 - cv)
            return BehaviorSignal(
                pattern_type="periodic_callback",
                confidence=confidence,
                description=f"Periodic connections to {dest_ip} every {mean:.0f}s",
                evidence={
                    "dest_ip": dest_ip,
                    "mean_interval": round(mean, 1),
                    "connection_count": len(timestamps),
                },
            )
        return None

    def _detect_dga_domain(self, flow: dict) -> BehaviorSignal | None:
        """Detect Domain Generation Algorithm domains via high entropy."""
        dns_query = flow.get("dns_query")
        if not dns_query:
            return None

        entropy = flow.get("dns_entropy", 0.0)

        # High entropy + long domain = likely DGA
        domain_parts = dns_query.split(".")
        sld = domain_parts[0] if domain_parts else dns_query  # Second-level domain

        if entropy >= 4.0 and len(sld) >= 12:
            # Check character distribution
            digit_ratio = sum(1 for c in sld if c.isdigit()) / len(sld)

            confidence = min(0.95, (entropy - 3.5) / 2.0)
            if digit_ratio > 0.4:
                confidence = min(1.0, confidence + 0.1)

            if confidence >= 0.5:
                return BehaviorSignal(
                    pattern_type="dga_domain",
                    confidence=confidence,
                    description=f"Suspected DGA domain: {dns_query} (entropy={entropy:.2f})",
                    evidence={
                        "domain": dns_query,
                        "entropy": entropy,
                        "length": len(sld),
                        "digit_ratio": round(digit_ratio, 2),
                    },
                )
        return None

    def _detect_data_exfiltration(self, flow: dict) -> BehaviorSignal | None:
        """Detect potential data exfiltration via high outbound/inbound ratio."""
        bytes_sent = flow.get("bytes_sent", 0)
        bytes_recv = flow.get("bytes_recv", 0)

        if bytes_sent < 10000:  # Minimum threshold
            return None

        if bytes_recv == 0:
            ratio = float("inf")
        else:
            ratio = bytes_sent / bytes_recv

        # Very high outbound ratio to external IP
        dest_ip = flow.get("dest_ip", "")
        if ratio > 10.0 and not dest_ip.startswith(("10.", "192.168.", "127.")):
            confidence = min(0.85, ratio / 50.0)
            return BehaviorSignal(
                pattern_type="data_exfiltration",
                confidence=confidence,
                description=f"High outbound ratio to {dest_ip}: {bytes_sent}B sent vs {bytes_recv}B received",
                evidence={
                    "dest_ip": dest_ip,
                    "bytes_sent": bytes_sent,
                    "bytes_recv": bytes_recv,
                    "ratio": round(ratio, 1),
                },
            )
        return None

    def _detect_long_encrypted_session(self, flow: dict) -> BehaviorSignal | None:
        """Detect long-lived encrypted sessions with low packet rate."""
        duration = flow.get("flow_duration", 0.0)
        dest_port = flow.get("dest_port", 0)
        packet_count = flow.get("packet_count", 0)

        # TLS ports with long duration and low activity
        if dest_port in (443, 8443, 993, 995) and duration > 1800:  # 30 minutes
            packet_rate = packet_count / max(1, duration)
            if packet_rate < 0.1:  # Less than 1 packet per 10 seconds
                confidence = min(0.7, duration / 7200)
                return BehaviorSignal(
                    pattern_type="long_encrypted_session",
                    confidence=confidence,
                    description=f"Long-lived encrypted session to port {dest_port}: {duration:.0f}s, {packet_rate:.3f} pkt/s",
                    evidence={
                        "dest_ip": flow.get("dest_ip"),
                        "dest_port": dest_port,
                        "duration_seconds": round(duration),
                        "packet_rate": round(packet_rate, 4),
                    },
                )
        return None
