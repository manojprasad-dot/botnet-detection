import pytest
from uuid import uuid4
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from backend.schemas.telemetry import (
    TelemetryIngestPayload,
    TelemetryEventItem,
    FlowTelemetryData,
    PredictionTelemetryData,
    RiskTelemetryData,
    Severity
)
from backend.services.telemetry_service import TelemetryService


@pytest.mark.asyncio
async def test_telemetry_ingestion_pipeline():
    # Setup mock telemetry batch payload
    device_id = uuid4()
    flow_start = datetime.now(timezone.utc)
    flow_end = datetime.now(timezone.utc)

    event_item = TelemetryEventItem(
        flow=FlowTelemetryData(
            source_ip="192.168.1.50",
            dest_ip="45.227.254.10",
            protocol="TCP",
            packet_count=150,
            byte_count=15400,
            flow_duration=12.5,
            start_time=flow_start,
            end_time=flow_end
        ),
        prediction=PredictionTelemetryData(
            xgb_score=0.92,
            is_anomaly=True,
            threat_type="Command & Control",
            features_used={"cpu_percent": 15.0}
        ),
        risk=RiskTelemetryData(
            risk_score=94,
            severity=Severity.critical,
            recommendation="Quarantine immediately."
        ),
        collected_at=datetime.now(timezone.utc)
    )

    payload = TelemetryIngestPayload(
        device_id=device_id,
        events=[event_item],
        generated_at=datetime.now(timezone.utc)
    )

    # Mock repositories and db dependencies
    db_mock = AsyncMock()
    
    with patch("backend.services.telemetry_service.device_repository") as dev_repo_mock, \
         patch("backend.services.telemetry_service.traffic_repository") as traffic_repo_mock, \
         patch("backend.services.telemetry_service.ml_prediction_repository") as ml_repo_mock, \
         patch("backend.services.telemetry_service.alert_repository") as alert_repo_mock, \
         patch("backend.services.telemetry_service.system_log_repository") as sys_log_mock, \
         patch("backend.services.telemetry_service.audit_log_repository") as audit_log_mock, \
         patch("backend.services.telemetry_service.ws_manager.broadcast", new_callable=AsyncMock) as ws_mock:

        # Set methods explicitly as AsyncMocks to support await expressions
        dev_repo_mock.get = AsyncMock(return_value=None)
        dev_repo_mock.create = AsyncMock(return_value=AsyncMock(id=device_id, hostname="test-agent"))
        dev_repo_mock.update_last_seen = AsyncMock()
        dev_repo_mock.update_risk_score = AsyncMock()

        traffic_repo_mock.create = AsyncMock(return_value=AsyncMock(id=uuid4()))
        ml_repo_mock.create = AsyncMock(return_value=AsyncMock(id=uuid4()))
        
        alert_rec = AsyncMock(id=uuid4(), severity=AsyncMock(value="critical"), status=AsyncMock(value="new"))
        alert_rec.created_at = datetime.now(timezone.utc)
        alert_rec.title = "Botnet C2 Detected"
        alert_rec.description = "Test alert description"
        alert_rec.evidence = {}
        alert_repo_mock.create = AsyncMock(return_value=alert_rec)

        sys_log_mock.create = AsyncMock()
        audit_log_mock.create = AsyncMock()

        service = TelemetryService()
        response = await service.ingest_payload(db_mock, payload)

        assert response.ingested_flows == 1
        assert response.generated_alerts == 1
        dev_repo_mock.update_risk_score.assert_called_once_with(db_mock, device_id, 94.0)
        ws_mock.assert_called()
