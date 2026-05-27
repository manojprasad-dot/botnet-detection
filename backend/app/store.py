import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Lock

from .config import settings
from .schemas import Alert, PlatformSummary, RegisteredDevice, TelemetryBatch, TelemetryRecord


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SQLiteStore:
    def __init__(self, database_path: str) -> None:
        self.database_path = Path(__file__).resolve().parents[1] / database_path
        self._lock = Lock()

    def init_db(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS devices (
                    device_id TEXT PRIMARY KEY,
                    device_fingerprint TEXT UNIQUE NOT NULL,
                    hostname TEXT NOT NULL,
                    ip_address TEXT,
                    operating_system TEXT NOT NULL,
                    os_version TEXT,
                    agent_version TEXT NOT NULL,
                    architecture TEXT,
                    tags_json TEXT NOT NULL,
                    registered_at TEXT NOT NULL,
                    last_seen_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS telemetry_events (
                    record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    source TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    collected_at TEXT NOT NULL,
                    generated_at TEXT NOT NULL,
                    FOREIGN KEY(device_id) REFERENCES devices(device_id)
                );

                CREATE TABLE IF NOT EXISTS alerts (
                    alert_id TEXT PRIMARY KEY,
                    device_id TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    confidence_score REAL NOT NULL,
                    created_at TEXT NOT NULL,
                    evidence_json TEXT NOT NULL,
                    FOREIGN KEY(device_id) REFERENCES devices(device_id)
                );
                """
            )

    def register_device(self, device: RegisteredDevice) -> RegisteredDevice:
        with self._lock, self._connect() as connection:
            existing = connection.execute(
                "SELECT device_id FROM devices WHERE device_fingerprint = ?",
                (device.device_fingerprint,),
            ).fetchone()

            if existing:
                connection.execute(
                    """
                    UPDATE devices
                    SET hostname = ?, ip_address = ?, operating_system = ?, os_version = ?,
                        agent_version = ?, architecture = ?, tags_json = ?, last_seen_at = ?
                    WHERE device_fingerprint = ?
                    """,
                    (
                        device.hostname,
                        device.ip_address,
                        device.operating_system,
                        device.os_version,
                        device.agent_version,
                        device.architecture,
                        json.dumps(device.tags),
                        device.last_seen_at.isoformat(),
                        device.device_fingerprint,
                    ),
                )
                row = connection.execute(
                    "SELECT * FROM devices WHERE device_fingerprint = ?",
                    (device.device_fingerprint,),
                ).fetchone()
                return self._row_to_device(row)

            connection.execute(
                """
                INSERT INTO devices (
                    device_id, device_fingerprint, hostname, ip_address, operating_system,
                    os_version, agent_version, architecture, tags_json, registered_at, last_seen_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    device.device_id,
                    device.device_fingerprint,
                    device.hostname,
                    device.ip_address,
                    device.operating_system,
                    device.os_version,
                    device.agent_version,
                    device.architecture,
                    json.dumps(device.tags),
                    device.registered_at.isoformat(),
                    device.last_seen_at.isoformat(),
                ),
            )
            row = connection.execute(
                "SELECT * FROM devices WHERE device_id = ?",
                (device.device_id,),
            ).fetchone()
            return self._row_to_device(row)

    def get_device(self, device_id: str) -> RegisteredDevice | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM devices WHERE device_id = ?",
                (device_id,),
            ).fetchone()
            if not row:
                return None
            return self._row_to_device(row)

    def list_devices(self) -> list[RegisteredDevice]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM devices ORDER BY last_seen_at DESC"
            ).fetchall()
            return [self._row_to_device(row) for row in rows]

    def ingest_telemetry(self, batch: TelemetryBatch, alerts: list[Alert]) -> None:
        with self._lock, self._connect() as connection:
            for event in batch.events:
                connection.execute(
                    """
                    INSERT INTO telemetry_events (
                        device_id, event_type, source, payload_json, collected_at, generated_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        batch.device_id,
                        event.event_type,
                        event.source,
                        json.dumps(event.payload),
                        event.collected_at.isoformat(),
                        batch.generated_at.isoformat(),
                    ),
                )

            for alert in alerts:
                connection.execute(
                    """
                    INSERT OR REPLACE INTO alerts (
                        alert_id, device_id, severity, title, description, confidence_score,
                        created_at, evidence_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        alert.alert_id,
                        alert.device_id,
                        alert.severity,
                        alert.title,
                        alert.description,
                        alert.confidence_score,
                        alert.created_at.isoformat(),
                        json.dumps(alert.evidence),
                    ),
                )

            connection.execute(
                "UPDATE devices SET last_seen_at = ? WHERE device_id = ?",
                (utc_now().isoformat(), batch.device_id),
            )

    def list_alerts(self, limit: int = 100, device_id: str | None = None) -> list[Alert]:
        with self._connect() as connection:
            if device_id:
                rows = connection.execute(
                    """
                    SELECT * FROM alerts
                    WHERE device_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (device_id, limit),
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT * FROM alerts ORDER BY created_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            return [self._row_to_alert(row) for row in rows]

    def list_telemetry(
        self, limit: int = 100, device_id: str | None = None
    ) -> list[TelemetryRecord]:
        with self._connect() as connection:
            if device_id:
                rows = connection.execute(
                    """
                    SELECT * FROM telemetry_events
                    WHERE device_id = ?
                    ORDER BY collected_at DESC
                    LIMIT ?
                    """,
                    (device_id, limit),
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT * FROM telemetry_events ORDER BY collected_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            return [self._row_to_telemetry(row) for row in rows]

    def get_summary(self) -> PlatformSummary:
        with self._connect() as connection:
            total_devices = self._count(connection, "SELECT COUNT(*) FROM devices")
            total_events = self._count(connection, "SELECT COUNT(*) FROM telemetry_events")
            total_alerts = self._count(connection, "SELECT COUNT(*) FROM alerts")
            active_cutoff = (utc_now() - timedelta(hours=24)).isoformat()
            active_devices = self._count(
                connection,
                "SELECT COUNT(*) FROM devices WHERE last_seen_at >= ?",
                (active_cutoff,),
            )

            alerts_by_severity = {
                row["severity"]: row["count"]
                for row in connection.execute(
                    """
                    SELECT severity, COUNT(*) AS count
                    FROM alerts
                    GROUP BY severity
                    """
                ).fetchall()
            }

            events_by_type = {
                row["event_type"]: row["count"]
                for row in connection.execute(
                    """
                    SELECT event_type, COUNT(*) AS count
                    FROM telemetry_events
                    GROUP BY event_type
                    """
                ).fetchall()
            }

        return PlatformSummary(
            total_devices=total_devices,
            active_devices_24h=active_devices,
            total_events=total_events,
            total_alerts=total_alerts,
            alerts_by_severity=alerts_by_severity,
            events_by_type=events_by_type,
            latest_alerts=self.list_alerts(limit=5),
        )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        return connection

    def _count(
        self, connection: sqlite3.Connection, query: str, params: tuple = ()
    ) -> int:
        row = connection.execute(query, params).fetchone()
        return int(row[0]) if row else 0

    def _row_to_device(self, row: sqlite3.Row) -> RegisteredDevice:
        return RegisteredDevice(
            device_id=row["device_id"],
            device_fingerprint=row["device_fingerprint"],
            hostname=row["hostname"],
            ip_address=row["ip_address"],
            operating_system=row["operating_system"],
            os_version=row["os_version"],
            agent_version=row["agent_version"],
            architecture=row["architecture"],
            tags=json.loads(row["tags_json"]),
            registered_at=datetime.fromisoformat(row["registered_at"]),
            last_seen_at=datetime.fromisoformat(row["last_seen_at"]),
        )

    def _row_to_alert(self, row: sqlite3.Row) -> Alert:
        return Alert(
            alert_id=row["alert_id"],
            device_id=row["device_id"],
            severity=row["severity"],
            title=row["title"],
            description=row["description"],
            confidence_score=row["confidence_score"],
            created_at=datetime.fromisoformat(row["created_at"]),
            evidence=json.loads(row["evidence_json"]),
        )

    def _row_to_telemetry(self, row: sqlite3.Row) -> TelemetryRecord:
        return TelemetryRecord(
            record_id=row["record_id"],
            device_id=row["device_id"],
            event_type=row["event_type"],
            source=row["source"],
            payload=json.loads(row["payload_json"]),
            collected_at=datetime.fromisoformat(row["collected_at"]),
            generated_at=datetime.fromisoformat(row["generated_at"]),
        )


store = SQLiteStore(settings.database_path)
