FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY occupancy.py .
COPY capacity.py .
COPY http_utils.py .
COPY scheduler.py .
COPY pool_aggregation/ ./pool_aggregation/

# Copy data directory (includes config and existing CSVs)
COPY data/ ./data/

# Ensure data directory exists for new files
RUN mkdir -p data/overall data/weekly

ENV TZ=Europe/Prague

CMD ["python", "scheduler.py"]