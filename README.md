# KOVIRX — AI-Powered Cross-Platform Botnet Detection & Threat Intelligence Platform

KOVIRX is an enterprise-grade, production-ready distributed cybersecurity platform designed for Security Operations Centers (SOCs) to monitor, analyze, and quarantine botnet activities in real time. 

---

## Technical Architecture & Core Stack

KOVIRX is built using a decoupled **Clean Architecture** layout:

* **Backend Engine (FastAPI)**: Python 3.12+ core with high-performance async route handling and lifespan lifecycle management.
* **Database & Migration (PostgreSQL + SQLAlchemy + Alembic)**: Fully async database interactions (`asyncpg` adapter) with Alembic migration version control.
* **Security & Access Control (JWT + RBAC)**: Strict role-based authorization enforcing permissions across four user tiers (`super_admin`, `soc_manager`, `security_analyst`, `viewer`) using secure cryptographically-signed JWT access and refresh tokens.
* **Machine Learning Pipeline (XGBoost + Isolation Forest + SHAP)**:
  * **XGBoost Classifier**: Binary classification to predict botnet vs benign flows.
  * **Isolation Forest**: Unsupervised anomaly detection on flow feature distributions.
  * **SHAP (SHapley Additive exPlanations)**: Tree explainers to provide feature-level contribution metrics explaining why a model flagged a threat.
* **Asynchronous Task Queue (Celery + Redis)**: Out-of-process job management (e.g., security report compilation).
* **Realtime Threat Intelligence (WebSockets)**: Authenticated live stream to broadcast new alerts, network flows, and device status updates.

---

## Repository Layout

```text
.
├── agent/                       # Python endpoint agent
├── frontend/                    # Vite + React SOC dashboard interface
├── backend/                     # Enterprise FastAPI core
│   ├── app/
│   │   ├── api/                 # Dependency injection & v1 routers
│   │   ├── core/                # Settings, Security helpers, and Celery setup
│   │   ├── database/            # SQLAlchemy session factory & base models
│   │   ├── models/              # Database schema models (User, Device, Alert, etc.)
│   │   ├── schemas/             # Pydantic request/response validation schemas
│   │   ├── services/            # Core business logic layer
│   │   ├── ml/                  # ML Engine, SHAP explainer, and training stub
│   │   ├── websocket/           # WS connection manager
│   │   └── utils/               # Rate limit middleware and helpers
│   ├── alembic/                 # Migration scripts
│   ├── tests/                   # Pytest automation suite
│   ├── docker/                  # Multi-stage production Dockerfile
│   ├── alembic.ini              # Alembic config
│   └── requirements.txt         # Package requirements
├── docker-compose.yml           # Multi-container orchestration (App, DB, Cache, Worker)
└── .env.example                 # Environment configuration template
```

---

## Quick Start (Development Environment)

### 1. Database & Caching Setup
The backend requires a running PostgreSQL and Redis instance. You can start them using docker-compose:
```bash
docker compose up -d postgres redis
```

### 2. Backend Setup
Initialize the virtual environment, install requirements, and run the FastAPI server:
```powershell
cd backend
py -3.13 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
> **Note**: On first startup, the lifespan hooks will automatically check for the ML model stubs. If missing, it will generate synthetic training data, train XGBoost and Isolation Forest stubs, and seed the initial super-admin credentials (`admin@kovirx.com` / `KovirX@2024!`) in the database.

### 3. Running Automated Tests
The backend features a fully async test suite using `pytest` and `aiosqlite` (file-based SQLite database for isolated local execution):
```powershell
.venv\Scripts\python -m pytest
```

### 4. Running the Frontend
```powershell
cd frontend
npm install
npm run dev
```

---

## Production Deployment (Docker Compose)

To spin up the entire KOVIRX platform in production-mode:
```bash
docker compose up --build -d
```
This orchestrates:
1. **kovirx_postgres**: PostgreSQL 16 database storing SOC entities.
2. **kovirx_redis**: Redis cache, rate limiter state, and Celery task broker.
3. **kovirx_backend**: Fast API instance executing inside a non-root, multi-stage secure container.
4. **kovirx_celery**: Celery worker executing background report jobs.

---

## API Documentation & Endpoint Reference

Interactive Swagger UI documentation is available at `http://127.0.0.1:8000/docs` once the server is running.

### Key API Paths:
* `/api/v1/auth/*` — Register, login, change password, forgot password, token rotation
* `/api/v1/devices/*` — Endpoint agent registration, CRUD, and health tagging
* `/api/v1/traffic/ingest` — Endpoint agent flow ingestion pipeline
* `/api/v1/ml/*` — Run inference, fetch SHAP explanations, view model accuracy/status
* `/api/v1/alerts/*` — Query alerts, update investigation status, assign to analysts
* `/api/v1/dashboard/summary` — SOC aggregation stats
* `/api/v1/reports/*` — Asynchronous PDF and CSV report compilation
* `/api/v1/logs/*` — Security audit trail logging
* `/ws/live?token=JWT_ACCESS_TOKEN` — Real-time WebSockets alert stream
