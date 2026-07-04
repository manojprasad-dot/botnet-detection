"""
KOVIRX Endpoint Agent — Structured Logger.

Provides structured JSON logging with rotating file handler,
console output, and configurable log levels.
"""

import json
import logging
import logging.handlers
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


class JSONFormatter(logging.Formatter):
    """Formats log records as structured JSON lines for machine parsing."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)

        if hasattr(record, "extra_data"):
            log_entry["data"] = record.extra_data

        return json.dumps(log_entry, default=str)


class ConsoleFormatter(logging.Formatter):
    """Colored console output formatter for development readability."""

    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"
    BOLD = "\033[1m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, "")
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = f"{color}{self.BOLD}[{record.levelname:>8}]{self.RESET}"
        name = f"\033[90m{record.name}\033[0m"
        return f"{timestamp} {prefix} {name}: {record.getMessage()}"


def setup_logging(
    level: str = "INFO",
    log_file: str = "kovirx_agent.log",
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
    json_format: bool = True,
) -> logging.Logger:
    """
    Configure structured logging for the endpoint agent.

    Args:
        level: Log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file
        max_bytes: Maximum log file size before rotation
        backup_count: Number of rotated files to keep
        json_format: Use JSON formatter for file output

    Returns:
        Root logger for the agent
    """
    root_logger = logging.getLogger("kovirx")
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Prevent duplicate handlers on re-init
    root_logger.handlers.clear()

    # ── Console Handler ───────────────────────────────────────────
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
    console_handler.setFormatter(ConsoleFormatter())
    root_logger.addHandler(console_handler)

    # ── File Handler (Rotating) ───────────────────────────────────
    try:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            filename=str(log_path),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)  # File captures everything

        if json_format:
            file_handler.setFormatter(JSONFormatter())
        else:
            file_handler.setFormatter(logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
            ))

        root_logger.addHandler(file_handler)
    except OSError as e:
        root_logger.warning("Could not create log file handler: %s", e)

    # Silence noisy third-party loggers
    logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a named logger under the kovirx namespace."""
    return logging.getLogger(f"kovirx.{name}")
