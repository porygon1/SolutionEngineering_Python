#!/usr/bin/env python3
"""
Populate cluster_id values in the database from trained model cluster labels
"""

import os
import pickle
import asyncio
import asyncpg
from loguru import logger


async def populate_cluster_ids():
    """Populate cluster_id values in the database from the trained model"""
    
    # Load cluster labels and song indices from trained model
    models_dir = "/app/models"
    labels_path = os.path.join(models_dir, "cluster_labels.pkl")
    indices_path = os.path.join(models_dir, "song_indices.pkl")
    
    logger.info("🏷️ Loading cluster labels from trained model...")
    with open(labels_path, 'rb') as f:
        cluster_labels = pickle.load(f)
    
    logger.info("📑 Loading song indices from trained model...")
    with open(indices_path, 'rb') as f:
        song_indices = pickle.load(f)
    
    track_ids = song_indices['track_ids']
    
    logger.info(f"📊 Found {len(cluster_labels)} cluster assignments for {len(track_ids)} tracks")
    
    # Connect to database
    database_url = os.environ.get(
        'DATABASE_URL', 
        'postgresql://spotify_user:spotify_password@database:5432/spotify_recommendations'
    )
    
    logger.info("🔌 Connecting to database...")
    conn = await asyncpg.connect(database_url)
    
    try:
        # Update cluster_id values in batches
        batch_size = 1000
        total_updated = 0
        
        for i in range(0, len(track_ids), batch_size):
            batch_track_ids = track_ids[i:i+batch_size]
            batch_cluster_ids = cluster_labels[i:i+batch_size]
            
            # Prepare update data
            update_data = [
                (track_id, int(cluster_id)) 
                for track_id, cluster_id in zip(batch_track_ids, batch_cluster_ids)
            ]
            
            # Execute batch update
            await conn.executemany(
                "UPDATE tracks SET cluster_id = $2 WHERE id = $1",
                update_data
            )
            
            total_updated += len(update_data)
            logger.info(f"📈 Updated {total_updated}/{len(track_ids)} tracks with cluster IDs")
        
        # Get cluster statistics
        cluster_stats = await conn.fetch("""
            SELECT cluster_id, COUNT(*) as size 
            FROM tracks 
            WHERE cluster_id IS NOT NULL AND cluster_id != -1
            GROUP BY cluster_id 
            ORDER BY cluster_id
        """)
        
        logger.success(f"✅ Successfully updated {total_updated} tracks with cluster IDs")
        logger.info(f"🎯 Found {len(cluster_stats)} clusters in database:")
        
        for stat in cluster_stats[:10]:  # Show first 10 clusters
            logger.info(f"   Cluster {stat['cluster_id']}: {stat['size']} tracks")
        
        if len(cluster_stats) > 10:
            logger.info(f"   ... and {len(cluster_stats) - 10} more clusters")
    
    finally:
        await conn.close()
        logger.info("🔌 Database connection closed")


if __name__ == "__main__":
    asyncio.run(populate_cluster_ids()) 