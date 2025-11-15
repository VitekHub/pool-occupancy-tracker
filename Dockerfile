FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY occupancy.py .
COPY capacity.py .
COPY data/ ./data/

# Create data directory if it doesn't exist
RUN mkdir -p data

# Set timezone to Prague
ENV TZ=Europe/Prague

# Run the occupancy tracker by default
CMD ["python", "occupancy.py"]