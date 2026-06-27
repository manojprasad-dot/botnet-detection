import argparse
import logging
import platform
import socket
import sys
import time
import signal
from datetime import datetime, timezone
import psutil

# Scapy warning filter
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)

from .client import PlatformApiClient
from .capture.sniffer import PacketSniffer
from .capture.flow_engine import FlowEngine
from .ml.detection_engine import LocalDetectionEngine
from .services.threat_intel import LocalThreatIntel
from .services.risk_engine import RiskEngine

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("kovirx.agent")

class EndpointAgent:
    """
    Unified Endpoint Agent class running packet sniffing, flow engine,
    ML local inference, and API uploads in a thread-safe background service loop.
    """

    def __init__(self, server_url: str, interval: int = 30):
        self.server_url = server_url
        self.interval = interval
        self.client = PlatformApiClient(server_url=server_url)
        self.sniffer = PacketSniffer()
        self.flow_engine = FlowEngine(active_timeout=interval * 2.0, idle_timeout=interval / 2.0)
        self.ml_engine = LocalDetectionEngine()
        self.intel = LocalThreatIntel()
        self.risk_engine = RiskEngine()

        self.device_id = None
        self.running = False
        self.local_ips = self._get_local_ips()

    def _get_local_ips(self) -> set[str]:
        """Resolve all IPv4 addresses bound to local network interfaces."""
        ips = {"127.0.0.1", "0.0.0.0"}
        try:
            for interface, addrs in psutil.net_if_addrs().items():
                for addr in addrs:
                    if addr.family == socket.AF_INET:
                        ips.add(addr.address)
        except Exception as e:
            logger.error("Failed to map local network interface IPs: %s", e)
            try:
                ips.add(socket.gethostbyname(socket.gethostname()))
            except OSError:
                pass
        return ips

    def _normalize_os(self) -> str:
        sys_name = platform.system()
        mapping = {"Windows": "windows", "Linux": "linux", "Darwin": "macos"}
        return mapping.get(sys_name, "unknown")

    def bootstrap(self) -> bool:
        """Log in and register the device with the platform backend."""
        # Authenticate using default seed super-admin credentials for security demonstration
        login_success = self.client.login("admin@kovirx.com", "KovirX@2024!")
        if not login_success:
            logger.warning("Could not login. Telemetry will be queued locally if server is offline.")
        
        reg_payload = {
            "hostname": socket.gethostname(),
            "ip_address": list(self.local_ips - {"127.0.0.1", "0.0.0.0"})[0] if len(self.local_ips) > 2 else "127.0.0.1",
            "operating_system": self._normalize_os(),
            "os_version": platform.version(),
            "agent_version": "1.0.0",
            "architecture": platform.machine(),
            "tags": ["agent", "phase-2", platform.system().lower()]
        }

        logger.info("Registering agent endpoint on backend: %s", reg_payload["hostname"])
        reg_res = self.client.register_device(reg_payload)
        if reg_res:
            self.device_id = reg_res.get("id")
            logger.info("Endpoint registered successfully. UUID: %s", self.device_id)
            return True
        else:
            # Fallback mock UUID for offline queueing
            import uuid
            self.device_id = str(uuid.uuid4())
            logger.warning("Agent registration offline fallback. Temporary local UUID: %s", self.device_id)
            return True

    def start(self) -> None:
        """Start the background packet capture sniffer and telemetry upload loops."""
        self.running = True
        self.ml_engine.load_models()

        # Start sniffing
        self.sniffer.start(callback=lambda pkt: self.flow_engine.process_packet(pkt, self.local_ips))

        logger.info("Agent ingestion service loop started.")
        while self.running:
            try:
                # Flush and get expired flows
                flows = self.flow_engine.flush_expired()
                if flows:
                    logger.info("Analyzing %d completed network flows...", len(flows))
                    self._process_and_upload(flows)

                # Periodic queue flush check
                self.client.flush_queue()

                time.sleep(2.0)
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error("Error in agent runner loop: %s", e)
                time.sleep(5.0)

    def _process_and_upload(self, flows: list[dict]) -> None:
        """
        Executes feature mapping, local ML classifications, risk calculations,
        and posts the telemetry batch to the backend.
        """
        events = []
        for flow in flows:
            # Compile matching 22-dimensional feature schema dict
            # We map this flow metrics into the 22 features
            # Calculate standard feature inputs:
            dns_entropy = flow.get("dns_entropy", 0.0)
            beacon_score = 0.9 if flow.get("beacon_interval", 0.0) > 0.0 else 0.0
            
            features = {
                "event_count": float(len(flows)),
                "network_event_count": float(len(flows)),
                "dns_query_count": 1.0 if flow.get("dns_query") else 0.0,
                "max_dns_entropy": dns_entropy,
                "avg_dns_entropy": dns_entropy,
                "flow_duration": flow.get("flow_duration", 0.0),
                "packet_rate": flow.get("packet_count", 0.0) / max(0.1, flow.get("flow_duration", 1.0)),
                "connection_count": float(len(flows)),
                "bytes_sent": float(flow.get("bytes_sent", 0)),
                "bytes_recv": float(flow.get("bytes_recv", 0)),
                "packets_sent": float(flow.get("packets_sent", 0)),
                "packets_recv": float(flow.get("packets_recv", 0)),
                "unique_remote_ips": 1.0,
                "public_remote_ips": 1.0 if not flow.get("dest_ip", "").startswith(("10.", "192.168.", "127.")) else 0.0,
                "listening_ports": 0.0,
                "top_remote_port_count": float(flow.get("packet_count", 0)),
                "failed_connection_ratio": 1.0 if flow.get("failed_connections", 0) > 0 else 0.0,
                "tcp_flag_score": 1.0 if "R" in flow.get("tcp_flags", "") else 0.0,
                "beacon_interval_score": beacon_score,
                "outbound_frequency": 1.0,
                "cpu_percent": float(psutil.cpu_percent()),
                "process_count": float(len(psutil.pids())),
            }

            # Local machine learning
            pred = self.ml_engine.predict(features)

            # Local Threat Intel lookup
            intel_matched, intel_score = self.intel.check_destination(
                flow.get("dest_ip", ""), flow.get("dns_query")
            )

            # Consolidate Risk Score
            risk = self.risk_engine.calculate_risk(
                xgb_score=pred["xgb_score"],
                is_anomaly=pred["is_anomaly"],
                intel_score=intel_score,
                features=features,
            )

            events.append({
                "flow": flow,
                "prediction": {
                    "xgb_score": pred["xgb_score"],
                    "is_anomaly": pred["is_anomaly"],
                    "threat_type": pred["threat_type"],
                    "features_used": features
                },
                "risk": risk,
                "collected_at": datetime.now(timezone.utc).isoformat()
            })

        batch = {
            "device_id": self.device_id,
            "events": events,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }

        self.client.send_telemetry(batch)

    def stop(self) -> None:
        """Stop packet sniffer and exit loops gracefully."""
        logger.info("Gracefully stopping Endpoint Agent daemon...")
        self.running = False
        self.sniffer.stop()
        logger.info("Endpoint Agent stopped successfully.")


def main() -> None:
    parser = argparse.ArgumentParser(description="KOVIRX Enterprise Endpoint Agent")
    parser.add_argument("--server", default="http://127.0.0.1:8000", help="FastAPI Server Target URL")
    parser.add_argument("--interval", type=int, default=30, help="Aggregator timeout interval in seconds")
    args = parser.parse_args()

    agent = EndpointAgent(server_url=args.server, interval=args.interval)

    # Register OS Signal Interceptor for Graceful Shutdown
    def handle_signal(sig, frame):
        logger.info("Received termination signal %d", sig)
        agent.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    if agent.bootstrap():
        agent.start()


if __name__ == "__main__":
    main()
