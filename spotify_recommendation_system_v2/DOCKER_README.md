# 🎵 Spotify Music Recommendation System v2 - Docker Setup

This document provides comprehensive instructions for setting up and running the Spotify Music Recommendation System v2 using Docker.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Services](#services)
- [Development vs Production](#development-vs-production)
- [Model Integration](#model-integration)
- [Troubleshooting](#troubleshooting)
- [Maintenance](#maintenance)

## 🔧 Prerequisites

Before you begin, ensure you have the following installed:

- **Docker**: Version 20.10+ ([Install Docker](https://docs.docker.com/get-docker/))
- **Docker Compose**: Version 2.0+ ([Install Docker Compose](https://docs.docker.com/compose/install/))
- **Git**: For cloning the repository
- **At least 4GB RAM**: Recommended for running all services
- **At least 10GB free disk space**: For data, models, and Docker images

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| RAM | 4GB | 8GB+ |
| CPU | 2 cores | 4+ cores |
| Storage | 10GB | 20GB+ |
| Docker | 20.10+ | Latest |

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)

**For Windows:**
```batch
cd spotify_recommendation_system_v2
docker-setup.bat full
```

**For Linux/Mac:**
```bash
cd spotify_recommendation_system_v2
chmod +x docker-setup.sh
./docker-setup.sh full
```

### Option 2: Manual Setup

1. **Clone and Navigate**
   ```bash
   git clone <repository-url>
   cd spotify_recommendation_system_v2
   ```

2. **Create Environment File**
   ```bash
   cp env.example .env
   # Edit .env with your specific configuration
   ```

3. **Build and Start Services**
   ```bash
   docker-compose build
   docker-compose up -d database
   # Wait for database to be ready
   docker-compose --profile setup run --rm model-prep
   docker-compose --profile setup run --rm data-import
   docker-compose up -d backend frontend
   ```

## ⚙️ Configuration

### Environment Variables

The system uses environment variables for configuration. Copy `env.example` to `.env` and modify as needed:

```bash
cp env.example .env
```

Key configuration sections:

#### Database Configuration
```env
DATABASE_URL=postgresql://spotify_user:spotify_password@database:5432/spotify_recommendations
POSTGRES_DB=spotify_recommendations
POSTGRES_USER=spotify_user
POSTGRES_PASSWORD=spotify_password
```

#### Model Paths
```env
MODELS_PATH=/app/models
LYRICS_VECTORIZER_PATH=/app/models/lyrics_tfidf_vectorizer.pkl
LYRICS_MODEL_PATH=/app/models/lyrics_similarity_model_knn_cosine.pkl
AUDIO_MODELS_PATH=/app/models/audio
```

#### Feature Flags
```env
ENABLE_LYRICS_SIMILARITY=true
ENABLE_AUDIO_CLUSTERING=true
ENABLE_HYBRID_RECOMMENDATIONS=true
ENABLE_MODEL_COMPARISON=true
```

### Data Requirements

Ensure your data files are placed in the correct locations:

```
../data/
├── raw/
│   ├── spotify_tracks.csv      # Main dataset
│   └── lyrics_data.csv         # Lyrics data (optional)
├── processed/                  # Processed data (auto-generated)
└── models/                     # Model files (auto-generated)
```

## 🐳 Services

The system consists of several Docker services:

### Core Services

| Service | Port | Description |
|---------|------|-------------|
| **database** | 5432 | PostgreSQL database |
| **backend** | 8000 | FastAPI backend API |
| **frontend** | 8501 | React frontend (production) |
| **frontend-dev** | 5173 | React frontend (development) |

### Setup Services (Profiles)

| Service | Profile | Description |
|---------|---------|-------------|
| **model-prep** | setup | Prepares ML models |
| **data-import** | setup | Imports data into database |

### Optional Services

| Service | Port | Profile | Description |
|---------|------|---------|-------------|
| **nginx** | 80, 443 | production | Reverse proxy |
| **pgadmin** | 5050 | admin | Database administration |

## 🔄 Development vs Production

### Development Environment

For active development with hot reload:

```bash
# Windows
docker-setup.bat dev

# Linux/Mac
./docker-setup.sh dev
```

**Development URLs:**
- Frontend: http://localhost:5173 (with hot reload)
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/api/v2/docs

### Production Environment

For production deployment:

```bash
# Windows
docker-setup.bat prod

# Linux/Mac
./docker-setup.sh prod
```

**Production URLs:**
- Application: http://localhost:80 (via nginx)
- Backend API: http://localhost:8000
- Frontend: http://localhost:8501

## 🤖 Model Integration

The system supports multiple recommendation models:

### Audio Clustering Models
- **HDBSCAN**: For clustering songs by audio features
- **KNN**: For finding similar songs within clusters

### Lyrics Similarity Models
- **TF-IDF Vectorizer**: For text feature extraction
- **Cosine Similarity KNN**: For lyrics-based recommendations

### Model Preparation

Models are automatically prepared during setup, but you can also run model preparation separately:

```bash
# Prepare all models
docker-compose --profile setup run --rm model-prep

# Or use the setup script
docker-setup.bat models  # Windows
./docker-setup.sh models  # Linux/Mac
```

### Model Files

Expected model files in the `models/` directory:

```
models/
├── audio/
│   ├── hdbscan_model.pkl
│   ├── knn_model.pkl
│   ├── audio_embeddings.pkl
│   └── cluster_labels.pkl
└── lyrics/
    ├── lyrics_tfidf_vectorizer.pkl
    ├── lyrics_similarity_model_knn_cosine.pkl
    └── lyrics_training_metadata.pkl
```

## 🔍 Monitoring and Debugging

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend

# Using setup script
docker-setup.bat logs  # Windows
./docker-setup.sh logs  # Linux/Mac
```

### Service Status

```bash
# Check service status
docker-compose ps

# Check resource usage
docker stats

# Using setup script
docker-setup.bat status  # Windows
./docker-setup.sh status  # Linux/Mac
```

### Health Checks

The system includes built-in health checks:

- **Database**: `pg_isready` check
- **Backend**: HTTP health endpoint at `/health`
- **Frontend**: HTTP accessibility check

## 🐛 Troubleshooting

### Common Issues

#### 1. Port Already in Use
```bash
# Check what's using the port
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # Linux/Mac

# Stop conflicting services or change ports in docker-compose.yml
```

#### 2. Database Connection Issues
```bash
# Check database status
docker-compose exec database pg_isready -U spotify_user

# Restart database
docker-compose restart database
```

#### 3. Model Files Missing
```bash
# Re-run model preparation
docker-compose --profile setup run --rm model-prep

# Check model files
docker-compose exec backend ls -la /app/models/
```

#### 4. Frontend Build Issues
```bash
# Rebuild frontend
docker-compose build --no-cache frontend

# Check frontend logs
docker-compose logs frontend
```

### Performance Issues

#### 1. Slow Model Loading
- Ensure model files are properly mounted
- Check available RAM (models can be memory-intensive)
- Consider using faster storage (SSD)

#### 2. Database Performance
- Increase database connection pool size
- Add database indexes for frequently queried columns
- Monitor database logs for slow queries

### Debugging Commands

```bash
# Enter backend container
docker-compose exec backend bash

# Enter database container
docker-compose exec database psql -U spotify_user -d spotify_recommendations

# Check backend API directly
curl http://localhost:8000/health
curl http://localhost:8000/api/v2/recommendations/stats
```

## 🧹 Maintenance

### Regular Maintenance

#### 1. Update Images
```bash
docker-compose pull
docker-compose build --no-cache
```

#### 2. Clean Up Resources
```bash
# Remove unused images
docker image prune -f

# Remove unused volumes (be careful!)
docker volume prune -f

# Complete cleanup (WARNING: removes all data!)
docker-setup.bat cleanup  # Windows
./docker-setup.sh cleanup  # Linux/Mac
```

#### 3. Backup Data
```bash
# Backup database
docker-compose exec database pg_dump -U spotify_user spotify_recommendations > backup.sql

# Backup model files
docker cp $(docker-compose ps -q backend):/app/models ./models_backup
```

### Updating the System

1. **Pull latest code**
   ```bash
   git pull origin main
   ```

2. **Rebuild services**
   ```bash
   docker-compose build --no-cache
   ```

3. **Update models** (if needed)
   ```bash
   docker-compose --profile setup run --rm model-prep
   ```

4. **Restart services**
   ```bash
   docker-compose restart
   ```

## 📊 Available Endpoints

### Backend API Endpoints

- **Health**: `GET /health`
- **API Docs**: `GET /api/v2/docs`
- **Recommendations**: `POST /api/v2/recommendations`
- **Model Comparison**: `POST /api/v2/recommendations/compare`
- **Songs**: `GET /api/v2/songs`
- **Clusters**: `GET /api/v2/clusters`

### Frontend Routes

- **Home**: `/`
- **Model Comparison**: `/compare`
- **Song Explorer**: `/songs`
- **Cluster Analysis**: `/clusters`

## 🆘 Getting Help

If you encounter issues:

1. **Check the logs**: `docker-compose logs -f`
2. **Verify configuration**: Review your `.env` file
3. **Check system resources**: Ensure sufficient RAM/disk space
4. **Restart services**: `docker-compose restart`
5. **Clean rebuild**: `docker-compose build --no-cache`

For persistent issues, please check the project's issue tracker or documentation.

## 📝 Notes

- **First run** may take 10-15 minutes to download images and prepare models
- **Model preparation** requires the lyrics similarity notebook to be run first
- **Data import** time depends on dataset size
- **Development mode** enables hot reload but uses more resources
- **Production mode** is optimized for performance and stability 