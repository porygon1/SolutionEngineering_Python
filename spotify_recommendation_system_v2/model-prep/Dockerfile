FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download NLTK data
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"

# Copy model generation scripts
COPY scripts/ ./scripts/
COPY model_pipeline.py .

# Create necessary directories
RUN mkdir -p /app/models /app/data /app/logs

# Set environment variables
ENV PYTHONPATH=/app
ENV MODELS_PATH=/app/models
ENV DATA_PATH=/app/data

# Make scripts executable
RUN chmod +x scripts/*.py
RUN chmod +x model_pipeline.py

# Default command - will be overridden by docker-compose
CMD ["python", "scripts/startup.py"] 