# Motorcade LeadGen — Lead Intake API container
#
# Build with Podman:
#   podman build -t motorcade/leadgen:dev -f Containerfile .
#
# Run (example):
#   podman run --rm -p 8000:8000 --env-file ./dev.env motorcade/leadgen:dev
#
# NOTE: In production we do NOT expose port 8000 publicly; NGINX/ALB will proxy on 443.

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1     PYTHONUNBUFFERED=1     PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps (kept minimal)
RUN apt-get update && apt-get install -y --no-install-recommends     ca-certificates  && rm -rf /var/lib/apt/lists/*

# Install Python deps
# NOTE: requirements.txt lives under app/api/ in this repo.
COPY app/api/requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip && pip install -r /app/requirements.txt

# Copy app code
COPY app /app/app

# Default env (override via env-file or secrets mount)
ENV LEADGEN_SERVICE_NAME=lead-intake-api     LEADGEN_VERSION=v1     LEADGEN_ENV=dev

EXPOSE 8000

# Start API
CMD ["python", "-m", "uvicorn", "app.api.leadgen_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
