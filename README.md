# Spotify Music Recommendation System

A sophisticated music discovery platform that leverages machine learning to provide personalized song recommendations. The system analyzes audio characteristics, clustering patterns, and lyrical content to deliver diverse and accurate music suggestions through an intuitive web interface.

## Overview

This system analyzes music characteristics using multiple approaches - audio features, clustering algorithms, and lyrical content - to provide diverse and accurate song recommendations. Built with scalability and user experience in mind, it features a React frontend, FastAPI backend, and PostgreSQL database.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend │    │  FastAPI Backend │    │  PostgreSQL DB  │
│                 │    │                 │    │                 │
│  • Song Search  │◄──►│  • ML Models    │◄──►│  • Track Data   │
│  • Recommendations│    │  • Clustering   │    │  • User Prefs   │
│  • User Interface│    │  • Similarity   │    │  • Clusters     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
           │                       │                       │
           │            ┌─────────────────┐               │
           └────────────┤   ML Pipeline   ├───────────────┘
                        │                 │
                        │ • HDBSCAN       │
                        │ • Lyrics Models │
                        │ • Feature Eng   │
                        └─────────────────┘
```

## Key Features

### 🎵 Multi-Modal Recommendations
- **Audio Feature Analysis**: Analyzes tempo, energy, valence, and other musical characteristics
- **Clustering-Based Discovery**: Groups similar songs using advanced clustering algorithms
- **Lyrical Similarity**: Finds songs with similar themes and lyrical content
- **Hybrid Approach**: Combines multiple recommendation strategies for better results

### 🔍 Advanced Search & Discovery
- Real-time song search with autocomplete
- Filter by genre, mood, energy level, and more
- Explore music through interactive cluster visualizations
- Discover new artists and songs based on your preferences

### 👤 Personalized Experience
- Like/unlike songs to improve recommendations
- View your music taste profile
- Track your listening history
- Get recommendations tailored to your preferences

### 🚀 Modern Technology Stack
- **Frontend**: React 18 with TypeScript, Vite, and modern UI components
- **Backend**: FastAPI with async support and automatic API documentation
- **Database**: PostgreSQL with optimized queries and indexing
- **ML Pipeline**: Scikit-learn, HDBSCAN, and custom feature engineering
- **Deployment**: Docker containers with nginx load balancing

## Machine Learning Models

### Clustering Models (HDBSCAN)
The system uses five different clustering approaches to group similar songs:

1. **Naive Features**: Basic audio characteristics (12 features)
2. **PCA Features**: Dimensionally reduced audio features (6 components)
3. **Combined Features**: Audio features + derived characteristics
4. **Low-Level Audio Features**: Detailed audio analysis
5. **Low-Level PCA**: Reduced low-level features (60 components)

### Lyrics Similarity Models
Four different approaches for finding songs with similar lyrical content:

1. **KNN Cosine**: Cosine similarity with k-nearest neighbors
2. **KNN Euclidean**: Euclidean distance-based similarity
3. **SVD + KNN**: Dimensionality reduction with similarity search
4. **KNN Cosine (k=20)**: Optimized cosine similarity with smaller k

## Quick Start

### 🚀 Get Started in 5 Minutes

1. **Prerequisites**: Docker, Docker Compose, Git, 4GB RAM
2. **Clone**: `git clone <repository-url> && cd spotify_recommendation_system_v2`
3. **Setup**: `./docker-setup.bat full` (Windows) or `./docker-setup.sh full` (Linux/Mac)
4. **Access**: Open http://localhost:3000

For detailed instructions, see the **[Quick Start Guide](spotify_recommendation_system_v2/QUICK_START.md)**.

### Development Setup

For development with hot reloading:

```bash
# Start development environment
docker-compose -f docker-compose.yml up -d

# View logs
docker-compose logs -f
```

## Usage Guide

### Basic Recommendations
1. Open the application in your browser
2. Search for a song you like
3. Click "Get Recommendations" to see similar songs
4. Use the like/unlike buttons to improve future recommendations

### Exploring Clusters
1. Navigate to the "Clusters" section
2. Browse different music clusters
3. Click on clusters to see all songs in that group
4. Discover new music based on cluster characteristics

### Model Comparison
1. Go to "Model Comparison" in the interface
2. Select different recommendation models
3. Compare results from different approaches
4. See which models work best for your taste

## Data Requirements

The system expects the following data files in the `data/raw/` directory:

- `spotify_tracks.csv`: Main track database with audio features
- `low_level_audio_features.csv`: Detailed audio analysis (optional)
- Additional data files as specified in the documentation

## Configuration

### Environment Variables
Key configuration options in `.env`:

```env
# Database
POSTGRES_HOST=database
POSTGRES_PORT=5432
POSTGRES_DB=spotify_recommendations
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password

