FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy scripts
COPY . .

# Make sure data directory exists
RUN mkdir -p /app/data/models

# Default command
CMD ["python", "prepare_models.py"] 