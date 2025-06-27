#!/usr/bin/env python3
"""
Generate HDBSCAN Model Variants
This script creates different HDBSCAN model variants based on different feature preprocessing approaches
to fix the issue where all models return the same results.
"""

import pandas as pd
import numpy as np
import pickle
import json
import os
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.decomposition import PCA
from sklearn.neighbors import NearestNeighbors
import hdbscan

# Ensure models directory exists
os.makedirs('../../data/models', exist_ok=True)

def create_model_variant(df_features, df_spotify_tracks, model_name, config):
    """Create a specific model variant with its own embeddings and KNN model"""
    
    print(f"\n🔧 Creating model variant: {model_name}")
    print(f"📊 Features shape: {df_features.shape}")
    
    # Remove label column if present
    feature_columns = [col for col in df_features.columns if col != 'label']
    X = df_features[feature_columns].values
    
    # Apply scaling if specified in config
    if config.get('has_scaler', False):
        scaler = MinMaxScaler()
        X = scaler.fit_transform(X)
        print(f"✅ Applied MinMaxScaler")
    
    # Apply PCA if specified in config
    if config.get('has_pca', False):
        n_components = config.get('pca_components', 6)
        pca = PCA(n_components=n_components)
        X = pca.fit_transform(X)
        print(f"✅ Applied PCA with {n_components} components")
    
    # Create HDBSCAN clustering
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=config.get('min_cluster_size', 30),
        min_samples=config.get('min_samples', 5),
        metric=config.get('metric', 'euclidean'),
        cluster_selection_method=config.get('cluster_selection_method', 'eom'),
        allow_single_cluster=False
    )
    
    cluster_labels = clusterer.fit_predict(X)
    n_clusters = len(np.unique(cluster_labels[cluster_labels != -1]))
    n_noise = np.sum(cluster_labels == -1)
    print(f"📈 Clusters: {n_clusters}, Noise: {n_noise} ({n_noise/len(cluster_labels)*100:.1f}%)")
    
    # Create KNN model
    knn_model = NearestNeighbors(n_neighbors=20, algorithm='auto', metric='euclidean')
    knn_model.fit(X)
    print(f"🔍 KNN model trained")
    
    # Export model-specific files
    model_prefix = f"{model_name}_"
    
    # Export HDBSCAN model
    with open(f'../../data/models/{model_prefix}hdbscan_model.pkl', 'wb') as f:
        pickle.dump(clusterer, f)
    
    # Export KNN model
    with open(f'../../data/models/{model_prefix}knn_model.pkl', 'wb') as f:
        pickle.dump(knn_model, f)
    
    # Export embeddings
    with open(f'../../data/models/{model_prefix}audio_embeddings.pkl', 'wb') as f:
        pickle.dump(X, f)
    
    # Export cluster labels
    with open(f'../../data/models/{model_prefix}cluster_labels.pkl', 'wb') as f:
        pickle.dump(cluster_labels, f)
    
    # Export song indices (same for all models)
    song_indices = {
        'track_ids': df_spotify_tracks['id'].values,
        'track_names': df_spotify_tracks['name'].values,
        'track_artists': df_spotify_tracks['artists_id'].values,
        'track_uris': df_spotify_tracks['uri'].values
    }
    with open(f'../../data/models/{model_prefix}song_indices.pkl', 'wb') as f:
        pickle.dump(song_indices, f)
    
    print(f"✅ Model variant {model_name} exported successfully!")
    
    return {
        'n_features': X.shape[1],
        'n_clusters': n_clusters,
        'n_noise': n_noise,
        'noise_percentage': n_noise/len(cluster_labels)*100
    }

