#!/usr/bin/env python3
"""
Simple cluster analysis and naming script
"""

import asyncio
import asyncpg
import json


async def analyze_clusters():
    """Analyze and name clusters based on audio features"""
    
    # Connect to database
    database_url = 'postgresql://spotify_user:spotify_password@database:5432/spotify_recommendations'
    
    print("🔌 Connecting to database...")
    conn = await asyncpg.connect(database_url)
    
    try:
        # Create clusters table
        create_table_sql = """
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
        await conn.execute(create_table_sql)
        print("✅ Clusters table created")
        
        # Clear existing data
        await conn.execute("DELETE FROM clusters")
        
        # Get cluster statistics
        cluster_stats_query = """
            SELECT 
                cluster_id,
                COUNT(*) as size,
                AVG(energy) as avg_energy,
                AVG(valence) as avg_valence,
                AVG(danceability) as avg_danceability,
                AVG(acousticness) as avg_acousticness,
                AVG(instrumentalness) as avg_instrumentalness,
                AVG(tempo) as avg_tempo,
                AVG(speechiness) as avg_speechiness,
                AVG(popularity) as avg_popularity
            FROM tracks 
            WHERE cluster_id IS NOT NULL AND cluster_id != -1
            GROUP BY cluster_id
            ORDER BY cluster_id
        """
        
        cluster_data = await conn.fetch(cluster_stats_query)
        print(f"📊 Found {len(cluster_data)} clusters")
        
        for cluster in cluster_data:
            cluster_id = cluster['cluster_id']
            size = cluster['size']
            
            avg_energy = float(cluster['avg_energy'] or 0)
            avg_valence = float(cluster['avg_valence'] or 0)
            avg_danceability = float(cluster['avg_danceability'] or 0)
            avg_acousticness = float(cluster['avg_acousticness'] or 0)
            avg_instrumentalness = float(cluster['avg_instrumentalness'] or 0)
            avg_tempo = float(cluster['avg_tempo'] or 120)
            avg_speechiness = float(cluster['avg_speechiness'] or 0)
            
            # Generate name
            name_parts = []
            
            if avg_energy > 0.8:
                name_parts.append("High-Energy")
            elif avg_energy > 0.6:
                name_parts.append("Energetic")
            elif avg_energy < 0.3:
                name_parts.append("Mellow")
            else:
                name_parts.append("Moderate")
            
            if avg_valence > 0.7:
                name_parts.append("Upbeat")
            elif avg_valence > 0.5:
                name_parts.append("Positive")
            elif avg_valence < 0.3:
                name_parts.append("Melancholic")
            else:
                name_parts.append("Balanced")
            
            if avg_danceability > 0.8:
                name_parts.append("Dance")
            elif avg_acousticness > 0.7:
                name_parts.append("Acoustic")
            elif avg_instrumentalness > 0.5:
                name_parts.append("Instrumental")
            elif avg_speechiness > 0.33:
                name_parts.append("Vocal")
            
            cluster_name = " ".join(name_parts[:3]) + " Music"
            
            # Calculate cohesion score
            cohesion_score = 0.5
            if avg_energy > 0.8 or avg_energy < 0.2:
                cohesion_score += 0.1
            if avg_valence > 0.8 or avg_valence < 0.2:
                cohesion_score += 0.1
            if avg_danceability > 0.8 or avg_danceability < 0.2:
                cohesion_score += 0.1
            if avg_acousticness > 0.7:
                cohesion_score += 0.1
            if avg_instrumentalness > 0.5:
                cohesion_score += 0.1
            
            cohesion_score = min(1.0, max(0.0, cohesion_score))
            
            # Dominant features
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
            
            description = f"A cluster of {size} tracks with {cluster_name.lower()} characteristics"
            
            audio_stats = {
                'energy': {'mean': avg_energy},
                'valence': {'mean': avg_valence},
                'danceability': {'mean': avg_danceability},
                'acousticness': {'mean': avg_acousticness},
                'tempo': {'mean': avg_tempo}
            }
            
            # Insert cluster
            insert_query = """
                INSERT INTO clusters (
                    id, name, description, size, cohesion_score, 
                    dominant_features, era, audio_stats
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """
            
            await conn.execute(
                insert_query,
                cluster_id,
                cluster_name,
                description,
                size,
                cohesion_score,
                dominant_features,
                "Mixed Era",
                json.dumps(audio_stats)
            )
            
            print(f"✅ {cluster_name}: {size} tracks (cohesion: {cohesion_score:.3f})")
        
        print(f"🎉 Named {len(cluster_data)} clusters!")
        
    finally:
        await conn.close()
        print("🔌 Database connection closed")


if __name__ == "__main__":
    asyncio.run(analyze_clusters()) 