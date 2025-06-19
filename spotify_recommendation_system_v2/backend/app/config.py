"""
Configuration settings for the Spotify Recommendation System v2
"""

import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings using Pydantic BaseSettings"""
    
    # API Configuration
    API_V2_STR: str = "/api/v2"
    PROJECT_NAME: str = "Spotify Music Recommendation System v2"
    VERSION: str = "2.0.0"
    DESCRIPTION: str = "AI-powered music recommendation using HDBSCAN clustering and KNN"
    
    # Server Configuration
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8080",
            "http://127.0.0.1:8080"
        ],
        env="CORS_ORIGINS"
    )
    
    # Database Configuration
    DATABASE_URL: str = Field(
        default="postgresql://spotify_user:spotify_password@localhost:5432/spotify_recommendations",
        env="DATABASE_URL"
    )
    DATABASE_HOST: str = Field(default="localhost", env="DATABASE_HOST")
    DATABASE_PORT: int = Field(default=5432, env="DATABASE_PORT")
    DATABASE_NAME: str = Field(default="spotify_recommendations", env="DATABASE_NAME")
    DATABASE_USER: str = Field(default="spotify_user", env="DATABASE_USER")
    DATABASE_PASSWORD: str = Field(default="spotify_password", env="DATABASE_PASSWORD")
    
    # Database Pool Configuration
    DATABASE_POOL_SIZE: int = Field(default=20, env="DATABASE_POOL_SIZE")
    DATABASE_MAX_OVERFLOW: int = Field(default=0, env="DATABASE_MAX_OVERFLOW")
    DATABASE_POOL_RECYCLE: int = Field(default=3600, env="DATABASE_POOL_RECYCLE")
    DATABASE_ECHO: bool = Field(default=False, env="DATABASE_ECHO")
    
    # Data Paths (for initial import)
    DATA_PATH: str = Field(default="../data", env="DATA_PATH")
    MODELS_PATH: str = Field(default="../data/models", env="MODELS_PATH")
    RAW_DATA_PATH: str = Field(default="../data/raw", env="RAW_DATA_PATH")
    
    # Model File Paths (relative to MODELS_PATH)
    HDBSCAN_MODEL_FILE: str = "hdbscan_model.pkl"
    KNN_MODEL_FILE: str = "knn_model.pkl"
    CLUSTER_LABELS_FILE: str = "cluster_labels.pkl"
    AUDIO_EMBEDDINGS_FILE: str = "audio_embeddings.pkl"
    SONG_INDICES_FILE: str = "song_indices.pkl"
    SCALER_FILE: str = "scaler.pkl"
    
    # Data File Paths (relative to RAW_DATA_PATH)
    SPOTIFY_TRACKS_FILE: str = "spotify_tracks.csv"
    LOW_LEVEL_AUDIO_FEATURES_FILE: str = "low_level_audio_features.csv"
    LYRICS_FEATURES_FILE: str = "lyrics_features.csv"
    SPOTIFY_ALBUMS_FILE: str = "spotify_albums.csv"
    SPOTIFY_ARTISTS_FILE: str = "spotify_artists.csv"
    
    # ML Configuration
    DEFAULT_N_RECOMMENDATIONS: int = 12
    MAX_N_RECOMMENDATIONS: int = 50
    MIN_CLUSTER_SIZE: int = 30
    KNN_METRIC: str = "euclidean"
    KNN_ALGORITHM: str = "auto"
    
    # Performance Configuration
    CACHE_TTL: int = 3600  # 1 hour in seconds
    MAX_WORKERS: int = 4
    REQUEST_TIMEOUT: int = 30
    
    # Logging Configuration
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    
    # Security Configuration
    SECRET_KEY: str = Field(default="your-secret-key-change-in-production", env="SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    

    
    # Feature Engineering Configuration
    FEATURE_SCALING: str = "minmax"  # "minmax", "standard", "robust"
    PCA_COMPONENTS: int = 60
    USE_PCA: bool = True
    
    # Recommendation Configuration
    RECOMMENDATION_TYPES: List[str] = ["cluster", "global", "hybrid"]
    DEFAULT_RECOMMENDATION_TYPE: str = "cluster"
    CLUSTER_WEIGHT: float = 0.7
    GLOBAL_WEIGHT: float = 0.3
    
    # Import Configuration
    IMPORT_BATCH_SIZE: int = Field(default=1000, env="IMPORT_BATCH_SIZE")
    IMPORT_SKIP_DUPLICATES: bool = Field(default=True, env="IMPORT_SKIP_DUPLICATES")
    IMPORT_VALIDATE_DATA: bool = Field(default=True, env="IMPORT_VALIDATE_DATA")
    
    # Audio Features Processing
    MEL_FEATURES_COUNT: int = 128
    MFCC_FEATURES_COUNT: int = 48
    CHROMA_FEATURES_COUNT: int = 12
    SPECTRAL_CONTRAST_COUNT: int = 7
    TONNETZ_FEATURES_COUNT: int = 6
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
    
    @property
    def models_path_full(self) -> str:
        """Get full path to models directory"""
        return os.path.abspath(self.MODELS_PATH)
    
    @property
    def data_path_full(self) -> str:
        """Get full path to data directory"""
        return os.path.abspath(self.DATA_PATH)
    
    @property
    def raw_data_path_full(self) -> str:
        """Get full path to raw data directory"""
        return os.path.abspath(self.RAW_DATA_PATH)
    
    def get_model_path(self, model_file: str) -> str:
        """Get full path to a model file"""
        return os.path.join(self.models_path_full, model_file)
    
    def get_data_path(self, data_file: str) -> str:
        """Get full path to a data file"""
        return os.path.join(self.raw_data_path_full, data_file)
    
    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL for migrations"""
        return self.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")


# Global settings instance
settings = Settings() 