"""
ModelService - ML model management and recommendation logic
Uses actual trained HDBSCAN clustering + KNN models for music recommendations
"""

import os
import pickle
import pandas as pd
import numpy as np
from typing import List, Optional, Dict, Any, Tuple
from loguru import logger
import asyncio
from datetime import datetime
from sklearn.neighbors import NearestNeighbors
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy import select, func

from app.schemas.recommendation import (
    Song, 
    RecommendationRequest, 
    RecommendationResponse,
    ClusterUsed
)
from app.database.database import get_database
from app.database.models import Track, Artist, Album
from app.config import settings
from app.services.lyrics_similarity_service import LyricsSimilarityService
from app.services.hdbscan_similarity_service import HDBSCANSimilarityService
from app.services.similarity_utils import similarity_calculator


class ModelService:
    """
    Service class for managing actual trained ML models and providing recommendations
    Uses real HDBSCAN clustering + KNN models trained on Spotify audio features
    """
    
    def __init__(self):
        """Initialize the ModelService"""
        self.hdbscan_model = None
        self.knn_model = None
        self.audio_embeddings = None
        self.cluster_labels = None
        self.song_indices = None
        self.track_id_to_index = {}
        self.index_to_track_id = {}
        self._is_ready = False
        
        # Initialize lyrics similarity service
        self.lyrics_service = LyricsSimilarityService()
        
        # Initialize HDBSCAN similarity service
        self.hdbscan_service = HDBSCANSimilarityService()
        
        # Model file paths - use environment variable or default path
        self.models_dir = os.environ.get('MODELS_PATH', '/app/models')
        self.hdbscan_path = os.path.join(self.models_dir, "hdbscan_model.pkl")
        self.knn_path = os.path.join(self.models_dir, "knn_model.pkl")
        self.embeddings_path = os.path.join(self.models_dir, "audio_embeddings.pkl")
        self.labels_path = os.path.join(self.models_dir, "cluster_labels.pkl")
        self.indices_path = os.path.join(self.models_dir, "song_indices.pkl")
        
        logger.info("🧠 ModelService initialized with trained models")
    
    def is_ready(self) -> bool:
        """Check if the model service is ready to serve requests"""
        return (
            self._is_ready and 
            self.hdbscan_model is not None and
            self.knn_model is not None and
            self.audio_embeddings is not None and
            self.cluster_labels is not None
        )
    
    async def initialize(self) -> None:
        """Initialize the model service by loading trained models"""
        logger.info("🚀 Loading trained ML models...")
        
        try:
            # Check if all model files exist
            required_files = [
                self.hdbscan_path, self.knn_path, self.embeddings_path,
                self.labels_path, self.indices_path
            ]
            
            for file_path in required_files:
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"Model file not found: {file_path}")
            
            # Load HDBSCAN model
            logger.info("📊 Loading HDBSCAN clustering model...")
            with open(self.hdbscan_path, 'rb') as f:
                self.hdbscan_model = pickle.load(f)
            
            # Load KNN model
            logger.info("🔍 Loading KNN recommendation model...")
            with open(self.knn_path, 'rb') as f:
                self.knn_model = pickle.load(f)
            
            # Load audio embeddings
            logger.info("🎵 Loading audio feature embeddings...")
            with open(self.embeddings_path, 'rb') as f:
                self.audio_embeddings = pickle.load(f)
            
            # Load cluster labels
            logger.info("🏷️ Loading cluster labels...")
            with open(self.labels_path, 'rb') as f:
                self.cluster_labels = pickle.load(f)
            
            # Load song indices
            logger.info("📑 Loading song index mappings...")
            with open(self.indices_path, 'rb') as f:
                self.song_indices = pickle.load(f)
            
            # Create bidirectional mapping between track IDs and indices
            self._create_index_mappings()
            
            # Validate data consistency
            self._validate_loaded_data()
            
            # Set ready flag for main models
            self._is_ready = True
            
            logger.success(f"✅ ML models loaded successfully!")
            logger.info(f"📈 {len(self.audio_embeddings)} tracks with {self.audio_embeddings.shape[1]} features")
            logger.info(f"🎯 {len(set(self.cluster_labels)) - (1 if -1 in self.cluster_labels else 0)} clusters found")
            
            # Initialize lyrics similarity service (non-blocking)
            try:
                await self.lyrics_service.initialize()
                logger.info("✅ Lyrics similarity service initialized")
            except Exception as e:
                logger.warning(f"⚠️ Lyrics similarity service failed to initialize: {e}")
                logger.info("📖 Lyrics-based recommendations will not be available, but other features will work")
            
            # Initialize HDBSCAN similarity service (non-blocking)
            try:
                await self.hdbscan_service.initialize()
                logger.info("✅ HDBSCAN similarity service initialized")
            except Exception as e:
                logger.warning(f"⚠️ HDBSCAN similarity service failed to initialize: {e}")
                logger.info("🔬 Advanced HDBSCAN-based recommendations will not be available, but other features will work")
            
        except Exception as e:
            logger.error(f"❌ Failed to load ML models: {e}")
            self._is_ready = False
            raise
    
    def _create_index_mappings(self):
        """Create bidirectional mappings between track IDs and array indices"""
        track_ids = self.song_indices['track_ids']
        
        for idx, track_id in enumerate(track_ids):
            self.track_id_to_index[track_id] = idx
            self.index_to_track_id[idx] = track_id
        
        logger.info(f"📍 Created index mappings for {len(track_ids)} tracks")
    
    def _validate_loaded_data(self):
        """Validate that all loaded data is consistent"""
        n_tracks = len(self.song_indices['track_ids'])
        
        if len(self.audio_embeddings) != n_tracks:
            raise ValueError(f"Embeddings length {len(self.audio_embeddings)} != tracks {n_tracks}")
        
        if len(self.cluster_labels) != n_tracks:
            raise ValueError(f"Labels length {len(self.cluster_labels)} != tracks {n_tracks}")
        
        logger.info("✅ Data validation passed")
    
    async def get_lyrics_recommendations(
        self,
        request: RecommendationRequest,
        db: AsyncSession
    ) -> RecommendationResponse:
        """
        Get song recommendations using lyrics similarity
        """
        if not self.lyrics_service.is_ready():
            logger.warning("📖 Lyrics similarity service not available, falling back to cluster-based recommendations")
            # Fall back to cluster-based recommendations
            return await self.get_recommendations_with_similarity(request, db)
        
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"📝 Getting lyrics-based recommendations for {len(request.liked_song_ids)} songs")
            
            all_recommendations = []
            
            # Get lyrics recommendations for each liked song
            for song_id in request.liked_song_ids:
                similar_songs = await self.lyrics_service.find_similar_by_track_id(
                    song_id, 
                    k=request.n_recommendations * 2,  # Get more to allow for filtering
                    db=db
                )
                
                for song_data in similar_songs:
                    if song_data['track_id'] not in request.liked_song_ids:
                        all_recommendations.append({
                            'track_id': song_data['track_id'],
                            'similarity_score': song_data['similarity_score'],
                            'source_song': song_id
                        })
            
            # Remove duplicates and sort by similarity score (higher is better)
            seen_tracks = set()
            unique_recommendations = []
            
            for rec in sorted(all_recommendations, key=lambda x: x['similarity_score'], reverse=True):  # Sort by similarity descending (higher is better)
                if rec['track_id'] not in seen_tracks:
                    unique_recommendations.append(rec)
                    seen_tracks.add(rec['track_id'])
                    
                    if len(unique_recommendations) >= request.n_recommendations:
                        break
            
            # Get full track information from database
            track_ids = [rec['track_id'] for rec in unique_recommendations]
            tracks_query = select(Track).options(
                joinedload(Track.artist),
                joinedload(Track.album)
            ).filter(Track.id.in_(track_ids))
            
            result = await db.execute(tracks_query)
            tracks = {track.id: track for track in result.scalars().all()}
            
            # Convert to Song objects with similarity scores
            recommendations = []
            for rec in unique_recommendations:
                track_id = rec['track_id']
                if track_id in tracks:
                    track = tracks[track_id]
                    song = self._track_to_song_with_similarity(track, rec['similarity_score'])
                    recommendations.append(song)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            response = RecommendationResponse(
                recommendations=recommendations,
                recommendation_type="lyrics",
                clusters_used=[],  # Lyrics-based doesn't use clusters
                total_found=len(recommendations),
                processing_time_ms=processing_time
            )
            
            logger.success(f"✅ Generated {len(recommendations)} lyrics-based recommendations in {processing_time:.1f}ms")
            return response
            
        except Exception as e:
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000 
            logger.error(f"❌ Error generating lyrics recommendations: {e} (took {processing_time:.1f}ms)")
            logger.warning("📖 Falling back to cluster-based recommendations")
            # Fall back to cluster-based recommendations
            return await self.get_recommendations_with_similarity(request, db)
    
    async def get_hdbscan_recommendations(
        self,
        request: RecommendationRequest,
        db: AsyncSession,
        model_type: str = None
    ) -> RecommendationResponse:
        """
        Get song recommendations using HDBSCAN similarity with different approaches
        """
        if not self.hdbscan_service.is_ready():
            logger.warning("🔬 HDBSCAN similarity service not available, falling back to cluster-based recommendations")
            # Fall back to cluster-based recommendations
            return await self.get_recommendations_with_similarity(request, db)
        
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"🔬 Getting HDBSCAN-based recommendations for {len(request.liked_song_ids)} songs")
            
            # If a specific model type is requested, switch to it
            if model_type and model_type != self.hdbscan_service.get_current_model_info().get('model_name'):
                switch_result = self.hdbscan_service.switch_model(model_type)
                if not switch_result.get('success'):
                    logger.warning(f"Failed to switch to model {model_type}, using current model")
            
            all_recommendations = []
            
            # Get HDBSCAN recommendations for each liked song
            for song_id in request.liked_song_ids:
                similar_songs = await self.hdbscan_service.find_similar_by_track_id(
                    song_id, 
                    k=request.n_recommendations * 2,  # Get more to allow for filtering
                    db=db
                )
                
                for song_data in similar_songs:
                    if song_data['track_id'] not in request.liked_song_ids:
                        all_recommendations.append({
                            'track_id': song_data['track_id'],
                            'similarity_score': song_data['similarity_score'],
                            'source_song': song_id
                        })
            
            # Remove duplicates and sort by similarity score (higher is better)
            seen_tracks = set()
            unique_recommendations = []
            
            for rec in sorted(all_recommendations, key=lambda x: x['similarity_score'], reverse=True):  # Sort by similarity descending (higher is better)
                if rec['track_id'] not in seen_tracks:
                    unique_recommendations.append(rec)
                    seen_tracks.add(rec['track_id'])
                    
                    if len(unique_recommendations) >= request.n_recommendations:
                        break
            
            # Get full track information from database
            track_ids = [rec['track_id'] for rec in unique_recommendations]
            tracks_query = select(Track).options(
                joinedload(Track.artist),
                joinedload(Track.album)
            ).filter(Track.id.in_(track_ids))
            
            result = await db.execute(tracks_query)
            tracks = {track.id: track for track in result.scalars().all()}
            
            # Convert to Song objects with similarity scores
            recommendations = []
            for rec in unique_recommendations:
                track_id = rec['track_id']
                if track_id in tracks:
                    track = tracks[track_id]
                    song = self._track_to_song_with_similarity(track, rec['similarity_score'])
                    recommendations.append(song)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            current_model_info = self.hdbscan_service.get_current_model_info()
            recommendation_type = f"hdbscan_{current_model_info.get('model_name', 'unknown')}"
            
            response = RecommendationResponse(
                recommendations=recommendations,
                recommendation_type=recommendation_type,
                clusters_used=[],  # HDBSCAN service handles its own clustering
                total_found=len(recommendations),
                processing_time_ms=processing_time
            )
            
            logger.success(f"✅ Generated {len(recommendations)} HDBSCAN-based recommendations in {processing_time:.1f}ms")
            return response
            
        except Exception as e:
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000 
            logger.error(f"❌ Error generating HDBSCAN recommendations: {e} (took {processing_time:.1f}ms)")
            logger.warning("🔬 Falling back to cluster-based recommendations")
            # Fall back to cluster-based recommendations
            return await self.get_recommendations_with_similarity(request, db)
    
    async def get_recommendations_with_similarity(
        self, 
        request: RecommendationRequest,
        db: AsyncSession
    ) -> RecommendationResponse:
        """
        Get song recommendations using actual trained models with similarity scores
        """
        if not self.is_ready():
            raise Exception("ModelService not ready - models not loaded")
        
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"🎵 Getting recommendations for {len(request.liked_song_ids)} songs using trained models")
            
            # Get indices for liked songs
            liked_indices = []
            valid_song_ids = []
            
            for song_id in request.liked_song_ids:
                if song_id in self.track_id_to_index:
                    idx = self.track_id_to_index[song_id]
                    liked_indices.append(idx)
                    valid_song_ids.append(song_id)
                else:
                    logger.warning(f"Song ID {song_id} not found in trained model dataset")
            
            if not liked_indices:
                raise Exception("None of the provided song IDs were found in the trained model dataset")
            
            logger.info(f"✅ Found {len(liked_indices)} valid songs in model dataset")
            
            # Get recommendations using KNN
            all_recommendations = []
            clusters_used = []
            
            for idx in liked_indices:
                song_id = self.index_to_track_id[idx]
                cluster_id = int(self.cluster_labels[idx])
                
                # Get KNN recommendations for this song
                song_embedding = self.audio_embeddings[idx].reshape(1, -1)
                distances, indices = self.knn_model.kneighbors(
                    song_embedding, 
                    n_neighbors=min(request.n_recommendations * 2, 50)
                )
                
                # Filter out the source song and already liked songs
                for dist, rec_idx in zip(distances[0], indices[0]):
                    rec_song_id = self.index_to_track_id[rec_idx]
                    
                    if rec_song_id not in request.liked_song_ids:
                        # Store distance for similarity calculation
                        all_recommendations.append({
                            'song_id': rec_song_id,
                            'distance': float(dist),
                            'source_song': song_id,
                            'cluster_id': int(self.cluster_labels[rec_idx])
                        })
                
                # Track cluster usage
                if cluster_id != -1:  # Not noise cluster
                    cluster_size = sum(1 for label in self.cluster_labels if label == cluster_id)
                    clusters_used.append(ClusterUsed(
                        cluster_id=cluster_id,
                        size=cluster_size,
                        source_song=song_id
                    ))
            
            # Calculate similarity scores for all recommendations
            all_recommendations = similarity_calculator.add_similarity_scores(all_recommendations, "hdbscan")
            
            # Remove duplicates and sort by similarity score (higher is better)
            seen_songs = set()
            unique_recommendations = []
            
            for rec in sorted(all_recommendations, key=lambda x: x['similarity_score'], reverse=True):  # Sort by similarity descending (higher is better)
                if rec['song_id'] not in seen_songs:
                    seen_songs.add(rec['song_id'])
                    unique_recommendations.append(rec)
                
                if len(unique_recommendations) >= request.n_recommendations:
                    break
            
            # Get song details from database
            recommendation_ids = [rec['song_id'] for rec in unique_recommendations]
            
            songs_query = select(Track).options(
                joinedload(Track.artist),
                joinedload(Track.album)
            ).filter(Track.id.in_(recommendation_ids))
            
            result = await db.execute(songs_query)
            tracks = result.scalars().all()
            
            # Create song objects with similarity scores
            recommendations = []
            track_dict = {track.id: track for track in tracks}
            
            for rec in unique_recommendations:
                track = track_dict.get(rec['song_id'])
                if track:
                    song = self._track_to_song_with_similarity(track, rec['similarity_score'])
                    recommendations.append(song)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            response = RecommendationResponse(
                recommendations=recommendations,
                recommendation_type=request.recommendation_type,
                clusters_used=clusters_used,
                total_found=len(recommendations),
                processing_time_ms=processing_time
            )
        
            logger.success(f"✅ Generated {len(recommendations)} recommendations with similarity scores in {processing_time:.1f}ms")
            return response
            
        except Exception as e:
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.error(f"❌ Error generating recommendations: {e} (took {processing_time:.1f}ms)")
            raise
    
    def _track_to_song_with_similarity(self, track: Track, similarity_score: float) -> Song:
        """Convert a Track database object to a Song schema object with similarity score"""
        # Extract album image URL from images JSON
        album_image_url = None
        if track.album and track.album.images:
            images = track.album.images
            if isinstance(images, list) and len(images) > 0:
                if len(images) > 1:
                    album_image_url = images[1].get('url') if isinstance(images[1], dict) else None
                else:
                    album_image_url = images[0].get('url') if isinstance(images[0], dict) else None
        
        return Song(
            id=track.id,
            name=track.name,
            artist=track.artist.name if track.artist else 'Unknown Artist',
            album=track.album.name if track.album else 'Unknown Album',
            duration_ms=track.duration_ms or 0,
            popularity=track.popularity or 0,
            acousticness=track.acousticness or 0.0,
            danceability=track.danceability or 0.0,
            energy=track.energy or 0.0,
            instrumentalness=track.instrumentalness or 0.0,
            liveness=track.liveness or 0.0,
            loudness=track.loudness or 0.0,
            speechiness=track.speechiness or 0.0,
            tempo=track.tempo or 120.0,
            valence=track.valence or 0.0,
            key=track.key or 0,
            mode=track.mode or 0,
            time_signature=track.time_signature or 4,
            cluster_id=track.cluster_id or -1,
            preview_url=track.preview_url,
            spotify_url=track.spotify_uri or f"https://open.spotify.com/track/{track.id}",
            album_image_url=album_image_url,
            similarity_score=similarity_score  # Add similarity score
        )
    
    async def search_similar_songs(
        self, 
        song_id: str, 
        n_recommendations: int = 12,
        db: AsyncSession = None
    ) -> List[Dict[str, Any]]:
        """Search for similar songs using KNN on audio features"""
        if not self.is_ready():
            raise Exception("ModelService not ready")
        
        if song_id not in self.track_id_to_index:
            raise ValueError(f"Song ID {song_id} not found in model dataset")
        
        idx = self.track_id_to_index[song_id]
        song_embedding = self.audio_embeddings[idx].reshape(1, -1)
        
        # Get similar songs
        distances, indices = self.knn_model.kneighbors(
            song_embedding, 
            n_neighbors=n_recommendations + 1  # +1 to exclude the source song
        )
        
        similar_songs = []
        for dist, rec_idx in zip(distances[0][1:], indices[0][1:]):  # Skip first (same song)
            rec_song_id = self.index_to_track_id[rec_idx]
            
            similar_songs.append({
                'song_id': rec_song_id,
                'distance': float(dist),
                'cluster_id': int(self.cluster_labels[rec_idx])
            })
        
        # Calculate similarity scores using the utility
        similar_songs = similarity_calculator.add_similarity_scores(similar_songs, "hdbscan")
        
        return similar_songs
    
    def get_cluster_info(self, cluster_id: int) -> Dict[str, Any]:
        """Get information about a specific cluster"""
        if not self.is_ready():
            raise Exception("ModelService not ready")
        
        cluster_mask = self.cluster_labels == cluster_id
        cluster_indices = np.where(cluster_mask)[0]
        
        if len(cluster_indices) == 0:
            raise ValueError(f"Cluster {cluster_id} not found")
        
        # Get track IDs in this cluster
        track_ids = [self.index_to_track_id[idx] for idx in cluster_indices]
        
        return {
            'cluster_id': cluster_id,
            'size': len(track_ids),
            'track_ids': track_ids[:100],  # Limit for performance
            'total_tracks': len(track_ids)
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get model statistics"""
        if not self.is_ready():
            return {"status": "not_ready"}
        
        unique_clusters = set(self.cluster_labels)
        n_clusters = len(unique_clusters) - (1 if -1 in unique_clusters else 0)
        n_noise = sum(1 for label in self.cluster_labels if label == -1)
        
        return {
            "status": "ready",
            "total_tracks": len(self.cluster_labels),
            "n_clusters": n_clusters,
            "n_noise_points": n_noise,
            "noise_percentage": (n_noise / len(self.cluster_labels)) * 100,
            "embedding_dimensions": self.audio_embeddings.shape[1],
            "model_type": "HDBSCAN + KNN",
            "knn_neighbors": getattr(self.knn_model, 'n_neighbors', 'unknown')
        }
    
    def cleanup(self) -> None:
        """Cleanup resources"""
        logger.info("🧹 Cleaning up ModelService...")
        
        self.hdbscan_model = None
        self.knn_model = None
        self.audio_embeddings = None
        self.cluster_labels = None
        self.song_indices = None
        self.track_id_to_index = {}
        self.index_to_track_id = {}
        self._is_ready = False
        
        logger.info("✅ ModelService cleanup completed") 