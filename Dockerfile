FROM python:3.11-slim AS builder

WORKDIR /app
ENV PIP_NO_CACHE_DIR=1

COPY pyproject.toml README.md /app/
COPY src /app/src
RUN python -m pip install --upgrade pip && pip install .

FROM python:3.11-slim AS runtime

WORKDIR /app
ENV PYTHONUNBUFFERED=1
RUN useradd -m appuser

COPY --from=builder /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=builder /usr/local/bin /usr/local/bin
COPY src /app/src
COPY alembic /app/alembic
COPY alembic.ini /app/alembic.ini

USER appuser
EXPOSE 8000
CMD ["uvicorn", "high_load_ai.main:app", "--host", "0.0.0.0", "--port", "8000", "--app-dir", "src"]
