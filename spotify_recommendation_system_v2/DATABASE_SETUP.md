# Database Setup Guide - Spotify Music Recommendation System v2

This guide explains the PostgreSQL database setup for the Spotify Music Recommendation System v2, including schema design, data import, and optimization strategies.

## 🏗️ Architecture Overview

The system uses a **normalized PostgreSQL database** designed for:
- **High performance** music similarity queries
- **Scalable** recommendation processing
- **Data integrity** with proper constraints
- **Advanced indexing** for fast text and similarity searches

## 📊 Database Schema

### Core Entities

#### 1. Artists Table
```sql
Table: artists
- id (VARCHAR(22), PRIMARY KEY) - Spotify Artist ID
- name (VARCHAR(255), NOT NULL) - Artist name
- popularity (INTEGER, 0-100) - Spotify popularity score
- followers (INTEGER) - Number of followers
- genres (ARRAY<STRING>) - Array of genre tags
- spotify_type (VARCHAR(50)) - Always 'artist'
- created_at, updated_at (TIMESTAMP) - Audit fields
```

#### 2. Albums Table
```sql
Table: albums
- id (VARCHAR(22), PRIMARY KEY) - Spotify Album ID
- name (VARCHAR(255), NOT NULL) - Album name
- album_type (VARCHAR(50)) - album, single, compilation
- release_date (VARCHAR(10)) - YYYY-MM-DD format
- total_tracks (INTEGER) - Number of tracks
- artist_id (VARCHAR(22), FOREIGN KEY) - References artists.id
- available_markets (ARRAY<STRING>) - Country codes
- external_urls, images (JSON) - Spotify metadata
- created_at, updated_at (TIMESTAMP) - Audit fields
```

#### 3. Tracks Table (Main Entity)
```sql
Table: tracks
- id (VARCHAR(22), PRIMARY KEY) - Spotify Track ID
- name (VARCHAR(255), NOT NULL) - Track name
- artist_id (VARCHAR(22), FOREIGN KEY) - References artists.id
- album_id (VARCHAR(22), FOREIGN KEY) - References albums.id
- popularity (INTEGER, 0-100) - Spotify popularity score
- duration_ms (INTEGER) - Track length in milliseconds

-- Audio Features (Spotify API)
- acousticness, danceability, energy (FLOAT, 0-1)
- instrumentalness, liveness, speechiness (FLOAT, 0-1)
- valence (FLOAT, 0-1) - Musical positivity
- loudness (FLOAT) - dB level
- tempo (FLOAT) - BPM

-- Musical Features
- key (INTEGER, 0-11) - Pitch class
- mode (INTEGER, 0-1) - 0=minor, 1=major
- time_signature (INTEGER, 1-7) - Beats per measure

-- ML Model Fields
- cluster_id (INTEGER) - HDBSCAN cluster assignment
- cluster_probability (FLOAT) - Cluster membership probability

- created_at, updated_at (TIMESTAMP) - Audit fields
```

#### 4. Audio Features Table (Low-level Analysis)
```sql
Table: audio_features
- id (SERIAL, PRIMARY KEY) - Auto-increment ID
- track_id (VARCHAR(22), FOREIGN KEY) - References tracks.id
- chroma_1 to chroma_12 (FLOAT) - Chromagram features
- mel_features (JSON) - Array of 128 MEL-frequency values
- mfcc_features (JSON) - Array of 48 MFCC values
- spectral_contrast_1 to spectral_contrast_7 (FLOAT)
- tonnetz_1 to tonnetz_6 (FLOAT) - Tonal centroid features
- zcr (FLOAT) - Zero crossing rate
- spectral_centroid, spectral_bandwidth (FLOAT)
- created_at, updated_at (TIMESTAMP)
```

#### 5. Lyrics Features Table
```sql
Table: lyrics_features
- id (SERIAL, PRIMARY KEY) - Auto-increment ID
- track_id (VARCHAR(22), FOREIGN KEY) - References tracks.id
- mean_syllables_word (FLOAT) - Average syllables per word
- mean_words_sentence (FLOAT) - Average words per sentence
- n_sentences, n_words (INTEGER) - Text statistics
- sentence_similarity (FLOAT, 0-1) - Internal similarity
- vocabulary_wealth (FLOAT, 0-1) - Lexical diversity
- created_at, updated_at (TIMESTAMP)
```

### ML and Analytics Tables

