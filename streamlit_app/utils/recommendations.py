"""
Recommendation utilities for the Spotify Music Recommendation System.
Handles KNN-based recommendations and clustering.
"""

import numpy as np
import time
from sklearn.neighbors import NearestNeighbors
from typing import Tuple, Optional, Any


def get_recommendations_within_cluster(
    knn_model: Any, 
    embeddings: np.ndarray, 
    labels: np.ndarray, 
    song_idx: int, 
    n_neighbors: int = 6
) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
    """
    Get song recommendations within the same cluster using KNN model.
    
    Args:
        knn_model: Trained KNN model
        embeddings (np.ndarray): Song embeddings
        labels (np.ndarray): Cluster labels
        song_idx (int): Index of the selected song
        n_neighbors (int): Number of neighbors to find
        
    Returns:
        Tuple[Optional[np.ndarray], Optional[np.ndarray]]: Distances and indices of recommendations
    """
    try:
        from logging_config import get_logger, log_recommendation_generation, log_performance
        logger = get_logger()
        logger.debug(f"Getting cluster recommendations for song_idx: {song_idx}, n_neighbors: {n_neighbors}")
    except:
        import logging
        logger = logging.getLogger(__name__)
        def log_recommendation_generation(*args, **kwargs): pass
        def log_performance(*args, **kwargs): pass
    
    start_time = time.time()
    
    if knn_model is None or embeddings is None or labels is None:
        logger.warning("Missing required models for cluster recommendations")
        return None, None
    
    try:
        # Get the cluster label for the selected song
        cluster_id = labels[song_idx]
        logger.debug(f"Song {song_idx} belongs to cluster {cluster_id}")
        
        # Find all songs in the same cluster
        cluster_mask = np.array(labels) == cluster_id
        cluster_indices = np.where(cluster_mask)[0]
        
        # If cluster has fewer songs than requested neighbors, adjust
        n_neighbors = min(n_neighbors, len(cluster_indices))
        logger.debug(f"Cluster {cluster_id} has {len(cluster_indices)} songs, using {n_neighbors} neighbors")
        
        if n_neighbors <= 1:
            logger.warning(f"Cluster {cluster_id} has too few songs for recommendations")
            return None, None
        
        # Get embeddings for songs in the same cluster
        cluster_embeddings = embeddings[cluster_mask]
        
        # Create KNN model for this cluster
        cluster_knn = NearestNeighbors(n_neighbors=n_neighbors, metric='euclidean')
        cluster_knn.fit(cluster_embeddings)
        
        # Find position of selected song within cluster
        song_cluster_idx = np.where(cluster_indices == song_idx)[0][0]
        
        # Get recommendations within cluster
        distances, local_indices = cluster_knn.kneighbors(
            cluster_embeddings[song_cluster_idx].reshape(1, -1), 
            n_neighbors=n_neighbors
        )
        
        # Convert local indices back to global indices
        global_indices = cluster_indices[local_indices[0]]
        
        processing_time = time.time() - start_time
        logger.info(f"Generated {len(global_indices)} cluster recommendations for song {song_idx}")
        
        # Log performance metrics
        log_recommendation_generation(
            method="cluster_based",
            song_idx=song_idx,
            num_recommendations=len(global_indices),
            processing_time=processing_time,
            details={
                'cluster_id': int(cluster_id),
                'cluster_size': len(cluster_indices),
                'requested_neighbors': n_neighbors
            }
        )
        
        return distances[0], global_indices
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Error getting cluster recommendations: {e}")
        log_performance("cluster_recommendations_error", processing_time, {
            'error': str(e),
            'song_idx': song_idx
        })
        return None, None


def get_global_recommendations(
    knn_model: Any, 
    embeddings: np.ndarray, 
    song_idx: int, 
    n_neighbors: int = 6
) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
    """
    Get song recommendations from entire dataset using pre-trained KNN model.
    
    Args:
        knn_model: Pre-trained KNN model
        embeddings (np.ndarray): Song embeddings
        song_idx (int): Index of the selected song
        n_neighbors (int): Number of neighbors to find
        
    Returns:
        Tuple[Optional[np.ndarray], Optional[np.ndarray]]: Distances and indices of recommendations
    """
    try:
        from logging_config import get_logger, log_recommendation_generation, log_performance
        logger = get_logger()
        logger.debug(f"Getting global recommendations for song_idx: {song_idx}, n_neighbors: {n_neighbors}")
    except:
        import logging
        logger = logging.getLogger(__name__)
        def log_recommendation_generation(*args, **kwargs): pass
        def log_performance(*args, **kwargs): pass
    
    start_time = time.time()
    
    if knn_model is None or embeddings is None:
        logger.warning("Missing required models for global recommendations")
        return None, None
    
    try:
        # Get the embedding for the selected song
        song_embedding = embeddings[song_idx].reshape(1, -1)
        
        # Find nearest neighbors
        distances, indices = knn_model.kneighbors(song_embedding, n_neighbors=n_neighbors)
        
        processing_time = time.time() - start_time
        logger.info(f"Generated {len(indices[0])} global recommendations for song {song_idx}")
        
        # Log performance metrics
        log_recommendation_generation(
            method="global_knn",
            song_idx=song_idx,
            num_recommendations=len(indices[0]),
            processing_time=processing_time,
            details={
                'embedding_dimensions': song_embedding.shape[1],
                'total_songs_searched': len(embeddings)
            }
        )
        
        return distances[0], indices[0]
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Error getting global recommendations: {e}")
        log_performance("global_recommendations_error", processing_time, {
            'error': str(e),
            'song_idx': song_idx
        })
        return None, None 