# Technical Guide - Spotify Recommendation System

## System Architecture

### Technology Stack

#### Frontend
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite for fast development and optimized builds
- **Styling**: CSS Modules with modern CSS features
- **State Management**: React Query for server state, React hooks for local state
- **HTTP Client**: Axios with interceptors for API communication

#### Backend
- **Framework**: FastAPI with Python 3.11+
- **Async Support**: Full async/await implementation
- **Validation**: Pydantic models for request/response validation
- **Documentation**: Automatic OpenAPI/Swagger documentation
- **CORS**: Configured for cross-origin requests

#### Database
- **Primary Database**: PostgreSQL 15+ with optimized indexing
- **Connection Pool**: SQLAlchemy with async support
- **Migrations**: Alembic for database schema management
- **Optimization**: Proper indexing and query optimization

#### Machine Learning
- **Core Libraries**: scikit-learn, HDBSCAN, NLTK
- **Feature Engineering**: Custom pipelines with pandas and numpy
- **Model Storage**: Pickle serialization with version control
- **Processing**: Async model loading and inference

### Container Architecture

```
┌─────────────────┐
│     nginx       │  ← Reverse proxy and load balancer
│   (Port 80)     │
└─────────┬───────┘
          │
    ┌─────▼─────┐
    │  frontend │  ← React application
    │ (Port 3000)│
    └───────────┘
          │
    ┌─────▼─────┐
    │  backend  │  ← FastAPI application
    │ (Port 8000)│
    └─────┬─────┘
          │
    ┌─────▼─────┐
    │ database  │  ← PostgreSQL
    │ (Port 5432)│
    └───────────┘
          │
    ┌─────▼─────┐
    │model-prep │  ← ML pipeline
    │           │
    └───────────┘
```

## API Reference

### Authentication
Currently using session-based authentication. Future versions will implement JWT tokens.

### Core Endpoints

#### Songs API

**Search Songs**
```http
GET /api/songs/search
Query Parameters:
  - q: string (search query)
  - limit: integer (default: 20, max: 100)
  - offset: integer (default: 0)

Response:
{
  "songs": [
    {
      "id": "string",
      "name": "string", 
      "artists": ["string"],
      "audio_features": {
        "danceability": float,
        "energy": float,
        "valence": float
      }
    }
  ],
  "total": integer,
  "has_more": boolean
}
```

**Get Song Details**
```http
GET /api/songs/{song_id}

Response:
{
  "id": "string",
  "name": "string",
  "artists": ["string"],
  "album": "string",
  "audio_features": { /* ... */ },
  "cluster_assignments": {
    "naive_features": integer,
    "pca_features": integer,
    // ... other models
  }
}
```

#### Recommendations API

**Get Recommendations**
```http
POST /api/recommendations
Content-Type: application/json

{
  "song_id": "string",
  "model_type": "naive_features|pca_features|combined_features|llav_features|llav_pca",
  "limit": integer
}

Response:
{
  "recommendations": [
    {
      "song": { /* song object */ },
      "similarity_score": float,
      "explanation": "string"
    }
  ],
  "model_info": {
    "type": "string",
    "parameters": { /* ... */ }
  }
}
```

#### Clusters API

**Get Clusters**
```http
GET /api/clusters
Query Parameters:
  - model_type: string (required)
  - limit: integer
  - include_songs: boolean

Response:
{
  "clusters": [
    {
      "id": integer,
      "size": integer,
      "characteristics": { /* ... */ },
      "songs": [ /* if include_songs=true */ ]
    }
  ]
}
```

**Get Cluster Details**
```http
GET /api/clusters/{cluster_id}
Query Parameters:
  - model_type: string (required)
  - song_limit: integer

Response:
{
  "cluster": {
    "id": integer,
    "size": integer,
    "characteristics": { /* ... */ },
    "songs": [ /* ... */ ],
    "representative_songs": [ /* ... */ ]
  }
}
```

#### User Preferences API

**Like Song**
```http
POST /api/songs/{song_id}/like

Response:
{
  "success": boolean,
  "message": "string"
}
```

**Unlike Song**
```http
DELETE /api/songs/{song_id}/like

Response:
{
  "success": boolean,
  "message": "string"
}
```