#### 6. Clusters Table
```sql
Table: clusters
- id (INTEGER, PRIMARY KEY) - HDBSCAN cluster ID
- name (VARCHAR(255)) - Human-readable name
- description (TEXT) - Cluster description
- size (INTEGER) - Number of tracks in cluster
- cohesion_score (FLOAT) - Internal cluster quality
- separation_score (FLOAT) - Distance from other clusters
- dominant_genres (ARRAY<STRING>) - Most common genres
- dominant_features (ARRAY<STRING>) - Key audio characteristics
- audio_stats (JSON) - Detailed feature statistics
- created_at, updated_at (TIMESTAMP)
```

#### 7. User Interactions Table
```sql
Table: user_interactions
- id (UUID, PRIMARY KEY) - Unique interaction ID
- user_id (VARCHAR(255)) - User identifier
- session_id (VARCHAR(255)) - Session identifier
- interaction_type (VARCHAR(50)) - like, dislike, play, skip
- track_id (VARCHAR(22), FOREIGN KEY) - References tracks.id
- recommendation_type (VARCHAR(50)) - cluster, global, hybrid
- rating (INTEGER, 1-5) - User rating
- created_at (TIMESTAMP) - Interaction timestamp
```

#### 8. Recommendation Cache Table
```sql
Table: recommendation_cache
- id (UUID, PRIMARY KEY) - Cache entry ID
- cache_key (VARCHAR(255), UNIQUE) - Hash of request parameters
- input_tracks (ARRAY<STRING>) - Input track IDs
- recommended_tracks (ARRAY<STRING>) - Output track IDs
- similarity_scores (ARRAY<FLOAT>) - Confidence scores
- processing_time_ms (FLOAT) - Response time
- expires_at (TIMESTAMP) - Cache expiration
- hit_count (INTEGER) - Usage counter
```

## 🔧 Database Setup Instructions

### 1. Using Docker Compose (Recommended)

```bash
# Start PostgreSQL with all services
docker-compose up database -d

# Wait for database to be ready
docker-compose logs database

# Run data import
docker-compose --profile setup up data-import

# Start the full application
docker-compose up
```

### 2. Manual Setup

#### Prerequisites
- PostgreSQL 15+
- Python 3.11+
- Required CSV data files in `../data/raw/`

#### Step 1: Create Database
```bash
sudo -u postgres createdb spotify_recommendations
sudo -u postgres createuser -P spotify_user
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE spotify_recommendations TO spotify_user;"
```

#### Step 2: Run Initialization Script
```bash
psql -U spotify_user -d spotify_recommendations -f database/init.sql
```

#### Step 3: Install Python Dependencies
```bash
cd backend
pip install -r requirements.txt
```

#### Step 4: Run Data Import
```bash
cd backend
python -m app.import_data
```

## 📈 Performance Optimizations

### Indexes Created
```sql
-- Text search indexes
CREATE INDEX idx_tracks_search ON tracks USING gin(name gin_trgm_ops);
CREATE INDEX idx_artists_search ON artists USING gin(name gin_trgm_ops);

-- Audio feature indexes for clustering
CREATE INDEX idx_tracks_audio_features ON tracks(energy, valence, danceability);
CREATE INDEX idx_tracks_cluster ON tracks(cluster_id);

-- Performance indexes
CREATE INDEX idx_tracks_popularity ON tracks(popularity DESC);
CREATE INDEX idx_artists_popularity ON artists(popularity DESC);
CREATE INDEX idx_albums_release_date ON albums(release_date);
```

### Custom Functions
```sql
-- Euclidean distance for audio similarity
SELECT euclidean_distance(ARRAY[0.8, 0.6, 0.9], ARRAY[0.7, 0.5, 0.8]);

-- Cosine similarity for feature vectors
SELECT cosine_similarity(ARRAY[0.1, 0.2, 0.3], ARRAY[0.2, 0.3, 0.4]);
```

## 🔄 Data Import Process

### CSV Files Required
- `spotify_tracks.csv` - Main track data (~101K rows)
- `spotify_artists.csv` - Artist metadata
- `spotify_albums.csv` - Album information
- `low_level_audio_features.csv` - Audio analysis data
- `lyrics_features.csv` - Text analysis data

### Import Order (Respects Foreign Keys)
1. **Artists** - No dependencies
2. **Albums** - Depends on Artists
3. **Tracks** - Depends on Artists and Albums
4. **Audio Features** - Depends on Tracks
5. **Lyrics Features** - Depends on Tracks

### Import Configuration
```python
# app/config.py
IMPORT_BATCH_SIZE = 1000        # Records per batch
IMPORT_SKIP_DUPLICATES = True   # Skip existing records
IMPORT_VALIDATE_DATA = True     # Validate before insert
```

