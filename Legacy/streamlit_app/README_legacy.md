# 🎵 Spotify Music Recommendation Streamlit App

[![Streamlit](https://img.shields.io/badge/Streamlit-1.40+-red?logo=streamlit)](https://streamlit.io/)
[![Python](https://img.shields.io/badge/Python-3.11+-green?logo=python)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue?logo=docker)](https://www.docker.com/)

An interactive web application for discovering music through **HDBSCAN clustering** and **audio-based recommendations** with **real-time preview capabilities**.

## 🎯 Application Overview

This Streamlit application provides an intuitive interface for exploring and discovering music using machine learning-powered recommendations. The system combines advanced clustering algorithms with audio preview functionality to offer both algorithmic and auditory song comparison.

### ✨ Key Features

#### 🎧 **Audio-First Experience**
- **30-second Spotify previews** embedded directly in the interface
- **Real-time audio comparison** between selected songs and recommendations
- **Batch audio playback** for side-by-side comparison of multiple tracks
- **Audio availability tracking** with coverage statistics

#### 🤖 **Intelligent Recommendations**
- **Global Recommendations**: Find similar songs across the entire dataset
- **Cluster-based Recommendations**: Discover songs within the same musical neighborhood
- **Similarity Scoring**: Visual representation of recommendation confidence
- **Multi-feature Analysis**: Combines audio, spectral, and metadata features

#### 🔍 **Interactive Search & Discovery**
- **Dynamic song search** with real-time filtering
- **Artist name resolution** from Spotify artist database
- **Random song discovery** for exploration
- **Visual feature comparison** between songs

#### 📊 **Data Visualization**
- **Interactive similarity charts** using Plotly
- **Audio feature comparison** with radar charts
- **Recommendation confidence visualization**
- **Cluster statistics and insights**

## 🏗️ Architecture

### Application Structure
```
streamlit_app/
├── app.py                      # Main application entry point
├── components/                 # UI Components
│   ├── __init__.py
│   ├── music_player.py        # Enhanced music player with rich media
│   ├── recommendation_cards.py # Smart recommendation cards
│   └── search_optimization.py  # Optimized search utilities
├── utils/                      # Utility Functions
│   ├── __init__.py
│   ├── data_utils.py          # Data loading and processing
│   ├── recommendations.py     # ML recommendation engines
│   └── styles.py              # CSS styling utilities
├── static/                     # Static Assets
│   └── css/
│       └── styles.css         # Application stylesheets
├── requirements.txt           # Python dependencies
├── Dockerfile                # Container configuration
├── logging_config.py         # Advanced logging system
├── spotify_api_client.py     # Spotify API integration
└── README.md                 # This documentation
```

### Core Components

#### 🎨 **User Interface Components**
- **Music Player**: Enhanced music player with rich media and interactive features
- **Recommendation Cards**: Smart recommendation cards with visual similarity indicators
- **Search Optimization**: Optimized search utilities for better performance

#### 🔧 **Utility Modules**
- **Data Utils**: Caching, loading, and data processing functions
- **Recommendations**: KNN and clustering recommendation algorithms  
- **Styles**: CSS management and dynamic styling

#### 🔄 **Data Pipeline**
1. **Data Loading**: Cached loading of CSV datasets
2. **Artist Mapping**: ID-to-name resolution using artist database
3. **Model Loading**: Pre-trained HDBSCAN and KNN models
4. **Feature Processing**: Audio and spectral feature normalization

#### 🧠 **ML Engine**
- **HDBSCAN Clustering**: Groups songs by audio similarity
- **K-Nearest Neighbors**: Finds closest matches in feature space
- **Feature Embeddings**: Pre-computed audio feature vectors
- **Similarity Metrics**: Euclidean distance in high-dimensional space

#### 🎵 **Audio System**
- **URL Validation**: Checks Spotify preview URL availability
- **Audio Streaming**: Direct browser-based playback
- **Preview Management**: Handles missing or invalid URLs gracefully
- **Coverage Analytics**: Tracks audio availability across dataset

## 🚀 Running the Application

### Option 1: Docker (Recommended)

**Prerequisites:**
- Docker and Docker Compose installed
- Spotify datasets in `../../data/raw/`
- Trained models in `../../data/models/`

```bash
# From project root directory
docker-compose up -d

# Access application
open http://localhost:8501
```

### Option 2: Local Development

**Prerequisites:**
- Python 3.11+
- Virtual environment (recommended)

```bash
# Setup environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
.\venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Run application
streamlit run app.py
```

### Option 3: Production Deployment

```bash
# Build production image
docker build -t spotify-recommender .

# Run with custom configuration
docker run -p 8501:8501 \
  -v $(pwd)/../../data:/app/data \
  -e STREAMLIT_SERVER_HEADLESS=true \
  spotify-recommender
```

## 📋 Requirements

### System Requirements
- **Memory**: 4GB+ RAM (8GB+ recommended for large datasets)
- **Storage**: 2GB+ for datasets and models
- **Network**: Internet connection for Spotify audio previews

### Data Dependencies
The application expects these datasets in `../../data/raw/`:

| File | Purpose | Required Columns |
|------|---------|-----------------|
| `spotify_tracks.csv` | Main track data | `name`, `artists_id`, `preview_url`, audio features |
| `spotify_artists.csv` | Artist information | `id`, `name` |
| `spotify_albums.csv` | Album metadata | `id`, `name`, album info |
| `low_level_audio_features.csv` | Spectral features | Track ID, MFCCs, chroma, spectral features |
| `lyrics_features.csv` | Text features | Track ID, sentiment, lyrical metrics |

### Model Dependencies
Pre-trained models required in `../../data/models/`:

| File | Description | Size |
|------|-------------|------|
| `hdbscan_model.pkl` | Clustering model | ~50MB |
| `knn_model.pkl` | Recommendation engine | ~100MB |
| `audio_embeddings.pkl` | Feature vectors | ~200MB |
| `cluster_labels.pkl` | Cluster assignments | ~10MB |
| `song_indices.pkl` | Index mapping | ~5MB |

## 🎨 User Interface

### Main Sections

#### 🎵 **Song Selection**
- **Search Interface**: Real-time song and artist search
- **Random Discovery**: Random song selection for exploration
- **Song Information**: Detailed metadata display with audio player

#### 🎧 **Audio Comparison**
- **Quick Comparison**: Top 3 recommendations with mini players
- **Selected Song Player**: Main audio preview with metadata
- **Expandable Recommendations**: Detailed view with full audio features

#### 🌍 **Global Recommendations Tab**
- **Dataset-wide Search**: Recommendations from entire collection
- **Similarity Visualization**: Interactive charts showing match confidence
- **Feature Analysis**: Detailed audio characteristic comparison

#### 🎯 **Cluster Recommendations Tab**
- **Neighborhood Discovery**: Songs from same musical cluster
- **Cluster Statistics**: Size and characteristics of song groups
- **Intra-cluster Analysis**: Similarity within musical neighborhoods

### Interactive Elements

#### 🔊 **Audio Controls**
- **Play/Pause**: Standard audio controls for each preview
- **Volume Control**: Browser-native audio management
- **Progress Tracking**: Visual progress bars for 30-second previews

#### 📊 **Visualization**
- **Similarity Bars**: Plotly charts showing recommendation scores
- **Feature Radar**: Multi-dimensional audio characteristic comparison
- **Responsive Design**: Adapts to different screen sizes

## ⚙️ Configuration

### Environment Variables
```bash
# .env file (optional)
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_SERVER_ENABLECORS=false

# Data paths
DATA_PATH=/app/data
RAW_DATA_PATH=/app/data/raw
MODELS_PATH=/app/data/models
```

### Streamlit Configuration
```toml
# .streamlit/config.toml
[server]
port = 8501
headless = true
enableCORS = false

[theme]
primaryColor = "#1DB954"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
```

## 🐛 Troubleshooting

### Common Issues

#### **Models Not Loading**
```bash
# Check if models directory exists and contains required files
ls -la ../../data/models/
```

#### **Audio Not Playing**
- Ensure internet connection for Spotify previews
- Check browser audio permissions
- Verify preview URLs in dataset

#### **Memory Issues**
- Increase Docker memory allocation
- Use smaller dataset for testing
- Check system resources

#### **Port Conflicts**
```bash
# Use different port if 8501 is occupied
streamlit run app.py --server.port 8502
```

### Docker Issues

#### **Container Won't Start**
```bash
# Check logs
docker-compose logs spotify-app

# Rebuild container
docker-compose build --no-cache
```

#### **Data Volume Issues**
```bash
# Check volume mounts
docker-compose config

# Fix permissions
sudo chown -R $USER:$USER ../../data/
```

## 🧪 Development

### Adding New Features

#### **New Component**
```python
# Create in components/
class MyNewComponent:
    def __init__(self):
        pass
    
    def render(self):
        st.write("New component")
```

#### **New Utility Function**
```python
# Add to utils/
def my_utility_function():
    return "utility result"
```

#### **Updating Styles**
```css
/* Add to static/css/styles.css */
.my-new-style {
    background: #1DB954;
    border-radius: 8px;
}
```

### Testing

```bash
# Run basic functionality test
streamlit run app.py --logger.level debug

# Test Docker build
docker build -t test-app .
docker run -p 8501:8501 test-app
```

## 📞 Support

### Resources
- **Streamlit Documentation**: https://docs.streamlit.io/
- **Docker Documentation**: https://docs.docker.com/
- **Spotify Web API**: https://developer.spotify.com/documentation/web-api/

### Common Solutions
1. **Memory errors**: Increase available RAM or use dataset sampling
2. **Model loading fails**: Verify model file integrity and paths
3. **Audio issues**: Check network connectivity and browser permissions
4. **Slow performance**: Enable caching and optimize data loading

For additional support, check the application logs and Docker container status. 