"""
KOVIRX — API v1 aggregated router.

Includes all module routers under the /api/v1 prefix.
"""

from fastapi import APIRouter

from backend.api.v1.alerts import router as alerts_router
from backend.api.v1.auth import router as auth_router
from backend.api.v1.dashboard import router as dashboard_router
from backend.api.v1.devices import router as devices_router
from backend.api.v1.features import router as features_router
from backend.api.v1.logs import router as logs_router
from backend.api.v1.ml import router as ml_router
from backend.api.v1.reports import router as reports_router
from backend.api.v1.threats import router as threats_router
from backend.api.v1.traffic import router as traffic_router
from backend.api.v1.telemetry import router as telemetry_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(auth_router)
api_v1_router.include_router(devices_router)
api_v1_router.include_router(traffic_router)
api_v1_router.include_router(telemetry_router)
api_v1_router.include_router(features_router)
api_v1_router.include_router(ml_router)
api_v1_router.include_router(threats_router)
api_v1_router.include_router(alerts_router)
api_v1_router.include_router(dashboard_router)
api_v1_router.include_router(reports_router)
api_v1_router.include_router(logs_router)
