# 🎵 Spotify Music Recommendation - AI-Powered Music Discovery System

[![Docker](https://img.shields.io/badge/Docker-Enabled-blue?logo=docker)](https://www.docker.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Latest-red?logo=streamlit)](https://streamlit.io/)
[![Python](https://img.shields.io/badge/Python-3.11+-green?logo=python)](https://www.python.org/)
[![Spotify API](https://img.shields.io/badge/Spotify-API_Integrated-1DB954?logo=spotify)](https://developer.spotify.com/documentation/web-api)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

A **modern music recommendation system** powered by **HDBSCAN clustering** and **K-Nearest Neighbors**, featuring a **Spotify-inspired interface**, **rich media integration**, and **AI-powered insights** for immersive music discovery. Built with Python, Streamlit, and deployed with Docker.

## 🎯 Project Overview

The **Spotify Music Recommendation** system analyzes Spotify track data using advanced machine learning techniques to provide highly accurate music recommendations with a beautiful, modern interface. Users can:

- **🎵 Immersive Music Experience**: Album artwork, audio features, and rich metadata display
- **🔍 Smart Discovery**: AI-powered search with mood-based browsing (Popular, Danceable, Energetic, Chill)
- **🤖 Intelligent Recommendations**: Advanced similarity matching with cluster-based and global recommendations
- **📊 Rich Visualizations**: Interactive audio features comparison and analytics
- **🎧 Spotify Integration**: Enhanced track information, album covers, and external links

## ✨ Key Features

### 🎨 Modern Spotify-Inspired UI
- **Dark Theme**: Spotify-inspired design with beautiful gradients and animations
- **Responsive Layout**: Clean, modern interface that adapts to any screen size
- **Interactive Elements**: Hover effects, smooth transitions, and modern typography
- **Rich Media Cards**: Album artwork and smart feature badges

### 🎵 Enhanced Music Experience
- **Album Artwork Display**: Real album covers from Spotify API with beautiful fallbacks
- **Track Information**: Comprehensive metadata including duration, popularity, and audio features
- **Smart Organization**: Featured tracks, search results, and personalized recommendations
- **Audio Feature Analysis**: Visual representation of track characteristics

### 🤖 AI-Powered Recommendations
- **Cluster-Based Recommendations**: Find similar tracks within the same musical style
- **Global Recommendations**: Discover similar songs across the entire dataset
- **Smart Similarity Matching**: Advanced algorithms for accurate music matching
- **Recommendation Insights**: Detailed analysis of why tracks were recommended

### 🔍 Intelligent Discovery
- **Mood-Based Browsing**: Quick discovery buttons for different musical moods
- **Enhanced Search**: Intelligent ranking with artist and track matching
- **Multiple View Modes**: Featured tracks, search results, and recommendations
- **Quick Actions**: Popular, Danceable, Energetic, and Chill music discovery

## 📁 Project Structure

```
📦 Spotify-Music-Recommendation/
├── 🎵 streamlit_app/                 # Streamlit application
│   ├── app.py                        # Main Spotify Music Recommendation app
│   ├── components/                   # UI Components
│   │   ├── sidebar.py                # Navigation and search sidebar
│   │   ├── track_grid.py             # Track display grid
│   │   ├── music_player.py           # Music player components
│   │   └── recommendations.py        # AI recommendations display
│   ├── utils/                        # Utility modules
│   │   ├── data_utils.py             # Data loading and caching
│   │   ├── recommendations.py        # AI recommendation engine
│   │   └── spotify_utils.py          # Spotify API utilities
│   ├── static/                       # Static assets
│   │   └── css/                      # Custom styling
│   ├── spotify_api_client.py         # Spotify Web API integration
│   ├── .streamlit/                   # Streamlit configuration
│   │   └── config.toml               # App theme and performance settings
│   ├── Dockerfile                    # Container configuration
│   └── requirements.txt              # Python dependencies
├── 📊 scripts/                       # Analysis and modeling scripts
│   ├── Models/                       # Machine learning models
│   │   └── HDBSCAN_Clusters_KNN.ipynb   # Main model training notebook
│   └── exploration_analysis/         # Exploratory data analysis
├── 📂 data/                          # Data storage
│   ├── raw/                          # Original Spotify datasets
│   │   ├── spotify_tracks.csv        # Main track data
│   │   └── spotify_artists.csv       # Artist information
│   └── models/                       # Trained ML models
│       ├── hdbscan_model.pkl         # Clustering model
│       ├── knn_model.pkl             # K-NN recommendation model
│       ├── audio_embeddings.pkl      # Feature embeddings
│       ├── cluster_labels.pkl        # Cluster assignments
│       └── song_indices.pkl          # Song index mapping
├── 🐳 Docker Configuration
│   ├── docker-compose.yml           # Multi-service orchestration
│   └── .dockerignore                # Docker ignore patterns
└── 📚 Documentation
    ├── README.md                     # This file
    ├── SETUP.md                      # Development setup guide
    ├── DOCKER_SETUP.md              # Docker deployment guide
    ├── SPOTIFY_SETUP.md             # Spotify API setup guide
    ├── CONTRIBUTING.md               # Contribution guidelines
    └── LICENSE                       # MIT License
```

## 🚀 Quick Start

### Option 1: Docker Deployment (Recommended)

**Prerequisites:**
- Docker and Docker Compose
- Spotify dataset files in `data/raw/`
- Trained models in `data/models/`
- *(Optional)* Spotify API credentials for enhanced features

```bash
# Clone the repository
git clone <your-repo-url>
cd spotify-music-recommendation

# Start the application
docker-compose up -d

# Access the Spotify Music Recommendation system
open http://localhost:8501
```

### Option 2: Local Development

**Prerequisites:**
- Python 3.11+
- pip package manager
- *(Optional)* Spotify API credentials

```bash
# Clone and setup
git clone <your-repo-url>
cd spotify-music-recommendation

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or .\venv\Scripts\activate on Windows

# Install dependencies
cd streamlit_app
pip install -r requirements.txt

# Configure environment variables
export DATA_PATH="data"  # or set in .env file

# Run the application
streamlit run app.py
```

### 🎵 Enable Enhanced Spotify Features

**Available Enhanced Features:**
- ✅ **Album Artwork**: High-quality cover images for visual discovery
- ✅ **Artist Information**: Profile images, follower counts, genres, and metadata
- ✅ **Track Metadata**: Detailed track information and enhanced audio features
- ✅ **External Links**: Direct links to Spotify for full playback

**To enable enhanced features:**

1. **Create a Spotify App** at [developer.spotify.com](https://developer.spotify.com/dashboard/applications)
2. **Get your credentials** (Client ID and Client Secret)
3. **Configure credentials:**
   - **Environment file**: Add to `.env` file
   - **Streamlit secrets**: Add to `.streamlit/secrets.toml`
   - **Environment variables**: Set `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET`

4. **Restart the application** to activate enhanced features

*The Spotify Music Recommendation system works perfectly without Spotify API credentials, providing a rich experience with your dataset's built-in features.*

## 🎯 How It Works

### 1. **Data Processing**
- **Audio Features**: tempo, energy, danceability, valence, acousticness, and more
- **Feature Engineering**: Smart feature comparison and similarity scoring
- **Rich Metadata**: Track popularity, duration, musical key, and mode information

### 2. **AI-Powered Clustering**
- **HDBSCAN Algorithm**: Groups songs into cohesive musical clusters
- **Smart Similarity**: Identifies tracks with similar "musical DNA"
- **Noise Detection**: Handles outliers and unique tracks intelligently

### 3. **Intelligent Recommendation Engine**
- **Global Similarity**: Finds similar songs across the entire dataset
- **Cluster-Based**: Recommends within the same musical style/genre
- **K-Nearest Neighbors**: Advanced similarity matching algorithms

### 4. **Rich User Experience**
- **Visual Discovery**: Album artwork and audio features visualization
- **Smart UI**: Responsive interface with Spotify-inspired design
- **Interactive Elements**: Seamless navigation and track selection

## 📊 Dataset Features Utilized

### 🎵 Track Information
- **Basic metadata**: Track name, artist, album, duration, popularity
- **Musical properties**: Key, mode, tempo, time signature
- **Audio characteristics**: All Spotify audio features (danceability, energy, valence, etc.)

### 🎨 Rich Media Content
- **Album artwork**: High-quality cover images via Spotify API
- **Artist information**: Enhanced metadata and profile information
- **External links**: Direct links to Spotify for full track access

### 📊 Advanced Analytics
- **Feature visualization**: Audio characteristics display
- **Similarity scoring**: Advanced matching algorithms
- **Recommendation insights**: AI-powered explanations and suggestions

## 🛠️ Technology Stack

### **Backend**
- **Python 3.11+**: Core application language
- **scikit-learn**: Machine learning framework
- **HDBSCAN**: Density-based clustering algorithm
- **pandas**: Data manipulation and analysis
- **NumPy**: Numerical computing

### **Frontend**
- **Streamlit**: Interactive web application framework
- **HTML/CSS**: Custom styling and responsive design
- **JavaScript**: Interactive elements and user experience

### **API Integration**
- **Spotify Web API**: Enhanced track and artist information
- **RESTful services**: External data integration

### **Deployment**
- **Docker**: Containerized deployment
- **Docker Compose**: Multi-service orchestration
- **Cross-platform**: Linux/Windows/macOS compatibility

## 📈 Performance Metrics

### **Model Performance**
- **Clustering Quality**: Silhouette score and cluster validation
- **Recommendation Accuracy**: Audio similarity correlation
- **Coverage**: Percentage of tracks with enhanced metadata

### **System Performance**
- **Response Time**: < 2 seconds for recommendations
- **Memory Usage**: Optimized for large datasets
- **Concurrent Users**: Supports multiple simultaneous sessions

## 🔧 Development

### **Model Training**
```bash
# Open Jupyter notebook for model training
jupyter notebook scripts/Models/HDBSCAN_Clusters_KNN.ipynb
```

### **Testing**
```bash
# Test the application
cd streamlit_app
streamlit run app.py
```

### **Data Updates**
1. Place new datasets in `data/raw/`
2. Run model training notebook
3. Export models to `data/models/`
4. Restart application

## 📚 Documentation

- **[SETUP.md](SETUP.md)**: Development environment setup
- **[DOCKER_SETUP.md](DOCKER_SETUP.md)**: Docker deployment guide
- **[SPOTIFY_SETUP.md](SPOTIFY_SETUP.md)**: Spotify API configuration
- **[CONTRIBUTING.md](CONTRIBUTING.md)**: Contribution guidelines
- **[Model Notebook](scripts/Models/HDBSCAN_Clusters_KNN.ipynb)**: Model training and validation

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details on:

- Setting up the development environment
- Coding standards and style guide
- Testing guidelines
- Pull request process

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Spotify** for providing the Web API and data capabilities
- **scikit-learn** community for excellent machine learning tools
- **Streamlit** team for the amazing web framework
- **HDBSCAN** developers for the clustering algorithm

## 📞 Support

- **Issues**: [GitHub Issues](../../issues)
- **Discussions**: [GitHub Discussions](../../discussions)
- **Documentation**: See documentation files in the repository

---

**🎵 Built with ❤️ for music lovers and data scientists**


