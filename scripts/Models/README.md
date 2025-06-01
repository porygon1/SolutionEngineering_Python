# 🤖 HDBSCAN Music Clustering & KNN Recommendation Models

[![Jupyter](https://img.shields.io/badge/Jupyter-Notebook-orange?logo=jupyter)](https://jupyter.org/)
[![Python](https://img.shields.io/badge/Python-3.11+-green?logo=python)](https://www.python.org/)
[![HDBSCAN](https://img.shields.io/badge/HDBSCAN-Clustering-blue)](https://hdbscan.readthedocs.io/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-ML-orange)](https://scikit-learn.org/)

This directory contains the machine learning pipeline for training **HDBSCAN clustering** and **K-Nearest Neighbors** models for the Spotify Music Recommendation System.

## 📋 Overview

The model training pipeline processes Spotify audio features to create clusters of similar songs and builds recommendation systems that can suggest music based on audio similarity. The approach combines **unsupervised clustering** with **nearest neighbor search** for accurate music discovery.

### 🎯 Key Objectives

1. **Song Clustering**: Group songs by audio similarity using HDBSCAN
2. **Feature Engineering**: Process and normalize audio features for ML
3. **Recommendation Engine**: Build KNN models for similarity search
4. **Model Export**: Save trained models for production deployment

## 📁 Directory Structure

```
scripts/Models/
├── HDBSCAN_Clusters_KNN.ipynb    # Main training notebook (1.8MB)
├── requirements.txt              # Python dependencies for training
└── README.md                     # This documentation
```

## 🧠 Model Architecture

### 1. **Data Processing Pipeline**
- **Multi-source Integration**: Combines track features, audio analysis, and metadata
- **Feature Normalization**: Standardizes audio features for clustering
- **Dimensionality Reduction**: Uses UMAP for visualization and preprocessing
- **Missing Data Handling**: Robust handling of incomplete feature vectors

### 2. **HDBSCAN Clustering**
- **Density-based Clustering**: Identifies natural groupings in audio feature space
- **Noise Detection**: Handles outliers and songs that don't fit clear clusters
- **Parameter Optimization**: Automatic tuning of min_cluster_size and min_samples
- **Cluster Validation**: Quality assessment using silhouette scores

### 3. **K-Nearest Neighbors (KNN)**
- **Global Model**: Finds similar songs across entire dataset
- **Cluster-specific Search**: Recommendations within the same musical cluster
- **Feature Space**: Operates on processed audio embeddings
- **Distance Metrics**: Euclidean distance in normalized feature space

### 4. **Feature Engineering**
- **Audio Features**: Tempo, energy, danceability, valence, acousticness
- **Spectral Features**: MFCCs, chroma vectors, spectral contrast
- **Low-level Analysis**: Zero-crossing rate, spectral centroid, rolloff
- **Lyrical Features**: Sentiment analysis and text-based metrics

## 🚀 Getting Started

### Prerequisites

**Software Requirements:**
- Python 3.11+
- Jupyter Notebook or JupyterLab
- 8GB+ RAM (16GB recommended for large datasets)

**Data Requirements:**
Your `../../data/raw/` directory should contain:
- `spotify_tracks.csv` - Main track dataset with audio features
- `spotify_artists.csv` - Artist information
- `low_level_audio_features.csv` - Spectral analysis features
- `lyrics_features.csv` - Text-based features

### Installation

```bash
# Navigate to the Models directory
cd scripts/Models

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
.\venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Start Jupyter
jupyter notebook HDBSCAN_Clusters_KNN.ipynb
```

### Quick Start Training

```bash
# One-command setup and training
pip install -r requirements.txt && \
jupyter nbconvert --execute HDBSCAN_Clusters_KNN.ipynb --to notebook
```

## 📊 Dataset Requirements

### Input Data Format

| Dataset | Required Columns | Purpose |
|---------|------------------|---------|
| **spotify_tracks.csv** | `id`, `name`, `artists_id`, `danceability`, `energy`, `valence`, `tempo`, `acousticness`, `instrumentalness`, `liveness`, `speechiness`, `loudness`, `duration_ms`, `key`, `mode`, `time_signature`, `popularity` | Main audio features and metadata |
| **low_level_audio_features.csv** | Track ID, MFCC features (1-13), chroma features (1-12), spectral features | Advanced spectral analysis |
| **lyrics_features.csv** | Track ID, sentiment scores, text metrics | Lyrical content analysis |
| **spotify_artists.csv** | `id`, `name`, `popularity`, `genres` | Artist metadata |

### Feature Categories

#### 🎵 **Audio Features (High-level)**
- **Danceability** (0.0-1.0): How suitable for dancing
- **Energy** (0.0-1.0): Perceptual measure of intensity
- **Valence** (0.0-1.0): Musical positivity/mood
- **Acousticness** (0.0-1.0): Acoustic vs. electronic
- **Instrumentalness** (0.0-1.0): Vocal vs. instrumental content
- **Liveness** (0.0-1.0): Live performance likelihood
- **Speechiness** (0.0-1.0): Spoken word content

#### 🎛️ **Technical Features**
- **Tempo** (BPM): Beats per minute
- **Loudness** (dB): Overall volume
- **Key** (0-11): Pitch class (C, C#, D, etc.)
- **Mode** (0-1): Major vs. minor
- **Time Signature** (3-7): Beats per bar

#### 🌊 **Spectral Features (Low-level)**
- **MFCCs** (1-13): Mel-frequency cepstral coefficients
- **Chroma** (1-12): Pitch class profiles
- **Spectral Contrast**: Difference between peaks and valleys
- **Zero Crossing Rate**: Rate of sign changes in signal
- **Spectral Centroid**: Brightness measure
- **Spectral Rolloff**: Frequency below which 85% of energy is contained

## 🔧 Model Training Process

### Step 1: Data Loading & Validation
```python
# Load and validate all datasets
tracks_df = pd.read_csv('../../data/raw/spotify_tracks.csv')
audio_features_df = pd.read_csv('../../data/raw/low_level_audio_features.csv')
lyrics_df = pd.read_csv('../../data/raw/lyrics_features.csv')

# Data quality checks
print(f"Tracks: {len(tracks_df):,} rows")
print(f"Audio features: {len(audio_features_df):,} rows")
print(f"Missing values: {tracks_df.isnull().sum().sum()}")
```

### Step 2: Feature Engineering
```python
# Combine and normalize features
feature_columns = [
    'danceability', 'energy', 'valence', 'tempo',
    'acousticness', 'instrumentalness', 'liveness',
    'speechiness', 'loudness'
]

# Standardization
scaler = StandardScaler()
features_scaled = scaler.fit_transform(tracks_df[feature_columns])
```

### Step 3: HDBSCAN Clustering
```python
# Optimize clustering parameters
clusterer = hdbscan.HDBSCAN(
    min_cluster_size=50,      # Minimum songs per cluster
    min_samples=10,           # Core point threshold
    metric='euclidean',       # Distance metric
    cluster_selection_epsilon=0.5
)

# Fit clustering model
cluster_labels = clusterer.fit_predict(features_scaled)
print(f"Found {len(set(cluster_labels)) - 1} clusters")
print(f"Noise points: {sum(cluster_labels == -1)}")
```

### Step 4: KNN Model Training
```python
# Build recommendation engine
knn_model = NearestNeighbors(
    n_neighbors=20,
    metric='euclidean',
    algorithm='auto'
)

# Fit on processed features
knn_model.fit(features_scaled)
```

### Step 5: Model Export
```python
# Save all models and data
joblib.dump(clusterer, '../../data/models/hdbscan_model.pkl')
joblib.dump(knn_model, '../../data/models/knn_model.pkl')
joblib.dump(features_scaled, '../../data/models/audio_embeddings.pkl')
joblib.dump(cluster_labels, '../../data/models/cluster_labels.pkl')
```

## 📈 Model Evaluation

### Clustering Quality Metrics

#### **Silhouette Score**
```python
from sklearn.metrics import silhouette_score

# Overall clustering quality
silhouette_avg = silhouette_score(features_scaled, cluster_labels)
print(f"Average silhouette score: {silhouette_avg:.3f}")

# Per-cluster analysis
cluster_scores = []
for cluster_id in set(cluster_labels):
    if cluster_id != -1:  # Exclude noise
        mask = cluster_labels == cluster_id
        score = silhouette_score(features_scaled[mask], cluster_labels[mask])
        cluster_scores.append((cluster_id, score))
```

#### **Cluster Characteristics**
```python
# Analyze cluster properties
for cluster_id in sorted(set(cluster_labels)):
    if cluster_id == -1:
        continue
    
    cluster_mask = cluster_labels == cluster_id
    cluster_data = tracks_df[cluster_mask]
    
    print(f"\nCluster {cluster_id} ({sum(cluster_mask)} songs):")
    print(f"  Avg Energy: {cluster_data['energy'].mean():.3f}")
    print(f"  Avg Danceability: {cluster_data['danceability'].mean():.3f}")
    print(f"  Avg Valence: {cluster_data['valence'].mean():.3f}")
    print(f"  Popular genres: {cluster_data['genre'].value_counts().head(3)}")
```

### Recommendation Quality

#### **Similarity Validation**
```python
# Test recommendation quality
def test_recommendations(song_idx, n_recommendations=5):
    distances, indices = knn_model.kneighbors(
        features_scaled[song_idx].reshape(1, -1),
        n_neighbors=n_recommendations + 1
    )
    
    original_song = tracks_df.iloc[song_idx]
    print(f"Original: {original_song['name']} - {original_song['artist']}")
    
    for i, (dist, idx) in enumerate(zip(distances[0][1:], indices[0][1:])):
        rec_song = tracks_df.iloc[idx]
        similarity = 1 - dist
        print(f"{i+1}. {rec_song['name']} - {rec_song['artist']} (sim: {similarity:.3f})")
```

## ⚙️ Hyperparameter Tuning

### HDBSCAN Parameters

| Parameter | Default | Description | Tuning Range |
|-----------|---------|-------------|--------------|
| `min_cluster_size` | 50 | Minimum songs per cluster | 10-200 |
| `min_samples` | 10 | Core point threshold | 5-50 |
| `cluster_selection_epsilon` | 0.5 | DBSCAN-like behavior | 0.0-1.0 |
| `metric` | 'euclidean' | Distance function | euclidean, manhattan, cosine |

### KNN Parameters

| Parameter | Default | Description | Tuning Range |
|-----------|---------|-------------|--------------|
| `n_neighbors` | 20 | Number of recommendations | 5-50 |
| `metric` | 'euclidean' | Distance function | euclidean, cosine, manhattan |
| `algorithm` | 'auto' | Search algorithm | auto, ball_tree, kd_tree, brute |

### Grid Search Example
```python
# Optimize HDBSCAN parameters
from sklearn.model_selection import ParameterGrid

param_grid = {
    'min_cluster_size': [30, 50, 100],
    'min_samples': [5, 10, 20],
    'cluster_selection_epsilon': [0.0, 0.5, 1.0]
}

best_score = -1
best_params = None

for params in ParameterGrid(param_grid):
    clusterer = hdbscan.HDBSCAN(**params)
    labels = clusterer.fit_predict(features_scaled)
    
    if len(set(labels)) > 1:  # Valid clustering
        score = silhouette_score(features_scaled, labels)
        if score > best_score:
            best_score = score
            best_params = params

print(f"Best parameters: {best_params}")
print(f"Best silhouette score: {best_score:.3f}")
```

## 📊 Visualization & Analysis

### Cluster Visualization
```python
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.manifold import TSNE

# t-SNE for 2D visualization
tsne = TSNE(n_components=2, random_state=42)
features_2d = tsne.fit_transform(features_scaled)

# Plot clusters
plt.figure(figsize=(12, 8))
scatter = plt.scatter(features_2d[:, 0], features_2d[:, 1], 
                     c=cluster_labels, cmap='viridis', alpha=0.6)
plt.colorbar(scatter)
plt.title('HDBSCAN Clusters (t-SNE Visualization)')
plt.xlabel('t-SNE Component 1')
plt.ylabel('t-SNE Component 2')
plt.show()
```

### Feature Analysis
```python
# Audio feature distributions by cluster
feature_cols = ['danceability', 'energy', 'valence', 'tempo']

fig, axes = plt.subplots(2, 2, figsize=(15, 10))
axes = axes.ravel()

for i, feature in enumerate(feature_cols):
    for cluster_id in sorted(set(cluster_labels)):
        if cluster_id == -1:
            continue
        
        cluster_data = tracks_df[cluster_labels == cluster_id][feature]
        axes[i].hist(cluster_data, alpha=0.6, label=f'Cluster {cluster_id}')
    
    axes[i].set_title(f'{feature.title()} Distribution')
    axes[i].legend()

plt.tight_layout()
plt.show()
```

## 🔍 Model Interpretation

### Cluster Characterization
```python
# Analyze what makes each cluster unique
def characterize_clusters(features_df, labels):
    cluster_profiles = {}
    
    for cluster_id in sorted(set(labels)):
        if cluster_id == -1:
            continue
            
        cluster_mask = labels == cluster_id
        cluster_features = features_df[cluster_mask]
        
        # Calculate cluster centroid
        centroid = cluster_features.mean()
        
        # Find most distinctive features
        global_mean = features_df.mean()
        feature_importance = abs(centroid - global_mean)
        
        cluster_profiles[cluster_id] = {
            'size': sum(cluster_mask),
            'centroid': centroid,
            'distinctive_features': feature_importance.nlargest(5)
        }
    
    return cluster_profiles

profiles = characterize_clusters(tracks_df[feature_columns], cluster_labels)
```

### Recommendation Explanation
```python
# Explain why songs are recommended
def explain_recommendation(original_idx, recommended_idx, feature_names):
    original_features = features_scaled[original_idx]
    recommended_features = features_scaled[recommended_idx]
    
    # Feature differences
    differences = abs(original_features - recommended_features)
    feature_similarity = 1 - differences
    
    # Most similar features
    most_similar = sorted(zip(feature_names, feature_similarity), 
                         key=lambda x: x[1], reverse=True)
    
    print("Most similar features:")
    for feature, similarity in most_similar[:5]:
        print(f"  {feature}: {similarity:.3f}")
```

## 🚀 Production Deployment

### Model Export Checklist
- [ ] HDBSCAN model saved (`hdbscan_model.pkl`)
- [ ] KNN model saved (`knn_model.pkl`)
- [ ] Feature embeddings saved (`audio_embeddings.pkl`)
- [ ] Cluster labels saved (`cluster_labels.pkl`)
- [ ] Song indices mapping saved (`song_indices.pkl`)
- [ ] Feature scaler saved (for new data processing)

### Model Loading Example
```python
import joblib

# Load all models
hdbscan_model = joblib.load('../../data/models/hdbscan_model.pkl')
knn_model = joblib.load('../../data/models/knn_model.pkl')
embeddings = joblib.load('../../data/models/audio_embeddings.pkl')
labels = joblib.load('../../data/models/cluster_labels.pkl')
indices = joblib.load('../../data/models/song_indices.pkl')

print("All models loaded successfully!")
```

## 🔧 Customization & Extensions

### Adding New Features
```python
# Example: Adding genre-based features
def add_genre_features(tracks_df):
    # One-hot encode genres
    genre_dummies = pd.get_dummies(tracks_df['genre'], prefix='genre')
    
    # Combine with existing features
    extended_features = pd.concat([
        tracks_df[audio_feature_columns],
        genre_dummies
    ], axis=1)
    
    return extended_features
```

### Alternative Clustering Methods
```python
# Compare with other clustering algorithms
from sklearn.cluster import KMeans, DBSCAN

# K-Means comparison
kmeans = KMeans(n_clusters=20, random_state=42)
kmeans_labels = kmeans.fit_predict(features_scaled)

# DBSCAN comparison
dbscan = DBSCAN(eps=0.5, min_samples=10)
dbscan_labels = dbscan.fit_predict(features_scaled)

# Compare clustering quality
print(f"HDBSCAN silhouette: {silhouette_score(features_scaled, cluster_labels):.3f}")
print(f"K-Means silhouette: {silhouette_score(features_scaled, kmeans_labels):.3f}")
print(f"DBSCAN silhouette: {silhouette_score(features_scaled, dbscan_labels):.3f}")
```

## 📚 Dependencies

### Core ML Libraries (requirements.txt)
```txt
# Machine Learning
scikit-learn>=1.6.0         # ML algorithms and metrics
hdbscan>=0.8.33             # Density-based clustering
umap-learn>=0.5.4           # Dimensionality reduction

# Data Processing
pandas>=2.2.0               # Data manipulation
numpy>=2.1.0                # Numerical computing
scipy>=1.15.0               # Scientific computing

# Visualization
matplotlib>=3.8.0           # Basic plotting
seaborn>=0.13.0             # Statistical visualization
plotly>=6.0.0               # Interactive plots

# Utilities
joblib>=1.4.0               # Model serialization
tqdm>=4.67.0                # Progress bars

# Jupyter Environment
jupyter>=1.0.0              # Notebook interface
ipywidgets>=8.0.0           # Interactive widgets
```

## 🚨 Troubleshooting

### Common Issues

#### **Memory Errors**
```python
# Solution: Process data in chunks
def process_in_chunks(data, chunk_size=10000):
    results = []
    for i in range(0, len(data), chunk_size):
        chunk = data[i:i+chunk_size]
        result = process_chunk(chunk)
        results.append(result)
    return pd.concat(results)
```

#### **Poor Clustering Quality**
- **Check feature scaling**: Ensure all features are normalized
- **Adjust parameters**: Try different min_cluster_size values
- **Feature selection**: Remove correlated or noisy features
- **Data quality**: Handle missing values and outliers

#### **Slow Training**
```python
# Enable parallel processing
clusterer = hdbscan.HDBSCAN(
    min_cluster_size=50,
    n_jobs=-1,  # Use all CPU cores
    core_dist_n_jobs=-1
)
```

#### **Model Export Errors**
```python
# Check file permissions and disk space
import os
os.makedirs('../../data/models', exist_ok=True)

# Use compression for large models
joblib.dump(model, 'model.pkl', compress=3)
```

## 📞 Support & Resources

### Documentation
- **HDBSCAN**: [hdbscan.readthedocs.io](https://hdbscan.readthedocs.io/)
- **scikit-learn**: [scikit-learn.org](https://scikit-learn.org/)
- **Pandas**: [pandas.pydata.org](https://pandas.pydata.org/)

### Academic References
- **HDBSCAN Paper**: "Accelerated Hierarchical Density Based Clustering" (Malzer & Baum, 2019)
- **Music Information Retrieval**: "Music Similarity and Retrieval" (Serra, 2012)
- **Audio Feature Analysis**: "Automatic Musical Pattern Feature Extraction" (Tzanetakis & Cook, 2002)

---

**For questions about the notebook or model training, please check the inline comments in `HDBSCAN_Clusters_KNN.ipynb` or refer to the main project [README](../../README.md).** 