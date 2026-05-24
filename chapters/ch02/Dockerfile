FROM python:3.14-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY . .

RUN uv sync --frozen --no-dev
RUN /app/.venv/bin/python -c "import uvicorn"

FROM python:3.14-slim

WORKDIR /app

COPY --from=builder /app /app
COPY --from=builder /app/.venv /app/.venv

ARG PORT=8000
ENV PORT=${PORT}
ENV UVICORN_RELOAD=false
ENV DB_PATH=/app/data/app.db
ENV DATABASE_URL=""
ENV PATH="/app/.venv/bin:${PATH}"

EXPOSE ${PORT}

CMD ["/app/.venv/bin/python", "main.py"]
