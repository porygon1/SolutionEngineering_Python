# 🛠️ Setup Guide - Spotify Music Recommendation System v2

**Complete setup instructions for the production-ready music recommendation system**

## 🎯 Overview

This guide covers the complete setup of the Spotify Music Recommendation System v2, including:
- **Data preparation** and validation
- **Model training** and preparation
- **Database setup** and import
- **Application deployment** with Docker
- **Development environment** configuration

## 📋 Prerequisites

### System Requirements
- **Docker Desktop** 4.0+ installed and running
- **8GB+ RAM** (16GB recommended for optimal performance)
- **20GB+ available disk space** for data and containers
- **Python 3.11+** (for development and model preparation)
- **Node.js 18+** (for frontend development)

### Required Data Files
Ensure you have these CSV files in the `data/raw/` directory:

| File | Description | Expected Size |
|------|-------------|---------------|
| `spotify_tracks.csv` | Main track data with audio features | ~101K rows |
| `spotify_artists.csv` | Artist metadata and genres | ~10K rows |
| `spotify_albums.csv` | Album information | ~20K rows |
| `low_level_audio_features.csv` | MEL, MFCC, chroma analysis | ~101K rows |
| `lyrics_features.csv` | Text and sentiment analysis | ~101K rows |

## 🚀 Quick Start (Recommended)

### 1. Clone and Prepare
```bash
# Clone the repository
git clone <your-repo-url>
cd spotify-recommendation-system

# Verify data files exist
ls -la data/raw/
```

### 2. Complete System Setup
```bash
# Navigate to v2 directory
cd spotify_recommendation_system_v2

# Start complete system (includes data import)
docker-compose --profile setup up --build

# Wait for initial setup to complete (~10-15 minutes)
# Watch logs: docker-compose logs -f
```

### 3. Launch Application
```bash
# Start the application
docker-compose up -d

# Access the system:
# Frontend: http://localhost:3000
# API: http://localhost:8000
# API Docs: http://localhost:8000/docs
# PgAdmin: http://localhost:5050
```

### 4. Verify Installation
```bash
# Check all services are running
docker-compose ps

# Test API health
curl http://localhost:8000/health

# Test frontend
open http://localhost:3000
```

## 🔧 Step-by-Step Setup

### Step 1: Data Validation
```bash
# Check data completeness
python -c "
import pandas as pd
import os

required_files = {
    'spotify_tracks.csv': 101000,
    'spotify_artists.csv': 10000,
    'spotify_albums.csv': 20000,
    'low_level_audio_features.csv': 101000,
    'lyrics_features.csv': 101000
}

print('🔍 Data Validation:')
all_good = True
for file, expected_rows in required_files.items():
    path = f'data/raw/{file}'
    if os.path.exists(path):
        try:
            df = pd.read_csv(path)
            actual_rows = len(df)
            if actual_rows >= expected_rows * 0.9:
                print(f'✅ {file}: {actual_rows:,} rows')
            else:
                print(f'⚠️  {file}: {actual_rows:,} rows (expected ~{expected_rows:,})')
                all_good = False
        except Exception as e:
            print(f'❌ {file}: Error reading - {e}')
            all_good = False
    else:
        print(f'❌ {file}: Missing')
        all_good = False

if all_good:
    print('\\n🎉 All data files are ready!')
else:
    print('\\n⚠️  Some data files need attention.')
"
```

### Step 2: Model Preparation
```bash
# Prepare machine learning models
cd spotify_recommendation_system_v2/model-prep

# Option A: Use Docker (recommended)
docker-compose up model-prep

# Option B: Local preparation
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate
pip install -r requirements.txt
python prepare_models.py

# Verify models are created
ls -la ../data/models/
```

### Step 3: Database Setup
```bash
# Start database service
cd spotify_recommendation_system_v2
docker-compose up database -d

# Wait for database to be ready
sleep 30

# Check database status
docker-compose exec database pg_isready -U spotify_user
```

### Step 4: Data Import
```bash
# Import data to database
docker-compose exec backend python import_data.py

# Populate clusters
docker-compose exec backend python populate_clusters.py

# Verify import success
docker-compose exec database psql -U spotify_user -d spotify_recommendations -c "
    SELECT 
        'artists' as table_name, COUNT(*) as row_count FROM artists
    UNION ALL
    SELECT 'albums', COUNT(*) FROM albums
    UNION ALL
    SELECT 'tracks', COUNT(*) FROM tracks
    UNION ALL
    SELECT 'audio_features', COUNT(*) FROM audio_features
    UNION ALL
    SELECT 'clusters', COUNT(*) FROM clusters;
"
```

