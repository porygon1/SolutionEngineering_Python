# 🎵 Spotify Music Recommendation System v2

**AI-Powered Music Recommendations using HDBSCAN Clustering & PostgreSQL**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-blue.svg)](https://reactjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue.svg)](https://docker.com)

> **Version 2** of the Spotify Music Recommendation System featuring a **PostgreSQL database**, **modern web architecture**, and **scalable deployment** with Docker Compose.

## 🚀 **Quick Start**

### **Option 1: Docker Compose (Recommended)**

```bash
# Clone the repository
git clone <repository-url>
cd spotify_recommendation_system_v2

# Start the complete system
docker-compose up --build

# Or start with data import
docker-compose --profile setup up --build
```

**Access the Application:**
- 🌐 **Frontend**: http://localhost:3000
- 🔧 **API**: http://localhost:8000
- 📊 **API Docs**: http://localhost:8000/api/v2/docs
- 🗄️ **PgAdmin**: http://localhost:5050

### **Option 2: Manual Setup**

```bash
# 1. Start PostgreSQL
docker-compose up database -d

# 2. Setup backend
cd backend
pip install -r requirements.txt
python -m app.import_data

# 3. Start FastAPI
uvicorn app.main:app --reload

# 4. Setup frontend
cd ../frontend
npm install
npm start
```

## 🏗️ **Architecture Overview**

```mermaid
graph TB
    subgraph "Frontend"
        A[React App] --> B[TypeScript/Tailwind]
        B --> C[Spotify UI Theme]
    end
    
    subgraph "Backend"
        D[FastAPI] --> E[PostgreSQL]
        D --> F[ML Models]
        F --> G[HDBSCAN Clustering]
        F --> H[KNN Recommendations]
    end
    
    subgraph "Database"
        E --> I[Artists Table]
        E --> J[Albums Table]
        E --> K[Tracks Table]
        E --> L[Audio Features]
        E --> M[Clusters Table]
    end
    
    subgraph "ML Pipeline"
        N[CSV Data] --> O[Data Import]
        O --> P[Feature Engineering]
        P --> Q[HDBSCAN Clustering]
        Q --> R[KNN Model Training]
        R --> S[Model Persistence]
    end
    
    A --> D
    G --> E
    H --> E
```

## 📊 **Key Features**

### **🎯 Smart Recommendations**
- **HDBSCAN Clustering**: Groups similar tracks into ~61 clusters
- **KNN Search**: Finds nearest neighbors within clusters
- **Hybrid Approach**: Combines cluster-based and global recommendations
- **Real-time Processing**: <100ms response times

### **🎨 Modern Web Interface**
- **Spotify-themed UI** with dark mode and green accents
- **Responsive design** optimized for all devices
- **Interactive components** with smooth animations
- **Search functionality** with autocomplete

### **📈 Database-Driven**
- **PostgreSQL 15** with normalized schema
- **~101K tracks** with comprehensive metadata
- **Advanced indexing** for fast similarity searches
- **Relationship mapping** between artists, albums, and tracks

### **🔧 Production-Ready**
- **Docker Compose** orchestration
- **Health checks** and monitoring
- **Automated backups** and migration support
- **Horizontal scaling** capabilities

## 📁 **Project Structure**

```
spotify_recommendation_system_v2/
├── 📦 backend/                    # FastAPI application
│   ├── app/
│   │   ├── database/             # Database models & connections
│   │   ├── routers/              # API endpoints
│   │   ├── schemas/              # Pydantic models
│   │   ├── services/             # Business logic
│   │   └── import_data.py        # Data import script
│   ├── Dockerfile                # Backend container
│   └── requirements.txt          # Python dependencies
├── 🌐 frontend/                   # React application
│   ├── src/
│   │   ├── components/           # Reusable UI components
│   │   ├── pages/                # Application pages
│   │   └── App.tsx               # Main application
│   ├── Dockerfile                # Frontend container
│   └── package.json              # Node.js dependencies
├── 🤖 model-prep/                 # ML model preparation
│   ├── prepare_models.py         # Model training script
│   └── requirements.txt          # ML dependencies
├── 🗄️ database/                   # Database setup
│   └── init.sql                  # PostgreSQL initialization
├── 🐳 docker-compose.yml          # Container orchestration
├── 📋 DATABASE_SETUP.md           # Database documentation
├── 🛠️ SETUP.md                    # Detailed setup guide
└── 📖 README.md                   # This file
```

## 🗄️ **Database Schema**

The system uses a **normalized PostgreSQL schema**:

### **Core Tables**
- **`artists`** - Artist information (22-char Spotify IDs)
- **`albums`** - Album metadata with artist relationships
- **`tracks`** - Main track data with audio features
- **`audio_features`** - Low-level audio analysis (MEL, MFCC, Chroma)
- **`lyrics_features`** - Text analysis features

### **ML Tables**
- **`clusters`** - HDBSCAN cluster metadata and statistics
- **`user_interactions`** - User feedback and behavior tracking
- **`recommendation_cache`** - Performance optimization cache

### **Key Relationships**
```sql
artists (1) ── (many) albums
artists (1) ── (many) tracks
albums (1) ── (many) tracks
tracks (1) ── (1) audio_features
tracks (many) ── (1) clusters
```

## 🧠 **Machine Learning Pipeline**

### **1. Data Processing**
- **MinMax Scaling** for audio features
- **PCA Dimensionality Reduction** to 60 components
- **Feature Engineering** with log transformations

### **2. Clustering (HDBSCAN)**
```python
# Clustering on key audio features
features = ['key', 'time_signature', 'tempo', 'mode', 'valence']
clusterer = HDBSCAN(min_cluster_size=30, metric='euclidean')
```

### **3. Recommendation (KNN)**
```python
# KNN within clusters for recommendations
knn = NearestNeighbors(n_neighbors=50, metric='euclidean')
```

### **4. Results**
- **61 clusters** identified from 101K tracks
- **0.7% noise points** (unclustered tracks)
- **Cluster sizes**: 30-3000+ tracks per cluster

## 🌐 **API Endpoints**

### **Recommendations**
- `POST /api/v2/recommendations/` - Get personalized recommendations
- `POST /api/v2/recommendations/preferences` - Set user preferences

### **Songs & Search**
- `GET /api/v2/songs/` - Search and browse tracks
- `GET /api/v2/songs/random` - Get random tracks
- `GET /api/v2/songs/popular` - Get popular tracks

### **Clusters**
- `GET /api/v2/clusters/` - Browse music clusters
- `GET /api/v2/clusters/{id}` - Get cluster details
- `GET /api/v2/clusters/stats/summary` - Cluster statistics

### **Health & Monitoring**
- `GET /health` - Application health check
- `GET /api/v2/status` - Detailed system status

## 🔧 **Configuration**

### **Environment Variables**
Copy `.env.example` to `.env` and configure:

```bash
# Database
DATABASE_URL=postgresql://spotify_user:spotify_password@localhost:5432/spotify_recommendations

# API
HOST=0.0.0.0
PORT=8000
DEBUG=false

# ML Models
DEFAULT_N_RECOMMENDATIONS=12
MIN_CLUSTER_SIZE=30

# Import
IMPORT_BATCH_SIZE=1000
```

### **Docker Profiles**
- **Default**: `docker-compose up` (app only)
- **Setup**: `docker-compose --profile setup up` (includes data import)
- **Production**: `docker-compose --profile production up` (with nginx)
- **Admin**: `docker-compose --profile admin up` (includes PgAdmin)


## 📊 **Performance Metrics**

### **Response Times**
- **Recommendations**: <100ms average
- **Search queries**: <50ms average
- **Cluster analysis**: <200ms average

### **Database Performance**
- **Indexed queries** for fast similarity searches
- **Connection pooling** (20 connections)
- **Query optimization** with EXPLAIN analysis

### **Scalability**
- **Horizontal scaling** ready with read replicas
- **Database-based caching** for recommendations
- **Load balancing** via nginx proxy

## 🛠️ **Development**

### **Backend Development**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### **Frontend Development**
```bash
cd frontend
npm install
npm start
```

### **Database Management**
```bash
# Access database
docker-compose exec database psql -U spotify_user -d spotify_recommendations

# Run migrations
cd backend
alembic upgrade head

# Import data
python -m app.import_data
```

## 🚀 **Deployment**

### **Production Deployment**
```bash
# Build and deploy
docker-compose --profile production up --build -d

# With SSL certificates
docker-compose --profile production --file docker-compose.prod.yml up -d

# Monitor logs
docker-compose logs -f backend frontend
```

### **Scaling Options**
- **Horizontal scaling** with multiple backend instances
- **Database read replicas** for analytics queries
- **CDN integration** for static assets
- **Kubernetes deployment** with provided manifests

## 📋 **Requirements**

### **System Requirements**
- **Docker & Docker Compose**
- **8GB RAM** minimum (16GB recommended)
- **20GB disk space** for data and models

### **Data Requirements**
Place CSV files in `../data/raw/`:
- `spotify_tracks.csv` (~101K tracks)
- `spotify_artists.csv` 
- `spotify_albums.csv`
- `low_level_audio_features.csv`
- `lyrics_features.csv`

## 📚 **Documentation**

- **[DATABASE_SETUP.md](DATABASE_SETUP.md)** - Database schema and setup
- **[SETUP.md](SETUP.md)** - Detailed installation guide
- **API Documentation** - Available at `/api/v2/docs` when running
- **Frontend Documentation** - Component documentation in `/frontend/docs`

## 🤝 **Contributing**

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit changes**: `git commit -m 'Add amazing feature'`
4. **Push to branch**: `git push origin feature/amazing-feature`
5. **Open a Pull Request**

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 **Support**

- **Issues**: Report bugs or request features via GitHub Issues
- **Documentation**: Check our comprehensive documentation
- **Community**: Join our discussions for questions and tips

---

**Built with ❤️ for music lovers and data scientists** 