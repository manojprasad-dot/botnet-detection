"""
KOVIRX Endpoint Agent — Heartbeat Service.

Sends periodic heartbeat payloads to the backend containing system metrics,
agent status, and capture health indicators. Runs every 30 seconds.
"""

import logging
import platform
import time

import psutil

logger = logging.getLogger("kovirx.agent.heartbeat")


class HeartbeatService:
    """
    Collects system metrics and sends heartbeat to the backend.

    Heartbeat payload:
        device_id, cpu_percent, ram_percent, disk_percent,
        uptime_seconds, agent_version, capture_status,
        flows_processed, packets_captured, threats_detected, queue_depth
    """

    def __init__(self, api_client, agent_state):
        """
        Args:
            api_client: PlatformApiClient instance for HTTP communication
            agent_state: Shared AgentState object with runtime counters
        """
        self.client = api_client
        self.state = agent_state
        self._boot_time = psutil.boot_time()

    def send_heartbeat(self) -> None:
        """Collect system metrics and POST heartbeat to backend."""
        try:
            payload = self._collect_metrics()
            success = self.client.send_heartbeat(payload)
            if success:
                self.state.last_heartbeat = time.time()
                logger.debug("Heartbeat sent. CPU=%.1f%% RAM=%.1f%%",
                             payload["cpu_percent"], payload["ram_percent"])
            else:
                logger.warning("Heartbeat delivery failed. Backend may be unreachable.")
        except Exception as e:
            logger.error("Heartbeat collection error: %s", e)

    def _collect_metrics(self) -> dict:
        """Collect current system and agent metrics."""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/") if platform.system() != "Windows" else psutil.disk_usage("C:\\")
        uptime = int(time.time() - self._boot_time)

        return {
            "device_id": self.state.device_id,
            "cpu_percent": round(cpu_percent, 1),
            "ram_percent": round(memory.percent, 1),
            "disk_percent": round(disk.percent, 1),
            "uptime_seconds": uptime,
            "agent_version": self.state.agent_version,
            "capture_status": self.state.capture_status,
            "flows_processed": self.state.flows_processed,
            "packets_captured": self.state.packets_captured,
            "threats_detected": self.state.threats_detected,
            "queue_depth": self.state.queue_depth,
        }
