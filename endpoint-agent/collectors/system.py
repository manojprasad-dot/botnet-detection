"""
KOVIRX Endpoint Agent — System Telemetry Collector.

Collects system metrics: network I/O, connection counts,
CPU/memory utilization, and process count.
"""

import logging
import platform
import socket

import psutil

logger = logging.getLogger("kovirx.agent.collectors.system")


class SystemTelemetryCollector:
    """
    Collects system-level telemetry for the endpoint agent.

    Gathered metrics:
        - Network I/O counters (bytes/packets sent/received)
        - Active connection count
        - CPU and memory utilization
        - Process count
        - Host identification
    """

    def collect(self) -> list[dict]:
        """Collect current system metrics."""
        events: list[dict] = []

        net_io = psutil.net_io_counters()
        connections = self._safe_connection_count()
        cpu_percent = psutil.cpu_percent(interval=0.1)
        process_count = len(psutil.pids())
        hostname = socket.gethostname()

        events.append({
            "event_type": "network_summary",
            "source": "system",
            "payload": {
                "hostname": hostname,
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv,
                "connection_count": connections,
            },
        })

        events.append({
            "event_type": "system_profile",
            "source": "system",
            "payload": {
                "platform": platform.platform(),
                "cpu_percent": cpu_percent,
                "process_count": process_count,
            },
        })

        return events

    def _safe_connection_count(self) -> int:
        """Get active connection count with error handling."""
        try:
            return len(psutil.net_connections(kind="inet"))
        except (psutil.AccessDenied, PermissionError):
            return 0
