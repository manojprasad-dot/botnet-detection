"""
KOVIRX Endpoint Agent — Health Monitor.

Monitors CPU, RAM, disk, network interface status, and agent process health.
Reports anomalies and resource exhaustion conditions.
"""

import logging
import platform
import time

import psutil

logger = logging.getLogger("kovirx.agent.health")


class HealthMonitor:
    """
    System and agent health monitoring service.

    Collects resource utilization metrics, detects anomalous system states,
    and monitors capture engine performance indicators.
    """

    # Thresholds for health warnings
    CPU_WARNING_THRESHOLD = 90.0
    RAM_WARNING_THRESHOLD = 90.0
    DISK_WARNING_THRESHOLD = 95.0

    def __init__(self):
        self._start_time = time.time()
        self._last_check: dict | None = None

    def check_health(self) -> dict:
        """
        Run a comprehensive health check on the system and agent.

        Returns:
            Health status dict with metrics and warnings.
        """
        cpu = psutil.cpu_percent(interval=0.2)
        memory = psutil.virtual_memory()
        disk_path = "C:\\" if platform.system() == "Windows" else "/"
        disk = psutil.disk_usage(disk_path)

        warnings: list[str] = []

        if cpu >= self.CPU_WARNING_THRESHOLD:
            warnings.append(f"CPU utilization critical: {cpu:.1f}%")
        if memory.percent >= self.RAM_WARNING_THRESHOLD:
            warnings.append(f"RAM utilization critical: {memory.percent:.1f}%")
        if disk.percent >= self.DISK_WARNING_THRESHOLD:
            warnings.append(f"Disk utilization critical: {disk.percent:.1f}%")

        # Network interfaces
        net_if = {}
        try:
            for iface, addrs in psutil.net_if_addrs().items():
                net_if[iface] = [
                    {"family": str(addr.family), "address": addr.address}
                    for addr in addrs
                    if addr.family.name in ("AF_INET", "AF_INET6")
                ]
        except Exception:
            pass

        # Network I/O
        net_io = psutil.net_io_counters()

        # Agent process info
        process = psutil.Process()
        agent_info = {
            "pid": process.pid,
            "memory_mb": round(process.memory_info().rss / (1024 * 1024), 1),
            "threads": process.num_threads(),
            "cpu_percent": process.cpu_percent(interval=0.1),
            "uptime_seconds": int(time.time() - self._start_time),
        }

        health = {
            "status": "degraded" if warnings else "healthy",
            "timestamp": time.time(),
            "system": {
                "cpu_percent": round(cpu, 1),
                "ram_percent": round(memory.percent, 1),
                "ram_total_gb": round(memory.total / (1024**3), 1),
                "ram_available_gb": round(memory.available / (1024**3), 1),
                "disk_percent": round(disk.percent, 1),
                "disk_total_gb": round(disk.total / (1024**3), 1),
                "disk_free_gb": round(disk.free / (1024**3), 1),
            },
            "network": {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv,
                "errors_in": net_io.errin,
                "errors_out": net_io.errout,
                "drops_in": net_io.dropin,
                "drops_out": net_io.dropout,
                "interfaces": net_if,
            },
            "agent": agent_info,
            "warnings": warnings,
        }

        if warnings:
            for w in warnings:
                logger.warning("Health: %s", w)

        self._last_check = health
        return health

    @property
    def last_check(self) -> dict | None:
        """Return the most recent health check result."""
        return self._last_check
