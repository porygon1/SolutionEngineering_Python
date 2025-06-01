# 🛠️ Development Setup Guide

This guide provides detailed instructions for setting up the Spotify Music Recommendation System development environment.

## 📋 Prerequisites

### Required Software
- **Python 3.11+** (recommended: 3.11 or 3.12)
- **Git** for version control
- **Docker & Docker Compose** (for containerized deployment)
- **Jupyter Notebook** (for model training)

### System Requirements
- **RAM**: Minimum 8GB (16GB recommended for model training)
- **Storage**: At least 5GB free space for datasets and models
- **Network**: Internet connection for downloading dependencies and audio previews

## 🚀 Quick Setup (Docker - Recommended)

### 1. Clone Repository
```bash
git clone <your-repo-url>
cd spotify-music-recommendation-system
```

### 2. Prepare Data
```bash
# Ensure your data structure looks like this:
data/
├── raw/
│   ├── spotify_tracks.csv          # Main track data with preview URLs
│   ├── spotify_artists.csv         # Artist information
│   ├── spotify_albums.csv          # Album metadata
│   ├── low_level_audio_features.csv # Spectral features
│   └── lyrics_features.csv         # Lyrical features
└── models/                         # Created after model training
    ├── hdbscan_model.pkl
    ├── knn_model.pkl
    ├── audio_embeddings.pkl
    ├── cluster_labels.pkl
    └── song_indices.pkl
```

### 3. Train Models (First Time Setup)
```bash
# Install Jupyter in your base environment or use Docker
pip install jupyter

# Run the model training notebook
jupyter notebook scripts/Models/HDBSCAN_Clusters_KNN.ipynb

# Follow the notebook to export models to data/models/
```

### 4. Start Application
```bash
# Build and start the application
docker-compose up -d

# Access the application
open http://localhost:8501
```

## 🐍 Local Development Setup

### Step 1: Environment Setup

#### Windows
```powershell
# Navigate to project directory
cd path\to\spotify-music-recommendation-system

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\activate

# Verify activation (should show (venv) in prompt)
python --version
```

#### Linux/macOS
```bash
# Navigate to project directory
cd path/to/spotify-music-recommendation-system

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Verify activation (should show (venv) in prompt)
python --version
```

### Step 2: Install Dependencies

#### For Streamlit App Development
```bash
cd streamlit_app
pip install -r requirements.txt
```

#### For Model Training
```bash
cd scripts/Models
pip install -r requirements.txt
```

#### For Full Development (All Components)
```bash
# Install all dependencies at once
pip install streamlit>=1.40.0 pandas>=2.2.0 numpy>=2.1.0 \
    scikit-learn>=1.6.0 hdbscan>=0.8.33 umap-learn>=0.5.4 \
    plotly>=6.0.0 joblib>=1.4.0 requests>=2.31.0 \
    jupyter notebook ipywidgets
```

### Step 3: Verify Installation
```bash
# Check Python version
python --version

# List installed packages
pip list

# Test imports
python -c "import streamlit, pandas, sklearn, hdbscan; print('All imports successful!')"
```

## 📊 Data Preparation

### Required Datasets
Your `data/raw/` directory should contain these CSV files:

1. **spotify_tracks.csv** - Main dataset with audio features and preview URLs
2. **spotify_artists.csv** - Artist names and metadata
3. **spotify_albums.csv** - Album information
4. **low_level_audio_features.csv** - Spectral analysis features (MFCCs, chroma, etc.)
5. **lyrics_features.csv** - Text-based lyrical features

### Data Validation
```bash
# Quick validation script
python -c "
import pandas as pd
import os

data_dir = 'data/raw'
required_files = [
    'spotify_tracks.csv',
    'spotify_artists.csv', 
    'spotify_albums.csv',
    'low_level_audio_features.csv',
    'lyrics_features.csv'
]

for file in required_files:
    path = os.path.join(data_dir, file)
    if os.path.exists(path):
        df = pd.read_csv(path)
        print(f'✅ {file}: {len(df):,} rows')
    else:
        print(f'❌ Missing: {file}')
"
```

## 🤖 Model Training Setup

### 1. Open Training Notebook
```bash
# Activate environment if not already active
source venv/bin/activate  # Linux/macOS
# or
.\venv\Scripts\activate   # Windows

# Start Jupyter
jupyter notebook scripts/Models/HDBSCAN_Clusters_KNN.ipynb
```

