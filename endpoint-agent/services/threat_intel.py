"""
KOVIRX Endpoint Agent — Threat Intelligence Service.

Local IOC database with sync capability from backend.
Checks destination IPs and domains against known malicious indicators.
"""

import json
import logging
import sqlite3
import threading
import time

logger = logging.getLogger("kovirx.agent.threat_intel")


class ThreatIntelService:
    """
    Local threat intelligence engine with backend sync.

    Maintains a local SQLite cache of IOCs (IPs, domains, hashes).
    Periodically syncs with the backend for updated indicators.
    """

    def __init__(self, db_path: str = "ioc_cache.db"):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_db()
        self._load_seed_iocs()

    def _init_db(self) -> None:
        """Initialize local IOC cache database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ioc_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ioc_type TEXT NOT NULL,
                    ioc_value TEXT NOT NULL UNIQUE,
                    threat_type TEXT DEFAULT 'botnet',
                    reputation_score REAL DEFAULT 0.9,
                    source TEXT DEFAULT 'seed',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_ioc_value
                ON ioc_cache (ioc_value)
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error("Failed to initialize IOC cache DB: %s", e)

    def _load_seed_iocs(self) -> None:
        """Load seed IOC indicators for bootstrapping."""
        seed_ips = {
            "185.220.101.1": ("tor_exit", 0.85),
            "45.227.254.10": ("botnet_c2", 0.95),
            "103.20.192.5": ("botnet_c2", 0.90),
            "198.51.100.1": ("scanner", 0.70),
        }
        seed_domains = {
            "c2-panel.kovirx.local": ("c2_panel", 0.98),
            "botnet-command.xyz": ("botnet_c2", 0.95),
            "malware-dns.net": ("malware_distribution", 0.92),
            "exfiltration-target.org": ("data_exfil", 0.88),
        }

        with self._lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                for ip, (threat_type, score) in seed_ips.items():
                    cursor.execute(
                        "INSERT OR IGNORE INTO ioc_cache (ioc_type, ioc_value, threat_type, reputation_score) VALUES (?, ?, ?, ?)",
                        ("ip", ip, threat_type, score),
                    )
                for domain, (threat_type, score) in seed_domains.items():
                    cursor.execute(
                        "INSERT OR IGNORE INTO ioc_cache (ioc_type, ioc_value, threat_type, reputation_score) VALUES (?, ?, ?, ?)",
                        ("domain", domain, threat_type, score),
                    )
                conn.commit()
                conn.close()
            except Exception as e:
                logger.error("Failed to load seed IOCs: %s", e)

    def check_destination(self, ip: str, domain: str | None = None) -> tuple[bool, float]:
        """
        Check destination IP and domain against IOC database.

        Returns:
            Tuple of (matched: bool, reputation_score: float)
        """
        with self._lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                # Check IP
                cursor.execute(
                    "SELECT reputation_score FROM ioc_cache WHERE ioc_value = ?",
                    (ip,),
                )
                row = cursor.fetchone()
                if row:
                    conn.close()
                    logger.warning("IOC Match: Malicious IP detected: %s (score: %.2f)", ip, row[0])
                    return True, float(row[0])

                # Check domain
                if domain:
                    cursor.execute(
                        "SELECT reputation_score FROM ioc_cache WHERE ioc_value = ?",
                        (domain,),
                    )
                    row = cursor.fetchone()
                    if row:
                        conn.close()
                        logger.warning("IOC Match: Malicious domain detected: %s (score: %.2f)", domain, row[0])
                        return True, float(row[0])

                conn.close()
                return False, 0.0
            except Exception as e:
                logger.error("IOC check error: %s", e)
                return False, 0.0

    def sync_from_backend(self, api_client) -> int:
        """
        Pull latest IOC feed from backend and update local cache.

        Args:
            api_client: PlatformApiClient instance

        Returns:
            Number of IOCs synced
        """
        try:
            feed = api_client.get_ioc_feed()
            if not feed:
                return 0

            synced = 0
            with self._lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                for ioc in feed:
                    cursor.execute(
                        """INSERT OR REPLACE INTO ioc_cache
                           (ioc_type, ioc_value, threat_type, reputation_score, source, updated_at)
                           VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
                        (
                            ioc.get("ioc_type", "ip"),
                            ioc["ioc_value"],
                            ioc.get("threat_type", "unknown"),
                            ioc.get("reputation_score", 0.8),
                            "backend_sync",
                        ),
                    )
                    synced += 1
                conn.commit()
                conn.close()

            logger.info("IOC sync complete. Synced %d indicators from backend.", synced)
            return synced
        except Exception as e:
            logger.error("IOC sync failed: %s", e)
            return 0

    def add_ioc(self, ioc_type: str, ioc_value: str, threat_type: str = "unknown", score: float = 0.8) -> bool:
        """Add a single IOC to the local cache (e.g., from WebSocket push)."""
        with self._lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute(
                    """INSERT OR REPLACE INTO ioc_cache
                       (ioc_type, ioc_value, threat_type, reputation_score, source, updated_at)
                       VALUES (?, ?, ?, ?, 'ws_push', CURRENT_TIMESTAMP)""",
                    (ioc_type, ioc_value, threat_type, score),
                )
                conn.commit()
                conn.close()
                logger.info("IOC added via push: %s=%s", ioc_type, ioc_value)
                return True
            except Exception as e:
                logger.error("Failed to add IOC: %s", e)
                return False

    @property
    def ioc_count(self) -> int:
        """Return total number of IOCs in the local cache."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM ioc_cache")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception:
            return 0
