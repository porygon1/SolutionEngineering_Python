cd# Model Preparation Service

This service generates all machine learning models needed for the Spotify Recommendation System v2. It's designed to be production-ready with incremental model generation, comprehensive error handling, and reproducible builds.

## Features

### 🚀 Production-Ready Design
- **Incremental Generation**: Only creates models that don't exist, saving time and resources
- **Force Regeneration**: Option to recreate all models when needed
- **Status Checking**: Verify existing models without regeneration
- **Comprehensive Logging**: Detailed progress and error reporting
- **Health Checks**: Docker health monitoring for automated deployments

### 🎯 Model Types Generated

#### HDBSCAN Clustering Models
1. **Naive Features** (`naive_features`)
   - Basic audio features (tempo, key, valence, energy, etc.)
   - MinMax scaling applied
   - 12 audio features

2. **PCA Features** (`pca_features`)
   - Principal Component Analysis on basic features
   - Reduced to 6 components
   - Dimensionality reduction for faster processing

3. **Combined Features** (`combined_features`)
   - Basic audio features + low-level audio features
   - Comprehensive feature set
   - Best of both worlds approach

4. **Low-Level Audio Features** (`llav_features`)
   - Detailed spectral and temporal audio analysis
   - Hundreds of features from audio processing
   - Most detailed audio representation

5. **LLAV PCA** (`llav_pca`)
   - PCA on low-level audio features
   - Reduced to 60 components
   - Optimal balance of detail and performance

Each model variant includes:
- HDBSCAN clustering model (`.pkl`)
- KNN similarity model (`.pkl`)
- Audio embeddings (`.pkl`)
- Cluster labels (`.pkl`)
- Song indices mapping (`.pkl`)
- Configuration metadata (`.json`)

## Usage

### Docker Compose Integration

#### Standard Model Generation (Incremental)
```bash
# Generate only missing models
docker-compose --profile setup run --rm model-prep

# Or using setup scripts
./docker-setup.sh models          # Linux/Mac
docker-setup.bat models          # Windows
```

#### Force Regeneration
```bash
# Regenerate all models
docker-compose --profile setup run --rm -e FORCE_REGENERATE=true model-prep

# Or using setup scripts
./docker-setup.sh models-force   # Linux/Mac  
docker-setup.bat models-force   # Windows
```

#### Status Checking
```bash
# Check model status without generation
docker-compose --profile setup run --rm model-prep python scripts/startup.py --check-only

# Or using setup scripts
./docker-setup.sh models-check   # Linux/Mac
docker-setup.bat models-check   # Windows
```

### Direct Usage

#### Basic Model Generation
```bash
cd model-prep
python model_pipeline.py
```

#### With Options
```bash
# Force regeneration
FORCE_REGENERATE=true python scripts/startup.py

# Status check only
python scripts/startup.py --check-only

# Force regeneration with startup script
python scripts/startup.py --force
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATA_PATH` | `/app/data` | Path to data directory |
| `MODELS_PATH` | `/app/models` | Path to save models |
| `RAW_DATA_PATH` | `/app/data/raw` | Path to raw data files |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `FORCE_REGENERATE` | `false` | Force regeneration of existing models |

### Required Data Files

**Minimum Required:**
- `spotify_tracks.csv` - Main track metadata and audio features

**Optional (enables additional models):**
- `low_level_audio_features.csv` - Detailed audio analysis
- `lyrics_features.csv` - Lyrics-based features (future)

### Data Directory Structure
```
data/
├── raw/                          # Input data files
│   ├── spotify_tracks.csv        # Required
│   ├── low_level_audio_features.csv  # Optional
│   └── lyrics_features.csv       # Optional
├── processed/                    # Intermediate processing
└── models/                       # Generated models
    ├── naive_features_*.pkl      # Naive features model files
    ├── pca_features_*.pkl        # PCA features model files
    ├── combined_features_*.pkl   # Combined features model files
    ├── llav_features_*.pkl       # LLAV features model files
    ├── llav_pca_*.pkl           # LLAV PCA model files
    └── hdbscan_config_*.json    # Model configurations
```

## Model Files Generated

For each model variant, the following files are created:

| File Pattern | Description |
|-------------|-------------|
| `{model}_hdbscan_model.pkl` | HDBSCAN clustering model |
| `{model}_knn_model.pkl` | K-Nearest Neighbors model |
| `{model}_audio_embeddings.pkl` | Processed feature embeddings |
| `{model}_cluster_labels.pkl` | Cluster assignments |
| `{model}_song_indices.pkl` | Track ID to index mapping |
| `hdbscan_config_{model}.json` | Model configuration metadata |

## Production Features

### 🔄 Incremental Generation
- Checks for existing model files before generation
- Only creates missing models, saving time and resources
- Logs which models exist vs. need generation

### 🔧 Force Regeneration
- Option to recreate all models for updates
- Useful when underlying data changes
- Preserves existing models as backup during generation

### 📊 Status Monitoring
- Health checks for Docker orchestration
- Success/failure markers in `/tmp/`
- Comprehensive logging with timestamps

### 🛡️ Error Handling
- Graceful handling of missing data files
- Continues processing if individual models fail
- Detailed error reporting and logging

### 📈 Performance Optimization
- Memory-efficient processing
- Progress tracking for long operations
- Parallel-ready architecture

## Integration with Backend

The generated models are automatically detected by the backend services:

1. **HDBSCANSimilarityService**: Loads model-specific files
2. **ModelService**: Falls back to base models if needed
3. **API Endpoints**: Exposes model switching capabilities

### Model Loading Priority
1. Model-specific files (e.g., `naive_features_*.pkl`)
2. Base model files (e.g., `hdbscan_model.pkl`)
3. Error handling if no models found

## Troubleshooting

### Common Issues

#### No Models Generated
```bash
# Check prerequisites
docker-compose --profile setup run --rm model-prep python scripts/startup.py --check-only

# Check logs
docker-compose --profile setup logs model-prep
```

#### Partial Model Generation
```bash
# Force regeneration
docker-compose --profile setup run --rm -e FORCE_REGENERATE=true model-prep
```

#### Memory Issues
- Reduce PCA components in model configurations
- Process smaller data subsets for testing
- Ensure sufficient Docker memory allocation

### Log Files
- Container logs: `docker-compose logs model-prep`
- Persistent logs: `backend/logs/model_pipeline.log`
- Success/failure markers: `/tmp/model_prep_*`

## Development

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run with development data
DATA_PATH=./data python model_pipeline.py
```

### Testing
```bash
# Quick test with minimal data
echo "track_id,name,tempo,key" > test_data.csv
echo "test123,Test Song,120,5" >> test_data.csv

DATA_PATH=./test_data python scripts/startup.py --check-only
```

### Adding New Model Types
1. Add configuration to `model_pipeline.py`
2. Update feature preparation logic
3. Add model-specific file patterns
4. Test incremental generation

## Monitoring

### Success Indicators
- Exit code 0
- Success marker file exists: `/tmp/model_prep_success`
- Model files present in models directory
- Docker health check passes

### Failure Indicators  
- Non-zero exit code
- Failure marker file: `/tmp/model_prep_failure`
- Error logs in container output
- Docker health check fails

### Performance Metrics
- Generation time per model (logged)
- File sizes of generated models
- Memory usage during processing
- Cluster quality metrics (silhouette score)

This service ensures reproducible, efficient, and production-ready model generation for the Spotify Recommendation System. 