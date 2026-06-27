# ── Stage 1: Build Dependencies ────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# Install compilation tools needed for C extensions (e.g. greenlet, xgboost)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ── Stage 2: Final Runtime ─────────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

# Install runtime libraries and curl for health check
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed libraries from builder stage
COPY --from=builder /root/.local /root/.local
COPY backend/requirements.txt .

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Copy source code modules
COPY backend ./backend
COPY database ./database
COPY ml ./ml

# Set up non-root user for secure containment
RUN useradd -u 10001 appuser && \
    chown -R appuser:appuser /app /root

USER appuser

EXPOSE 8000

# Health check probe
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Execute migrations and start server
CMD ["sh", "-c", "alembic -c database/alembic.ini upgrade head && uvicorn backend.main:app --host 0.0.0.0 --port 8000"]
