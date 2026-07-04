"""
KOVIRX — API v1 aggregated router (domain-split architecture).

Each domain directory (auth/, devices/, telemetry/, etc.) contains its
own routes.py, service.py, and schemas.py for self-contained modularity.

Legacy routes in backend/api/v1/*.py are preserved for backwards
compatibility; new domain routes are added here as they're built.
"""

from fastapi import APIRouter

# ── Existing routes (kept for backward compat) ────────────────────
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

# ── New domain routers ────────────────────────────────────────────
from backend.api.heartbeat.routes import router as heartbeat_router
from backend.api.risk_engine.routes import router as risk_engine_router
from backend.api.behavior.routes import router as behavior_router
from backend.api.agent_ws.routes import router as agent_ws_router

api_v1_router = APIRouter(prefix="/api/v1")

# Existing routes
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

# New domain routes
api_v1_router.include_router(heartbeat_router)
api_v1_router.include_router(risk_engine_router)
api_v1_router.include_router(behavior_router)
api_v1_router.include_router(agent_ws_router)
