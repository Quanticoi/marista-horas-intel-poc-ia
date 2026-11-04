FROM python:3.12.9-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 MLFLOW_HTTP_REQUEST_TIMEOUT=15 MLFLOW_HTTP_REQUEST_MAX_RETRIES=2
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends postgresql-client ca-certificates git && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml ./
COPY config/requirements.lock ./requirements.lock
RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.lock
COPY src ./src
RUN pip install --no-deps . && pip check && useradd --uid 1000 --create-home poc
COPY config ./config
COPY sql ./sql
COPY alembic.ini ./
COPY notebooks ./notebooks
COPY tests ./tests
COPY deployment/scripts/reset_poc.py ./deployment/scripts/reset_poc.py
COPY deployment/scripts/init_env.py ./deployment/scripts/init_env.py
USER 1000:1000
ARG CODE_VERSION=uncommitted
ENV CODE_VERSION=${CODE_VERSION}
CMD ["python", "-m", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
