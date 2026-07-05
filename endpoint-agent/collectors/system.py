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
        - Active connection count and network interface details
        - CPU, RAM, and Disk utilization
        - Operating system and logged-in user information
        - Running processes profiling
    """

    def collect(self) -> list[dict]:
        """Collect current system metrics."""
        events: list[dict] = []

        try:
            net_io = psutil.net_io_counters()
            connections = self._safe_connection_count()
            cpu_percent = psutil.cpu_percent(interval=0.1)
            ram = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            process_count = len(psutil.pids())
            hostname = socket.gethostname()

            # OS version & Logged-in users
            os_version = f"{platform.system()} {platform.release()} ({platform.version()})"
            try:
                users = [u.name for u in psutil.users()]
            except Exception:
                users = []

            # Network Interfaces
            interfaces = []
            try:
                for name, addrs in psutil.net_if_addrs().items():
                    ip_addr = next((a.address for a in addrs if a.family == socket.AF_INET), None)
                    mac_addr = next((a.address for a in addrs if a.family == psutil.AF_LINK), None)
                    if ip_addr or mac_addr:
                        interfaces.append({
                            "name": name,
                            "ip": ip_addr,
                            "mac": mac_addr,
                            "is_up": psutil.net_if_stats().get(name).isup if name in psutil.net_if_stats() else True
                        })
            except Exception as e:
                logger.debug("Failed to collect interfaces: %s", e)

            # Running Processes (Top 10 by CPU / Memory consumption for efficiency)
            processes = []
            try:
                for proc in sorted(psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']), 
                                   key=lambda p: (p.info.get('cpu_percent') or 0.0) + (p.info.get('memory_percent') or 0.0), 
                                   reverse=True)[:10]:
                    processes.append({
                        "pid": proc.info['pid'],
                        "name": proc.info['name'],
                        "cpu": proc.info['cpu_percent'],
                        "memory": proc.info['memory_percent']
                    })
            except Exception as e:
                logger.debug("Failed to collect running processes: %s", e)

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
                    "interfaces": interfaces,
                },
            })

            events.append({
                "event_type": "system_profile",
                "source": "system",
                "payload": {
                    "platform": platform.platform(),
                    "os_version": os_version,
                    "cpu_percent": cpu_percent,
                    "ram_percent": ram.percent,
                    "disk_percent": disk.percent,
                    "process_count": process_count,
                    "logged_in_users": users,
                    "processes": processes,
                },
            })
        except Exception as e:
            logger.error("System metrics collection failed: %s", e)

        return events

    def _safe_connection_count(self) -> int:
        """Get active connection count with error handling."""
        try:
            return len(psutil.net_connections(kind="inet"))
        except (psutil.AccessDenied, PermissionError):
            return 0
