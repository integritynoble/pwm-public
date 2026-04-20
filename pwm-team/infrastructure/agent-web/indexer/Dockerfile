FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/indexer
ENV PYTHONPATH=/app
CMD ["python", "-m", "indexer.main"]
