# Quick Start Guide

Get the Spotify Recommendation System up and running in minutes.

## Prerequisites

Before you begin, ensure you have:
- **Docker** and **Docker Compose** installed
- **Git** for cloning the repository
- At least **4GB RAM** available for containers
- **10GB disk space** for data and models

## Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd spotify_recommendation_system_v2
```

### 2. Configure Environment
```bash
# Copy the example environment file
cp env.example .env

# Edit the configuration (optional for basic setup)
# The default settings work for local development
```

### 3. Start the System

#### Option A: Complete Setup (Recommended)
```bash
# Windows users
./docker-setup.bat full

# Linux/Mac users
./docker-setup.sh full
```

This command will:
- Build all Docker containers
- Set up the database
- Generate machine learning models
- Import sample data
- Start all services

#### Option B: Quick Development Setup
```bash
# Start with existing models (faster)
docker-compose up -d
```

### 4. Access the Application

Once the setup is complete, access the system at:

- **Web Application**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Database**: localhost:5432 (if needed)

## First Steps

### 1. Explore the Interface
- Open http://localhost:3000 in your browser
- Use the search bar to find songs
- Click on any song to see its details

### 2. Get Recommendations
- Search for a song you like
- Click "Get Recommendations"
- Explore similar songs suggested by different models

### 3. Compare Models
- Navigate to "Model Comparison"
- Select a reference song
- Compare results from different algorithms
- See which model works best for your taste

### 4. Explore Clusters
- Visit the "Clusters" section
- Browse music grouped by similar characteristics
- Discover new songs within your preferred clusters

## System Status

### Check if Everything is Running
```bash
# View all services
docker-compose ps

# Check logs if needed
docker-compose logs -f
```

### Verify Models are Ready
```bash
# Check model generation status
docker-compose exec model-prep python model_pipeline.py --check-only
```

### Test the API
```bash
# Quick API health check
curl http://localhost:8000/health
```

## Common Commands

### Managing the System
```bash
# Stop all services
docker-compose down

# Restart a specific service
docker-compose restart backend

# View logs for a service
docker-compose logs backend

# Update and rebuild
git pull
docker-compose build
docker-compose up -d
```

### Model Management
```bash
# Regenerate all models (takes 15-30 minutes)
docker-compose exec model-prep python model_pipeline.py --force

# Check model status
docker-compose exec model-prep python model_pipeline.py --check-only
```

### Database Management
```bash
# Access database directly
docker-compose exec database psql -U postgres -d spotify_recommendations

# Reset database (caution: deletes all data)
docker-compose down
docker volume rm spotify_recommendation_system_v2_postgres_data
docker-compose up -d
```

## Troubleshooting

### Application Won't Start
1. **Check Docker is running**
   ```bash
   docker --version
   docker-compose --version
   ```

2. **Ensure ports are available**
   - Port 3000 (frontend)
   - Port 8000 (backend)
   - Port 5432 (database)

3. **Check system resources**
   - At least 4GB RAM available
   - Sufficient disk space

### Models Not Loading
```bash
# Check if models exist
docker-compose exec model-prep ls -la /app/data/models/

# Regenerate models if missing
docker-compose exec model-prep python model_pipeline.py --force
```

### Database Connection Errors
```bash
# Check database is running
docker-compose ps database

# Restart database
docker-compose restart database

# Check database logs
docker-compose logs database
```

### Slow Performance
1. **Increase Docker memory limits** in Docker Desktop settings
2. **Close other applications** to free up resources
3. **Check disk space** - models require significant storage

## Data Requirements

The system works with:
- **spotify_tracks.csv**: Main track database with audio features
- **low_level_audio_features.csv**: Detailed audio analysis (optional)

Place data files in the `data/raw/` directory before starting the system.

## Next Steps

Once your system is running:

1. **Read the [User Guide](USER_GUIDE.md)** for detailed feature explanations
2. **Check the [Technical Guide](TECHNICAL_GUIDE.md)** for development information
3. **Review the [Project Overview](PROJECT_OVERVIEW.md)** for system architecture

## Getting Help

If you encounter issues:

1. **Check the logs**: `docker-compose logs -f`
2. **Verify system status**: `docker-compose ps`
3. **Review troubleshooting section** above
4. **Check the documentation** for detailed guides

## System Requirements

### Minimum Requirements
- **RAM**: 4GB available
- **Storage**: 10GB free space
- **CPU**: 2 cores
- **OS**: Windows 10+, macOS 10.14+, or Linux

### Recommended Requirements
- **RAM**: 8GB available
- **Storage**: 20GB free space
- **CPU**: 4 cores
- **SSD**: For better performance

The system is designed to run efficiently on modern development machines and can be scaled for production deployment. 