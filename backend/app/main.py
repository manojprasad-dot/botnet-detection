from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from .config import settings
from .schemas import (
    DeviceRegistration,
    PlatformSummary,
    RegisteredDevice,
    TelemetryBatch,
    TelemetryIngestResponse,
    TelemetryRecord,
)
from .services import (
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
    summary = get_platform_summary()
    alerts = list_alerts(limit=10)
    devices = list_devices()[:10]

    alert_items = "".join(
        (
            "<li>"
            f"<strong>{alert.severity.upper()}</strong> - {alert.title} "
            f"({alert.device_id})"
            "</li>"
        )
        for alert in alerts
    ) or "<li>No alerts yet.</li>"

    device_items = "".join(
        (
            "<li>"
            f"{device.hostname} ({device.operating_system}) - last seen {device.last_seen_at.isoformat()}"
            "</li>"
        )
        for device in devices
    ) or "<li>No devices registered yet.</li>"

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>Botnet Detection Dashboard</title>
        <style>
            :root {{
                color-scheme: light;
                --bg: #f3f6ef;
                --panel: #ffffff;
                --ink: #15231a;
                --muted: #5e6b61;
                --accent: #1f7a4c;
                --accent-soft: #dff3e8;
                --danger: #9f1f1f;
                --border: #d9e4d9;
            }}
            body {{
                margin: 0;
                font-family: "Segoe UI", sans-serif;
                color: var(--ink);
                background:
                    radial-gradient(circle at top right, #d8efe0 0, transparent 32%),
                    linear-gradient(180deg, #eef5ea 0%, var(--bg) 100%);
            }}
            .wrap {{
                max-width: 1100px;
                margin: 0 auto;
                padding: 32px 20px 48px;
            }}
            h1 {{
                margin-bottom: 8px;
            }}
            .sub {{
                color: var(--muted);
                margin-bottom: 24px;
            }}
            .grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
                gap: 16px;
                margin-bottom: 24px;
            }}
            .card {{
                background: var(--panel);
                border: 1px solid var(--border);
                border-radius: 18px;
                padding: 18px;
                box-shadow: 0 10px 24px rgba(21, 35, 26, 0.06);
            }}
            .metric {{
                font-size: 30px;
                font-weight: 700;
                margin-top: 8px;
            }}
            .pill {{
                display: inline-block;
                background: var(--accent-soft);
                color: var(--accent);
                border-radius: 999px;
                padding: 6px 10px;
                font-size: 12px;
                font-weight: 600;
            }}
            .sections {{
                display: grid;
                grid-template-columns: 1.2fr 1fr;
                gap: 16px;
            }}
            ul {{
                padding-left: 18px;
                margin: 12px 0 0;
            }}
            li {{
                margin-bottom: 10px;
                color: var(--ink);
            }}
            .severity {{
                color: var(--danger);
                font-weight: 600;
            }}
            .meta {{
                color: var(--muted);
                font-size: 14px;
            }}
            @media (max-width: 800px) {{
                .sections {{
                    grid-template-columns: 1fr;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="wrap">
            <span class="pill">Persistent MVP Dashboard</span>
            <h1>Botnet Traffic Detection Platform</h1>
            <p class="sub">Live snapshot of registered devices, telemetry ingestion, and alert activity.</p>
            <div class="grid">
                <div class="card"><div class="meta">Registered devices</div><div class="metric">{summary.total_devices}</div></div>
                <div class="card"><div class="meta">Active in 24h</div><div class="metric">{summary.active_devices_24h}</div></div>
                <div class="card"><div class="meta">Telemetry events</div><div class="metric">{summary.total_events}</div></div>
                <div class="card"><div class="meta">Alerts</div><div class="metric">{summary.total_alerts}</div></div>
            </div>
            <div class="sections">
                <div class="card">
                    <h2>Latest Alerts</h2>
                    <ul>{alert_items}</ul>
                </div>
                <div class="card">
                    <h2>Recent Devices</h2>
                    <ul>{device_items}</ul>
                </div>
            </div>
        </div>
    </body>
    </html>
    """


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
