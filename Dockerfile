# Provenance demo — deterministic, offline, single-container deploy.
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Bake the deterministic demo artifacts into the image (campaign pipeline + observability
# trace) so the inspector + observatory are populated on first load. Synthetic, offline, $0.
RUN python -m scripts.pipeline && python -m scripts.trace

EXPOSE 8000
# Railway injects $PORT; default 8000 for local runs.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
