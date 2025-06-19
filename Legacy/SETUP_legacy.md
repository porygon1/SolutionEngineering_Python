# 🛠️ Setup Guide - Spotify Music Recommendation System

**Complete setup instructions for both implementations**

## 🌟 **Choose Your Implementation**

### **Version 2 (Recommended) - Production System**
**📁 Directory**: `spotify_recommendation_system_v2/`
- **Database**: PostgreSQL with normalized schema
- **Backend**: FastAPI with async support
- **Frontend**: React with TypeScript and Tailwind
- **Deployment**: Docker Compose orchestration

### **Streamlit Version - Prototype System**
**📁 Directory**: `streamlit_app/`
- **Interface**: Streamlit web app
- **Data**: CSV files with Pandas
- **Deployment**: Single container or local Python

---

## 🚀 **Quick Start - Version 2 (Recommended)**

### **Prerequisites**
- **Docker Desktop** installed and running
- **8GB RAM** minimum (16GB recommended)
- **20GB disk space** for data and containers

### **1. Setup Data**
```bash
# Ensure data files are in place:
data/raw/
├── spotify_tracks.csv          # ~101K tracks
├── spotify_artists.csv         # Artist metadata  
├── spotify_albums.csv          # Album information
├── low_level_audio_features.csv # Audio analysis
└── lyrics_features.csv         # Text analysis
```

### **2. Start the System**
```bash
# Clone and navigate
git clone <repository-url>
cd spotify_recommendation_system_v2

# Start database and import data
docker-compose --profile setup up --build

# Start the complete application
docker-compose up --build
```

### **3. Access Applications**
- **🌐 Frontend**: http://localhost:3000
- **🔧 API**: http://localhost:8000
- **📊 API Docs**: http://localhost:8000/api/v2/docs
- **🗄️ PgAdmin**: http://localhost:5050 (admin@spotify.local / admin_password)

### **4. Verify Setup**
```bash
# Check services status
docker-compose ps

# View logs
docker-compose logs backend frontend

# Test API
curl http://localhost:8000/health
```

---

## ⚡ **Quick Start - Streamlit Version**

### **Prerequisites**
- **Python 3.11+**
- **4GB RAM** minimum
- **5GB disk space**

### **1. Setup Environment**
```bash
# Navigate to streamlit app
cd streamlit_app

# Create virtual environment
python -m venv venv

# Activate environment
source venv/bin/activate  # Linux/macOS
# or
.\venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### **2. Prepare Models**
```bash
# Run model training notebook
jupyter notebook ../scripts/Models/HDBSCAN_Clusters_KNN.ipynb

# Or use Docker for model preparation
docker-compose --profile legacy up streamlit-app
```

### **3. Run Application**
```bash
# Start Streamlit
streamlit run main.py

# Access application
open http://localhost:8501
```

---

## 🛠️ **Development Setup - Version 2**

### **Backend Development**
```bash
cd spotify_recommendation_system_v2/backend

# Setup Python environment
python -m venv venv
source venv/bin/activate  # or .\venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Start database
docker-compose up database -d

# Run data import
python -m app.import_data

# Start FastAPI with hot reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### **Frontend Development**
```bash
cd spotify_recommendation_system_v2/frontend

# Install Node.js dependencies
npm install

# Start development server
npm start

# Application available at http://localhost:3000
```

### **Database Management**
```bash
# Access PostgreSQL
docker-compose exec database psql -U spotify_user -d spotify_recommendations

# View database via PgAdmin
open http://localhost:5050

# Backup database
docker-compose exec database pg_dump -U spotify_user spotify_recommendations > backup.sql

# Restore database
docker-compose exec -T database psql -U spotify_user spotify_recommendations < backup.sql
```

---

## 📊 **Data Setup**

### **Required Files**
Place these CSV files in `data/raw/`:

| File | Description | Expected Size |
|------|-------------|---------------|
| `spotify_tracks.csv` | Main track data with audio features | ~101K rows |
| `spotify_artists.csv` | Artist metadata and genres | ~10K rows |
| `spotify_albums.csv` | Album information | ~20K rows |
| `low_level_audio_features.csv` | Audio analysis (MEL, MFCC, etc.) | ~101K rows |
| `lyrics_features.csv` | Text analysis features | ~101K rows |

### **Data Validation**
```bash
# Check data files
ls -la data/raw/

# Validate with Python
python -c "
import pandas as pd
import os

files = ['spotify_tracks.csv', 'spotify_artists.csv', 'spotify_albums.csv', 
         'low_level_audio_features.csv', 'lyrics_features.csv']

for file in files:
    path = f'data/raw/{file}'
    if os.path.exists(path):
        df = pd.read_csv(path)
        print(f'✅ {file}: {len(df):,} rows, {len(df.columns)} columns')
    else:
        print(f'❌ Missing: {file}')
"
```

