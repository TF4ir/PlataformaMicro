# Multi-stage Dockerfile for the FastAPI Predictive & Adaptive Service.
# Build context MUST be the repository root so that `ml/` is available:
#   docker build -f services/ml-api/Dockerfile -t nexo-ml-api .
# Target: linux/amd64 (blitz.cloud, Fly.io, Render, local Docker Compose).

FROM python:3.11-slim AS builder

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY services/ml-api/pyproject.toml services/ml-api/README.md ./
RUN pip install --upgrade pip && \
    pip install poetry && \
    poetry config virtualenvs.in-project true && \
    poetry install --only main --no-root --no-interaction --no-ansi

# Runner stage
FROM python:3.11-slim AS runner

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PATH="/app/.venv/bin:$PATH" \
    PORT=8000

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 appuser

COPY --from=builder /app/.venv /app/.venv
COPY --chown=appuser:appuser services/ml-api/app/ /app/app/
COPY --chown=appuser:appuser services/ml-api/README.md /app/README.md
# Scientific package required by app.prediction.* (ml.src.*)
COPY --chown=appuser:appuser ml/ /app/ml/

USER appuser

EXPOSE 8000

# Healthcheck probe for container orchestrators (blitz.cloud, Fly.io, Render).
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f "http://localhost:${PORT}/api/v1/health" || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
