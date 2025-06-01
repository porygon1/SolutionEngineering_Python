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
├── app.py                    # Main application file (708 lines)
├── requirements.txt          # Python dependencies
├── Dockerfile               # Container configuration
└── README.md               # This documentation
```

### Core Components

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
- Spotify datasets in `../data/raw/`
- Trained models in `../data/models/`

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
  -v $(pwd)/../data:/app/data \
  -e STREAMLIT_SERVER_HEADLESS=true \
  spotify-recommender
```

## 📋 Requirements

### System Requirements
- **Memory**: 4GB+ RAM (8GB+ recommended for large datasets)
- **Storage**: 2GB+ for datasets and models
- **Network**: Internet connection for Spotify audio previews

### Data Dependencies
The application expects these datasets in `../data/raw/`:

| File | Purpose | Required Columns |
|------|---------|-----------------|
| `spotify_tracks.csv` | Main track data | `name`, `artists_id`, `preview_url`, audio features |
| `spotify_artists.csv` | Artist information | `id`, `name` |
| `spotify_albums.csv` | Album metadata | `id`, `name`, album info |
| `low_level_audio_features.csv` | Spectral features | Track ID, MFCCs, chroma, spectral features |
| `lyrics_features.csv` | Text features | Track ID, sentiment, lyrical metrics |

### Model Dependencies
Pre-trained models required in `../data/models/`:

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
enableCORS = false
enableXsrfProtection = false

[theme]
primaryColor = "#1DB954"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"

[client]
showErrorDetails = true
```

## 🧪 Testing & Validation

### Manual Testing
```bash
# Test data loading
python -c "import app; print('Data loading test passed')"

# Test model loading
python -c "import app; models = app.load_all_models(); print(f'Loaded {len(models)} models')"

# Test audio URL validation
python -c "import app; print(app.check_audio_url('https://p.scdn.co/mp3-preview/test'))"
```

### Performance Testing
```bash
# Memory usage monitoring
python -c "
import psutil
import app
process = psutil.Process()
print(f'Memory usage: {process.memory_info().rss / 1024 / 1024:.1f} MB')
"

# Recommendation speed test
python -c "
import time
import app
models = app.load_all_models()
start = time.time()
# Test recommendation generation
print(f'Recommendation time: {time.time() - start:.2f}s')
"
```

## 🔧 Customization

### Adding New Features
1. **Audio Features**: Modify feature extraction in data processing
2. **Recommendation Algorithms**: Extend the ML pipeline
3. **UI Components**: Add new Streamlit widgets and layouts
4. **Visualization**: Create additional Plotly charts

### Styling Customization
```python
# Custom CSS injection
st.markdown("""
<style>
    .custom-audio-player {
        border-radius: 15px;
        padding: 20px;
        background: linear-gradient(45deg, #1DB954, #1ed760);
    }
</style>
""", unsafe_allow_html=True)
```

### Data Integration
```python
# Adding new data sources
@st.cache_data
def load_custom_data(file_path):
    """Load additional datasets"""
    return pd.read_csv(file_path)

# Integration example
custom_data = load_custom_data("data/raw/custom_features.csv")
```

## 📈 Performance Optimization

### Caching Strategy
- **@st.cache_data**: Data loading and processing
- **@st.cache_resource**: Model loading and expensive computations
- **Session State**: User selections and temporary data

### Memory Management
```python
# Efficient data handling
- Use pandas chunks for large datasets
- Implement lazy loading for audio features
- Clear unused variables in functions
```

### Speed Optimization
```python
# Fast recommendations
- Pre-compute embeddings
- Use efficient similarity metrics
- Implement result pagination
```

## 🚨 Troubleshooting

### Common Issues

#### **Audio Not Playing**
```bash
# Check preview URL format
df['preview_url'].head()

# Validate URLs
df['preview_url'].apply(lambda x: x.startswith('http')).sum()
```

#### **Model Loading Errors**
```bash
# Verify model files exist
ls -la ../data/models/

# Check file permissions
stat ../data/models/hdbscan_model.pkl
```

#### **Memory Issues**
- Reduce dataset size for testing
- Increase Docker memory allocation
- Use streaming data processing

#### **Slow Performance**
- Enable Streamlit caching
- Optimize data loading
- Use smaller model embeddings

### Debug Mode
```bash
# Run with debugging
streamlit run app.py --logger.level=debug

# Check Streamlit logs
tail -f ~/.streamlit/logs/streamlit.log
```

## 📦 Dependencies

### Core Dependencies (requirements.txt)
```txt
streamlit>=1.40.0          # Web application framework
pandas>=2.2.0             # Data manipulation
numpy>=2.1.0              # Numerical computing
scikit-learn>=1.6.0       # Machine learning
hdbscan>=0.8.33           # Clustering algorithm
umap-learn>=0.5.4         # Dimensionality reduction
plotly>=6.0.0             # Interactive visualizations
joblib>=1.4.0             # Model serialization
requests>=2.31.0          # HTTP requests
```

### Optional Dependencies
```bash
# Development tools
pip install black flake8 pytest streamlit-profiler

# Additional visualization
pip install seaborn matplotlib altair

# Performance monitoring
pip install memory-profiler psutil
```

## 🔄 Updates & Maintenance

### Regular Updates
1. **Dependency Updates**: Monthly security and feature updates
2. **Model Retraining**: Quarterly with new data
3. **Performance Monitoring**: Weekly performance reviews
4. **User Feedback**: Continuous UI/UX improvements

### Version Control
```bash
# Tag releases
git tag -a v1.0.0 -m "Audio preview release"

# Track dependencies
pip freeze > requirements.txt

# Document changes
# See CHANGELOG.md for version history
```

## 📄 License & Credits

This application is part of the **Spotify Music Recommendation System** project.

### Acknowledgments
- **Spotify Web API** for audio preview capabilities
- **Streamlit** team for the excellent framework
- **scikit-learn** community for ML tools
- **Plotly** for interactive visualizations

### Data Attribution
- Spotify dataset used under academic/research license
- Audio previews © Spotify AB
- Artist and track metadata from Spotify

---

**For more information, see the [main project README](../README.md) and [setup guide](../SETUP.md).** 