### Data Validation
- **Required Fields**: Validates non-null constraints
- **Data Types**: Converts and validates numeric values
- **Constraints**: Enforces check constraints (e.g., popularity 0-100)
- **Foreign Keys**: Validates relationships exist

## 🔍 Query Examples

### Find Similar Tracks
```sql
-- Get tracks similar to a specific track by audio features
SELECT t.id, t.name, a.name as artist_name,
       euclidean_distance(
         ARRAY[t.energy, t.valence, t.danceability, t.tempo/200.0],
         ARRAY[0.8, 0.6, 0.7, 0.6]
       ) as similarity_score
FROM tracks t
JOIN artists a ON t.artist_id = a.id
WHERE t.cluster_id = (SELECT cluster_id FROM tracks WHERE id = 'target_track_id')
ORDER BY similarity_score ASC
LIMIT 10;
```

### Cluster Analysis
```sql
-- Get cluster statistics with dominant characteristics
SELECT 
    c.id,
    c.name,
    c.size,
    c.dominant_genres,
    AVG(t.energy) as avg_energy,
    AVG(t.valence) as avg_valence,
    COUNT(DISTINCT t.artist_id) as unique_artists
FROM clusters c
JOIN tracks t ON c.id = t.cluster_id
GROUP BY c.id, c.name, c.size, c.dominant_genres
ORDER BY c.size DESC;
```

### Search Tracks
```sql
-- Full-text search with similarity ranking
SELECT t.id, t.name, a.name as artist_name,
       similarity(t.name, 'search query') as name_similarity
FROM tracks t
JOIN artists a ON t.artist_id = a.id
WHERE t.name % 'search query' OR a.name % 'search query'
ORDER BY name_similarity DESC
LIMIT 20;
```

## 🛠️ Maintenance Tasks

### Regular Maintenance
```sql
-- Update table statistics
ANALYZE;

-- Vacuum tables to reclaim space
VACUUM ANALYZE tracks;
VACUUM ANALYZE audio_features;

-- Clean old cache entries
DELETE FROM recommendation_cache WHERE expires_at < NOW();

-- Clean old performance logs
SELECT cleanup_performance_logs(30);
```

### Performance Monitoring
```sql
-- Check slow queries
SELECT query, mean_exec_time, calls, total_exec_time
FROM pg_stat_statements
WHERE mean_exec_time > 100
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
WHERE idx_scan = 0;
```

## 🔐 Security Considerations

### Database Security
- **Limited Permissions**: Application user has only necessary privileges
- **Connection Security**: Uses encrypted connections in production
- **Input Validation**: All inputs validated before database interaction
- **SQL Injection Prevention**: Uses parameterized queries exclusively

### Backup Strategy
```bash
# Daily backup
pg_dump -U spotify_user -h localhost spotify_recommendations > backup_$(date +%Y%m%d).sql

# Restore from backup
psql -U spotify_user -h localhost spotify_recommendations < backup_20240101.sql
```

## 🚀 Scaling Considerations

### Read Replicas
- Configure read replicas for heavy analytical queries
- Route recommendation requests to read replicas
- Keep write operations on master

### Partitioning
```sql
-- Partition user_interactions by date for better performance
CREATE TABLE user_interactions_2024_01 PARTITION OF user_interactions
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

### Connection Pooling
- Use PgBouncer for connection pooling
- Configure appropriate pool sizes for your workload

## 📋 Troubleshooting

### Common Issues

#### 1. Import Errors
```bash
# Check CSV file format
head -n 5 data/raw/spotify_tracks.csv

# Validate foreign key relationships
SELECT COUNT(*) FROM tracks WHERE artist_id NOT IN (SELECT id FROM artists);
```

#### 2. Performance Issues
```sql
-- Check missing indexes
SELECT schemaname, tablename, attname, n_distinct, correlation
FROM pg_stats
WHERE schemaname = 'public' AND n_distinct > 100;

-- Monitor active queries
SELECT pid, now() - pg_stat_activity.query_start AS duration, query
FROM pg_stat_activity
WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes';
```

#### 3. Connection Issues
```bash
# Check PostgreSQL status
systemctl status postgresql

# Check connection limits
SELECT * FROM pg_stat_activity;
```

## 📚 Additional Resources

- [PostgreSQL Performance Tuning](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [SQLAlchemy Async Documentation](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [FastAPI Database Integration](https://fastapi.tiangolo.com/tutorial/sql-databases/)

---

This database setup provides a robust foundation for the Spotify Music Recommendation System v2, ensuring **data integrity**, **high performance**, and **scalability** for production use. 