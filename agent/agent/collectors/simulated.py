from ..models import TelemetryEvent


class SimulatedBotnetCollector:
    def collect(self) -> list[TelemetryEvent]:
        return [
            TelemetryEvent(
                event_type="dns_query",
                source="simulation",
                payload={
                    "query": "aj3k29q0zmx81qv4n2c7botnet-control.example",
                    "resolver": "8.8.8.8",
                },
            ),
            TelemetryEvent(
                event_type="network_summary",
                source="simulation",
                payload={
                    "hostname": "simulated-endpoint",
                    "bytes_sent": 4_200_000,
                    "bytes_recv": 1_300_000,
                    "packets_sent": 28_000,
                    "packets_recv": 11_000,
                    "connection_count": 240,
                },
            ),
            TelemetryEvent(
                event_type="socket_snapshot",
                source="simulation",
                payload={
                    "unique_remote_ips": 48,
                    "public_remote_ips": 41,
                    "listening_ports": 3,
                    "top_remote_ports": [
                        {"port": 443, "count": 14},
                        {"port": 8080, "count": 9},
                        {"port": 53, "count": 6},
                    ],
                },
            ),
        ]
