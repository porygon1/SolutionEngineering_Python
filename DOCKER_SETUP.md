# 🐳 Docker Setup for Spotify Recommendation System

This guide explains how to run the Spotify Music Recommendation System using Docker.

## 📁 Required Directory Structure

Before running, ensure your project has this structure:

```
├── data/
│   ├── raw/                          # Raw data files
│   │   ├── spotify_tracks.csv
│   │   ├── spotify_artists.csv
│   │   ├── spotify_albums.csv
│   │   ├── lyrics_features.csv
│   │   └── low_level_audio_features.csv
│   └── models/                       # Generated models from HDBSCAN notebook
│       ├── hdbscan_model.pkl
│       ├── knn_model.pkl
│       ├── audio_embeddings.pkl
│       ├── cluster_labels.pkl
│       └── song_indices.pkl
├── scripts/
│   └── Models/
│       ├── requirements.txt
│       └── HDBSCAN_Clusters_KNN.ipynb
├── streamlit_app/
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml
└── DOCKER_SETUP.md
```

## 🚀 Quick Start

### Step 1: Generate Models from HDBSCAN Notebook

**Important**: Before running the Docker application, you need to run the HDBSCAN notebook to generate the required model files.

1. Open `scripts/Models/HDBSCAN_Clusters_KNN.ipynb`
2. Run all cells to train the models
3. Ensure the following files are exported to `data/models/`:
   - `hdbscan_model.pkl` - HDBSCAN clustering model
   - `knn_model.pkl` - KNN recommendation model
   - `audio_embeddings.pkl` - Audio feature embeddings
   - `cluster_labels.pkl` - Cluster labels for each song
   - `song_indices.pkl` - Song metadata mapping

### Step 2: Start the Application

```bash
# Start the recommendation system
docker-compose up
```

### Step 3: Access the Application

- **Recommendation System**: http://localhost:8501
- **Health Check**: http://localhost:8501/_stcore/health

## 📋 Available Services

### 🎵 Streamlit Recommendation System
**Container**: `spotify-recommendation-system`
**Port**: 8501
**Purpose**: Main recommendation web application

```bash
# Start the Streamlit app
docker-compose up

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f streamlit
```

## 🔧 Model Requirements

The application expects these model files in `data/models/`:

| File | Description | Required |
|------|-------------|----------|
| `hdbscan_model.pkl` | HDBSCAN clustering model | Optional |
| `knn_model.pkl` | K-Nearest Neighbors model | ✅ Required |
| `audio_embeddings.pkl` | Feature embeddings | ✅ Required |
| `cluster_labels.pkl` | Cluster assignments | Optional |
| `song_indices.pkl` | Song metadata mapping | Optional |

**Note**: The app will work with just the KNN model and embeddings, but clustering features require the HDBSCAN model and labels.

## 🔍 Monitoring and Debugging

### Check Service Status
```bash
docker-compose ps
```

### View Logs
```bash
# All services
docker-compose logs

# Real-time logs
docker-compose logs -f streamlit
```

### Health Checks
```bash
# Check if Streamlit is healthy
curl http://localhost:8501/_stcore/health

# Check container health
docker-compose ps
```

### Restart Services
```bash
# Restart
docker-compose restart

# Stop and start
docker-compose down && docker-compose up -d
```

## 🛠️ Troubleshooting

### Models Not Found Error
1. Ensure raw data files exist in `data/raw/`
2. Run the HDBSCAN notebook completely:
   ```bash
   # Install notebook dependencies
   pip install -r scripts/Models/requirements.txt
   
   # Run Jupyter notebook
   jupyter notebook scripts/Models/HDBSCAN_Clusters_KNN.ipynb
   ```
3. Check model files were created:
   ```bash
   ls -la data/models/
   ```

### Missing Essential Models
The app requires at minimum:
- `knn_model.pkl`
- `audio_embeddings.pkl`

If these are missing, add export code to your notebook:
```python
# At the end of your HDBSCAN notebook
import pickle
import os

os.makedirs('../../data/models', exist_ok=True)

# Export KNN model
with open('../../data/models/knn_model.pkl', 'wb') as f:
    pickle.dump(your_knn_model, f)

# Export embeddings
with open('../../data/models/audio_embeddings.pkl', 'wb') as f:
    pickle.dump(your_embeddings, f)
```

### Permission Issues
```bash
# Fix permissions on data directory
sudo chown -R $USER:$USER data/
chmod -R 755 data/
```

### Port Conflicts
Change ports in `docker-compose.yml` if 8501 is in use:
```yaml
ports:
  - "8502:8501"  # Change external port
```

### Memory Issues
- Increase Docker memory allocation (4GB+ recommended)
- Large audio embeddings may require more memory

## 🧹 Cleanup

### Remove Containers
```bash
docker-compose down
```

### Remove Containers and Volumes
```bash
docker-compose down -v
```

### Remove Images
```bash
docker-compose down --rmi all
```

### Full Cleanup
```bash
docker-compose down -v --rmi all
docker system prune -f
```

## 🔧 Customization

### Environment Variables
Add to `docker-compose.yml` under `environment:`:

```yaml
environment:
  - STREAMLIT_SERVER_PORT=8501
  - STREAMLIT_SERVER_HEADLESS=true
```

### Volume Mounts
Modify volume mounts in `docker-compose.yml`:

```yaml
volumes:
  - ./custom_data:/app/data:ro
  - ./custom_models:/app/data/models:ro
```

## 📱 Development Workflow

1. **Prepare Data**: Ensure raw data files are in `data/raw/`

2. **Generate Models**: 
   ```bash
   # Install dependencies
   pip install -r scripts/Models/requirements.txt
   
   # Run HDBSCAN notebook
   jupyter notebook scripts/Models/HDBSCAN_Clusters_KNN.ipynb
   ```

3. **Test Locally**:
   ```bash
   # Start application
   docker-compose up
   
   # Test at http://localhost:8501
   ```

4. **Production Deployment**:
   ```bash
   docker-compose up -d
   ```

## 🎯 Features

The recommendation system provides:

- **🌍 Global Recommendations**: Similar songs from the entire dataset
- **🎯 Cluster-Based Recommendations**: Songs from the same musical cluster
- **🔍 Search Functionality**: Find songs by name or artist
- **📊 Similarity Visualization**: Visual representation of song similarity
- **🎲 Random Discovery**: Random song selection for exploration

This simplified setup focuses on the core HDBSCAN clustering and KNN recommendation functionality! 