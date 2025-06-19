"""
SQLAlchemy models for the Spotify Music Recommendation System
Normalized database schema with proper relationships and constraints
"""

from sqlalchemy import (
    Column, Integer, String, Float, Text, Boolean, DateTime, 
    ForeignKey, Index, CheckConstraint, UniqueConstraint,
    ARRAY, JSON
)
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, List
import uuid

from app.database.database import Base


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps"""
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class Artist(Base, TimestampMixin):
    """Artist entity - normalized from spotify_artists.csv"""
    __tablename__ = "artists"
    
    id = Column(String(22), primary_key=True)  # Spotify artist ID
    name = Column(String(255), nullable=False, index=True)
    popularity = Column(Integer, CheckConstraint('popularity >= 0 AND popularity <= 100'))
    followers = Column(Integer, CheckConstraint('followers >= 0'))
    genres = Column(ARRAY(String), default=list)  # Array of genre strings
    spotify_type = Column(String(50), default='artist')
    
    # Relationships
    albums = relationship("Album", back_populates="artist", cascade="all, delete-orphan")
    tracks = relationship("Track", back_populates="artist", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('ix_artists_name_popularity', 'name', 'popularity'),
        Index('ix_artists_genres', 'genres', postgresql_using='gin'),
    )

    def __repr__(self):
        return f"<Artist(id='{self.id}', name='{self.name}')>"


class Album(Base, TimestampMixin):
    """Album entity - normalized from spotify_albums.csv"""
    __tablename__ = "albums"
    
    id = Column(String(22), primary_key=True)  # Spotify album ID
    name = Column(String(255), nullable=False, index=True)
    album_type = Column(String(50))  # album, single, compilation
    release_date = Column(String(10))  # YYYY, YYYY-MM, or YYYY-MM-DD
    release_date_precision = Column(String(10))  # year, month, day
    total_tracks = Column(Integer, CheckConstraint('total_tracks > 0'))
    available_markets = Column(ARRAY(String), default=list)
    external_urls = Column(JSON)
    images = Column(JSON)  # Array of image objects
    spotify_uri = Column(String(255))
    spotify_href = Column(String(255))
    spotify_type = Column(String(50), default='album')
    
    # Foreign Keys
    artist_id = Column(String(22), ForeignKey('artists.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Relationships
    artist = relationship("Artist", back_populates="albums")
    tracks = relationship("Track", back_populates="album", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('ix_albums_artist_name', 'artist_id', 'name'),
        Index('ix_albums_release_date', 'release_date'),
        Index('ix_albums_type', 'album_type'),
    )

    def __repr__(self):
        return f"<Album(id='{self.id}', name='{self.name}')>"


class Track(Base, TimestampMixin):
    """Track entity - main tracks table from spotify_tracks.csv"""
    __tablename__ = "tracks"
    
    id = Column(String(22), primary_key=True)  # Spotify track ID
    name = Column(String(255), nullable=False, index=True)
    duration_ms = Column(Integer, CheckConstraint('duration_ms > 0'))
    popularity = Column(Integer, CheckConstraint('popularity >= 0 AND popularity <= 100'))
    track_number = Column(Integer, CheckConstraint('track_number > 0'))
    disc_number = Column(Integer, CheckConstraint('disc_number > 0'))
    explicit = Column(Boolean, default=False)
    is_local = Column(Boolean, default=False)
    
    # Audio Features (from Spotify API)
    acousticness = Column(Float, CheckConstraint('acousticness >= 0 AND acousticness <= 1'))
    danceability = Column(Float, CheckConstraint('danceability >= 0 AND danceability <= 1'))
    energy = Column(Float, CheckConstraint('energy >= 0 AND energy <= 1'))
    instrumentalness = Column(Float, CheckConstraint('instrumentalness >= 0 AND instrumentalness <= 1'))
    liveness = Column(Float, CheckConstraint('liveness >= 0 AND liveness <= 1'))
    loudness = Column(Float)  # dB, can be negative
    speechiness = Column(Float, CheckConstraint('speechiness >= 0 AND speechiness <= 1'))
    valence = Column(Float, CheckConstraint('valence >= 0 AND valence <= 1'))
    tempo = Column(Float, CheckConstraint('tempo > 0'))
    
    # Musical Features
    key = Column(Integer, CheckConstraint('key >= 0 AND key <= 11'))  # Pitch class
    mode = Column(Integer, CheckConstraint('mode >= 0 AND mode <= 1'))  # 0=minor, 1=major
    time_signature = Column(Integer, CheckConstraint('time_signature >= 1 AND time_signature <= 7'))
    
    # URLs and metadata
    preview_url = Column(String(255))
    spotify_uri = Column(String(255))
    spotify_href = Column(String(255))
    track_href = Column(String(255))
    analysis_url = Column(String(255))
    spotify_type = Column(String(50), default='track')
    
    # Additional metadata
    available_markets = Column(ARRAY(String), default=list)
    country = Column(String(5))  # ISO country code
    playlist = Column(String(255))  # Source playlist if any
    lyrics = Column(Text)  # Full lyrics text
    
    # Foreign Keys
    artist_id = Column(String(22), ForeignKey('artists.id', ondelete='CASCADE'), nullable=False, index=True)
    album_id = Column(String(22), ForeignKey('albums.id', ondelete='SET NULL'), index=True)
    
    # ML Model Fields
    cluster_id = Column(Integer, index=True)  # HDBSCAN cluster assignment
    cluster_probability = Column(Float)  # Cluster membership probability
    
    # Relationships
    artist = relationship("Artist", back_populates="tracks")
    album = relationship("Album", back_populates="tracks")
    audio_features = relationship("AudioFeatures", back_populates="track", uselist=False, cascade="all, delete-orphan")
    lyrics_features = relationship("LyricsFeatures", back_populates="track", uselist=False, cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index('ix_tracks_artist_album', 'artist_id', 'album_id'),
        Index('ix_tracks_popularity_name', 'popularity', 'name'),
        Index('ix_tracks_audio_features', 'energy', 'valence', 'danceability'),
        Index('ix_tracks_musical_features', 'key', 'mode', 'tempo'),
        Index('ix_tracks_cluster', 'cluster_id'),
        Index('ix_tracks_search', 'name', postgresql_ops={'name': 'gin_trgm_ops'}, postgresql_using='gin'),
    )

    def __repr__(self):
        return f"<Track(id='{self.id}', name='{self.name}')>"


class AudioFeatures(Base, TimestampMixin):
    """Low-level audio features - from low_level_audio_features.csv"""
    __tablename__ = "audio_features"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    track_id = Column(String(22), ForeignKey('tracks.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)
    
    # Chroma features (12 values)
    chroma_1 = Column(Float)
    chroma_2 = Column(Float)
    chroma_3 = Column(Float)
    chroma_4 = Column(Float)
    chroma_5 = Column(Float)
    chroma_6 = Column(Float)
    chroma_7 = Column(Float)
    chroma_8 = Column(Float)
    chroma_9 = Column(Float)
    chroma_10 = Column(Float)
    chroma_11 = Column(Float)
    chroma_12 = Column(Float)
    
    # MEL-frequency features (128 values) - stored as JSON for efficiency
    mel_features = Column(JSON)  # Array of 128 MEL values
    
    # MFCC features (48 values) - stored as JSON for efficiency  
    mfcc_features = Column(JSON)  # Array of 48 MFCC values
    
    # Spectral contrast (7 values)
    spectral_contrast_1 = Column(Float)
    spectral_contrast_2 = Column(Float)
    spectral_contrast_3 = Column(Float)
    spectral_contrast_4 = Column(Float)
    spectral_contrast_5 = Column(Float)
    spectral_contrast_6 = Column(Float)
    spectral_contrast_7 = Column(Float)
    
    # Tonnetz features (6 values)
    tonnetz_1 = Column(Float)
    tonnetz_2 = Column(Float)
    tonnetz_3 = Column(Float)
    tonnetz_4 = Column(Float)
    tonnetz_5 = Column(Float)
    tonnetz_6 = Column(Float)
    
    # Additional audio features
    zcr = Column(Float)  # Zero crossing rate
    entropy_energy = Column(Float)
    spectral_bandwidth = Column(Float)
    spectral_centroid = Column(Float)
    spectral_rolloff_max = Column(Float)
    spectral_rolloff_min = Column(Float)
    
    # Relationship
    track = relationship("Track", back_populates="audio_features")
    
    # Indexes
    __table_args__ = (
        Index('ix_audio_features_spectral', 'spectral_centroid', 'spectral_bandwidth'),
    )

    def __repr__(self):
        return f"<AudioFeatures(track_id='{self.track_id}')>"


class LyricsFeatures(Base, TimestampMixin):
    """Lyrics analysis features - from lyrics_features.csv"""
    __tablename__ = "lyrics_features"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    track_id = Column(String(22), ForeignKey('tracks.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)
    
    # Text analysis features
    mean_syllables_word = Column(Float, CheckConstraint('mean_syllables_word > 0'))
    mean_words_sentence = Column(Float, CheckConstraint('mean_words_sentence > 0'))
    n_sentences = Column(Integer, CheckConstraint('n_sentences >= 0'))
    n_words = Column(Integer, CheckConstraint('n_words >= 0'))
    sentence_similarity = Column(Float, CheckConstraint('sentence_similarity >= 0 AND sentence_similarity <= 1'))
    vocabulary_wealth = Column(Float, CheckConstraint('vocabulary_wealth >= 0 AND vocabulary_wealth <= 1'))
    
    # Additional text metrics
    language = Column(String(10))  # Language code
    sentiment_score = Column(Float)  # Sentiment analysis (-1 to 1)
    reading_level = Column(Float)  # Reading difficulty score
    
    # Relationship
    track = relationship("Track", back_populates="lyrics_features")

    def __repr__(self):
        return f"<LyricsFeatures(track_id='{self.track_id}')>"


class Cluster(Base, TimestampMixin):
    """HDBSCAN cluster information and statistics"""
    __tablename__ = "clusters"
    
    id = Column(Integer, primary_key=True)  # Cluster ID from HDBSCAN
    name = Column(String(255))  # Human-readable cluster name
    description = Column(Text)  # Cluster description
    
    # Cluster statistics
    size = Column(Integer, CheckConstraint('size > 0'))
    cohesion_score = Column(Float)  # Internal cluster cohesion
    separation_score = Column(Float)  # Separation from other clusters
    
    # Audio feature statistics (JSON for flexibility)
    audio_stats = Column(JSON)  # Mean, std, min, max for each audio feature
    
    # Dominant characteristics
    dominant_genres = Column(ARRAY(String))
    dominant_features = Column(ARRAY(String))  # Most distinctive audio features
    era = Column(String(50))  # Dominant time period
    
    # Indexes
    __table_args__ = (
        Index('ix_clusters_size', 'size'),
    )

    def __repr__(self):
        return f"<Cluster(id={self.id}, name='{self.name}', size={self.size})>"


class UserInteraction(Base, TimestampMixin):
    """User interactions for recommendation improvement"""
    __tablename__ = "user_interactions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(255), index=True)  # User identifier
    session_id = Column(String(255), index=True)  # Session identifier
    
    # Interaction details
    interaction_type = Column(String(50), nullable=False)  # like, dislike, play, skip, save
    track_id = Column(String(22), ForeignKey('tracks.id', ondelete='CASCADE'), nullable=False, index=True)
    recommendation_id = Column(String(255))  # Links to recommendation session
    
    # Context
    recommendation_type = Column(String(50))  # cluster, global, hybrid
    position_in_list = Column(Integer)  # Position in recommendation list
    source_tracks = Column(ARRAY(String))  # Tracks used to generate recommendation
    
    # Feedback
    rating = Column(Integer, CheckConstraint('rating >= 1 AND rating <= 5'))
    feedback_text = Column(Text)
    
    # Relationship
    track = relationship("Track")
    
    # Indexes
    __table_args__ = (
        Index('ix_interactions_user_type', 'user_id', 'interaction_type'),
        Index('ix_interactions_track_type', 'track_id', 'interaction_type'),
        Index('ix_interactions_timestamp', 'created_at'),
    )

    def __repr__(self):
        return f"<UserInteraction(user_id='{self.user_id}', type='{self.interaction_type}')>"


class RecommendationCache(Base, TimestampMixin):
    """Cache for recommendation results"""
    __tablename__ = "recommendation_cache"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cache_key = Column(String(255), nullable=False, unique=True, index=True)
    
    # Request parameters
    input_tracks = Column(ARRAY(String), nullable=False)  # Input track IDs
    recommendation_type = Column(String(50), nullable=False)
    n_recommendations = Column(Integer, nullable=False)
    filters_applied = Column(JSON)
    
    # Results
    recommended_tracks = Column(ARRAY(String), nullable=False)  # Output track IDs
    similarity_scores = Column(ARRAY(Float))
    clusters_used = Column(ARRAY(Integer))
    processing_time_ms = Column(Float)
    
    # Cache metadata
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    hit_count = Column(Integer, default=0)
    
    # Indexes
    __table_args__ = (
        Index('ix_cache_expires', 'expires_at'),
        Index('ix_cache_type', 'recommendation_type'),
    )

    def __repr__(self):
        return f"<RecommendationCache(cache_key='{self.cache_key}')>" 