# API
API_HOST=0.0.0.0
API_PORT=8000

# Frontend
VITE_API_URL=http://localhost:8000
```

### Model Configuration
Models can be configured in the `model-prep/` directory:
- Adjust clustering parameters
- Modify feature engineering
- Configure similarity thresholds

## API Reference

### Core Endpoints

**Get Recommendations**
```http
POST /api/recommendations
Content-Type: application/json

{
  "song_id": "track_id",
  "model_type": "hdbscan",
  "limit": 10
}
```

**Search Songs**
```http
GET /api/songs/search?q=song_name&limit=20
```

**Get Clusters**
```http
GET /api/clusters?model_type=naive_features
```

**Like/Unlike Song**
```http
POST /api/songs/{song_id}/like
DELETE /api/songs/{song_id}/like
```

### Model Endpoints

**Get Available Models**
```http
GET /api/models
```

**Model Health Check**
```http
GET /api/health
```

## Performance & Scaling

### Optimization Features
- Database indexing on frequently queried columns
- Caching of model predictions
- Async request handling
- Connection pooling
- Efficient batch processing

### Scaling Recommendations
- Use multiple worker processes for the API
- Implement Redis for caching recommendations
- Consider model serving with dedicated ML servers
- Database read replicas for heavy read workloads

## Troubleshooting

### Common Issues

**Models not loading**
```bash
# Check model generation status
docker-compose exec model-prep python model_pipeline.py --check-only

# Regenerate models if needed
docker-compose exec model-prep python model_pipeline.py --force
```

**Database connection errors**
```bash
# Check database status
docker-compose ps database

# View database logs
docker-compose logs database
```

**Frontend not loading**
```bash
# Rebuild frontend
docker-compose build frontend

# Check frontend logs
docker-compose logs frontend
```

### Performance Issues
- Increase container memory limits
- Check disk space for model files
- Monitor database query performance
- Review API response times

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details on:
- Code style and standards
- Testing requirements
- Pull request process
- Development workflow

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Documentation

### 📚 Complete Documentation Suite

- **[Quick Start Guide](spotify_recommendation_system_v2/QUICK_START.md)** - Get running in 5 minutes
- **[User Guide](spotify_recommendation_system_v2/USER_GUIDE.md)** - Complete feature walkthrough
- **[Technical Guide](spotify_recommendation_system_v2/TECHNICAL_GUIDE.md)** - Developer documentation
- **[Project Overview](spotify_recommendation_system_v2/PROJECT_OVERVIEW.md)** - System architecture and design
- **[Setup Instructions](spotify_recommendation_system_v2/SETUP.md)** - Detailed installation guide
- **[Database Setup](spotify_recommendation_system_v2/DATABASE_SETUP.md)** - Database configuration
- **[Docker Guide](spotify_recommendation_system_v2/DOCKER_README.md)** - Container deployment

### 🔧 Configuration Files

- **[Environment Template](spotify_recommendation_system_v2/env.example)** - Configuration options
- **[Docker Compose](spotify_recommendation_system_v2/docker-compose.yml)** - Service definitions
- **[Setup Scripts](spotify_recommendation_system_v2/)** - Automated deployment tools

## Support

### Getting Help

- **[Quick Start Guide](spotify_recommendation_system_v2/QUICK_START.md)** - Common setup issues
- **[Technical Guide](spotify_recommendation_system_v2/TECHNICAL_GUIDE.md)** - Troubleshooting section
- **[User Guide](spotify_recommendation_system_v2/USER_GUIDE.md)** - Feature questions
- **GitHub Issues** - Report bugs and request features

### Community

- **API Documentation**: http://localhost:8000/docs (when running)
- **System Health**: http://localhost:8000/health
- **Frontend**: http://localhost:3000

---

Built with ❤️ for music discovery and powered by advanced machine learning. 