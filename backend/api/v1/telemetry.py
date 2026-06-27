from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user
from database.session import get_db
from database.models.user import User
from backend.schemas.telemetry import TelemetryIngestPayload, TelemetryIngestResponse
from backend.services.telemetry_service import telemetry_service

router = APIRouter(prefix="/telemetry", tags=["Telemetry Ingestion"])


@router.post("/ingest", response_model=TelemetryIngestResponse)
async def ingest_telemetry(
    payload: TelemetryIngestPayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Secure endpoint for Endpoint Agents to stream live packet flow telemetries
    with local AI predictions and calculated risk levels.
    """
    return await telemetry_service.ingest_payload(db, payload, registered_by_id=current_user.id)
