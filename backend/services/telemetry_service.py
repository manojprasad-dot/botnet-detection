import logging
from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from backend.schemas.telemetry import TelemetryIngestPayload, TelemetryIngestResponse
from database.models.traffic import NetworkFlow
from database.models.ml import MLPrediction, RiskLevel
from database.models.alert import Alert, AlertSeverity, AlertStatus
from database.models.log import SystemLog, LogLevel, AuditLog
from database.repositories.traffic import traffic_repository
from database.repositories.ml import ml_prediction_repository
from database.repositories.alert import alert_repository
from database.repositories.device import device_repository
from database.repositories.log import system_log_repository, audit_log_repository
from backend.websocket.manager import ws_manager

logger = logging.getLogger("kovirx.telemetry")


class TelemetryService:
    """
    Ingests and processes flow telemetries from Endpoint Agent.
    Saves flow metrics, predictions, risk scores, generates alerts,
    and updates frontend dashboard clients using Websockets.
    """

    async def ingest_payload(
        self,
        db: AsyncSession,
        payload: TelemetryIngestPayload,
        registered_by_id: UUID | None = None
    ) -> TelemetryIngestResponse:
        device_id = payload.device_id
        
        # 1. Verify/Register Device is active, update last_seen_at
        device = await device_repository.get(db, device_id)
        if not device:
            # Auto-register device if missing
            device_in = {
                "id": device_id,
                "hostname": f"agent-{str(device_id)[:8]}",
                "operating_system": "unknown",
                "last_seen_at": datetime.now(timezone.utc),
                "registered_by": registered_by_id
            }
            device = await device_repository.create(db, obj_in=device_in)
            logger.info("Auto-registered device during telemetry ingestion: %s", device_id)
        else:
            await device_repository.update_last_seen(db, device_id)

        ingested_flows = 0
        generated_alerts = 0
        highest_risk = 0.0

        for event in payload.events:
            flow_data = event.flow
            pred_data = event.prediction
            risk_data = event.risk

            # 2. Insert NetworkFlow
            flow_in = {
                "device_id": device_id,
                "source_ip": flow_data.source_ip,
                "source_port": flow_data.source_port,
                "dest_ip": flow_data.dest_ip,
                "dest_port": flow_data.dest_port,
                "protocol": flow_data.protocol,
                "packet_count": flow_data.packet_count,
                "byte_count": flow_data.byte_count,
                "flow_duration": flow_data.flow_duration,
                "tcp_flags": flow_data.tcp_flags,
                "dns_query": flow_data.dns_query,
                "dns_entropy": flow_data.dns_entropy,
                "beacon_interval": flow_data.beacon_interval,
                "start_time": flow_data.start_time,
                "end_time": flow_data.end_time,
            }
            flow_rec = await traffic_repository.create(db, obj_in=flow_in)
            await db.flush()
            ingested_flows += 1

            # 3. Insert ML Prediction
            # Map risk level enum
            risk_level_mapping = {
                "low": RiskLevel.low,
                "medium": RiskLevel.medium,
                "high": RiskLevel.high,
                "critical": RiskLevel.critical,
            }
            # We map backend schemas
            pred_in = {
                "device_id": device_id,
                "flow_id": flow_rec.id,
                "model_name": "local_hybrid_detector",
                "threat_type": pred_data.threat_type,
                "confidence_score": pred_data.xgb_score,
                "risk_level": risk_level_mapping.get(risk_data.severity.value, RiskLevel.safe),
                "features_used": pred_data.features_used,
            }
            pred_rec = await ml_prediction_repository.create(db, obj_in=pred_in)
            await db.flush()

            # Track highest risk score
            highest_risk = max(highest_risk, float(risk_data.risk_score))

            # 4. Generate Alert if Risk Score is High or Critical
            if risk_data.risk_score >= 50:
                alert_severity_mapping = {
                    "low": AlertSeverity.low,
                    "medium": AlertSeverity.medium,
                    "high": AlertSeverity.high,
                    "critical": AlertSeverity.critical,
                }
                
                alert_in = {
                    "device_id": device_id,
                    "prediction_id": pred_rec.id,
                    "severity": alert_severity_mapping.get(risk_data.severity.value, AlertSeverity.medium),
                    "title": f"Botnet {pred_data.threat_type.upper()} Detected",
                    "description": (
                        f"Live packet capture flow to {flow_data.dest_ip} identified as "
                        f"{pred_data.threat_type.upper()} activity by endpoint agent. "
                        f"ML Score: {pred_data.xgb_score:.2f}. Local risk engine rating: {risk_data.risk_score}/100."
                    ),
                    "status": AlertStatus.new,
                    "evidence": {
                        "dest_ip": flow_data.dest_ip,
                        "dest_port": flow_data.dest_port,
                        "dns_query": flow_data.dns_query,
                        "prediction": pred_data.model_dump(),
                        "risk": risk_data.model_dump(),
                        "recommendation": risk_data.recommendation
                    }
                }
                alert_rec = await alert_repository.create(db, obj_in=alert_in)
                await db.flush()
                generated_alerts += 1

                # Log alert event
                sys_log_in = {
                    "level": LogLevel.warning,
                    "module": "kovirx.telemetry",
                    "message": f"Threat detected on device {device_id}. Risk score: {risk_data.risk_score}",
                    "details": {"alert_id": str(alert_rec.id), "risk_score": risk_data.risk_score}
                }
                await system_log_repository.create(db, obj_in=sys_log_in)

                # Broadcast new alert via WebSocket
                await ws_manager.broadcast({
                    "channel": "alerts",
                    "event": "new",
                    "data": {
                        "id": str(alert_rec.id),
                        "device_id": str(device_id),
                        "severity": alert_rec.severity.value,
                        "title": alert_rec.title,
                        "description": alert_rec.description,
                        "status": alert_rec.status.value,
                        "evidence": alert_rec.evidence,
                        "created_at": alert_rec.created_at.isoformat()
                    }
                })

        # 5. Update Device Risk Score
        if highest_risk > 0:
            await device_repository.update_risk_score(db, device_id, highest_risk)

        # 6. Broadcast general traffic flow updates via WebSocket
        await ws_manager.broadcast({
            "channel": "traffic",
            "event": "ingested",
            "data": {
                "device_id": str(device_id),
                "flow_count": ingested_flows
            }
        })

        # 7. Write audit logs
        audit_in = {
            "action": "telemetry_ingested",
            "resource": "telemetry",
            "resource_id": str(device_id),
            "details": {
                "ingested_flows": ingested_flows,
                "generated_alerts": generated_alerts,
                "highest_risk": highest_risk
            }
        }
        await audit_log_repository.create(db, obj_in=audit_in)
        await db.commit()

        logger.info(
            "Telemetry ingested successfully: %d flows, %d alerts for device %s",
            ingested_flows, generated_alerts, device_id
        )

        return TelemetryIngestResponse(
            ingested_flows=ingested_flows,
            generated_alerts=generated_alerts
        )


telemetry_service = TelemetryService()
