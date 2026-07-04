"""
KOVIRX Endpoint Agent — Centralised Configuration.

All settings are loaded from environment variables, .env file, or command-line arguments.
Provides safe defaults for development, must be overridden in production deployments.
"""

import os
import uuid
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# Persistent UUID storage — ensures stable device identity across restarts
_AGENT_DIR = Path(__file__).resolve().parent
_UUID_FILE = _AGENT_DIR / ".agent_uuid"


def _load_or_generate_uuid() -> str:
    """Load persistent agent UUID from disk, or generate and save a new one."""
    if _UUID_FILE.exists():
        stored = _UUID_FILE.read_text(encoding="utf-8").strip()
        if stored:
            return stored
    new_uuid = str(uuid.uuid4())
    try:
        _UUID_FILE.write_text(new_uuid, encoding="utf-8")
    except OSError:
        pass
    return new_uuid


class AgentSettings(BaseSettings):
    """Endpoint Agent settings injected from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="KOVIRX_AGENT_",
        extra="ignore",
        case_sensitive=False,
    )

    # ── Identity ──────────────────────────────────────────────────
    agent_uuid: str = Field(default_factory=_load_or_generate_uuid)
    agent_version: str = "1.0.0"
    agent_name: str = "kovirx-endpoint-agent"

    # ── Server ────────────────────────────────────────────────────
    server_url: str = Field(default="http://127.0.0.1:8000")
    server_ws_url: str = Field(default="ws://127.0.0.1:8000/ws/agent")
    api_timeout: int = Field(default=15, description="HTTP request timeout in seconds")

    # ── Authentication ────────────────────────────────────────────
    auth_email: str = "admin@kovirx.com"
    auth_password: str = "KovirX@2024!"

    # ── Capture ───────────────────────────────────────────────────
    capture_interface: str | None = Field(default=None, description="Network interface to sniff (None = all)")
    capture_filter: str = "ip"
    capture_timeout: float = Field(default=0.5, description="Scapy sniff timeout per iteration")
    capture_buffer_size: int = Field(default=256, description="Max packets to buffer before processing")

    # ── Flow Engine ───────────────────────────────────────────────
    flow_active_timeout: float = Field(default=60.0, description="Max flow duration before forced flush")
    flow_idle_timeout: float = Field(default=5.0, description="Idle time before flow is considered complete")
    flow_flush_interval: float = Field(default=2.0, description="Seconds between flow flush checks")

    # ── Heartbeat ─────────────────────────────────────────────────
    heartbeat_interval: int = Field(default=30, description="Heartbeat interval in seconds")

    # ── Telemetry Upload ──────────────────────────────────────────
    batch_size: int = Field(default=50, description="Max events per telemetry batch")
    flush_interval: float = Field(default=10.0, description="Seconds between queue flush attempts")
    compression_enabled: bool = Field(default=True, description="gzip compress payloads")
    compression_threshold: int = Field(default=1024, description="Min payload size to compress (bytes)")

    # ── Retry ─────────────────────────────────────────────────────
    retry_max_attempts: int = Field(default=5, description="Max retry attempts for failed requests")
    retry_backoff_base: float = Field(default=2.0, description="Exponential backoff base in seconds")
    retry_backoff_max: float = Field(default=60.0, description="Max backoff duration in seconds")

    # ── Offline Cache ─────────────────────────────────────────────
    offline_cache_path: str = Field(default="agent_queue.db")
    offline_cache_max_size: int = Field(default=10000, description="Max queued telemetry items")

    # ── ML ────────────────────────────────────────────────────────
    model_dir: str = Field(default="", description="Path to ML model artifacts (empty = auto-detect)")

    # ── Logging ───────────────────────────────────────────────────
    log_level: str = Field(default="INFO")
    log_file: str = Field(default="kovirx_agent.log")
    log_max_bytes: int = Field(default=10 * 1024 * 1024, description="Max log file size (10MB)")
    log_backup_count: int = Field(default=5, description="Number of rotated log files to keep")

    # ── Health Monitor ────────────────────────────────────────────
    health_check_interval: int = Field(default=60, description="Health check interval in seconds")

    # ── Updater ───────────────────────────────────────────────────
    update_check_interval: int = Field(default=3600, description="Update check interval in seconds")
    auto_update_enabled: bool = Field(default=False, description="Enable automatic self-updates")

    @property
    def resolved_model_dir(self) -> Path:
        """Resolve ML model directory path."""
        if self.model_dir:
            return Path(self.model_dir)
        # Default: look for ai-engine/saved_models relative to project root
        project_root = _AGENT_DIR.parent
        candidates = [
            project_root / "ai-engine" / "saved_models",
            project_root / "ml" / "saved_models",  # Legacy fallback
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return candidates[0]  # Return ai-engine path even if missing


settings = AgentSettings()
