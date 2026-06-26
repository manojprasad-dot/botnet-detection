"""
KOVIRX — Traffic routes: /api/v1/traffic/*
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.traffic import FlowBatchIngestRequest, FlowListResponse, FlowResponse, TrafficIngestResponse
from app.services import alert_service, device_service, ml_service, traffic_service
from app.websocket.manager import ws_manager

router = APIRouter(prefix="/traffic", tags=["Traffic Collection"])


@router.post("/ingest", response_model=TrafficIngestResponse)
async def ingest_traffic(
    batch: FlowBatchIngestRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Ingest network flows from an endpoint agent.

    Pipeline: ingest → feature extraction → ML prediction → alerts.
    """
    # 1. Store flows
    flows = await traffic_service.ingest_flows(db, batch)

    # 2. Update device last_seen
    await device_service.update_device_last_seen(db, batch.device_id)

    # 3. Run ML predictions
    alert_count = 0
    if flows:
        flow_ids = [f.id for f in flows]
        try:
            predictions = await ml_service.run_prediction(db, flow_ids)

            # 4. Generate alerts from predictions
            for pred in predictions:
                alert = await alert_service.create_alert_from_prediction(db, pred)
                if alert:
                    alert_count += 1
                    # 5. Update device risk score
                    await device_service.update_device_risk_score(
                        db, batch.device_id, pred.confidence_score * 100
                    )
                    # 6. Broadcast via WebSocket
                    await ws_manager.broadcast({
                        "channel": "alerts",
                        "event": "new",
                        "data": alert.model_dump(mode="json"),
                    })
        except Exception:
            pass  # ML pipeline errors should not block ingestion

    # Broadcast new traffic event
    await ws_manager.broadcast({
        "channel": "traffic",
        "event": "ingested",
        "data": {"device_id": str(batch.device_id), "flow_count": len(flows)},
    })

    return TrafficIngestResponse(ingested_flows=len(flows), generated_alerts=alert_count)


@router.get("/flows", response_model=FlowListResponse)
async def list_flows(
    device_id: UUID | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List network flows with pagination and optional device filter."""
    return await traffic_service.list_flows(db, device_id=device_id, skip=skip, limit=limit)


@router.get("/flows/{flow_id}", response_model=FlowResponse)
async def get_flow(
    flow_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single flow record by ID."""
    return await traffic_service.get_flow(db, flow_id)
