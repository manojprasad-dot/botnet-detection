# Botnet Traffic Detection Platform

This repository is a starter implementation of a cross-platform botnet traffic detection platform. It is intentionally structured like a distributed security product instead of a desktop-only app so you can grow it from a student MVP into a stronger enterprise-style system.

## Current MVP Scope

- Cross-platform Python endpoint agent skeleton
- FastAPI cloud backend for device registration, telemetry ingestion, and alerts
- Shared telemetry model aligned with endpoint-to-cloud workflows
- Containerized local backend runtime
- Architecture docs for future Android, Rust, Kafka, and Kubernetes evolution

## Repository Layout

```text
.
├── agent
│   ├── agent
│   │   ├── collectors
│   │   ├── client.py
│   │   ├── config.py
│   │   ├── main.py
│   │   └── models.py
│   └── requirements.txt
├── backend
│   ├── app
│   │   ├── config.py
│   │   ├── main.py
│   │   ├── schemas.py
│   │   ├── services.py
│   │   └── store.py
│   └── requirements.txt
├── frontend
│   ├── src
│   │   ├── assets
│   │   │   └── logo.jpg
│   │   ├── components
│   │   │   └── KovirXDashboard.jsx
│   │   ├── App.jsx
│   │   ├── index.css
│   │   └── main.jsx
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── docs
│   └── architecture.md
├── .env.example
└── docker-compose.yml
```

## Architecture Direction

The MVP follows this flow:

1. The endpoint agent gathers device metadata and lightweight telemetry.
2. The agent sends telemetry to a central API over HTTPS-ready client logic.
3. The backend performs simple detection and creates alerts.
4. A future dashboard, stream processor, and ML services can consume the same contracts.

The design is intentionally compatible with a later migration path:

- Python agent -> Rust or Go agent
- In-memory backend store -> PostgreSQL and Kafka
- Heuristic detection -> XGBoost, Isolation Forest, sequence models
- CLI/runtime ops -> Docker Compose, then Kubernetes
- Desktop-only telemetry -> Windows ETW, Linux eBPF, macOS NetworkExtension, Android VPN telemetry

## Quick Start

### 1. Backend

```powershell
cd "D:\botnet detection\backend"
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Agent

Open a second shell:

```powershell
cd "D:\botnet detection\agent"
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m agent.main --server http://127.0.0.1:8000 --once
```

### 3. Frontend (KovirX Dashboard)

Open a third shell:

```powershell
cd "D:\botnet detection\frontend"
npm install
npm run dev
```

The Vite dev server starts at `http://localhost:5173` and proxies `/api/*` requests to the backend on `:8000`.

### 4. API Endpoints

- `GET /health`
- `POST /api/v1/devices/register`
- `GET /api/v1/devices`
- `POST /api/v1/telemetry/ingest`
- `GET /api/v1/alerts`

Interactive docs are available at `http://127.0.0.1:8000/docs`.

## Docker Compose

```powershell
cd "D:\botnet detection"
docker compose up --build
```

This starts the FastAPI backend locally. The agent is left as a separate process so you can run it from different host environments.

## Recommended Next Steps

1. Replace the in-memory backend store with PostgreSQL.
2. Add JWT or mTLS-based device authentication.
3. Split detection into ingestion, feature extraction, and alert services.
4. Add OS-specific collectors for Windows, Linux, and macOS.
5. Add a React dashboard and alert timeline.
6. Add Android VPN telemetry as a separate mobile client.

## Notes

This scaffold is intentionally realistic but lightweight. It gives you clean architecture boundaries without pretending the full enterprise feature set is already implemented.
