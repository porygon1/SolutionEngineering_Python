"""
Pydantic schemas for recommendation-related data structures
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime


class Song(BaseModel):
    """Song data model"""
    id: str = Field(..., description="Spotify track ID")
    name: str = Field(..., description="Song name")
    artist: str = Field(..., description="Artist name or ID")
    album: str = Field(default="", description="Album name or ID")
    duration_ms: int = Field(default=0, description="Duration in milliseconds")
    popularity: int = Field(default=0, description="Spotify popularity score (0-100)")
    
    # Audio features
    acousticness: float = Field(default=0.0, ge=0.0, le=1.0)
    danceability: float = Field(default=0.0, ge=0.0, le=1.0)
    energy: float = Field(default=0.0, ge=0.0, le=1.0)
    instrumentalness: float = Field(default=0.0, ge=0.0, le=1.0)
    liveness: float = Field(default=0.0, ge=0.0, le=1.0)
    loudness: float = Field(default=0.0, description="Loudness in dB")
    speechiness: float = Field(default=0.0, ge=0.0, le=1.0)
    tempo: float = Field(default=0.0, gt=0.0, description="Tempo in BPM")
    valence: float = Field(default=0.0, ge=0.0, le=1.0)
    
    # Musical features
    key: int = Field(default=0, ge=0, le=11, description="Pitch class (0-11)")
    mode: int = Field(default=0, ge=0, le=1, description="Modality (0=minor, 1=major)")
    time_signature: int = Field(default=4, ge=1, le=7, description="Time signature")
    
    # Clustering info
    cluster_id: int = Field(default=-1, description="HDBSCAN cluster ID")
    
    # URLs
    preview_url: Optional[str] = Field(default=None, description="30-second preview URL")
    spotify_url: str = Field(default="", description="Spotify Web Player URL")
    album_image_url: Optional[str] = Field(default=None, description="Album cover image URL")
    
    # Recommendation metadata
    similarity_score: Optional[float] = Field(default=None, description="Similarity score (0-1) when from recommendations")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "4iV5W9uYEdYUVa79Axb7Rh",
                "name": "Somebody That I Used to Know",
                "artist": "Gotye feat. Kimbra",
                "album": "Making Mirrors",
                "duration_ms": 244533,
                "popularity": 85,
                "acousticness": 0.334,
                "danceability": 0.708,
                "energy": 0.723,
                "instrumentalness": 0.0,
                "liveness": 0.0985,
                "loudness": -5.934,
                "speechiness": 0.0395,
                "tempo": 129.049,
                "valence": 0.446,
                "key": 1,
                "mode": 1,
                "time_signature": 4,
                "cluster_id": 42,
                "preview_url": "https://p.scdn.co/mp3-preview/...",
                "spotify_url": "https://open.spotify.com/track/4iV5W9uYEdYUVa79Axb7Rh",
                "album_image_url": "https://i.scdn.co/image/ab67616d0000b273..."
            }
        }


class RecommendationRequest(BaseModel):
    """Request model for getting recommendations"""
    liked_song_ids: List[str] = Field(
        ..., 
        min_items=1, 
        max_items=10,
        description="List of Spotify track IDs that the user likes"
    )
    n_recommendations: int = Field(
        default=12,
        ge=1,
        le=50,
        description="Number of recommendations to return"
    )
    recommendation_type: str = Field(
        default="cluster",
        description="Type of recommendation algorithm"
    )
    filters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional filters for recommendations"
    )
    user_id: Optional[str] = Field(
        default=None,
        description="Optional user ID for personalization"
    )
    
    @validator('recommendation_type')
    def validate_recommendation_type(cls, v):
        allowed_types = [
            "cluster", "global", "hybrid", "lyrics", "hdbscan_knn", "artist_based", "genre_based",
            # HDBSCAN model variants
            "hdbscan_naive_features", "hdbscan_pca_features", "hdbscan_llav_features", 
            "hdbscan_llav_pca", "hdbscan_combined_features",
            # Lyrics model variants
            "svd_knn", "knn_cosine", "knn_cosine_k20", "knn_euclidean"
        ]
        if v not in allowed_types:
            raise ValueError(f"recommendation_type must be one of {allowed_types}")
        return v
    
    @validator('liked_song_ids')
    def validate_liked_songs(cls, v):
        if not v:
            raise ValueError("At least one liked song ID is required")
        # Basic Spotify ID format check
        for song_id in v:
            if not isinstance(song_id, str) or len(song_id) != 22:
                raise ValueError(f"Invalid Spotify track ID format: {song_id}")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "liked_song_ids": [
                    "4iV5W9uYEdYUVa79Axb7Rh",
                    "7ouMYWpwJ422jRcDASZB7P",
                    "0VjIjW4GlULA3CxJSZ4Lx1"
                ],
                "n_recommendations": 12,
                "recommendation_type": "cluster",
                "filters": {
                    "min_popularity": 20,
                    "max_tempo": 140
                },
                "user_id": "user123"
            }
        }


class ClusterUsed(BaseModel):
    """Information about clusters used in recommendations"""
    cluster_id: int
    size: int
    source_song: str
    
    class Config:
        schema_extra = {
            "example": {
                "cluster_id": 42,
                "size": 156,
                "source_song": "4iV5W9uYEdYUVa79Axb7Rh"
            }
        }


class RecommendationResponse(BaseModel):
    """Response model for recommendations"""
    recommendations: List[Song] = Field(..., description="List of recommended songs")
    recommendation_type: str = Field(..., description="Type of algorithm used")
    clusters_used: List[ClusterUsed] = Field(
        default_factory=list,
        description="Information about clusters used"
    )
    total_found: int = Field(..., description="Total number of recommendations found")
    processing_time_ms: float = Field(default=0.0, description="Processing time in milliseconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Metadata
    filters_applied: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Filters that were applied"
    )
    similarity_scores: Optional[List[float]] = Field(
        default=None,
        description="Similarity scores for recommendations"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "recommendations": [
                    {
                        "id": "7ouMYWpwJ422jRcDASZB7P",
                        "name": "Heat Waves",
                        "artist": "Glass Animals",
                        "cluster_id": 42
                    }
                ],
                "recommendation_type": "cluster",
                "clusters_used": [
                    {
                        "cluster_id": 42,
                        "size": 156,
                        "source_song": "4iV5W9uYEdYUVa79Axb7Rh"
                    }
                ],
                "total_found": 12,
                "processing_time_ms": 45.2,
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }


class PreferenceRequest(BaseModel):
    """Request for initial song preference selection"""
    genres: Optional[List[str]] = Field(default=None, description="Preferred genres")
    artists: Optional[List[str]] = Field(default=None, description="Preferred artists")
    audio_features: Optional[Dict[str, float]] = Field(
        default=None,
        description="Preferred audio feature ranges"
    )
    decade: Optional[str] = Field(default=None, description="Preferred decade")
    popularity_range: Optional[List[int]] = Field(
        default=None,
        description="Popularity range [min, max]"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "genres": ["indie rock", "alternative"],
                "artists": ["Arctic Monkeys", "Tame Impala"],
                "audio_features": {
                    "energy": 0.7,
                    "danceability": 0.6,
                    "valence": 0.5
                },
                "decade": "2010s",
                "popularity_range": [40, 80]
            }
        }


class PreferenceResponse(BaseModel):
    """Response with song suggestions for preference selection"""
    suggested_songs: List[Song] = Field(..., description="Songs to choose from")
    total_available: int = Field(..., description="Total songs matching criteria")
    categories: Dict[str, int] = Field(
        default_factory=dict,
        description="Categories and counts"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "suggested_songs": [],
                "total_available": 500,
                "categories": {
                    "indie rock": 150,
                    "alternative": 200,
                    "pop rock": 100
                }
            }
        }


class UserFeedback(BaseModel):
    """User feedback on recommendations"""
    recommendation_id: str = Field(..., description="ID of the recommendation session")
    song_id: str = Field(..., description="ID of the recommended song")
    feedback_type: str = Field(..., description="Type of feedback")
    rating: Optional[int] = Field(default=None, ge=1, le=5, description="Rating 1-5")
    comment: Optional[str] = Field(default=None, max_length=500)
    
    @validator('feedback_type')
    def validate_feedback_type(cls, v):
        allowed_types = ["like", "dislike", "skip", "play", "save"]
        if v not in allowed_types:
            raise ValueError(f"feedback_type must be one of {allowed_types}")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "recommendation_id": "rec_123456",
                "song_id": "4iV5W9uYEdYUVa79Axb7Rh",
                "feedback_type": "like",
                "rating": 4,
                "comment": "Great recommendation!"
            }
        }


class ModelComparisonRequest(BaseModel):
    """Request model for comparing different recommendation models"""
    liked_song_ids: List[str] = Field(
        ..., 
        min_items=1, 
        max_items=5,
        description="List of Spotify track IDs that the user likes"
    )
    models_to_compare: List[str] = Field(
        default=["cluster", "lyrics"],
        description="List of model types to compare"
    )
    n_recommendations: int = Field(
        default=10,
        ge=1,
        le=20,
        description="Number of recommendations per model"
    )
    
    @validator('models_to_compare')
    def validate_models(cls, v):
        allowed_models = [
            "cluster", "global", "hybrid", "lyrics", "hdbscan_knn", "artist_based", "genre_based",
            # HDBSCAN model variants
            "hdbscan_naive_features", "hdbscan_pca_features", "hdbscan_llav_features", 
            "hdbscan_llav_pca", "hdbscan_combined_features",
            # Lyrics model variants
            "svd_knn", "knn_cosine", "knn_cosine_k20", "knn_euclidean"
        ]
        for model in v:
            if model not in allowed_models:
                raise ValueError(f"Model {model} not supported. Must be one of {allowed_models}")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "liked_song_ids": [
                    "4iV5W9uYEdYUVa79Axb7Rh",
                    "7ouMYWpwJ422jRcDASZB7P"
                ],
                "models_to_compare": ["cluster", "lyrics"],
                "n_recommendations": 10
            }
        }


class ModelComparisonResult(BaseModel):
    """Results from a single model in comparison"""
    model_type: str = Field(..., description="Type of recommendation model")
    recommendations: List[Song] = Field(..., description="Recommended songs")
    processing_time_ms: float = Field(..., description="Time taken to generate recommendations")
    total_found: int = Field(..., description="Total recommendations found")
    error: Optional[str] = Field(default=None, description="Error message if model failed")
    
    class Config:
        schema_extra = {
            "example": {
                "model_type": "lyrics",
                "recommendations": [],
                "processing_time_ms": 45.2,
                "total_found": 10,
                "error": None
            }
        }


class ModelComparisonResponse(BaseModel):
    """Response model for model comparison"""
    query_songs: List[Song] = Field(..., description="Songs that were used as input")
    results: List[ModelComparisonResult] = Field(..., description="Results from each model")
    total_processing_time_ms: float = Field(..., description="Total time for all models")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        schema_extra = {
            "example": {
                "query_songs": [],
                "results": [
                    {
                        "model_type": "cluster",
                        "recommendations": [],
                        "processing_time_ms": 25.1,
                        "total_found": 10
                    },
                    {
                        "model_type": "lyrics", 
                        "recommendations": [],
                        "processing_time_ms": 67.3,
                        "total_found": 8
                    }
                ],
                "total_processing_time_ms": 92.4,
                "timestamp": "2024-01-15T10:30:00Z"
            }
        } 