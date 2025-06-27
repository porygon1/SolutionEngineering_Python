"""
HDBSCAN Similarity Service - Handles different HDBSCAN clustering approaches
Supports multiple feature extraction and dimensionality reduction methods
"""

import os
import pickle
import json
import pandas as pd
import numpy as np
from typing import List, Optional, Dict, Any, Tuple
from loguru import logger
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import MinMaxScaler
from sklearn.decomposition import PCA
from sklearn.impute import KNNImputer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy import select

from app.database.models import Track, Artist, Album
from app.config import settings
from app.services.similarity_utils import similarity_calculator


class CompatibleHDBSCANModel:
    """Model loader that handles different HDBSCAN approach configurations"""
    
    def __init__(self, models_dir: str, model_name: str = None):
        self.models_dir = models_dir
        self.model_name = model_name
        self.hdbscan_model = None
        self.knn_model = None
        self.scaler = None
        self.pca_model = None
        self.audio_embeddings = None
        self.cluster_labels = None
        self.song_indices = None
        self.config = None
        self.track_id_to_index = {}
        self.index_to_track_id = {}
        
    def load_model(self, model_name: str = None):
        """Load a specific HDBSCAN model configuration by name"""
        if model_name:
            self.model_name = model_name
            
        if not self.model_name:
            raise ValueError("Model name must be specified")
            
        # Load model configuration
        config_path = os.path.join(self.models_dir, f"hdbscan_config_{self.model_name}.json")
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # Try to load model-specific files first, fallback to base files if needed
        model_prefix = f"{self.model_name}_"
        
        # Load HDBSCAN model
        hdbscan_path = os.path.join(self.models_dir, f"{model_prefix}hdbscan_model.pkl")
        if not os.path.exists(hdbscan_path):
            # Fallback to base model
            hdbscan_path = os.path.join(self.models_dir, "hdbscan_model.pkl")
            logger.warning(f"Using base HDBSCAN model for {self.model_name}")
        
        with open(hdbscan_path, 'rb') as f:
            self.hdbscan_model = pickle.load(f)
            
        # Load KNN model
        knn_path = os.path.join(self.models_dir, f"{model_prefix}knn_model.pkl")
        if not os.path.exists(knn_path):
            # Fallback to base model
            knn_path = os.path.join(self.models_dir, "knn_model.pkl")
            logger.warning(f"Using base KNN model for {self.model_name}")
            
        with open(knn_path, 'rb') as f:
            self.knn_model = pickle.load(f)
            
        # Load audio embeddings
        embeddings_path = os.path.join(self.models_dir, f"{model_prefix}audio_embeddings.pkl")
        if not os.path.exists(embeddings_path):
            # Fallback to base embeddings
            embeddings_path = os.path.join(self.models_dir, "audio_embeddings.pkl")
            logger.warning(f"Using base audio embeddings for {self.model_name}")
            
        with open(embeddings_path, 'rb') as f:
            self.audio_embeddings = pickle.load(f)
            
        # Load cluster labels
        labels_path = os.path.join(self.models_dir, f"{model_prefix}cluster_labels.pkl")
        if not os.path.exists(labels_path):
            # Fallback to base labels
            labels_path = os.path.join(self.models_dir, "cluster_labels.pkl")
            logger.warning(f"Using base cluster labels for {self.model_name}")
            
        with open(labels_path, 'rb') as f:
            self.cluster_labels = pickle.load(f)
            
        # Load song indices
        indices_path = os.path.join(self.models_dir, f"{model_prefix}song_indices.pkl")
        if not os.path.exists(indices_path):
            # Fallback to base indices
            indices_path = os.path.join(self.models_dir, "song_indices.pkl")
            logger.warning(f"Using base song indices for {self.model_name}")
            
        with open(indices_path, 'rb') as f:
            self.song_indices = pickle.load(f)
                
        # Build index mappings
        if 'track_ids' in self.song_indices:
            for idx, track_id in enumerate(self.song_indices['track_ids']):
                self.track_id_to_index[track_id] = idx
                self.index_to_track_id[idx] = track_id
        
        # Log which files were actually loaded
        files_used = []
        if os.path.exists(os.path.join(self.models_dir, f"{model_prefix}hdbscan_model.pkl")):
            files_used.append("model-specific HDBSCAN")
        else:
            files_used.append("base HDBSCAN")
            
        if os.path.exists(os.path.join(self.models_dir, f"{model_prefix}knn_model.pkl")):
            files_used.append("model-specific KNN")
        else:
            files_used.append("base KNN")
            
        if os.path.exists(os.path.join(self.models_dir, f"{model_prefix}audio_embeddings.pkl")):
            files_used.append("model-specific embeddings")
        else:
            files_used.append("base embeddings")
            
        logger.info(f"📂 Loaded {self.model_name} using: {', '.join(files_used)}")
                
        return self
        
    def find_similar(self, track_id: str, k: int = 10) -> Tuple[List[str], List[float]]:
        """Find similar songs using the loaded HDBSCAN+KNN model"""
        if track_id not in self.track_id_to_index:
            raise ValueError(f"Track ID {track_id} not found in model dataset")
            
        idx = self.track_id_to_index[track_id]
        cluster_id = self.cluster_labels[idx]
        
        # Get song embedding
        song_embedding = self.audio_embeddings[idx].reshape(1, -1)
        
        # Find similar songs within the same cluster or globally based on config
        if self.config.get('cluster_based', True) and cluster_id != -1:
            # Cluster-based search
            cluster_mask = self.cluster_labels == cluster_id
            cluster_indices = np.where(cluster_mask)[0]
            cluster_embeddings = self.audio_embeddings[cluster_mask]
            
            # Fit KNN on cluster
            cluster_knn = NearestNeighbors(n_neighbors=min(k+1, len(cluster_embeddings)))
            cluster_knn.fit(cluster_embeddings)
            distances, local_indices = cluster_knn.kneighbors(song_embedding)
            
            # Convert to global indices
            global_indices = cluster_indices[local_indices[0]]
            distances = distances[0]
        else:
            # Global search
            distances, indices = self.knn_model.kneighbors(song_embedding, n_neighbors=k+1)
            global_indices = indices[0]
            distances = distances[0]
        
        # Filter out the source song and get track IDs
        similar_track_ids = []
        similar_distances = []
        
        for dist, idx in zip(distances, global_indices):
            if idx != self.track_id_to_index[track_id]:  # Skip source song
                similar_track_ids.append(self.index_to_track_id[idx])
                similar_distances.append(float(dist))
                
                if len(similar_track_ids) >= k:
                    break
                    
        return similar_track_ids, similar_distances
        
    def get_available_models(self) -> List[str]:
        """Get list of available HDBSCAN models"""
        models = []
        for filename in os.listdir(self.models_dir):
            if filename.startswith('hdbscan_config_') and filename.endswith('.json'):
                model_name = filename.replace('hdbscan_config_', '').replace('.json', '')
                # Return model name WITHOUT prefix for internal use
                models.append(model_name)
        return models
        
    def get_model_info(self) -> dict:
        """Get information about the loaded model"""
        if not self.config:
            return {}
            
        return {
            'model_name': self.model_name,
            'approach': self.config.get('approach'),
            'feature_type': self.config.get('feature_type'),
            'has_pca': self.config.get('has_pca', False),
            'pca_components': self.config.get('pca_components'),
            'has_scaler': self.config.get('has_scaler', False),
            'cluster_based': self.config.get('cluster_based', True),
            'min_cluster_size': self.config.get('min_cluster_size'),
            'metric': self.config.get('metric', 'euclidean'),
            'n_clusters': len(np.unique(self.cluster_labels)) if self.cluster_labels is not None else 0,
            'n_songs': len(self.audio_embeddings) if self.audio_embeddings is not None else 0
        }