---

## 🐳 **Docker Configuration**

### **Environment Variables**
Create `.env` file in `spotify_recommendation_system_v2/`:
```bash
# Copy example
cp .env.example .env

# Edit configuration
nano .env
```

### **Service Profiles**
```bash
# Default (app only)
docker-compose up

# With data import
docker-compose --profile setup up

# Production with nginx
docker-compose --profile production up

# With database admin
docker-compose --profile admin up


```

### **Useful Commands**
```bash
# View service status
docker-compose ps

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Scale services
docker-compose up --scale backend=3

# Clean restart
docker-compose down -v
docker-compose up --build
```

---

## 🔧 **Configuration Options**

### **Version 2 Configuration**
Edit `spotify_recommendation_system_v2/.env`:
```bash
# Database
DATABASE_URL=postgresql://spotify_user:spotify_password@localhost:5432/spotify_recommendations

# API Settings
HOST=0.0.0.0
PORT=8000
DEBUG=false
LOG_LEVEL=INFO

# ML Configuration
DEFAULT_N_RECOMMENDATIONS=12
MIN_CLUSTER_SIZE=30
IMPORT_BATCH_SIZE=1000

# Performance
CACHE_TTL=3600
MAX_WORKERS=4
```

### **Streamlit Configuration**
Edit `streamlit_app/.streamlit/config.toml`:
```toml
[server]
port = 8501
enableCORS = false

[theme]
primaryColor = "#1DB954"
backgroundColor = "#121212"
secondaryBackgroundColor = "#1F1F1F"
textColor = "#FFFFFF"
```

---

## 🧪 **Testing**

### **Backend Tests**
```bash
cd spotify_recommendation_system_v2/backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test
pytest tests/test_models.py
```

### **Frontend Tests**
```bash
cd spotify_recommendation_system_v2/frontend

# Run all tests
npm test

# Run with coverage
npm test -- --coverage

# Build test
npm run build
```

### **Integration Tests**
```bash
# Test complete system
docker-compose -f docker-compose.test.yml up --abort-on-container-exit

# API health check
curl http://localhost:8000/health

# Frontend health check
curl http://localhost:3000
```

---

## 🚨 **Troubleshooting**

### **Common Issues**

#### **Docker Issues**
```bash
# Docker not running
# Solution: Start Docker Desktop

# Port conflicts
# Solution: Stop conflicting services or change ports in docker-compose.yml

# Out of disk space
docker system prune -f
docker volume prune -f
```

#### **Database Issues**
```bash
# Connection refused
# Check if PostgreSQL is running:
docker-compose ps database

# Permission denied
# Reset PostgreSQL data:
docker-compose down -v
docker-compose up database
```

#### **Import Issues**
```bash
# CSV files not found
# Ensure files are in data/raw/ directory

# Import fails
# Check CSV format and run with verbose logging:
cd backend
python -m app.import_data --log-level DEBUG
```

#### **Frontend Issues**
```bash
# Node modules issues
cd frontend
rm -rf node_modules package-lock.json
npm install

# Build fails
# Check Node.js version (requires 16+)
node --version
```

### **Performance Issues**
```bash
# High memory usage
# Reduce IMPORT_BATCH_SIZE in .env
# Add more RAM or use swap

# Slow responses
# Enable Redis caching
docker-compose --profile cache up

# Check database performance
docker-compose exec database psql -U spotify_user -d spotify_recommendations -c "SELECT * FROM pg_stat_activity;"
```

---

## 📚 **Additional Resources**

### **Documentation**
- **[Database Setup](spotify_recommendation_system_v2/DATABASE_SETUP.md)** - PostgreSQL schema details
- **[API Documentation](http://localhost:8000/api/v2/docs)** - Interactive API explorer
- **[Docker Setup](DOCKER_SETUP.md)** - Advanced Docker configuration

### **Development Tools**
- **VSCode Extensions**: Python, Docker, PostgreSQL
- **Database Tools**: PgAdmin, DBeaver, DataGrip
- **API Testing**: Postman, Insomnia, curl

### **Monitoring**
```bash
# System resources
docker stats

# Application logs  
docker-compose logs -f

# Database monitoring
docker-compose exec database psql -U spotify_user -d spotify_recommendations -c "SELECT * FROM pg_stat_statements LIMIT 10;"
```

---

## 🤝 **Getting Help**

### **Support Channels**
- **GitHub Issues**: Report bugs and request features
- **Documentation**: Check comprehensive docs in each directory
- **Logs**: Always check application logs first

### **Before Asking for Help**
1. **Check logs**: `docker-compose logs -f`
2. **Verify data**: Ensure CSV files are present and valid
3. **Test connectivity**: Verify database and API connections
4. **Review configuration**: Check .env files and settings

---

**🎵 Ready to discover music with AI? Choose your implementation and get started!**