### 2. Training Process
The notebook will guide you through:
1. **Data Loading**: Import and validate all datasets
2. **Feature Engineering**: Process audio and spectral features
3. **HDBSCAN Clustering**: Train clustering model
4. **KNN Model**: Build recommendation system
5. **Model Export**: Save models to `data/models/`

### 3. Expected Output Files
After training, you should have:
```
data/models/
├── hdbscan_model.pkl         # Trained clustering model
├── knn_model.pkl            # K-NN recommendation model  
├── audio_embeddings.pkl     # Processed feature embeddings
├── cluster_labels.pkl       # Cluster assignments for each song
└── song_indices.pkl         # Index mapping for songs
```

## 🧪 Running the Application

### Local Development
```bash
# Navigate to streamlit app directory
cd streamlit_app

# Run Streamlit application
streamlit run app.py

# Application will open at http://localhost:8501
```

### Docker Development
```bash
# Build and run with live reload for development
docker-compose -f docker-compose.yml up --build

# For production deployment
docker-compose up -d
```

## 🔧 Development Tools

### Code Quality
```bash
# Install development tools
pip install black flake8 pytest

# Format code
black streamlit_app/app.py

# Check code style
flake8 streamlit_app/app.py

# Run tests (if available)
pytest streamlit_app/tests/
```

### Debugging
```bash
# Run Streamlit in debug mode
streamlit run app.py --logger.level=debug

# Check Docker logs
docker-compose logs streamlit

# Access running container
docker-compose exec streamlit bash
```

## 📱 Environment Variables

Create a `.env` file in the project root for customization:
```bash
# .env file
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ENABLECORS=false
STREAMLIT_SERVER_ENABLEXSRFPROTECTION=false

# Data paths (if different from defaults)
DATA_PATH=/app/data
RAW_DATA_PATH=/app/data/raw
MODELS_PATH=/app/data/models
```

## 🚨 Troubleshooting

### Common Issues

#### 1. **Import Errors**
```bash
# Solution: Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

#### 2. **Model Loading Errors**
```bash
# Check if models exist
ls -la data/models/

# Retrain models if missing
jupyter notebook scripts/Models/HDBSCAN_Clusters_KNN.ipynb
```

#### 3. **Audio Preview Issues**
- Ensure `preview_url` column exists in spotify_tracks.csv
- Check internet connection for Spotify previews
- Verify URLs are valid Spotify preview links

#### 4. **Docker Issues**
```bash
# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Check container logs
docker-compose logs
```

#### 5. **Memory Issues**
- Increase Docker memory allocation (8GB+)
- Use smaller dataset for testing
- Enable swap space on Linux systems

### Performance Optimization
```bash
# For large datasets, consider:
# 1. Increase available memory
# 2. Use SSD storage for data
# 3. Enable multiprocessing in model training
# 4. Use GPU for UMAP if available
```

## 🔄 Updates and Maintenance

### Updating Dependencies
```bash
# Check for updates
pip list --outdated

# Update specific package
pip install --upgrade streamlit

# Update all packages (use with caution)
pip install --upgrade -r requirements.txt
```

### Data Updates
1. Replace CSV files in `data/raw/`
2. Retrain models using the notebook
3. Restart the application

### Model Retraining
```bash
# Schedule regular retraining for production
# Run monthly or when new data is available
jupyter nbconvert --execute scripts/Models/HDBSCAN_Clusters_KNN.ipynb
```

## 📞 Getting Help

### Documentation
- **Main README**: [README.md](README.md)
- **Docker Setup**: [DOCKER_SETUP.md](DOCKER_SETUP.md)
- **App Documentation**: [streamlit_app/README.md](streamlit_app/README.md)

### Support Channels
- **GitHub Issues**: Report bugs and feature requests
- **Model Training**: Check Jupyter notebook comments
- **Docker Issues**: Review Docker logs and DOCKER_SETUP.md

## ✅ Verification Checklist

- [ ] Python 3.11+ installed
- [ ] Virtual environment created and activated
- [ ] All dependencies installed successfully
- [ ] Data files present in `data/raw/`
- [ ] Models trained and exported to `data/models/`
- [ ] Streamlit app runs without errors
- [ ] Audio previews working in browser
- [ ] Docker setup functional (if using containerized deployment)

## 🎯 Next Steps

After successful setup:
1. **Explore the App**: Try different songs and recommendation modes
2. **Model Experimentation**: Modify clustering parameters in the notebook
3. **Feature Engineering**: Add new audio features or data sources
4. **UI Improvements**: Enhance the Streamlit interface
5. **Deployment**: Deploy to cloud platforms for production use

---

**Happy coding! 🎵🚀**