def main():
    """Generate all HDBSCAN model variants"""
    
    print("🚀 Loading data...")
    
    # Load base data
    df_spotify_tracks = pd.read_csv("../../data/raw/spotify_tracks.csv")
    df_low_level_audio_features = pd.read_csv("../../data/raw/low_level_audio_features.csv")
    
    # Clean base track data
    df_tracks_clean = df_spotify_tracks.copy()
    columns_to_drop = [
        "Unnamed: 0", "analysis_url", "available_markets", "disc_number", 
        "href", "lyrics", "playlist", "preview_url", "track_number", 
        "uri", "type", "track_name_prev", "track_href", "artists_id", 
        "album_id", "name", "country"
    ]
    for col in columns_to_drop:
        if col in df_tracks_clean.columns:
            df_tracks_clean.drop(col, axis=1, inplace=True)
    
    print(f"📊 Track features: {df_tracks_clean.columns.tolist()}")
    print(f"📊 Tracks: {len(df_tracks_clean)}")
    
    # Add log transformations
    df_tracks_clean["speechiness_log"] = np.log(df_tracks_clean["speechiness"] + 1)
    df_tracks_clean["liveness_log"] = np.log(df_tracks_clean["liveness"] + 1)
    
    # Prepare different feature sets
    
    # 1. Naive Features (basic audio features)
    naive_features = ["key", "time_signature", "tempo", "mode", "valence", "energy",
                     "acousticness", "danceability", "instrumentalness", "liveness", 
                     "loudness", "speechiness"]
    df_naive = df_tracks_clean[naive_features].copy()
    
    # 2. PCA Features (PCA-reduced basic features)
    df_pca_source = df_tracks_clean[["key", "time_signature", "tempo", "mode", "valence"]].copy()
    
    # 3. Combined Features (track + low-level audio features)
    df_combined = df_tracks_clean.copy()
    # Merge with low-level audio features
    df_llav_merged = pd.merge(df_combined[["id"]], df_low_level_audio_features, 
                             how="left", left_on='id', right_on="track_id")
    if not df_llav_merged.empty:
        # Add low-level features to combined
        llav_feature_cols = [col for col in df_llav_merged.columns 
                            if col not in ['id', 'track_id', 'Unnamed: 0']]
        df_combined = pd.concat([df_combined, df_llav_merged[llav_feature_cols]], axis=1)
        df_combined.dropna(inplace=True)
    
    # 4. LLAV Features (low-level audio features only)
    df_llav = df_llav_merged.copy()
    if 'Unnamed: 0' in df_llav.columns:
        df_llav.drop('Unnamed: 0', axis=1, inplace=True)
    df_llav.drop(['id', 'track_id'], axis=1, inplace=True, errors='ignore')
    df_llav.dropna(inplace=True)
    
    # 5. LLAV PCA Features (PCA-reduced low-level audio features)
    df_llav_pca_source = df_llav.copy()
    
    # Load model configurations
    configs = {
        'naive_features': {
            "model_name": "naive_features",
            "approach": "Naive Audio Features",
            "feature_type": "basic_audio_features",
            "has_pca": False,
            "has_scaler": True,
            "cluster_based": True,
            "min_cluster_size": 30,
            "min_samples": 5,
            "metric": "euclidean",
            "cluster_selection_method": "eom"
        },
        'pca_features': {
            "model_name": "pca_features",
            "approach": "PCA-Reduced Audio Features", 
            "feature_type": "pca_audio_features",
            "has_pca": True,
            "pca_components": 6,
            "has_scaler": True,
            "cluster_based": True,
            "min_cluster_size": 30,
            "min_samples": 5,
            "metric": "euclidean",
            "cluster_selection_method": "eom"
        },
        'combined_features': {
            "model_name": "combined_features",
            "approach": "Combined Audio Features",
            "feature_type": "combined_features",
            "has_pca": False,
            "has_scaler": True,
            "cluster_based": True,
            "min_cluster_size": 30,
            "min_samples": 5,
            "metric": "euclidean",
            "cluster_selection_method": "eom"
        },
        'llav_features': {
            "model_name": "llav_features",
            "approach": "Low-Level Audio Features",
            "feature_type": "low_level_audio_features",
            "has_pca": False,
            "has_scaler": True,
            "cluster_based": True,
            "min_cluster_size": 30,
            "min_samples": 5,
            "metric": "euclidean",
            "cluster_selection_method": "eom"
        },
        'llav_pca': {
            "model_name": "llav_pca",
            "approach": "PCA Low-Level Audio Features",
            "feature_type": "pca_low_level_audio_features",
            "has_pca": True,
            "pca_components": 60,
            "has_scaler": True,
            "cluster_based": True,
            "min_cluster_size": 30,
            "min_samples": 5,
            "metric": "euclidean",
            "cluster_selection_method": "eom"
        }
    }
    
    # Create model variants
    results = {}
    
    # Only create models if we have sufficient data
    if len(df_naive) > 100:
        results['naive_features'] = create_model_variant(
            df_naive, df_spotify_tracks, 'naive_features', configs['naive_features']
        )
    
    if len(df_pca_source) > 100:
        results['pca_features'] = create_model_variant(
            df_pca_source, df_spotify_tracks, 'pca_features', configs['pca_features']
        )
    
    if len(df_combined) > 100:
        results['combined_features'] = create_model_variant(
            df_combined, df_spotify_tracks, 'combined_features', configs['combined_features']
        )
    
    if len(df_llav) > 100:
        results['llav_features'] = create_model_variant(
            df_llav, df_spotify_tracks, 'llav_features', configs['llav_features']
        )
    
    if len(df_llav_pca_source) > 100:
        results['llav_pca'] = create_model_variant(
            df_llav_pca_source, df_spotify_tracks, 'llav_pca', configs['llav_pca']
        )
    
    # Print summary
    print("\n📋 Model Generation Summary:")
    print("=" * 50)
    for model_name, stats in results.items():
        print(f"{model_name:20} | Features: {stats['n_features']:3d} | Clusters: {stats['n_clusters']:3d} | Noise: {stats['noise_percentage']:5.1f}%")
    
    print(f"\n✅ Generated {len(results)} model variants successfully!")
    print("🔧 Next step: Update the backend to load model-specific files")

if __name__ == "__main__":
    main() 