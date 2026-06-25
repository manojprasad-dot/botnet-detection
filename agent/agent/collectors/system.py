import platform
import socket

import psutil

from ..models import TelemetryEvent


class SystemTelemetryCollector:
    def collect(self) -> list[TelemetryEvent]:
        events: list[TelemetryEvent] = []

        net_io = psutil.net_io_counters()
        connections = self._safe_connection_count()
        cpu_percent = psutil.cpu_percent(interval=0.1)
        process_count = len(psutil.pids())
        hostname = socket.gethostname()

        events.append(
            TelemetryEvent(
                event_type="network_summary",
                source="system",
                payload={
                    "hostname": hostname,
                    "bytes_sent": net_io.bytes_sent,
                    "bytes_recv": net_io.bytes_recv,
                    "packets_sent": net_io.packets_sent,
                    "packets_recv": net_io.packets_recv,
                    "connection_count": connections,
                },
            )
        )

        events.append(
            TelemetryEvent(
                event_type="system_profile",
                source="system",
                payload={
                    "platform": platform.platform(),
                    "cpu_percent": cpu_percent,
                    "process_count": process_count,
                },
            )
        )

        return events

    def _safe_connection_count(self) -> int:
        try:
            return len(psutil.net_connections(kind="inet"))
        except (psutil.AccessDenied, PermissionError):
            return 0