### Step 5: Frontend Setup
```bash
# Install frontend dependencies
cd frontend
npm install

# Build production assets
npm run build

# Start frontend service
cd ..
docker-compose up frontend -d
```

### Step 6: Final Verification
```bash
# Check all services
docker-compose ps

# Test API endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/v2/songs/random?limit=1
curl http://localhost:8000/api/v2/clusters?limit=5

# Test frontend
curl -I http://localhost:3000
```

## 🛠️ Development Setup

### Backend Development
```bash
cd spotify_recommendation_system_v2/backend

# Create Python environment
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate

# Install development dependencies
pip install -r requirements.txt

# Start database
docker-compose up database -d

# Run data import (first time only)
python import_data.py

# Start FastAPI with hot reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development
```bash
cd spotify_recommendation_system_v2/frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Access at http://localhost:3000
```

### Database Development
```bash
# Access PostgreSQL CLI
docker-compose exec database psql -U spotify_user -d spotify_recommendations

# Access PgAdmin
open http://localhost:5050
# Login: admin@spotify.local / admin_password

# Database migrations
cd backend
python -m app.database.migrate
```

## 📊 Data Import Process

### Understanding the Import Pipeline
```bash
# The data import happens in this sequence:
# 1. Artists table (from spotify_artists.csv)
# 2. Albums table (from spotify_albums.csv)
# 3. Tracks table (from spotify_tracks.csv)
# 4. Audio Features table (from low_level_audio_features.csv)
# 5. Lyrics Features (merged into tracks)
# 6. Clusters table (from ML model results)
```

### Manual Data Import
```bash
cd spotify_recommendation_system_v2/backend

# Import step by step
python -c "
from app.import_data import ImportManager
import asyncio

async def main():
    manager = ImportManager()
    await manager.import_artists()
    await manager.import_albums()
    await manager.import_tracks()
    await manager.import_audio_features()
    await manager.import_lyrics_features()
    print('✅ Data import completed!')

asyncio.run(main())
"
```

### Populate Clusters
```bash
# After data import, populate clusters
python -c "
from app.populate_clusters import ClusterPopulator
import asyncio

async def main():
    populator = ClusterPopulator()
    await populator.populate_all_clusters()
    print('✅ Clusters populated!')

asyncio.run(main())
"
```

## 🤖 Model Preparation

### Training New Models
```bash
cd spotify_recommendation_system_v2/model-prep

# Prepare all models
python prepare_models.py

# This creates:
# - HDBSCAN clustering model
# - KNN recommendation model
# - Feature embeddings
# - Cluster labels
# - Song indices
```

### Model Files Generated
```bash
# Check generated models
ls -la ../data/models/

# Expected files:
# hdbscan_model.pkl          # HDBSCAN clustering model
# knn_model.pkl              # KNN recommendation model
# scaler.pkl                 # Feature scaler
# pca_model.pkl              # PCA dimensionality reduction
# cluster_labels.pkl         # Cluster assignments
# song_indices.pkl           # Song index mapping
# feature_embeddings.pkl     # Processed feature vectors
```

## 🐳 Docker Configuration

### Service Overview
```yaml
# docker-compose.yml includes:
services:
  database:      # PostgreSQL 15
  backend:       # FastAPI application
  frontend:      # React development server
  pgadmin:       # Database administration
  model-prep:    # ML model preparation (--profile setup)
```

### Environment Variables
```bash
# Create .env file (optional)
cat > .env << EOF
# Database
POSTGRES_DB=spotify_recommendations
POSTGRES_USER=spotify_user
POSTGRES_PASSWORD=secure_password_here

# API
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true

# Frontend
REACT_APP_API_URL=http://localhost:8000
REACT_APP_ENVIRONMENT=development
EOF
```

### Custom Configuration
```bash
# For production deployment
ENVIRONMENT=production docker-compose up --build

# For development with hot reload
ENVIRONMENT=development docker-compose up --build

# Scale services
docker-compose up --scale backend=2 --scale frontend=2
```

## 🔧 Troubleshooting

### Common Issues and Solutions

#### ❌ Database Connection Errors
```bash
# Check database status
docker-compose logs database

# Restart database
docker-compose restart database

# Check connectivity
docker-compose exec backend python -c "
from app.database.database import get_database_connection
import asyncio

