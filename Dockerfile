FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml /app/pyproject.toml
COPY alembic.ini /app/alembic.ini
COPY alembic /app/alembic
COPY src /app/src

RUN pip install --no-cache-dir uv && \
    uv sync --frozen

FROM python:3.12-slim AS runner

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

COPY --from=builder /app/src /app/src
COPY --from=builder /app/alembic /app/alembic
COPY --from=builder /app/alembic.ini /app/alembic.ini
COPY --from=builder /app/pyproject.toml /app/pyproject.toml

ENV PYTHONPATH="/app/src:${PYTHONPATH}"
ENV PORT=3027
ENV NODE_ENV=production

EXPOSE 3027

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3027/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3027"]