**Get Liked Songs**
```http
GET /api/user/liked-songs
Query Parameters:
  - limit: integer
  - offset: integer

Response:
{
  "liked_songs": [ /* song objects */ ],
  "total": integer
}
```

### Error Handling

All endpoints return consistent error responses:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": { /* additional context */ }
  }
}
```

Common HTTP status codes:
- `200`: Success
- `400`: Bad Request (validation errors)
- `404`: Not Found
- `422`: Unprocessable Entity (Pydantic validation)
- `500`: Internal Server Error

## Database Schema

### Core Tables

#### tracks
```sql
CREATE TABLE tracks (
    id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    artists_id TEXT[], 
    popularity INTEGER,
    danceability FLOAT,
    energy FLOAT,
    valence FLOAT,
    acousticness FLOAT,
    instrumentalness FLOAT,
    liveness FLOAT,
    loudness FLOAT,
    speechiness FLOAT,
    tempo FLOAT,
    key INTEGER,
    mode INTEGER,
    time_signature INTEGER,
    lyrics TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Performance indexes
CREATE INDEX idx_tracks_name ON tracks USING gin(to_tsvector('english', name));
CREATE INDEX idx_tracks_artists ON tracks USING gin(artists_id);
CREATE INDEX idx_tracks_popularity ON tracks(popularity DESC);
```

#### clusters
```sql
CREATE TABLE clusters (
    id SERIAL PRIMARY KEY,
    model_type VARCHAR NOT NULL,
    cluster_id INTEGER NOT NULL,
    track_id VARCHAR NOT NULL REFERENCES tracks(id),
    similarity_score FLOAT,
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(model_type, cluster_id, track_id)
);

CREATE INDEX idx_clusters_model_type ON clusters(model_type);
CREATE INDEX idx_clusters_cluster_id ON clusters(model_type, cluster_id);
```

#### user_preferences
```sql
CREATE TABLE user_preferences (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR NOT NULL, -- Session ID for now
    track_id VARCHAR NOT NULL REFERENCES tracks(id),
    preference_type VARCHAR NOT NULL, -- 'like', 'dislike'
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(user_id, track_id)
);

CREATE INDEX idx_user_preferences_user_id ON user_preferences(user_id);
CREATE INDEX idx_user_preferences_track_id ON user_preferences(track_id);
```

## Machine Learning Pipeline

### Model Architecture

Each HDBSCAN model variant includes:
- `{variant}_hdbscan_model.pkl` - Trained HDBSCAN clusterer
- `{variant}_knn_model.pkl` - KNN model for similarity
- `{variant}_audio_embeddings.pkl` - Feature vectors
- `{variant}_cluster_labels.pkl` - Cluster assignments
- `{variant}_song_indices.pkl` - Track ID mappings
- `hdbscan_config_{variant}.json` - Model configuration

### Model Loading and Inference

#### Lazy Loading Pattern
```python
class ModelService:
    def __init__(self):
        self._models = {}
        self._model_configs = {}
    
    async def get_model(self, model_type: str):
        if model_type not in self._models:
            await self._load_model(model_type)
        return self._models[model_type]
    
    async def _load_model(self, model_type: str):
        # Load model files asynchronously
        # Cache in memory for future requests
```

#### Error Handling and Fallbacks
```python
async def get_recommendations(song_id: str, model_type: str):
    try:
        model = await model_service.get_model(model_type)
        return await model.predict(song_id)
    except ModelNotFoundError:
        # Fallback to default model
        logger.warning(f"Model {model_type} not found, using default")
        return await get_recommendations(song_id, "naive_features")
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise RecommendationError("Unable to generate recommendations")
```

### Feature Engineering

#### Audio Feature Processing
```python
def prepare_audio_features(df: pd.DataFrame) -> np.ndarray:
    """Prepare audio features for model training"""
    
    # Basic features
    basic_features = ['danceability', 'energy', 'valence', 
                     'acousticness', 'instrumentalness', 'liveness',
                     'loudness', 'speechiness', 'tempo', 'key', 
                     'mode', 'time_signature']
    
    # Feature interactions
    df['energy_valence'] = df['energy'] * df['valence']
    df['dance_energy'] = df['danceability'] * df['energy']
    
    # Normalization
    scaler = StandardScaler()
    features = scaler.fit_transform(df[basic_features])
    
    return features
```

#### Text Preprocessing for Lyrics
```python
def preprocess_lyrics(text: str) -> str:
    """Clean and preprocess lyrics text"""
    
    # Lowercase and clean
    text = text.lower()
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Tokenization and lemmatization
    tokens = word_tokenize(text)
    lemmatizer = WordNetLemmatizer()
    stop_words = set(stopwords.words('english'))
    
    processed_tokens = [
        lemmatizer.lemmatize(token) 
        for token in tokens 
        if token not in stop_words and len(token) > 2
    ]
    
    return ' '.join(processed_tokens)
```

## Development Workflow

### Local Development Setup

#### Prerequisites
```bash
# Required software
- Docker and Docker Compose
- Python 3.11+
- Node.js 18+
- Git

# Optional but recommended
- VS Code with Python and TypeScript extensions
- pgAdmin for database management
```

#### Environment Setup
```bash
# Clone repository
git clone <repository-url>
cd spotify_recommendation_system_v2

# Copy environment template
cp env.example .env

# Edit .env with your settings
# Key variables:
# - POSTGRES_PASSWORD
# - API_SECRET_KEY
# - ENVIRONMENT=development
```

#### Development Commands
```bash
# Start all services
docker-compose up -d

# Start with logs
docker-compose up

# Rebuild specific service
docker-compose build backend
docker-compose up -d backend

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Execute commands in containers
docker-compose exec backend python -m pytest
docker-compose exec frontend npm test

# Check model status
docker-compose exec model-prep python model_pipeline.py --check-only
```

### Code Structure

#### Backend Structure
```
backend/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration management
│   ├── database/
│   │   ├── __init__.py
│   │   ├── database.py      # Database connection
│   │   └── models.py        # SQLAlchemy models
│   ├── routers/
│   │   ├── songs.py         # Song-related endpoints
│   │   ├── recommendations.py # Recommendation endpoints
│   │   ├── clusters.py      # Cluster endpoints
│   │   └── health.py        # Health check endpoints
│   ├── services/
│   │   ├── model_service.py # ML model management
│   │   ├── hdbscan_similarity_service.py
│   │   ├── lyrics_similarity_service.py
│   │   └── similarity_utils.py
│   ├── schemas/
│   │   ├── recommendation.py # Pydantic models
│   │   └── cluster.py
│   └── middleware/
│       ├── logging.py       # Request logging
│       └── performance.py   # Performance monitoring
├── requirements.txt
└── Dockerfile
```

#### Frontend Structure
```
frontend/
├── src/
│   ├── components/
│   │   ├── SongCard.tsx     # Reusable song display
│   │   ├── ModelSelector.tsx # Model selection
│   │   ├── ClusterCard.tsx  # Cluster display
│   │   └── Navbar.tsx       # Navigation
│   ├── pages/
│   │   └── Home.tsx         # Main page component
│   ├── services/
│   │   ├── api.ts           # API client
│   │   └── spotify.ts       # Spotify-specific logic
│   ├── hooks/               # Custom React hooks
│   ├── App.tsx              # Main application
│   └── index.tsx           # Entry point
├── package.json
├── vite.config.ts
└── Dockerfile
```

### Testing Strategy

#### Backend Testing
```python
# pytest configuration in pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Example test
async def test_get_recommendations():
    response = await client.post("/api/recommendations", json={
        "song_id": "test_song_id",
        "model_type": "naive_features",
        "limit": 10
    })
    assert response.status_code == 200
    data = response.json()
    assert "recommendations" in data
    assert len(data["recommendations"]) <= 10
```

#### Frontend Testing
```typescript
// Jest configuration for React Testing Library
import { render, screen, fireEvent } from '@testing-library/react';
import { SongCard } from '../components/SongCard';

test('displays song information correctly', () => {
  const song = {
    id: '1',
    name: 'Test Song',
    artists: ['Test Artist']
  };
  
  render(<SongCard song={song} />);
  
  expect(screen.getByText('Test Song')).toBeInTheDocument();
  expect(screen.getByText('Test Artist')).toBeInTheDocument();
});
```

### Performance Monitoring

#### Backend Metrics
```python
# Custom middleware for performance tracking
import time
from fastapi import Request

async def performance_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    # Log slow requests
    if process_time > 1.0:
        logger.warning(f"Slow request: {request.url} took {process_time:.2f}s")
    
    response.headers["X-Process-Time"] = str(process_time)
    return response
```

#### Database Query Monitoring
```python
# SQLAlchemy event listeners for query logging
from sqlalchemy import event
from sqlalchemy.engine import Engine

@event.listens_for(Engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    context._query_start_time = time.time()

@event.listens_for(Engine, "after_cursor_execute")  
def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - context._query_start_time
    if total > 0.1:  # Log queries taking more than 100ms
        logger.warning(f"Slow query: {total:.2f}s - {statement[:100]}...")
```

## Deployment

### Production Configuration

#### Environment Variables
```bash
# Production .env
ENVIRONMENT=production
DEBUG=false

# Database
POSTGRES_HOST=production-db-host
POSTGRES_DB=spotify_recommendations_prod
POSTGRES_USER=app_user
POSTGRES_PASSWORD=secure_password

# Security
API_SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Performance
WORKERS=4
MAX_CONNECTIONS=100
```

#### Docker Compose Production
```yaml
version: '3.8'
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - backend

  backend:
    build: ./backend
    environment:
      - ENVIRONMENT=production
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M
```

### Health Checks and Monitoring

#### Health Check Endpoints
```python
@router.get("/health")
async def health_check():
    """Basic health check"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@router.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with dependencies"""
    checks = {
        "database": await check_database_connection(),
        "models": await check_model_availability(),
        "memory": check_memory_usage(),
        "disk": check_disk_space()
    }
    
    status = "healthy" if all(checks.values()) else "unhealthy"
    return {"status": status, "checks": checks}
```

#### Logging Configuration
```python
import logging
from pythonjsonlogger import jsonlogger

# Production logging setup
def setup_logging():
    logger = logging.getLogger()
    handler = logging.StreamHandler()
    
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
```

### Security Considerations

#### API Security
- **Input Validation**: Pydantic models for all inputs
- **Rate Limiting**: Implement rate limiting for API endpoints
- **CORS**: Properly configured CORS policies
- **HTTPS**: SSL/TLS encryption in production
- **Authentication**: Secure session management

#### Data Security
- **Database Security**: Encrypted connections, limited user permissions
- **Secrets Management**: Environment variables, not hardcoded secrets
- **Data Validation**: Sanitize all user inputs
- **Audit Logging**: Track sensitive operations

## Troubleshooting

### Common Development Issues

#### Model Loading Errors
```bash
# Check model files exist
ls -la data/models/

# Verify model generation
docker-compose exec model-prep python model_pipeline.py --check-only

# Regenerate models
docker-compose exec model-prep python model_pipeline.py --force
```

#### Database Connection Issues
```bash
# Check database status
docker-compose ps database

# Test database connection
docker-compose exec backend python -c "
from app.database.database import get_database
import asyncio
asyncio.run(get_database().execute('SELECT 1'))
"
```

#### Frontend Build Issues
```bash
# Clear node modules and reinstall
docker-compose exec frontend rm -rf node_modules
docker-compose exec frontend npm install

# Check for TypeScript errors
docker-compose exec frontend npm run type-check
```

### Performance Debugging

#### Slow API Responses
1. **Check database queries**: Use query logging to identify slow queries
2. **Profile model inference**: Add timing to model prediction calls
3. **Monitor memory usage**: Check for memory leaks in long-running processes
4. **Review caching**: Ensure frequently accessed data is cached

#### High Memory Usage
1. **Model loading**: Implement lazy loading for ML models
2. **Database connections**: Check connection pool configuration
3. **Memory leaks**: Use memory profiling tools
4. **Container limits**: Adjust Docker memory limits

### Monitoring and Alerting

#### Key Metrics to Monitor
- **Response Times**: API endpoint latency
- **Error Rates**: 4xx and 5xx error percentages
- **Database Performance**: Query execution times
- **Model Performance**: Prediction accuracy and speed
- **Resource Usage**: CPU, memory, disk usage

#### Alerting Thresholds
- **High Error Rate**: > 5% error rate for 5 minutes
- **Slow Responses**: > 2 second average response time
- **Database Issues**: Connection failures or slow queries
- **Model Failures**: Model loading or prediction errors
- **Resource Exhaustion**: > 90% memory or disk usage

This technical guide provides the foundation for developing, deploying, and maintaining the Spotify Recommendation System. Regular updates to this documentation ensure it remains current with system evolution and best practices. 