"""
Lyrics Similarity Service - Handles lyrics-based song recommendations
Uses the new compatible model format to avoid pickle compatibility issues
"""

import os
import joblib
import json
import pandas as pd
import numpy as np
from typing import List, Optional, Dict, Any, Tuple
from loguru import logger
import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy import select

from app.database.models import Track, Artist, Album
from app.config import settings
from app.services.similarity_utils import similarity_calculator


class CompatibleLyricsSimilarityModel:
    """Model loader that handles individual model files for maximum compatibility"""
    
    def __init__(self, models_dir: str, model_name: str = None):
        self.models_dir = models_dir
        self.model_name = model_name
        self.vectorizer = None
        self.model = None
        self.svd_model = None
        self.config = None
        self.metadata = None
        
    def load_model(self, model_name: str = None):
        """Load a specific model by name"""
        if model_name:
            self.model_name = model_name
            
        if not self.model_name:
            raise ValueError("Model name must be specified")
            
        # Load vectorizer (shared by all models)
        vectorizer_path = os.path.join(self.models_dir, "lyrics_tfidf_vectorizer.pkl")
        self.vectorizer = joblib.load(vectorizer_path)
        
        # Load model configuration
        config_path = os.path.join(self.models_dir, f"lyrics_config_{self.model_name}.json")
        with open(config_path, 'r') as f:
            self.config = json.load(f)
            
        # Load the actual model(s)
        if self.config.get('has_svd', False):
            # Load SVD + KNN models separately
            svd_path = os.path.join(self.models_dir, f"lyrics_svd_model_{self.model_name}.pkl")
            knn_path = os.path.join(self.models_dir, f"lyrics_knn_model_{self.model_name}.pkl")
            
            self.svd_model = joblib.load(svd_path)
            self.model = joblib.load(knn_path)
        else:
            # Load direct model
            model_path = os.path.join(self.models_dir, f"lyrics_similarity_model_{self.model_name}.pkl")
            self.model = joblib.load(model_path)
            
        # Load metadata
        metadata_path = os.path.join(self.models_dir, "lyrics_training_metadata.pkl")
        self.metadata = joblib.load(metadata_path)
        
        return self
        
    def find_similar(self, query_vector, k: int = 10) -> Tuple[List[int], List[float]]:
        """Find similar songs using the loaded model"""
        if self.config.get('has_svd', False):
            # Transform using SVD first
            query_reduced = self.svd_model.transform(query_vector)
            distances, indices = self.model.kneighbors(query_reduced, n_neighbors=k)
        else:
            distances, indices = self.model.kneighbors(query_vector, n_neighbors=k)
            
        # Return actual distances instead of converting to similarities
        return indices[0].tolist(), distances[0].tolist()
        
    def preprocess_lyrics(self, text: str) -> str:
        """Preprocess lyrics using the same method as training"""
        if not text:
            return ""
            
        # Basic cleaning
        text = text.lower()
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Tokenize and process based on training method
        try:
            tokens = word_tokenize(text)
            lemmatizer = WordNetLemmatizer()
            stop_words = set(stopwords.words('english'))
            
            processed_tokens = [lemmatizer.lemmatize(token) for token in tokens 
                              if token not in stop_words and len(token) > 2]
            
            return ' '.join(processed_tokens)
        except:
            # Fallback to basic processing
            tokens = text.split()
            return ' '.join([token for token in tokens if len(token) > 2])
            
    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        models = []
        for filename in os.listdir(self.models_dir):
            if filename.startswith('lyrics_config_') and filename.endswith('.json'):
                model_name = filename.replace('lyrics_config_', '').replace('.json', '')
                models.append(model_name)
        return models
        
    def get_model_info(self) -> dict:
        """Get information about the loaded model"""
        if not self.config:
            return {}
            
        return {
            'model_name': self.model_name,
            'model_type': self.config.get('model_type'),
            'has_svd': self.config.get('has_svd', False),
            'sklearn_version': self.config.get('sklearn_version'),
            'parameters': self.config.get('model_params', {}),
            'vocabulary_size': len(self.vectorizer.vocabulary_) if self.vectorizer else 0
        }


