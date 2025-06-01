# 🎵 Spotify Music Recommendation System

[![Docker](https://img.shields.io/badge/Docker-Enabled-blue?logo=docker)](https://www.docker.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Latest-red?logo=streamlit)](https://streamlit.io/)
[![Python](https://img.shields.io/badge/Python-3.11+-green?logo=python)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

An intelligent music recommendation system powered by **HDBSCAN clustering** and **K-Nearest Neighbors**, featuring **audio preview capabilities** for direct song comparison. Built with Python, Streamlit, and deployed with Docker.

## 🎯 Project Overview

This system analyzes Spotify track data using advanced machine learning techniques to provide highly accurate music recommendations. Users can:

- **🔍 Search & Discover**: Find songs by name or artist
- **🎧 Listen & Compare**: Play 30-second Spotify previews directly in the app
- **🎯 Smart Recommendations**: Get suggestions based on audio similarity within clusters or globally
- **📊 Visual Analysis**: Explore similarity scores and audio features interactively

## ✨ Key Features

### 🎵 Audio-First Experience
- **Direct Audio Playback**: 30-second Spotify previews for immediate comparison
- **Side-by-Side Comparison**: Listen to selected song and recommendations simultaneously
- **Audio Statistics**: Coverage metrics and availability tracking

### 🤖 Advanced ML Pipeline
- **HDBSCAN Clustering**: Groups songs by audio similarity patterns
- **K-Nearest Neighbors**: Finds most similar tracks within clusters or globally
- **Multi-Feature Analysis**: Uses audio features, low-level spectral data, and more

### 🎨 Interactive Interface
- **Real-time Search**: Dynamic song search with artist name resolution
- **Visual Similarity**: Interactive charts showing recommendation scores
- **Responsive Design**: Modern UI with audio controls and expandable sections

## 📁 Project Structure

```
📦 Spotify-Music-Recommendation-System/
├── 🎵 streamlit_app/                 # Main Streamlit application
│   ├── app.py                        # Main application with audio features
│   ├── Dockerfile                    # Container configuration
│   ├── requirements.txt              # Python dependencies
│   └── README.md                     # App-specific documentation
├── 📊 scripts/                       # Analysis and modeling scripts
│   ├── Models/                       # Machine learning models
│   │   ├── HDBSCAN_Clusters_KNN.ipynb   # Main model training notebook
│   │   └── requirements.txt          # Model training dependencies
│   └── exploration_analysis/         # Exploratory data analysis
├── 📂 data/                          # Data storage
│   ├── raw/                          # Original Spotify datasets
│   │   ├── spotify_tracks.csv        # Main track data with preview URLs
│   │   ├── spotify_artists.csv       # Artist information
│   │   ├── spotify_albums.csv        # Album metadata
│   │   ├── low_level_audio_features.csv  # Spectral and audio features
│   │   └── lyrics_features.csv       # Lyrical analysis features
│   └── models/                       # Trained ML models
│       ├── hdbscan_model.pkl         # Clustering model
│       ├── knn_model.pkl             # K-NN recommendation model
│       ├── audio_embeddings.pkl      # Feature embeddings
│       ├── cluster_labels.pkl        # Cluster assignments
│       └── song_indices.pkl          # Song index mapping
├── 🐳 Docker Configuration
│   ├── docker-compose.yml            # Multi-service orchestration
│   ├── .dockerignore                 # Docker ignore patterns
│   └── DOCKER_SETUP.md               # Docker deployment guide
└── 📚 Documentation
    ├── README.md                     # This file
    ├── SETUP.md                      # Development setup guide
    └── .gitignore                    # Git ignore patterns
```

## 🚀 Quick Start

### Option 1: Docker Deployment (Recommended)

**Prerequisites:**
- Docker and Docker Compose
- Spotify dataset files in `data/raw/`
- Trained models in `data/models/`

```bash
# Clone the repository
git clone <your-repo-url>
cd spotify-music-recommendation-system

# Start the application
docker-compose up -d

# Access the app
open http://localhost:8501
```

### Option 2: Local Development

**Prerequisites:**
- Python 3.11+
- pip package manager

```bash
# Clone and setup
git clone <your-repo-url>
cd spotify-music-recommendation-system

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or .\venv\Scripts\activate on Windows

# Install dependencies
cd streamlit_app
pip install -r requirements.txt

# Run the application
streamlit run app.py
```

## 🎯 How It Works

### 1. **Data Processing**
- Analyzes audio features (tempo, energy, danceability, etc.)
- Processes low-level spectral features (MFCCs, chroma, spectral contrast)
- Integrates lyrical and metadata features

### 2. **Clustering with HDBSCAN**
- Groups songs into clusters based on audio similarity
- Identifies noise points and outliers
- Creates cohesive musical neighborhoods

### 3. **Recommendation Engine**
- **Global Mode**: Finds similar songs across entire dataset
- **Cluster Mode**: Recommends within same musical cluster
- Uses K-Nearest Neighbors for similarity ranking

### 4. **Audio Comparison**
- Streams 30-second Spotify previews
- Enables direct A/B testing of recommendations
- Validates algorithmic similarity with human perception

## 📊 Dataset

The system uses multiple Spotify datasets:

| Dataset | Records | Features | Purpose |
|---------|---------|-----------|---------|
| **Tracks** | ~100K+ | 30+ | Main dataset with preview URLs |
| **Artists** | ~50K+ | 8 | Artist name resolution |
| **Audio Features** | ~100K+ | 190+ | Low-level spectral analysis |
| **Lyrics** | ~100K+ | 7 | Text-based features |

**Key Features Used:**
- Audio: danceability, energy, valence, tempo, acousticness
- Spectral: MFCCs, chroma vectors, spectral contrast
- Metadata: popularity, duration, key, mode

## 🎵 Audio Features

### 🔊 Preview Capabilities
- **30-second previews** from Spotify's API
- **Real-time streaming** directly in browser
- **Batch comparison** with multiple simultaneous players

### 📈 Coverage Statistics
- Automatic calculation of audio availability
- Preview URL validation and error handling
- Coverage metrics displayed in app interface

### 🎧 Comparison Tools
- **Quick Comparison**: Top 3 recommendations side-by-side
- **Detailed Analysis**: Expandable sections with full audio features
- **Similarity Correlation**: Visual matching of algorithmic and audio similarity

## 🛠️ Technology Stack

### **Backend**
- **Python 3.11+**: Core application language
- **scikit-learn 1.6+**: Machine learning framework
- **HDBSCAN**: Density-based clustering algorithm
- **pandas 2.2+**: Data manipulation and analysis
- **NumPy 2.1+**: Numerical computing

### **Frontend**
- **Streamlit 1.40+**: Interactive web application framework
- **Plotly 6.0+**: Interactive visualizations and charts
- **HTML/CSS**: Custom styling and responsive design

### **Deployment**
- **Docker**: Containerized deployment
- **Docker Compose**: Multi-service orchestration
- **Linux/Windows**: Cross-platform compatibility

## 📈 Performance Metrics

### **Model Performance**
- **Clustering Quality**: Silhouette score and cluster validation
- **Recommendation Accuracy**: User feedback and audio similarity correlation
- **Coverage**: Percentage of tracks with audio previews

### **System Performance**
- **Response Time**: < 2 seconds for recommendations
- **Memory Usage**: Optimized for large datasets
- **Concurrent Users**: Supports multiple simultaneous sessions

## 🔧 Development

### **Running Tests**
```bash
# Model validation
python scripts/Models/validate_models.py

# App testing
cd streamlit_app
python -m pytest tests/
```

### **Model Training**
```bash
# Open Jupyter notebook for model training
jupyter notebook scripts/Models/HDBSCAN_Clusters_KNN.ipynb
```

### **Data Updates**
1. Place new datasets in `data/raw/`
2. Run model training notebook
3. Export models to `data/models/`
4. Restart application

## 📚 Documentation

- **[SETUP.md](SETUP.md)**: Development environment setup
- **[DOCKER_SETUP.md](DOCKER_SETUP.md)**: Docker deployment guide
- **[streamlit_app/README.md](streamlit_app/README.md)**: Application-specific docs
- **[Model Notebook](scripts/Models/HDBSCAN_Clusters_KNN.ipynb)**: Model training and validation

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Spotify** for providing the Web API and preview capabilities
- **scikit-learn** community for excellent ML tools
- **Streamlit** team for the amazing web framework
- **HDBSCAN** developers for the clustering algorithm

## 📞 Support

- **Issues**: [GitHub Issues](../../issues)
- **Discussions**: [GitHub Discussions](../../discussions)
- **Documentation**: See docs/ directory

---

**Built with ❤️ for music lovers and data scientists**


