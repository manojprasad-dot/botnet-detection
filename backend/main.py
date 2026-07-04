"""
KOVIRX — Main Application Entry Point.

Configures the FastAPI application, middleware, routing, WebSocket live stream,
and startup/shutdown lifecycle tasks (lifespan).
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from backend.api.v1.router import api_v1_router
from backend.core.config import settings
from backend.core.security import decode_token, hash_password
from database.session import async_session_factory
from ml.models.isolation_forest import MODEL_PATH as IF_PATH
from ml.models.xgboost_model import MODEL_PATH as XGB_PATH
from ml.train_stub import train_models
from database.models.user import User, UserRole
from backend.utils.rate_limit import RateLimitMiddleware
from backend.websocket.manager import ws_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("kovirx.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles startup and shutdown events for the KOVIRX platform."""
    logger.info("Initializing KOVIRX Backend...")

    # 1. Train ML model stubs on first run if they don't exist
    if not os.path.exists(XGB_PATH) or not os.path.exists(IF_PATH):
        logger.info("ML model stubs not found. Training stubs with synthetic data...")
        try:
            train_models()
            # Force reload models in the detection engine
            from ml.engine import detection_engine
            detection_engine.xgboost._load_model()
            detection_engine.iforest._load_model()
        except Exception as e:
            logger.error("Failed to train ML model stubs on startup: %s", e)

    # 2. Seed first super-admin user if table is empty
    try:
        async with async_session_factory() as session:
            # Check if any user exists
            result = await session.execute(select(User).limit(1))
            if not result.scalar():
                logger.info("No users found in database. Seeding initial super-admin...")
                admin = User(
                    email=settings.first_superadmin_email,
                    username="admin",
                    hashed_password=hash_password(settings.first_superadmin_password),
                    role=UserRole.super_admin,
                    is_active=True,
                )
                session.add(admin)
                await session.commit()
                logger.info("Initial super-admin seeded successfully.")
            else:
                logger.info("Database users exist. Skipping super-admin seeding.")
    except Exception as e:
        logger.warning("Could not check/seed super-admin user on startup (db may not be ready): %s", e)

    yield

    logger.info("Shutting down KOVIRX Backend...")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="KOVIRX — AI-Powered Cross-Platform Botnet Detection & Threat Intelligence Platform",
    lifespan=lifespan,
)

# ── Middleware ──────────────────────────────────────────────────────

@app.middleware("http")
async def add_security_headers(request, call_next):
    # Skip WebSocket upgrade requests — they are incompatible with HTTP middleware
    if request.url.path.startswith("/ws/"):
        return await call_next(request)

    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    if not request.url.path.startswith(("/docs", "/redoc", "/openapi.json")):
        response.headers["Content-Security-Policy"] = "default-src 'self';"
    return response


# CORS Middleware
allowed_origins = (
    ["*"] if settings.allowed_origins == "*" else settings.allowed_origins.split(",")
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate Limiting Middleware
app.add_middleware(RateLimitMiddleware)


# ── Routes ──────────────────────────────────────────────────────────

# Health check
@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    """Health check endpoint to verify API server is online."""
    return {"status": "ok", "app": settings.app_name, "version": settings.app_version}


# WebSocket Live Stream
@app.websocket("/ws/live")
async def websocket_live(websocket: WebSocket, token: str | None = Query(None)):
    """
    WebSocket endpoint for real-time security alerts and telemetry feeds.
    Requires authentication via token query parameter.
    """
    if not token:
        logger.warning("WebSocket connection rejected: Missing authentication token.")
        await websocket.close(code=1008)  # Policy Violation
        return

    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            logger.warning("WebSocket connection rejected: Token is not an access token.")
            await websocket.close(code=1008)
            return
    except Exception as e:
        logger.warning("WebSocket connection rejected: Invalid token: %s", e)
        await websocket.close(code=1008)
        return

    await ws_manager.connect(websocket)
    try:
        while True:
            # We don't expect messages from client, but must read to detect disconnect
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error("WebSocket error: %s", e)
        ws_manager.disconnect(websocket)


# WebSocket Agent Endpoint — bidirectional communication with agents
@app.websocket("/ws/agent")
async def websocket_agent(websocket: WebSocket, token: str | None = Query(None)):
    """
    WebSocket endpoint for endpoint agent connections.
    Receives agent status and pushes commands (block_ip, sync_ioc, etc.).
    """
    from backend.api.agent_ws.handler import agent_ws_manager

    if not token:
        await websocket.close(code=1008)
        return

    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            await websocket.close(code=1008)
            return
    except Exception:
        await websocket.close(code=1008)
        return

    # Extract device_id from query or use user_id
    device_id = websocket.query_params.get("device_id", payload.get("sub", "unknown"))
    await agent_ws_manager.connect(websocket, device_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Agent can send status updates; log them
            logger.debug("Agent %s message: %s", device_id, data[:200])
    except WebSocketDisconnect:
        agent_ws_manager.disconnect(device_id)
    except Exception as e:
        logger.error("Agent WebSocket error: %s", e)
        agent_ws_manager.disconnect(device_id)


# Register API v1 routes
app.include_router(api_v1_router)
