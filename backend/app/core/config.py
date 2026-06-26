"""
KOVIRX Platform — Centralised Configuration.

All values are loaded from environment variables or .env file.
Secrets MUST be overridden in production.
"""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide settings injected from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ── Application ────────────────────────────────────────────────
    app_name: str = "KOVIRX"
    app_version: str = "1.0.0"
    debug: bool = False
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    allowed_origins: str = Field(default="*")

    # ── Database (PostgreSQL) ──────────────────────────────────────
    database_url: str = Field(
        default="postgresql+asyncpg://kovirx:kovirx@localhost:5432/kovirx"
    )
    db_echo: bool = False  # SQLAlchemy SQL echo for debugging

    # ── Redis ──────────────────────────────────────────────────────
    redis_url: str = Field(default="redis://localhost:6379/0")

    # ── JWT Authentication ─────────────────────────────────────────
    jwt_secret_key: str = Field(default="CHANGE-ME-IN-PRODUCTION-USE-LONG-RANDOM-STRING")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # ── Rate Limiting ──────────────────────────────────────────────
    rate_limit_requests: int = 100   # per window
    rate_limit_window_seconds: int = 60

    # ── ML Detection Thresholds ────────────────────────────────────
    ml_confidence_critical: float = 0.90
    ml_confidence_high: float = 0.75
    ml_confidence_medium: float = 0.50

    # ── Legacy heuristic thresholds (kept for backwards compat) ───
    alert_dns_entropy_threshold: float = 4.0
    alert_connection_threshold: int = 120

    # ── Celery ─────────────────────────────────────────────────────
    celery_broker_url: str = Field(default="redis://localhost:6379/1")
    celery_result_backend: str = Field(default="redis://localhost:6379/2")

    # ── SMTP (mock in dev) ─────────────────────────────────────────
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "noreply@kovirx.local"

    # ── First Super-Admin seed ─────────────────────────────────────
    first_superadmin_email: str = "admin@kovirx.com"
    first_superadmin_password: str = "KovirX@2024!"

    @field_validator("database_url", mode="before")
    @classmethod
    def assemble_db_url(cls, v: str) -> str:
        if isinstance(v, str) and v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v


settings = Settings()
