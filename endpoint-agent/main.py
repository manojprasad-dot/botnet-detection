"""
KOVIRX Endpoint Agent — Main Entry Point.

Enterprise EDR-style lifecycle:
    Agent Starts → Generate UUID → Collect Host Info → POST /devices/register
    → Receive JWT → Start Scheduler → Heartbeat + Capture + ML + Upload

All background loops are managed by the AgentScheduler.
Graceful shutdown on SIGINT/SIGTERM.
"""

import os
import platform
import signal
import socket
import sys
import threading
import time
import uuid
import logging

# ── Add this directory to sys.path so internal imports resolve ────
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

from config import AgentSettings, settings
from services.logger import setup_logging, get_logger
from services.scheduler import AgentScheduler
from services.heartbeat import HeartbeatService
from services.queue import TelemetryQueue, Priority
from services.compression import compress_payload
from services.retry import RetryPolicy
from services.health_monitor import HealthMonitor
from services.updater import AgentUpdater
from services.firewall import FirewallManager
from services.risk_engine import RiskEngine
from services.threat_intel import ThreatIntelService
from client.api_client import PlatformApiClient
from client.websocket_client import WebSocketClient
from capture.sniffer import PacketSniffer
from capture.flow_engine import FlowEngine
from ml.detection_engine import LocalDetectionEngine
from ml.feature_extractor import extract_features
from behavior.analyzer import BehaviorAnalyzer
from behavior.patterns import PatternDetector
from behavior.session_tracker import SessionTracker

try:
    import psutil
except ImportError:
    psutil = None

logger: logging.Logger = None  # type: ignore  — set in main()


# ── Shared Agent State ───────────────────────────────────────────


class AgentState:
    """Shared mutable state visible to all services."""

    def __init__(self, cfg: AgentSettings):
        self.device_id: str = cfg.agent_uuid
        self.agent_version: str = cfg.agent_version
        self.capture_status: str = "initializing"
        self.flows_processed: int = 0
        self.packets_captured: int = 0
        self.threats_detected: int = 0
        self.queue_depth: int = 0
        self.last_heartbeat: float | None = None
        self.last_upload: float | None = None
        self.blocked_ips: list[str] = []


# ── Endpoint Agent ───────────────────────────────────────────────