class HDBSCANSimilarityService:
    """
    Service for HDBSCAN-based song recommendations using different approaches
    """
    
    def __init__(self):
        """Initialize the HDBSCAN Similarity Service"""
        self.models_dir = os.environ.get('MODELS_PATH', '/app/models')
        self.model_loader = CompatibleHDBSCANModel(self.models_dir)
        self.current_model = None
        self._is_ready = False
        
        logger.info("🔬 HDBSCANSimilarityService initialized with multiple approach support")
    
    def is_ready(self) -> bool:
        """Check if the HDBSCAN similarity service is ready"""
        return self._is_ready and self.current_model is not None
    
    async def initialize(self) -> None:
        """Initialize the HDBSCAN similarity service by loading the best available model"""
        logger.info("🚀 Loading HDBSCAN similarity models...")
        
        try:
            # Get available models
            available_models = self.model_loader.get_available_models()
            logger.info(f"📋 Available HDBSCAN models: {available_models}")
            
            if not available_models:
                raise FileNotFoundError("No compatible HDBSCAN model files found")
            
            # Try to load the best model (priority order)
            preferred_models = ['llav_pca', 'pca_features', 'combined_features', 'naive_features', 'llav_features']
            selected_model = None
            
            for preferred_model in preferred_models:
                if preferred_model in available_models:
                    selected_model = preferred_model
                    break
                    
            if not selected_model:
                # Fallback to any available model
                selected_model = available_models[0]
            
            # Load the selected model
            logger.info(f"🔧 Loading HDBSCAN model: {selected_model}")
            self.current_model = self.model_loader.load_model(selected_model)
            
            model_info = self.current_model.get_model_info()
            logger.success(f"✅ HDBSCAN similarity model loaded successfully!")
            logger.info(f"📊 Model: {model_info.get('model_name')}")
            logger.info(f"🎯 Approach: {model_info.get('approach')}")
            logger.info(f"📈 Feature type: {model_info.get('feature_type')}")
            logger.info(f"🔢 Clusters: {model_info.get('n_clusters')}")
            logger.info(f"🎵 Songs: {model_info.get('n_songs')}")
            
            self._is_ready = True
            
        except Exception as e:
            logger.error(f"❌ Failed to load HDBSCAN similarity models: {e}")
            logger.error(f"🔍 Available files in models directory:")
            try:
                for file in os.listdir(self.models_dir):
                    logger.error(f"  - {file}")
            except:
                logger.error(f"  Could not list directory: {self.models_dir}")
            self._is_ready = False
            raise
    
    def switch_model(self, model_name: str) -> Dict[str, Any]:
        """Switch to a different HDBSCAN model at runtime"""
        try:
            # Remove hdbscan_ prefix if present for internal model loading
            internal_model_name = model_name.replace('hdbscan_', '') if model_name.startswith('hdbscan_') else model_name
            
            available_models = self.model_loader.get_available_models()
            if internal_model_name not in available_models:
                raise ValueError(f"Model {internal_model_name} not available. Available: {available_models}")
                
            self.current_model = self.model_loader.load_model(internal_model_name)
            model_info = self.current_model.get_model_info()
            
            logger.info(f"🔄 Switched to HDBSCAN model: {model_name}")
            return {
                "success": True,
                "model": model_name,
                "info": model_info
            }
        except Exception as e:
            logger.error(f"❌ Failed to switch to HDBSCAN model {model_name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_available_models(self) -> List[str]:
        """Get list of available HDBSCAN models"""
        # Get internal model names and add hdbscan_ prefix for API consistency
        internal_models = self.model_loader.get_available_models()
        return [f"hdbscan_{model}" for model in internal_models]
    
    def get_current_model_info(self) -> Dict[str, Any]:
        """Get information about the currently loaded HDBSCAN model"""
        if not self.current_model:
            return {"error": "No model loaded"}
        return self.current_model.get_model_info()
    
    async def find_similar_by_track_id(
        self, 
        track_id: str, 
        k: int = 10,
        db: AsyncSession = None
    ) -> List[Dict[str, Any]]:
        """
        Find similar songs based on a track's audio features using HDBSCAN clustering
        
        Args:
            track_id (str): Spotify track ID
            k (int): Number of similar songs to return
            db (AsyncSession): Database session
        
        Returns:
            list: List of similar songs with similarity scores
        """
        if not self.is_ready():
            raise Exception("HDBSCANSimilarityService not ready - models not loaded")
        
        try:
            # Find similar songs using the current model
            similar_track_ids, distances = self.current_model.find_similar(track_id, k)
            
            # Format results with distance
            results = []
            for track_id, distance in zip(similar_track_ids, distances):
                results.append({
                    'track_id': track_id,
                    'distance': float(distance)
                })
            
            # Calculate similarity scores using the utility
            model_type = self.current_model.get_model_info().get('approach', 'hdbscan')
            results = similarity_calculator.add_similarity_scores(results, model_type)
            
            # Enrich with database information if available
            if db:
                results = await self._enrich_with_db_info(results, db)
            
            return results
            
        except Exception as e:
            logger.error(f"Error finding similar songs by HDBSCAN: {e}")
            return []
    
    async def _enrich_with_db_info(self, results: List[Dict], db: AsyncSession) -> List[Dict[str, Any]]:
        """Enrich results with database information"""
        try:
            track_ids = [r['track_id'] for r in results]
            
            tracks_query = select(Track).options(
                joinedload(Track.artist),
                joinedload(Track.album)
            ).filter(Track.id.in_(track_ids))
            
            result = await db.execute(tracks_query)
            tracks = {track.id: track for track in result.scalars().all()}
            
            enriched_results = []
            for result_data in results:
                track_id = result_data['track_id']
                if track_id in tracks:
                    track = tracks[track_id]
                    enriched_results.append({
                        **result_data,
                        'name': track.name,
                        'artist': track.artist.name if track.artist else 'Unknown Artist',
                        'album': track.album.name if track.album else 'Unknown Album',
                        'cluster_id': track.cluster_id
                    })
                else:
                    enriched_results.append(result_data)
                    
            return enriched_results
            
        except Exception as e:
            logger.warning(f"Failed to enrich results with DB info: {e}")
            return results 