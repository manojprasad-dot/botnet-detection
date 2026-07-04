"""
KOVIRX Endpoint Agent — Session Tracker.

Tracks long-lived network connections and identifies persistent
encrypted channels that may indicate C2 communication.
"""

import logging
import time
from dataclasses import dataclass, field

logger = logging.getLogger("kovirx.agent.behavior.session_tracker")


@dataclass
class TrackedSession:
    """A tracked long-lived network session."""
    flow_key: str
    dest_ip: str
    dest_port: int
    first_seen: float
    last_seen: float
    total_packets: int = 0
    total_bytes: int = 0
    is_encrypted: bool = False

    @property
    def duration(self) -> float:
        return self.last_seen - self.first_seen

    @property
    def avg_packet_rate(self) -> float:
        dur = self.duration
        return self.total_packets / dur if dur > 0 else 0.0


class SessionTracker:
    """
    Monitors long-lived sessions for suspicious persistence patterns.

    Flags sessions that:
        - Exceed 30 minutes duration
        - Use encrypted ports (443, 8443, etc.)
        - Have very low packet rates (keep-alive only)
    """

    ENCRYPTED_PORTS = {443, 8443, 993, 995, 465, 587}
    DURATION_THRESHOLD = 1800  # 30 minutes
    LOW_RATE_THRESHOLD = 0.1   # packets per second

    def __init__(self):
        self._sessions: dict[str, TrackedSession] = {}

    def update(self, flow: dict) -> None:
        """Update session tracking with a new flow."""
        dest_ip = flow.get("dest_ip", "")
        dest_port = flow.get("dest_port", 0)
        key = f"{dest_ip}:{dest_port}"
        now = time.time()

        if key not in self._sessions:
            self._sessions[key] = TrackedSession(
                flow_key=key,
                dest_ip=dest_ip,
                dest_port=dest_port,
                first_seen=now,
                last_seen=now,
                is_encrypted=dest_port in self.ENCRYPTED_PORTS,
            )

        session = self._sessions[key]
        session.last_seen = now
        session.total_packets += flow.get("packet_count", 0)
        session.total_bytes += flow.get("byte_count", 0)

    def get_suspicious_sessions(self) -> list[TrackedSession]:
        """Return sessions that match suspicious patterns."""
        suspicious = []
        for session in self._sessions.values():
            if (
                session.duration >= self.DURATION_THRESHOLD
                and session.is_encrypted
                and session.avg_packet_rate < self.LOW_RATE_THRESHOLD
            ):
                suspicious.append(session)
        return suspicious

    def cleanup_old(self, max_age: float = 7200.0) -> int:
        """Remove tracked sessions older than max_age seconds."""
        now = time.time()
        expired = [k for k, s in self._sessions.items() if now - s.last_seen > max_age]
        for k in expired:
            del self._sessions[k]
        return len(expired)