async def test():
    try:
        async with get_database_connection() as conn:
            result = await conn.fetch('SELECT 1')
            print('✅ Database connection successful')
    except Exception as e:
        print(f'❌ Database connection failed: {e}')

asyncio.run(test())
"
```

#### ❌ Data Import Failures
```bash
# Check data file integrity
python -c "
import pandas as pd
files = ['spotify_tracks.csv', 'spotify_artists.csv', 'spotify_albums.csv']
for file in files:
    try:
        df = pd.read_csv(f'data/raw/{file}')
        print(f'✅ {file}: {len(df)} rows, {len(df.columns)} columns')
    except Exception as e:
        print(f'❌ {file}: {e}')
"

# Retry import
docker-compose exec backend python import_data.py --force
```

#### ❌ Model Loading Issues
```bash
# Check model files
ls -la data/models/

# Regenerate models
cd spotify_recommendation_system_v2/model-prep
python prepare_models.py --force

# Test model loading
python -c "
import pickle
try:
    with open('../data/models/hdbscan_model.pkl', 'rb') as f:
        model = pickle.load(f)
    print('✅ HDBSCAN model loaded successfully')
except Exception as e:
    print(f'❌ Model loading failed: {e}')
"
```

#### ❌ Frontend Build Issues
```bash
# Clear cache and reinstall
cd spotify_recommendation_system_v2/frontend
rm -rf node_modules package-lock.json
npm cache clean --force
npm install

# Check for Node.js version compatibility
node --version  # Should be 18+
npm --version
```

#### ❌ Port Conflicts
```bash
# Check what's using ports
netstat -tulpn | grep :3000
netstat -tulpn | grep :8000
netstat -tulpn | grep :5432

# Kill conflicting processes
sudo kill $(sudo lsof -t -i:3000)
sudo kill $(sudo lsof -t -i:8000)

# Or change ports in docker-compose.yml
```

### Performance Optimization

#### Database Optimization
```sql
-- Run these queries in PgAdmin or psql
-- Create additional indexes for better performance
CREATE INDEX CONCURRENTLY idx_tracks_popularity ON tracks(popularity DESC);
CREATE INDEX CONCURRENTLY idx_tracks_cluster ON tracks(cluster_id);
CREATE INDEX CONCURRENTLY idx_audio_features_composite ON audio_features(energy, valence, danceability);

-- Analyze tables for query optimization
ANALYZE artists;
ANALYZE albums;
ANALYZE tracks;
ANALYZE audio_features;
ANALYZE clusters;
```

#### Memory Configuration
```bash
# Increase Docker memory limit
# Docker Desktop -> Settings -> Resources -> Memory -> 8GB+

# PostgreSQL memory tuning (in docker-compose.yml)
environment:
  - POSTGRES_SHARED_BUFFERS=256MB
  - POSTGRES_EFFECTIVE_CACHE_SIZE=1GB
  - POSTGRES_WORK_MEM=64MB
```

## 📊 Monitoring and Maintenance

### Health Checks
```bash
# System health
curl http://localhost:8000/health

# Database health
docker-compose exec database pg_isready -U spotify_user

# Service status
docker-compose ps
```

### Log Monitoring
```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f database

# Log rotation and cleanup
docker-compose exec backend python -m app.utils.log_cleanup
```

### Database Maintenance
```bash
# Backup database
docker-compose exec database pg_dump -U spotify_user spotify_recommendations > backup_$(date +%Y%m%d).sql

# Restore database
docker-compose exec -T database psql -U spotify_user spotify_recommendations < backup_20240101.sql

# Vacuum and analyze
docker-compose exec database psql -U spotify_user -d spotify_recommendations -c "VACUUM ANALYZE;"
```

## 🎯 Next Steps

After successful setup:

1. **🎵 Test Recommendations**: Use the frontend to test music recommendations
2. **📊 Explore Data**: Use PgAdmin to explore the database schema
3. **🔧 Customize**: Modify recommendation algorithms in the backend
4. **🎨 Personalize**: Customize the frontend UI/UX
5. **📈 Monitor**: Set up monitoring and logging for production use

## 🤝 Getting Help

- **📚 Documentation**: Check the README.md for feature overview
- **🐛 Issues**: Create GitHub issues for bugs and feature requests
- **💬 Discussions**: Use GitHub discussions for questions
- **🔧 Development**: See the development setup section for contributions

---

**🎵 Enjoy your music discovery journey!** 🎵 