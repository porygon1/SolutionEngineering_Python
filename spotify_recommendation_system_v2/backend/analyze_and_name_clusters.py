#!/usr/bin/env python3
"""
Analyze and name clusters based on their musical characteristics
"""

import os
import pickle
import asyncio
import asyncpg
import numpy as np
import pandas as pd
from loguru import logger
from sklearn.metrics import silhouette_score
from collections import Counter
import json


async def analyze_and_name_clusters():
    """Analyze cluster characteristics and assign meaningful names"""
    
    # Load trained models and data
    models_dir = "/app/models"
    
    logger.info("🧠 Loading trained models and data...")
    
    # Load cluster labels and embeddings
    with open(os.path.join(models_dir, "cluster_labels.pkl"), 'rb') as f:
        cluster_labels = pickle.load(f)
    
    with open(os.path.join(models_dir, "audio_embeddings.pkl"), 'rb') as f:
        audio_embeddings = pickle.load(f)
    
    with open(os.path.join(models_dir, "song_indices.pkl"), 'rb') as f:
        song_indices = pickle.load(f)
    
    track_ids = song_indices['track_ids']
    
    logger.info(f"📊 Loaded {len(cluster_labels)} tracks with {len(set(cluster_labels))} clusters")
    
    # Connect to database
    database_url = os.environ.get(
        'DATABASE_URL', 
        'postgresql://spotify_user:spotify_password@database:5432/spotify_recommendations'
    )
    
    logger.info("🔌 Connecting to database...")
    conn = await asyncpg.connect(database_url)
    
    try:
        # Get track data with audio features
        tracks_query = """
            SELECT 
                t.id, t.name, t.popularity,
                t.acousticness, t.danceability, t.energy, t.instrumentalness,
                t.liveness, t.loudness, t.speechiness, t.tempo, t.valence,
                t.key, t.mode, t.time_signature, t.cluster_id,
                a.name as artist_name,
                al.name as album_name,
                al.release_date
            FROM tracks t
            LEFT JOIN artists a ON t.artist_id = a.id
            LEFT JOIN albums al ON t.album_id = al.id
            WHERE t.cluster_id IS NOT NULL AND t.cluster_id != -1
            ORDER BY t.cluster_id
        """
        
        tracks_data = await conn.fetch(tracks_query)
        df = pd.DataFrame([dict(row) for row in tracks_data])
        
        logger.info(f"📈 Retrieved {len(df)} tracks from database")
        
        # Calculate cohesion scores for each cluster
        logger.info("🎯 Calculating cluster cohesion scores...")
        cluster_cohesion = {}
        
        for cluster_id in sorted(set(cluster_labels)):
            if cluster_id == -1:  # Skip noise
                continue
                
            cluster_mask = cluster_labels == cluster_id
            if np.sum(cluster_mask) < 2:  # Need at least 2 points for silhouette
                cluster_cohesion[cluster_id] = 0.0
                continue
                
            cluster_embeddings = audio_embeddings[cluster_mask]
            cluster_labels_subset = cluster_labels[cluster_mask]
            
            # Calculate silhouette score for this cluster
            if len(set(cluster_labels)) > 1:  # Need multiple clusters for silhouette
                try:
                    cohesion = silhouette_score(audio_embeddings, cluster_labels, 
                                              labels=[cluster_id] * len(cluster_embeddings))
                    cluster_cohesion[cluster_id] = max(0.0, cohesion)  # Ensure non-negative
                except:
                    cluster_cohesion[cluster_id] = 0.5  # Default moderate cohesion
            else:
                cluster_cohesion[cluster_id] = 0.5
        
        # Analyze each cluster and generate names
        cluster_analyses = []
        
        for cluster_id in sorted(df['cluster_id'].unique()):
            if cluster_id == -1:
                continue
                
            cluster_df = df[df['cluster_id'] == cluster_id]
            
            if len(cluster_df) == 0:
                continue
            
            logger.info(f"🔍 Analyzing Cluster {cluster_id} ({len(cluster_df)} tracks)")
            
            # Calculate audio feature statistics
            audio_features = ['acousticness', 'danceability', 'energy', 'instrumentalness',
                            'liveness', 'loudness', 'speechiness', 'tempo', 'valence']
            
            feature_stats = {}
            for feature in audio_features:
                feature_stats[feature] = {
                    'mean': float(cluster_df[feature].mean()),
                    'std': float(cluster_df[feature].std()),
                    'min': float(cluster_df[feature].min()),
                    'max': float(cluster_df[feature].max())
                }
            
            # Analyze musical characteristics
            avg_energy = cluster_df['energy'].mean()
            avg_valence = cluster_df['valence'].mean()
            avg_danceability = cluster_df['danceability'].mean()
            avg_acousticness = cluster_df['acousticness'].mean()
            avg_instrumentalness = cluster_df['instrumentalness'].mean()
            avg_tempo = cluster_df['tempo'].mean()
            avg_speechiness = cluster_df['speechiness'].mean()
            
            # Determine dominant musical key and mode
            dominant_key = cluster_df['key'].mode().iloc[0] if len(cluster_df['key'].mode()) > 0 else 0
            dominant_mode = cluster_df['mode'].mode().iloc[0] if len(cluster_df['mode'].mode()) > 0 else 1
            
            # Key names
            key_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            key_name = key_names[int(dominant_key)]
            mode_name = "Major" if dominant_mode == 1 else "Minor"
            
            # Analyze era based on release dates
            release_years = []
            for date_str in cluster_df['release_date'].dropna():
                try:
                    if isinstance(date_str, str) and len(date_str) >= 4:
                        year = int(date_str[:4])
                        if 1950 <= year <= 2024:
                            release_years.append(year)
                except:
                    continue
            
            era = "Mixed Era"
            if release_years:
                avg_year = np.mean(release_years)
                if avg_year < 1980:
                    era = "Classic Era"
                elif avg_year < 1990:
                    era = "80s Era"
                elif avg_year < 2000:
                    era = "90s Era"
                elif avg_year < 2010:
                    era = "2000s Era"
                elif avg_year < 2020:
                    era = "2010s Era"
                else:
                    era = "Modern Era"
            
            # Generate cluster name based on characteristics
            name_parts = []
            
            # Energy level
            if avg_energy > 0.8:
                name_parts.append("High-Energy")
            elif avg_energy > 0.6:
                name_parts.append("Energetic")
            elif avg_energy < 0.3:
                name_parts.append("Mellow")
            else:
                name_parts.append("Moderate")
            
            # Mood/Valence
            if avg_valence > 0.7:
                name_parts.append("Upbeat")
            elif avg_valence > 0.5:
                name_parts.append("Positive")
            elif avg_valence < 0.3:
                name_parts.append("Melancholic")
            else:
                name_parts.append("Balanced")
            
            # Style characteristics
            if avg_danceability > 0.8:
                name_parts.append("Dance")
            elif avg_acousticness > 0.7:
                name_parts.append("Acoustic")
            elif avg_instrumentalness > 0.5:
                name_parts.append("Instrumental")
            elif avg_speechiness > 0.33:
                name_parts.append("Vocal-Heavy")
            
            # Tempo
            if avg_tempo > 140:
                name_parts.append("Fast-Tempo")
            elif avg_tempo < 80:
                name_parts.append("Slow-Tempo")
            
            # Generate final name
            if len(name_parts) > 3:
                name_parts = name_parts[:3]  # Limit to 3 descriptors
            
            cluster_name = " ".join(name_parts)
            if not cluster_name.strip():
                cluster_name = f"Mixed Style {key_name} {mode_name}"
            else:
                cluster_name += f" ({key_name} {mode_name})"
            
            # Generate description
            description = f"A cluster of {len(cluster_df)} tracks characterized by "
            descriptors = []
            
            if avg_energy > 0.7:
                descriptors.append("high energy")
            if avg_danceability > 0.7:
                descriptors.append("strong danceability")
            if avg_valence > 0.6:
                descriptors.append("positive mood")
            elif avg_valence < 0.4:
                descriptors.append("melancholic mood")
            if avg_acousticness > 0.5:
                descriptors.append("acoustic elements")
            if avg_tempo > 120:
                descriptors.append("upbeat tempo")
            elif avg_tempo < 90:
                descriptors.append("slow tempo")
            
            if descriptors:
                description += ", ".join(descriptors)
            else:
                description += "diverse musical characteristics"
            
            description += f". Predominantly in {key_name} {mode_name} with an average tempo of {avg_tempo:.0f} BPM."
            
            # Determine dominant features
            dominant_features = []
            if avg_energy > 0.7:
                dominant_features.append("High Energy")
            if avg_danceability > 0.7:
                dominant_features.append("Danceable")
            if avg_valence > 0.6:
                dominant_features.append("Positive")
            elif avg_valence < 0.4:
                dominant_features.append("Melancholic")
            if avg_acousticness > 0.5:
                dominant_features.append("Acoustic")
            if avg_instrumentalness > 0.5:
                dominant_features.append("Instrumental")
            if avg_speechiness > 0.33:
                dominant_features.append("Vocal-Heavy")
            
            # Get cohesion score
            cohesion_score = cluster_cohesion.get(cluster_id, 0.5)
            
            cluster_analyses.append({
                'id': cluster_id,
                'name': cluster_name,
                'description': description,
                'size': len(cluster_df),
                'cohesion_score': cohesion_score,
                'dominant_features': dominant_features,
                'era': era,
                'audio_stats': feature_stats,
                'key_signature': f"{key_name} {mode_name}",
                'avg_tempo': avg_tempo,
                'avg_popularity': float(cluster_df['popularity'].mean())
            })
        
        # Update database with cluster information
        logger.info("💾 Updating database with cluster information...")
        
        # First, create clusters table if it doesn't exist
        create_clusters_table = """
            CREATE TABLE IF NOT EXISTS clusters (
                id INTEGER PRIMARY KEY,
                name VARCHAR(255),
                description TEXT,
                size INTEGER,
                cohesion_score FLOAT,
                separation_score FLOAT,
                dominant_genres TEXT[],
                dominant_features TEXT[],
                era VARCHAR(50),
                audio_stats JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """
        await conn.execute(create_clusters_table)
        
        # Clear existing cluster data
        await conn.execute("DELETE FROM clusters")
        
        # Insert new cluster data
        for cluster in cluster_analyses:
            insert_query = """
                INSERT INTO clusters (
                    id, name, description, size, cohesion_score, 
                    dominant_features, era, audio_stats
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """
            
            await conn.execute(
                insert_query,
                cluster['id'],
                cluster['name'],
                cluster['description'],
                cluster['size'],
                cluster['cohesion_score'],
                cluster['dominant_features'],
                cluster['era'],
                json.dumps(cluster['audio_stats'])
            )
        
        logger.success(f"✅ Successfully analyzed and named {len(cluster_analyses)} clusters!")
        
        # Print summary
        logger.info("📋 Cluster Summary:")
        for cluster in sorted(cluster_analyses, key=lambda x: x['size'], reverse=True)[:10]:
            logger.info(f"  {cluster['name']} - {cluster['size']} tracks (cohesion: {cluster['cohesion_score']:.3f})")
    
    finally:
        await conn.close()
        logger.info("🔌 Database connection closed")


if __name__ == "__main__":
    asyncio.run(analyze_and_name_clusters()) 