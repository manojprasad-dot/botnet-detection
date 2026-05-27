import ipaddress
import platform
import socket
from collections import Counter

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

        socket_event = self._build_socket_snapshot()
        if socket_event is not None:
            events.append(socket_event)

        return events

    def _safe_connection_count(self) -> int:
        try:
            return len(psutil.net_connections(kind="inet"))
        except (psutil.AccessDenied, PermissionError):
            return 0

    def _build_socket_snapshot(self) -> TelemetryEvent | None:
        try:
            connections = psutil.net_connections(kind="inet")
        except (psutil.AccessDenied, PermissionError):
            return None

        remote_ips: list[str] = []
        public_remote_ips: list[str] = []
        remote_ports: Counter[int] = Counter()
        listening_ports = 0

        for connection in connections:
            if connection.status == psutil.CONN_LISTEN:
                listening_ports += 1

            if not connection.raddr:
                continue

            remote_ip = connection.raddr.ip
            remote_port = connection.raddr.port
            remote_ips.append(remote_ip)
            remote_ports[remote_port] += 1
            if self._is_public_ip(remote_ip):
                public_remote_ips.append(remote_ip)

        top_remote_ports = [
            {"port": port, "count": count}
            for port, count in remote_ports.most_common(5)
        ]

        return TelemetryEvent(
            event_type="socket_snapshot",
            source="system",
            payload={
                "unique_remote_ips": len(set(remote_ips)),
                "public_remote_ips": len(set(public_remote_ips)),
                "listening_ports": listening_ports,
                "top_remote_ports": top_remote_ports,
            },
        )

    def _is_public_ip(self, ip_address: str) -> bool:
        try:
            parsed = ipaddress.ip_address(ip_address)
        except ValueError:
            return False

        return not any(
            (
                parsed.is_private,
                parsed.is_loopback,
                parsed.is_link_local,
                parsed.is_multicast,
                parsed.is_reserved,
                parsed.is_unspecified,
            )
        )
