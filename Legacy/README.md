# Legacy Spotify Music Recommendation System

This folder contains the legacy version of the Spotify Music Recommendation System, which was built using Streamlit. This version is maintained for compatibility purposes.

## ⚠️ Important Notice

**This is the legacy version of the system.** For new development and production use, please use the **Version 2 system** located in the `../spotify_recommendation_system_v2/` directory, which features:

- Modern React frontend with Spotify-like UI
- FastAPI backend with async support
- PostgreSQL database with normalized schema
- Production-ready Docker deployment
- Advanced ML pipeline with caching
- Comprehensive API documentation

## Legacy System Contents

### Documentation
- `README_legacy.md` - Original README for the Streamlit application
- `SETUP_legacy.md` - Legacy setup instructions
- `DOCKER_SETUP_legacy.md` - Legacy Docker setup guide
- `CONTRIBUTING_legacy.md` - Legacy contribution guidelines
- `PROJECT_STATUS_legacy.md` - Legacy project status
- Other legacy documentation files

### Application
- `streamlit_app/` - Complete Streamlit application
- `docker-compose_legacy.yml` - Docker Compose configuration for legacy system
- `pytest.ini` - Test configuration for legacy system

## Quick Start (Legacy System)

### Prerequisites
- Python 3.8+
- Docker & Docker Compose (for containerized deployment)
- Spotify datasets in `../data/raw/`
- Trained ML models in `../data/models/`

### Local Development
```bash
cd Legacy/streamlit_app
pip install -r requirements.txt
streamlit run app.py
```

### Docker Deployment
```bash
cd Legacy
docker-compose -f docker-compose_legacy.yml up --build
```

The legacy application will be available at `http://localhost:8501`

## Data Requirements

The legacy system expects data in the following structure:
```
../data/
├── raw/
│   ├── spotify_tracks.csv
│   └── spotify_artists.csv
└── models/
    ├── hdbscan_model.pkl
    ├── knn_model.pkl
    ├── audio_embeddings.pkl
    ├── cluster_labels.pkl
    └── song_indices.pkl
```

## Path Updates

**Important:** The paths in this legacy system have been updated to work from the new `Legacy/` location:
- Data paths now point to `../../data/` (relative to `Legacy/streamlit_app/`)
- Docker volume mounts have been updated accordingly
- All documentation references have been corrected

## Migration to V2

If you're currently using this legacy system and want to migrate to V2, please see:
- `../spotify_recommendation_system_v2/README.md` for V2 setup instructions
- `../SETUP.md` for comprehensive migration guide
- `../spotify_recommendation_system_v2/IMPORT_FIXES.md` for data migration help

## Support

For issues with the legacy system:
1. Check `README_legacy.md` for original documentation
2. Review `SETUP_legacy.md` for troubleshooting
3. Consider migrating to V2 for better support and features

For new features and active development, please use the V2 system in `../spotify_recommendation_system_v2/`. 