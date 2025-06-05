# 🛠️ Development Setup Guide - Spotify Music Recommendation

This guide provides detailed instructions for setting up the **Spotify Music Recommendation** development environment.

## 📋 Prerequisites

### Required Software
- **Python 3.11+** (recommended: 3.11 or 3.12)
- **Git** for version control
- **Docker & Docker Compose** (for containerized deployment)
- **Jupyter Notebook** (for model training)

### System Requirements
- **RAM**: Minimum 8GB (16GB recommended for model training)
- **Storage**: At least 5GB free space for datasets and models
- **Network**: Internet connection for downloading dependencies and Spotify API features

## 🚀 Quick Setup (Docker - Recommended)

### 1. Clone Repository
```bash
git clone <your-repo-url>
cd spotify-music-recommendation
```

### 2. Prepare Data
```bash
# Ensure your data structure looks like this:
data/
├── raw/
│   ├── spotify_tracks.csv          # Main track data
│   └── spotify_artists.csv         # Artist information
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

# Access the Spotify Music Recommendation system
open http://localhost:8501
```

## 🐍 Local Development Setup

### Step 1: Environment Setup

#### Windows
```powershell
# Navigate to project directory
cd path\to\spotify-music-recommendation

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
cd path/to/spotify-music-recommendation

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Verify activation (should show (venv) in prompt)
python --version
```

### Step 2: Install Dependencies

#### For Spotify Music Recommendation Development
```bash
cd streamlit_app
pip install -r requirements.txt
```

#### For Model Training
```bash
cd scripts/Models
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables
```bash
# Set data path for local development
export DATA_PATH="data"

# Optional: Configure Spotify API credentials
export SPOTIFY_CLIENT_ID="your_client_id"
export SPOTIFY_CLIENT_SECRET="your_client_secret"
```

### Step 4: Run the Application
```bash
# Navigate to streamlit app directory
cd streamlit_app

# Run the Spotify Music Recommendation system
streamlit run app.py
```

### Step 5: Verify Installation
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

1. **spotify_tracks.csv** - Main dataset with audio features and track metadata
2. **spotify_artists.csv** - Artist names and metadata  

### Data Validation
```bash
# Quick validation script
python -c "
import pandas as pd
import os

data_dir = 'data/raw'
required_files = [
    'spotify_tracks.csv',
    'spotify_artists.csv'
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
2. **Feature Engineering**: Process audio features
3. **HDBSCAN Clustering**: Train clustering model
4. **KNN Model**: Build recommendation system
5. **Model Export**: Save models to `data/models/`

### 3. Expected Output Files
After training, you should have these files in `data/models/`:
- `hdbscan_model.pkl` - Trained HDBSCAN clustering model
- `knn_model.pkl` - K-Nearest Neighbors model for recommendations
- `audio_embeddings.pkl` - Audio feature embeddings
- `cluster_labels.pkl` - Cluster assignments for each track
- `song_indices.pkl` - Song index mapping

## 🎵 Spotify API Configuration (Optional)

### 1. Create Spotify App
1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/applications)
2. Click "Create App"
3. Fill in app details
4. Note your Client ID and Client Secret

### 2. Configure Credentials
Choose one of these methods:

#### Method 1: Environment Variables
```bash
export SPOTIFY_CLIENT_ID="your_client_id_here"
export SPOTIFY_CLIENT_SECRET="your_client_secret_here"
```

#### Method 2: Streamlit Secrets
Create `.streamlit/secrets.toml`:
```toml
[spotify]
client_id = "your_client_id_here"
client_secret = "your_client_secret_here"
```

#### Method 3: Environment File
Create `.env` file:
```env
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
```

### 3. Verify API Connection
```bash
# Test Spotify API connection
python -c "
try:
    from streamlit_app.spotify_api_client import create_spotify_client
    client = create_spotify_client()
    if client:
        print('✅ Spotify API connection successful')
    else:
        print('❌ Spotify API connection failed')
except Exception as e:
    print(f'❌ Error: {e}')
"
```

## 🐳 Docker Development

### Build and Run with Docker
```bash
# Build the container
docker-compose build

# Start the application
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the application
docker-compose down
```

### Development with Docker
```bash
# Rebuild after code changes
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Missing Data Files
```bash
# Check if data files exist
ls -la data/raw/
ls -la data/models/
```

#### 2. Import Errors
```bash
# Reinstall dependencies
pip install -r streamlit_app/requirements.txt --force-reinstall
```

#### 3. Port Already in Use
```bash
# Find process using port 8501
lsof -i :8501  # Linux/macOS
netstat -ano | findstr :8501  # Windows

# Kill the process or use different port
streamlit run app.py --server.port 8502
```

#### 4. Docker Issues
```bash
# Clean Docker system
docker system prune -f

# Rebuild without cache
docker-compose build --no-cache
```

### Performance Optimization

#### Memory Usage
```bash
# Monitor memory usage
docker stats

# Limit container memory
docker-compose up -d --memory=4g
```

#### Faster Startup
```bash
# Use cached models
export CACHE_MODELS=true

# Disable Spotify API for testing
export DISABLE_SPOTIFY_API=true
```

## 📝 Development Workflow

### 1. Code Changes
```bash
# Make your changes
git add .
git commit -m "feat: description of changes"
```

### 2. Testing
```bash
# Test locally
cd streamlit_app
streamlit run app.py

# Test with Docker
docker-compose up -d
```

### 3. Deployment
```bash
# Push changes
git push origin main

# Deploy to production
docker-compose -f docker-compose.prod.yml up -d
```

## 📚 Next Steps

1. **Explore the Application**: Start with the basic setup and explore all features
2. **Train Models**: Follow the model training notebook for custom datasets
3. **Customize UI**: Modify the Streamlit components for your specific needs
4. **Add Features**: Extend functionality with new recommendation algorithms
5. **Deploy**: Use Docker for production deployment

## 🆘 Getting Help

- **Documentation**: Check other `.md` files in the repository
- **Issues**: Create an issue on GitHub for bugs or feature requests
- **Discussions**: Use GitHub Discussions for questions and ideas

---

**🎵 Happy coding! Enjoy building with the Spotify Music Recommendation system.**