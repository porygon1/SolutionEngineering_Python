FROM python:3.11-slim

WORKDIR /app

# Install system dependencies needed for scientific packages
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the main Streamlit app (new version)
COPY app.py .

# Copy supporting modules
COPY spotify_api_client.py .
COPY logging_config.py .

# Copy modular components
COPY utils/ ./utils/
COPY components/ ./components/

# Copy Streamlit configuration
COPY .streamlit/ ./.streamlit/

# Copy static files (CSS, images, etc.)
COPY static/ ./static/

# Create directory structure for data and models
RUN mkdir -p /app/data/raw /app/data/models /app/logs

# Expose the port Streamlit runs on
EXPOSE 8501

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_HEADLESS=true
ENV PYTHONPATH=/app
ENV DATA_PATH=/app/data

# Set default Spotify API environment variables (can be overridden)
ENV SPOTIFY_API_BASE_URL=https://api.spotify.com/v1
ENV SPOTIFY_TOKEN_URL=https://accounts.spotify.com/api/token
ENV SPOTIFY_REQUESTS_PER_SECOND=10
ENV SPOTIFY_MAX_RETRIES=3
ENV ENABLE_SPOTIFY_API=true

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Command to run the new app version
ENTRYPOINT ["streamlit", "run", "app.py", "--server.enableCORS=false", "--server.enableXsrfProtection=false"] 