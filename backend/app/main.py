from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .schemas import DeviceRegistration, RegisteredDevice, TelemetryBatch, TelemetryIngestResponse
from .services import ingest_telemetry, list_alerts, list_devices, register_device
from .store import store

app = FastAPI(
    title="Botnet Traffic Detection Platform API",
    version="0.1.0",
    description=(
        "Central control-plane API for device registration, telemetry ingestion, "
        "and early-stage alert generation."
    ),
)

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


@app.post("/api/v1/devices/register", response_model=RegisteredDevice)
def register(device: DeviceRegistration) -> RegisteredDevice:
    registered = RegisteredDevice(device_id=str(uuid4()), **device.model_dump())
    return register_device(registered)


@app.get("/api/v1/devices", response_model=list[RegisteredDevice])
def get_devices() -> list[RegisteredDevice]:
    return list_devices()


@app.post("/api/v1/telemetry/ingest", response_model=TelemetryIngestResponse)
def ingest(batch: TelemetryBatch) -> TelemetryIngestResponse:
    if batch.device_id not in store.devices:
        raise HTTPException(status_code=404, detail="Unknown device_id")

    alerts = ingest_telemetry(batch)
    return TelemetryIngestResponse(
        ingested_events=len(batch.events),
        generated_alerts=alerts,
    )


@app.get("/api/v1/alerts")
def get_alerts() -> list[dict]:
    return [alert.model_dump(mode="json") for alert in list_alerts()]