class LyricsSimilarityService:
    """
    Service for lyrics-based song recommendations using the new compatible model format
    """
    
    def __init__(self):
        """Initialize the Lyrics Similarity Service"""
        self.models_dir = os.environ.get('MODELS_PATH', '/app/models')
        self.model_loader = CompatibleLyricsSimilarityModel(self.models_dir)
        self.current_model = None
        self.lemmatizer = None
        self.stop_words = None
        self._is_ready = False
        
        logger.info("📝 LyricsSimilarityService initialized with compatible model loader")
    
    def is_ready(self) -> bool:
        """Check if the lyrics similarity service is ready"""
        return self._is_ready and self.current_model is not None
    
    async def initialize(self) -> None:
        """Initialize the lyrics similarity service by loading the best available model"""
        logger.info("🚀 Loading lyrics similarity models...")
        
        try:
            # Initialize NLTK components
            try:
                nltk.download('punkt', quiet=True)
                nltk.download('stopwords', quiet=True)
                nltk.download('wordnet', quiet=True)
                self.lemmatizer = WordNetLemmatizer()
                self.stop_words = set(stopwords.words('english'))
            except Exception as e:
                logger.warning(f"NLTK initialization warning: {e}")
                self.lemmatizer = None
                self.stop_words = set()
            
            # Get available models
            available_models = self.model_loader.get_available_models()
            logger.info(f"📋 Available models: {available_models}")
            
            if not available_models:
                raise FileNotFoundError("No compatible model files found")
            
            # Try to load the best model (priority order)
            preferred_models = ['svd_knn', 'svd_knn_large', 'knn_cosine', 'knn_cosine_k20']
            selected_model = None
            
            for preferred_model in preferred_models:
                if preferred_model in available_models:
                    selected_model = preferred_model
                    break
                    
            if not selected_model:
                # Fallback to any available model
                selected_model = available_models[0]
            
            # Load the selected model
            logger.info(f"🔧 Loading model: {selected_model}")
            self.current_model = self.model_loader.load_model(selected_model)
            
            model_info = self.current_model.get_model_info()
            logger.success(f"✅ Lyrics similarity model loaded successfully!")
            logger.info(f"📝 Model: {model_info.get('model_name')}")
            logger.info(f"📊 Vocabulary size: {model_info.get('vocabulary_size')}")
            logger.info(f"🔧 Has SVD: {model_info.get('has_svd')}")
            logger.info(f"📅 SKLearn version: {model_info.get('sklearn_version')}")
            
            self._is_ready = True
            
        except Exception as e:
            logger.error(f"❌ Failed to load lyrics similarity models: {e}")
            logger.error(f"🔍 Available files in models directory:")
            try:
                for file in os.listdir(self.models_dir):
                    logger.error(f"  - {file}")
            except:
                logger.error(f"  Could not list directory: {self.models_dir}")
            self._is_ready = False
            raise
    
    def switch_model(self, model_name: str) -> Dict[str, Any]:
        """Switch to a different model at runtime"""
        try:
            available_models = self.model_loader.get_available_models()
            if model_name not in available_models:
                raise ValueError(f"Model {model_name} not available. Available: {available_models}")
                
            self.current_model = self.model_loader.load_model(model_name)
            model_info = self.current_model.get_model_info()
            
            logger.info(f"🔄 Switched to model: {model_name}")
            return {
                "success": True,
                "model": model_name,
                "info": model_info
            }
        except Exception as e:
            logger.error(f"❌ Failed to switch to model {model_name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        return self.model_loader.get_available_models()
    
    def get_current_model_info(self) -> Dict[str, Any]:
        """Get information about the currently loaded model"""
        if not self.current_model:
            return {"error": "No model loaded"}
        return self.current_model.get_model_info()
    
    def preprocess_lyrics(self, text: str) -> str:
        """Preprocess lyrics using the same method as training"""
        if pd.isna(text) or not text:
            return ""
        
        # Convert to lowercase and clean
        text = text.lower()
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        if not self.lemmatizer or not self.stop_words:
            return text
        
        try:
            # Tokenize
            tokens = word_tokenize(text)
            
            # Apply lemmatization and remove stopwords
            processed_tokens = [
                self.lemmatizer.lemmatize(token) 
                for token in tokens 
                if token not in self.stop_words and len(token) > 2
            ]
            
            return ' '.join(processed_tokens)
        except Exception as e:
            logger.warning(f"Error in text preprocessing: {e}, falling back to basic cleaning")
            return text
    
    async def find_similar_by_lyrics(
        self, 
        lyrics_text: str, 
        k: int = 10,
        db: AsyncSession = None
    ) -> List[Dict[str, Any]]:
        """
        Find similar songs based on lyrics content
        
        Args:
            lyrics_text (str): Lyrics text to find similar songs for
            k (int): Number of similar songs to return
            db (AsyncSession): Database session for enriching results
        
        Returns:
            list: List of similar songs with similarity scores
        """
        if not self.is_ready():
            raise Exception("LyricsSimilarityService not ready - models not loaded")
        
        # Preprocess the input lyrics
        processed_lyrics = self.preprocess_lyrics(lyrics_text)
        
        if not processed_lyrics:
            return []
        
        try:
            # Vectorize the lyrics
            lyrics_vector = self.current_model.vectorizer.transform([processed_lyrics])
            
            # Find similar songs based on model type
            similar_indices, distances = self.current_model.find_similar(lyrics_vector, k=k)
            
            # Format results with distance
            results = []
            for idx, distance in zip(similar_indices, distances):
                if idx < len(self.current_model.metadata['training_songs']):
                    song_info = self.current_model.metadata['training_songs'][idx]
                    results.append({
                        'track_id': song_info['id'],
                        'name': song_info['name'],
                        'artist': song_info['artists_id'],
                        'distance': float(distance)
                    })
            
            # Calculate similarity scores using the utility
            model_info = self.current_model.get_model_info()
            model_type = model_info.get('model_type', 'lyrics')
            results = similarity_calculator.add_similarity_scores(results, model_type)
            
            # Enrich with database information if available
            if db:
                results = await self._enrich_with_db_info(results, db)
            
            return results
            
        except Exception as e:
            logger.error(f"Error finding similar songs by lyrics: {e}")
            return []
    
    async def find_similar_by_track_id(
        self, 
        track_id: str, 
        k: int = 10,
        db: AsyncSession = None
    ) -> List[Dict[str, Any]]:
        """
        Find similar songs based on a track's lyrics
        
        Args:
            track_id (str): Spotify track ID
            k (int): Number of similar songs to return
            db (AsyncSession): Database session
        
        Returns:
            list: List of similar songs with similarity scores
        """
        if not db:
            raise ValueError("Database session required for track-based similarity")
        
        # Get track lyrics from database
        track_query = select(Track).filter(Track.id == track_id)
        result = await db.execute(track_query)
        track = result.scalar_one_or_none()
        
        if not track or not track.lyrics:
            logger.warning(f"No lyrics found for track {track_id}")
            return []
        
        return await self.find_similar_by_lyrics(track.lyrics, k, db)
    
    async def _enrich_with_db_info(
        self, 
        results: List[Dict[str, Any]], 
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """Enrich results with additional database information"""
        track_ids = [result['track_id'] for result in results]
        
        # Query database for additional track information
        tracks_query = select(Track).options(
            joinedload(Track.artist),
            joinedload(Track.album)
        ).filter(Track.id.in_(track_ids))
        
        db_result = await db.execute(tracks_query)
        tracks = {track.id: track for track in db_result.scalars().all()}
        
        # Enrich results
        enriched_results = []
        for result in results:
            track_id = result['track_id']
            if track_id in tracks:
                track = tracks[track_id]
                result.update({
                    'album': track.album.name if track.album else 'Unknown Album',
                    'popularity': track.popularity or 0,
                    'preview_url': track.preview_url,
                    'spotify_url': track.spotify_uri or f"https://open.spotify.com/track/{track_id}",
                    'duration_ms': track.duration_ms or 0,
                    # Audio features for additional context
                    'danceability': track.danceability or 0.0,
                    'energy': track.energy or 0.0,
                    'valence': track.valence or 0.0
                })
            enriched_results.append(result)
        
        return enriched_results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the lyrics similarity service"""
        if not self.is_ready():
            return {"status": "not_ready"}
        
        return {
            "status": "ready",
            "vocabulary_size": self.current_model.metadata.get('vocabulary_size', 0),
            "training_dataset_size": self.current_model.metadata.get('dataset_size', 0),
            "preprocessing_method": self.current_model.metadata.get('preprocessing_method', 'unknown'),
            "tfidf_config": self.current_model.metadata.get('tfidf_config', 'unknown'),
            "model_type": self.current_model.metadata.get('model_type', 'unknown'),
            "training_date": self.current_model.metadata.get('training_date', 'unknown')
        }
    
    def cleanup(self) -> None:
        """Cleanup resources"""
        self.current_model = None
        self._is_ready = False
        logger.info("🧹 LyricsSimilarityService cleaned up") 