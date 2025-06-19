# �� Docker Setup Guide - Spotify Music Recommendation

This guide covers containerized deployment of the **Spotify Music Recommendation** system using Docker and Docker Compose.

## 🚀 Quick Start

### Prerequisites
- Docker 20.10+ and Docker Compose 2.0+
- Spotify dataset files in `data/raw/`
- Trained models in `data/models/`
- *(Optional)* Spotify API credentials for enhanced features

### 1. Basic Deployment

```bash
# Clone the repository
git clone <your-repo-url>
cd spotify-music-recommendation

# Start the application
docker-compose up -d

# Access the Spotify Music Recommendation system
open http://localhost:8501
```

### 2. Enhanced Deployment with Spotify API

For full features including album artwork, enhanced track information, and rich media:

```bash
# Copy environment template
cp .env.template .env

# Edit .env with your Spotify credentials
# Get credentials from: https://developer.spotify.com/dashboard/applications
nano .env

# Start with enhanced features
docker-compose up -d
```

## 🔧 Configuration

### Environment Variables

The Spotify Music Recommendation system supports the following environment variables:

#### Enhanced Features
```bash
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
```

#### Application Configuration
```bash
# Data path (Docker uses /app/data by default)
DATA_PATH=/app/data

# Streamlit configuration
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_SERVER_ENABLECORS=false
STREAMLIT_SERVER_ENABLEXSRFPROTECTION=false
```

#### Logging Configuration
```bash
# Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO)
LOG_LEVEL=INFO

# Enable/disable file logging (default: true)
ENABLE_FILE_LOGGING=true

# Enable/disable JSON structured logging (default: false)
ENABLE_JSON_LOGGING=false

# Enable/disable performance logging (default: true)
ENABLE_PERFORMANCE_LOGGING=true

# Maximum number of log files to keep during rotation (default: 30)
MAX_LOG_FILES=30

# Maximum log file size in MB before rotation (default: 50)
MAX_LOG_SIZE_MB=50

# Optional logging settings
LOG_FORMAT=standard
LOG_TO_CONSOLE=true
LOG_TIMEZONE=UTC
```

#### Optional API Configuration
```bash
# API Settings
SPOTIFY_API_BASE_URL=https://api.spotify.com/v1
SPOTIFY_TOKEN_URL=https://accounts.spotify.com/api/token
SPOTIFY_REQUESTS_PER_SECOND=10
SPOTIFY_MAX_RETRIES=3
ENABLE_SPOTIFY_API=true

# Streamlit Settings
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_SERVER_ENABLECORS=false
STREAMLIT_SERVER_ENABLEXSRFPROTECTION=false
```

### Using .env File

Create a `.env` file in the project root:

```bash
# Copy template (includes all logging variables)
cp .env.template .env

# Edit with your credentials and logging preferences
SPOTIFY_CLIENT_ID=your_actual_client_id
SPOTIFY_CLIENT_SECRET=your_actual_client_secret
LOG_LEVEL=INFO
ENABLE_PERFORMANCE_LOGGING=true
```

**Security Note**: The `.env` file is automatically ignored by Docker and Git to prevent credential leaks.

### Environment Variable Examples

#### Development Setup (Verbose Logging)
```bash
LOG_LEVEL=DEBUG
ENABLE_PERFORMANCE_LOGGING=true
ENABLE_JSON_LOGGING=false
ENABLE_FILE_LOGGING=true
```

#### Production Setup (Optimized)
```bash
LOG_LEVEL=WARNING
ENABLE_PERFORMANCE_LOGGING=true
ENABLE_JSON_LOGGING=true
MAX_LOG_SIZE_MB=100
MAX_LOG_FILES=50
```

#### Minimal Setup (Basic Features Only)
```bash
ENABLE_FILE_LOGGING=false
LOG_LEVEL=ERROR
ENABLE_PERFORMANCE_LOGGING=false
```

## 📁 Volume Mounts

The Docker setup includes the following volume mounts:

```yaml
volumes:
  - ./data/raw:/app/data/raw:ro      # Raw data (read-only)
  - ./data/models:/app/data/models:ro # Models (read-only)
  - ./logs:/app/logs                  # Logs directory (read-write)
```

### Required Directory Structure
```
📦 Project Root/
├── data/
│   ├── raw/
│   │   ├── spotify_tracks.csv
│   │   ├── spotify_artists.csv
│   │   └── low_level_audio_features.csv
│   └── models/
│       ├── hdbscan_model.pkl
│       ├── knn_model.pkl
│       ├── audio_embeddings.pkl
│       ├── cluster_labels.pkl
│       └── song_indices.pkl
├── logs/                   # Auto-created for log files
├── .env                    # Your environment variables
└── docker-compose.yml     # Docker configuration
```

**Note**: The `logs/` directory will be automatically created when the container starts if it doesn't exist.

## 🎛️ Service Management

### Starting Services
```bash
# Start in background
docker-compose up -d

# Start with logs
docker-compose up

# Start specific service
docker-compose up streamlit
```

### Stopping Services
```bash
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Force stop and cleanup
docker-compose down --remove-orphans
```

