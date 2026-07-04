"""
KOVIRX Endpoint Agent — Pattern Matching Rules.

Advanced pattern detection for port scanning, lateral movement,
and connection fan-out analysis across the flow window.
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field

logger = logging.getLogger("kovirx.agent.behavior.patterns")


@dataclass
class PatternResult:
    """Detected pattern with metadata."""
    pattern_type: str
    confidence: float
    targets: list[str] = field(default_factory=list)
    details: dict = field(default_factory=dict)


class PatternDetector:
    """
    Detects network scanning and lateral movement patterns
    across a window of flows.
    """

    def __init__(self):
        self._port_scan_tracker: dict[str, set[int]] = defaultdict(set)
        self._lateral_tracker: dict[str, set[str]] = defaultdict(set)

    def analyze_flows(self, flows: list[dict]) -> list[PatternResult]:
        """Analyze a batch of flows for scanning and movement patterns."""
        results: list[PatternResult] = []

        self._port_scan_tracker.clear()
        self._lateral_tracker.clear()

        for flow in flows:
            src_ip = flow.get("source_ip", "")
            dest_ip = flow.get("dest_ip", "")
            dest_port = flow.get("dest_port", 0)

            if dest_port:
                self._port_scan_tracker[src_ip].add(dest_port)
            if dest_ip.startswith(("10.", "192.168.", "172.16.")):
                self._lateral_tracker[src_ip].add(dest_ip)

        # Port scanning detection
        for src_ip, ports in self._port_scan_tracker.items():
            if len(ports) >= 15:
                confidence = min(0.95, len(ports) / 50.0)
                results.append(PatternResult(
                    pattern_type="port_scan",
                    confidence=confidence,
                    targets=[src_ip],
                    details={
                        "source_ip": src_ip,
                        "unique_ports": len(ports),
                        "port_sample": sorted(list(ports))[:20],
                    },
                ))

        # Lateral movement detection
        for src_ip, targets in self._lateral_tracker.items():
            if len(targets) >= 5:
                confidence = min(0.85, len(targets) / 20.0)
                results.append(PatternResult(
                    pattern_type="lateral_movement",
                    confidence=confidence,
                    targets=sorted(targets),
                    details={
                        "source_ip": src_ip,
                        "internal_targets": len(targets),
                    },
                ))

        return results
