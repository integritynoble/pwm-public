# Build context is expected to be `infrastructure/agent-web/` (not `api/`) so that
# the Dockerfile can pick up the indexer's schema.sql without escaping the context.
FROM python:3.12-slim

WORKDIR /app
COPY api/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY api      /app/api
COPY indexer  /app/indexer
ENV PYTHONPATH=/app
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
