from pathlib import Path
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .dashboard import render_command_center
from .schemas import (
    CommandCenterSnapshot,
    DeviceRegistration,
    PlatformSummary,
    RegisteredDevice,
    TelemetryBatch,
    TelemetryIngestResponse,
    TelemetryRecord,
)
from .services import (
    get_command_center_snapshot,
    get_device,
    get_platform_summary,
    ingest_telemetry,
    list_alerts,
    list_devices,
    list_telemetry,
    register_device,
)
from .store import store


@asynccontextmanager
async def lifespan(_: FastAPI):
    store.init_db()
    yield


app = FastAPI(
    title="Botnet Traffic Detection Platform API",
    version="0.2.0",
    description=(
        "Central control-plane API for device registration, telemetry ingestion, "
        "persistent storage, and early-stage alert generation."
    ),
    lifespan=lifespan,
)
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")

allowed_origins = ["*"] if settings.allowed_origins == "*" else settings.allowed_origins.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard() -> str:
    return render_command_center()


@app.post("/api/v1/devices/register", response_model=RegisteredDevice)
def register(device: DeviceRegistration) -> RegisteredDevice:
    registered = RegisteredDevice(device_id=str(uuid4()), **device.model_dump())
    return register_device(registered)


@app.get("/api/v1/devices", response_model=list[RegisteredDevice])
def get_devices() -> list[RegisteredDevice]:
    return list_devices()


@app.get("/api/v1/devices/{device_id}", response_model=RegisteredDevice)
def get_device_by_id(device_id: str) -> RegisteredDevice:
    device = get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Unknown device_id")
    return device


@app.post("/api/v1/telemetry/ingest", response_model=TelemetryIngestResponse)
def ingest(batch: TelemetryBatch) -> TelemetryIngestResponse:
    if not get_device(batch.device_id):
        raise HTTPException(status_code=404, detail="Unknown device_id")

    alerts = ingest_telemetry(batch)
    return TelemetryIngestResponse(
        ingested_events=len(batch.events),
        generated_alerts=alerts,
    )


@app.get("/api/v1/telemetry", response_model=list[TelemetryRecord])
def get_telemetry(
    device_id: str | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
) -> list[TelemetryRecord]:
    return list_telemetry(limit=limit, device_id=device_id)


@app.get("/api/v1/alerts")
def get_alerts(
    device_id: str | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
) -> list[dict]:
    return [alert.model_dump(mode="json") for alert in list_alerts(limit=limit, device_id=device_id)]


@app.get("/api/v1/summary", response_model=PlatformSummary)
def get_summary() -> PlatformSummary:
    return get_platform_summary()


@app.get("/api/v1/command-center", response_model=CommandCenterSnapshot)
def get_command_center() -> CommandCenterSnapshot:
    return get_command_center_snapshot()