class EndpointAgent:
    """
    Enterprise Endpoint Agent — main orchestrator.

    Lifecycle:
        1. Authenticate with backend
        2. Register device
        3. Load ML models
        4. Start packet capture
        5. Start all scheduled services
        6. Block until shutdown signal
    """

    def __init__(self):
        self.cfg = settings
        self.state = AgentState(self.cfg)
        self._shutdown_event = threading.Event()

        # ── Core services ─────────────────────────────────────────
        self.api_client = PlatformApiClient(
            server_url=self.cfg.server_url,
            timeout=self.cfg.api_timeout,
        )
        self.retry_policy = RetryPolicy(
            max_attempts=self.cfg.retry_max_attempts,
            backoff_base=self.cfg.retry_backoff_base,
            backoff_max=self.cfg.retry_backoff_max,
        )
        self.queue = TelemetryQueue(
            db_path=self.cfg.offline_cache_path,
            max_size=self.cfg.offline_cache_max_size,
        )
        self.scheduler = AgentScheduler()
        self.heartbeat_service = HeartbeatService(self.api_client, self.state)
        self.health_monitor = HealthMonitor()
        self.updater = AgentUpdater(self.api_client, self.cfg.agent_version)
        self.firewall = FirewallManager()
        self.risk_engine = RiskEngine()
        self.threat_intel = ThreatIntelService()

        # ── Capture & Analysis ────────────────────────────────────
        self.sniffer = PacketSniffer(
            interface=self.cfg.capture_interface,
            filter_str=self.cfg.capture_filter,
            timeout=self.cfg.capture_timeout,
        )
        self.flow_engine = FlowEngine(
            active_timeout=self.cfg.flow_active_timeout,
            idle_timeout=self.cfg.flow_idle_timeout,
        )

        # ── ML & Behavior ────────────────────────────────────────
        self.ml_engine = LocalDetectionEngine(model_dir=self.cfg.resolved_model_dir)
        self.behavior_analyzer = BehaviorAnalyzer()
        self.pattern_detector = PatternDetector()
        self.session_tracker = SessionTracker()

        # ── WebSocket ─────────────────────────────────────────────
        self.ws_client = WebSocketClient(
            ws_url=self.cfg.server_ws_url,
            on_command=self._handle_ws_command,
        )

        # ── Local IP cache ────────────────────────────────────────
        self._local_ips: set[str] = set()

    # ── Lifecycle ─────────────────────────────────────────────────

    def start(self) -> None:
        """Full agent startup sequence."""
        logger.info("╔══════════════════════════════════════════════════╗")
        logger.info("║         KOVIRX ENDPOINT AGENT v%s            ║", self.cfg.agent_version)
        logger.info("║     Enterprise Botnet Detection Platform         ║")
        logger.info("╚══════════════════════════════════════════════════╝")
        logger.info("Agent UUID: %s", self.state.device_id)

        # Step 1: Collect local IPs for flow directionality
        self._collect_local_ips()

        # Step 2: Authenticate
        logger.info("Authenticating with backend at %s...", self.cfg.server_url)
        authenticated = self._authenticate()
        if not authenticated:
            logger.warning("Authentication failed. Running in offline mode.")
        else:
            # Step 3: Register device
            self._register_device()

        # Step 4: Load ML models
        self._load_ml_models()

        # Step 5: Start packet capture
        self._start_capture()

        # Step 6: Register and start all scheduled tasks
        self._register_scheduled_tasks()
        self.scheduler.start_all()

        # Step 7: Start WebSocket client (if authenticated)
        if self.api_client.token:
            self.ws_client.token = self.api_client.token
            self.ws_client.start()

        self.state.capture_status = "active"
        logger.info("Agent fully operational. Monitoring network traffic...")

    def stop(self) -> None:
        """Graceful shutdown sequence."""
        logger.info("Initiating graceful shutdown...")
        self.state.capture_status = "stopped"

        # Stop capture first
        self.sniffer.stop()

        # Flush remaining flows
        remaining_flows = self.flow_engine.flush_all()
        if remaining_flows:
            logger.info("Flushing %d remaining flows...", len(remaining_flows))
            self._process_flows(remaining_flows)

        # Upload remaining queue
        self._flush_queue()

        # Stop services
        self.ws_client.stop()
        self.scheduler.stop_all()

        logger.info("Agent shutdown complete. Packets: %d, Flows: %d, Threats: %d",
                     self.state.packets_captured,
                     self.state.flows_processed,
                     self.state.threats_detected)

    def run(self) -> None:
        """Start agent and block until shutdown signal."""
        self.start()
        try:
            while not self._shutdown_event.is_set():
                self._shutdown_event.wait(timeout=1.0)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received.")
        finally:
            self.stop()

    def request_shutdown(self) -> None:
        """Signal the agent to shut down."""
        self._shutdown_event.set()

    # ── Step Implementations ──────────────────────────────────────

    def _authenticate(self) -> bool:
        """Authenticate with backend and obtain JWT token."""
        try:
            return self.retry_policy.execute(
                lambda: self.api_client.login(
                    self.cfg.auth_email,
                    self.cfg.auth_password,
                )
            )
        except Exception as e:
            logger.error("Authentication failed after retries: %s", e)
            return False

    def _register_device(self) -> None:
        """Register this endpoint device with the backend."""
        hostname = socket.gethostname()
        ip_address = self._get_primary_ip()

        payload = {
            "hostname": hostname,
            "ip_address": ip_address,
            "mac_address": self._get_mac_address(),
            "operating_system": platform.system(),
            "os_version": platform.version(),
            "agent_version": self.cfg.agent_version,
            "architecture": platform.machine(),
            "cpu_model": platform.processor() or "Unknown",
            "ram_total_gb": round(psutil.virtual_memory().total / (1024**3), 1) if psutil else 0,
            "tags": [platform.system().lower(), "endpoint"],
        }

        try:
            result = self.api_client.register_device(payload)
            if result:
                device_id = result.get("id") or result.get("device_id")
                if device_id:
                    self.state.device_id = str(device_id)
                logger.info("Device registered. ID: %s", self.state.device_id)
        except Exception as e:
            logger.warning("Device registration failed (continuing with local UUID): %s", e)

    def _load_ml_models(self) -> None:
        """Load trained ML model artifacts."""
        try:
            loaded = self.ml_engine.load_models()
            if loaded:
                logger.info("ML Detection Engine loaded successfully.")
            else:
                logger.warning("ML models unavailable. Using heuristic fallback.")
        except Exception as e:
            logger.error("ML model loading error: %s", e)

    def _start_capture(self) -> None:
        """Start the packet sniffer in a background thread."""
        logger.info("Starting packet capture...")
        self.sniffer.start(callback=self._on_packet)

    def _collect_local_ips(self) -> None:
        """Cache local IP addresses for flow directionality."""
        self._local_ips = {"127.0.0.1", "::1"}
        if psutil:
            for iface, addrs in psutil.net_if_addrs().items():
                for addr in addrs:
                    if addr.family.name in ("AF_INET", "AF_INET6"):
                        self._local_ips.add(addr.address)
        logger.debug("Local IPs cached: %d addresses", len(self._local_ips))

    # ── Scheduled Task Callbacks ──────────────────────────────────

    def _register_scheduled_tasks(self) -> None:
        """Register all background tasks with the scheduler."""
        self.scheduler.register("heartbeat",
                                self.heartbeat_service.send_heartbeat,
                                interval=self.cfg.heartbeat_interval)

        self.scheduler.register("flow_flush",
                                self._tick_flow_flush,
                                interval=self.cfg.flow_flush_interval)

        self.scheduler.register("queue_flush",
                                self._flush_queue,
                                interval=self.cfg.flush_interval,
                                initial_delay=5.0)

        self.scheduler.register("health_check",
                                self._tick_health_check,
                                interval=self.cfg.health_check_interval,
                                initial_delay=10.0)

        self.scheduler.register("ioc_sync",
                                self._tick_ioc_sync,
                                interval=3600,
                                initial_delay=30.0)

        if self.cfg.auto_update_enabled:
            self.scheduler.register("version_check",
                                    self._tick_version_check,
                                    interval=self.cfg.update_check_interval,
                                    initial_delay=60.0)

    def _tick_flow_flush(self) -> None:
        """Flush expired flows, process through ML + behavior, enqueue."""
        expired_flows = self.flow_engine.flush_expired()
        if expired_flows:
            self._process_flows(expired_flows)

    def _tick_health_check(self) -> None:
        """Run periodic health check."""
        health = self.health_monitor.check_health()
        self.state.packets_captured = self.sniffer.packets_captured
        self.state.queue_depth = self.queue.depth

    def _tick_ioc_sync(self) -> None:
        """Sync IOC feed from backend."""
        if self.api_client.token:
            self.threat_intel.sync_from_backend(self.api_client)

    def _tick_version_check(self) -> None:
        """Check for agent updates."""
        update_info = self.updater.check_for_update()
        if update_info:
            logger.info("Update available: %s", update_info.get("latest_version"))

    # ── Packet Processing Pipeline ────────────────────────────────

    def _on_packet(self, pkt) -> None:
        """Callback invoked for each captured packet."""
        self.state.packets_captured += 1
        self.flow_engine.process_packet(pkt, self._local_ips)

    def _process_flows(self, flows: list[dict]) -> None:
        """
        Full processing pipeline for completed flows:
            Flow → IOC Check → Feature Extraction → ML Prediction
            → Behavior Analysis → Risk Scoring → Enqueue for Upload
        """
        unique_ips = len({f["dest_ip"] for f in flows})
        public_ips = len({
            f["dest_ip"] for f in flows
            if not f["dest_ip"].startswith(("10.", "192.168.", "172.16.", "127.", "0."))
        })

        events = []
        for flow in flows:
            self.state.flows_processed += 1

            # 1. IOC Check
            ioc_matched, ioc_score = self.threat_intel.check_destination(
                flow["dest_ip"],
                flow.get("dns_query"),
            )

            # 2. Feature Extraction
            features = extract_features(
                flow,
                batch_size=len(flows),
                unique_ips=unique_ips,
                public_ips=public_ips,
            )

            # 3. ML Prediction
            prediction = self.ml_engine.predict(features)

            # 4. Behavior Analysis
            behavior_signals = self.behavior_analyzer.analyze(flow)
            behavior_score = self.behavior_analyzer.get_behavior_score(behavior_signals)

            # 5. Session Tracking
            self.session_tracker.update(flow)

            # 6. Risk Scoring (multi-source)
            risk = self.risk_engine.calculate_risk(
                xgb_score=prediction["xgb_score"],
                is_anomaly=prediction["is_anomaly"],
                intel_score=ioc_score,
                behavior_score=behavior_score,
                history_score=0.0,  # Agent has no history DB — server fills this
                features=features,
            )

            # 7. IOC-matching flows get immediate priority
            if ioc_matched:
                priority = Priority.CRITICAL
            elif risk["risk_score"] >= 60:
                priority = Priority.HIGH
                self.state.threats_detected += 1
            else:
                priority = Priority.NORMAL

            # 8. Auto-block if critical
            if risk["risk_score"] >= 95 and flow["dest_ip"] not in self._local_ips:
                self.firewall.block_ip(flow["dest_ip"])
                self.state.blocked_ips = self.firewall.blocked_ips

            # 9. Build telemetry event
            event = {
                "flow": flow,
                "prediction": prediction,
                "risk": risk,
                "behavior": {
                    "behavior_score": behavior_score,
                    "behavior_type": behavior_signals[0].pattern_type if behavior_signals else "normal",
                    "patterns_detected": [s.pattern_type for s in behavior_signals],
                    "details": {s.pattern_type: s.evidence for s in behavior_signals},
                },
            }

            events.append((event, priority))

            # Log threats
            if risk["risk_score"] >= 60:
                logger.warning(
                    "⚠ THREAT: %s → %s | Risk=%d%% | Type=%s | ML=%.2f | Behavior=%.2f | IOC=%s",
                    flow["source_ip"], flow["dest_ip"],
                    risk["risk_score"], prediction["threat_type"],
                    prediction["xgb_score"], behavior_score,
                    "✓" if ioc_matched else "✗",
                )

        # Enqueue batch for upload
        if events:
            payload = {
                "device_id": self.state.device_id,
                "events": [e[0] for e in events],
                "generated_at": time.time(),
            }
            # Use the highest priority in the batch
            max_priority = min(e[1] for e in events)
            self.queue.enqueue(payload, priority=max_priority)

    def _flush_queue(self) -> None:
        """Dequeue and upload telemetry batches to backend."""
        if not self.api_client.token:
            return

        items = self.queue.dequeue(batch_size=self.cfg.batch_size)
        if not items:
            return

        uploaded_ids = []
        for row_id, payload in items:
            try:
                if self.cfg.compression_enabled:
                    compressed, is_compressed = compress_payload(
                        payload,
                        threshold=self.cfg.compression_threshold,
                    )
                    result = self.api_client.send_telemetry(
                        payload,
                        compressed_data=compressed,
                        is_compressed=is_compressed,
                    )
                else:
                    result = self.api_client.send_telemetry(payload)

                if result is not None:
                    uploaded_ids.append(row_id)
                    self.state.last_upload = time.time()
            except Exception as e:
                logger.warning("Telemetry upload failed for batch %d: %s", row_id, e)
                break  # Stop on first failure — will retry next tick

        if uploaded_ids:
            self.queue.remove(uploaded_ids)
            logger.info("Uploaded %d telemetry batch(es).", len(uploaded_ids))

    # ── WebSocket Command Handler ─────────────────────────────────

    def _handle_ws_command(self, data: dict) -> None:
        """Dispatch commands received from backend WebSocket."""
        command = data.get("command", "")
        target = data.get("target", "")
        payload = data.get("payload", {})

        logger.info("Processing WS command: %s (target=%s)", command, target)

        if command == "block_ip":
            if target:
                self.firewall.block_ip(target)
                self.state.blocked_ips = self.firewall.blocked_ips

        elif command == "unblock_ip":
            if target:
                self.firewall.unblock_ip(target)
                self.state.blocked_ips = self.firewall.blocked_ips

        elif command == "sync_ioc":
            ioc_type = payload.get("ioc_type", "ip")
            ioc_value = payload.get("ioc_value", target)
            score = payload.get("reputation_score", 0.9)
            self.threat_intel.add_ioc(ioc_type, ioc_value, score=score)

        elif command == "restart_capture":
            logger.info("Restarting packet capture...")
            self.sniffer.stop()
            time.sleep(1)
            self.sniffer.start(callback=self._on_packet)

        elif command == "shutdown":
            logger.info("Shutdown command received from backend.")
            self.request_shutdown()

        else:
            logger.warning("Unknown command: %s", command)

    # ── Utility ───────────────────────────────────────────────────

    @staticmethod
    def _get_primary_ip() -> str:
        """Get the primary outbound IP address."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    @staticmethod
    def _get_mac_address() -> str:
        """Get the primary MAC address."""
        mac_int = uuid.getnode()
        return ":".join(f"{(mac_int >> (8 * i)) & 0xFF:02x}" for i in reversed(range(6)))


# ── Entry Point ──────────────────────────────────────────────────


def main():
    global logger
    root = setup_logging(
        level=settings.log_level,
        log_file=settings.log_file,
        max_bytes=settings.log_max_bytes,
        backup_count=settings.log_backup_count,
    )
    logger = get_logger("main")

    agent = EndpointAgent()

    # Register signal handlers for graceful shutdown
    def _signal_handler(signum, frame):
        logger.info("Signal %d received. Shutting down...", signum)
        agent.request_shutdown()

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    agent.run()


if __name__ == "__main__":
    main()