### Viewing Logs
```bash
# View all logs
docker-compose logs

# Follow logs
docker-compose logs -f

# Service-specific logs
docker-compose logs streamlit

# View application log files (from host)
tail -f logs/spotify_recommender.log
tail -f logs/spotify_recommender_errors.log
tail -f logs/spotify_recommender_performance.log
```

## 📊 Logging and Monitoring

### Log Files (Available on Host)

When using Docker, log files are mounted to your local `logs/` directory:

```bash
# View real-time application logs
tail -f logs/spotify_recommender.log

# View performance metrics
tail -f logs/spotify_recommender_performance.log

# View errors only
tail -f logs/spotify_recommender_errors.log

# View structured JSON logs (if enabled)
tail -f logs/spotify_recommender_structured.json | jq '.'
```

### Log Analysis Examples

```bash
# Count recommendation types
grep "recommendation" logs/spotify_recommender.log | cut -d' ' -f8 | sort | uniq -c

# Monitor API response times
grep "Spotify API" logs/spotify_recommender_performance.log | grep -o "[0-9]\+\.[0-9]\+s"

# Check error rates
grep -c "ERROR\|CRITICAL" logs/spotify_recommender_errors.log
```

### Logging Dashboard

Access the built-in logging dashboard at `http://localhost:8501` → Sidebar → "📊 Logging Dashboard"

Features:
- Real-time log statistics
- Configuration viewing
- Test log generation
- File size monitoring

## 🔍 Monitoring and Health Checks

### Health Check Status
```bash
# Check container health
docker-compose ps

# Detailed health information
docker inspect spotify-recommendation-system
```

### Application Health
The application includes built-in health checks:
- **Endpoint**: `http://localhost:8501/_stcore/health`
- **Interval**: 30 seconds
- **Timeout**: 10 seconds
- **Retries**: 3

### Resource Monitoring
```bash
# View resource usage
docker stats spotify-recommendation-system

# Container information
docker inspect spotify-recommendation-system

# Log file sizes
du -sh logs/*
```

## 🛠️ Development and Debugging

### Development Mode
```bash
# Mount source code for development
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

### Debugging
```bash
# Execute shell in container
docker-compose exec streamlit bash

# View environment variables
docker-compose exec streamlit env | grep SPOTIFY

# Test API connectivity
docker-compose exec streamlit python -c "from spotify_api_client import create_spotify_client; client = create_spotify_client(); print('Connected!' if client._get_access_token() else 'Failed')"
```

### Rebuilding
```bash
# Rebuild after code changes
docker-compose build --no-cache

# Rebuild and restart
docker-compose up --build -d
```

## 📊 Performance Optimization

### Memory Configuration
```bash
# Increase memory limit if needed
docker run --memory="2g" spotify-recommendation-system
```

### CPU Configuration
```bash
# Limit CPU usage
docker run --cpus="1.0" spotify-recommendation-system
```

### Container Optimization
- Uses `python:3.11-slim` for smaller image size
- Multi-stage builds for production deployments
- Proper layer caching for faster rebuilds

## 🚀 Production Deployment

### Security Hardening
```bash
# Run as non-root user
docker run --user 1000:1000 spotify-recommendation-system

# Read-only file system
docker run --read-only spotify-recommendation-system
```

### Scaling
```bash
# Scale to multiple instances
docker-compose up --scale streamlit=3

# Load balancing (requires nginx configuration)
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Reverse Proxy Configuration
```nginx
# nginx.conf
upstream streamlit {
    server localhost:8501;
    server localhost:8502;
    server localhost:8503;
}

server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://streamlit;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 🔧 Troubleshooting

### Common Issues

#### Container Won't Start
```bash
# Check logs
docker-compose logs streamlit

# Verify port availability
netstat -tulpn | grep 8501

# Check Docker daemon
docker info
```

#### Spotify API Not Working
```bash
# Verify environment variables
docker-compose exec streamlit env | grep SPOTIFY

# Test API connectivity
docker-compose exec streamlit curl -v https://accounts.spotify.com/api/token

# Check credentials format
docker-compose exec streamlit python -c "import os; print('ID:', len(os.getenv('SPOTIFY_CLIENT_ID', ''))); print('Secret:', len(os.getenv('SPOTIFY_CLIENT_SECRET', '')))"
```

#### Data Not Loading
```bash
# Check volume mounts
docker-compose exec streamlit ls -la /app/data/raw/
docker-compose exec streamlit ls -la /app/data/models/

# Verify file permissions
ls -la data/raw/
ls -la data/models/
```

#### Performance Issues
```bash
# Monitor resource usage
docker stats

# Check memory limits
docker-compose exec streamlit free -h

# Verify CPU usage
docker-compose exec streamlit top
```

### Getting Help
- **Logs**: Always check `docker-compose logs` first
- **Health**: Monitor health check status
- **Resources**: Ensure adequate memory and CPU
- **Network**: Verify port accessibility
- **Credentials**: Double-check Spotify API setup

## 📚 Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Streamlit Docker Deployment](https://docs.streamlit.io/knowledge-base/tutorials/deploy/docker)
- [Spotify API Setup Guide](SPOTIFY_SETUP.md)
- [Application Documentation](README.md)

---

🐳 **Happy containerizing!** 🐳 