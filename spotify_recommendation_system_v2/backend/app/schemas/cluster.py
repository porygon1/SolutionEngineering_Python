"""
Pydantic schemas for cluster-related API responses
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class ClusterInfo(BaseModel):
    """Basic cluster information"""
    id: int = Field(..., description="Cluster ID")
    name: Optional[str] = Field(None, description="Human-readable cluster name")
    description: Optional[str] = Field(None, description="Cluster description")
    size: int = Field(..., description="Number of tracks in cluster")
    cohesion_score: Optional[float] = Field(None, description="Internal cluster cohesion score")
    separation_score: Optional[float] = Field(None, description="Separation from other clusters")
    dominant_genres: List[str] = Field(default_factory=list, description="Most common genres in cluster")
    dominant_features: List[str] = Field(default_factory=list, description="Most distinctive audio features")
    era: Optional[str] = Field(None, description="Dominant time period")
    
    class Config:
        from_attributes = True


class ClusterStats(BaseModel):
    """Cluster statistics"""
    total_tracks: int = Field(..., description="Total number of tracks")
    avg_popularity: float = Field(..., description="Average popularity score")
    avg_energy: float = Field(..., description="Average energy level")
    avg_valence: float = Field(..., description="Average valence (positivity)")
    avg_danceability: float = Field(..., description="Average danceability")
    avg_tempo: float = Field(..., description="Average tempo (BPM)")
    unique_artists: int = Field(..., description="Number of unique artists")


class ClusterTrack(BaseModel):
    """Track information within a cluster"""
    id: str = Field(..., description="Track ID")
    name: str = Field(..., description="Track name")
    artist_name: str = Field(..., description="Artist name")
    popularity: Optional[int] = Field(None, description="Popularity score")
    energy: Optional[float] = Field(None, description="Energy level")
    valence: Optional[float] = Field(None, description="Valence (positivity)")
    danceability: Optional[float] = Field(None, description="Danceability")
    tempo: Optional[float] = Field(None, description="Tempo (BPM)")


class ClusterResponse(BaseModel):
    """Detailed cluster response"""
    id: int = Field(..., description="Cluster ID")
    name: Optional[str] = Field(None, description="Human-readable cluster name")
    description: Optional[str] = Field(None, description="Cluster description")
    size: int = Field(..., description="Number of tracks in cluster")
    cohesion_score: Optional[float] = Field(None, description="Internal cluster cohesion score")
    separation_score: Optional[float] = Field(None, description="Separation from other clusters")
    dominant_genres: List[str] = Field(default_factory=list, description="Most common genres in cluster")
    dominant_features: List[str] = Field(default_factory=list, description="Most distinctive audio features")
    era: Optional[str] = Field(None, description="Dominant time period")
    statistics: ClusterStats = Field(..., description="Cluster statistics")
    sample_tracks: List[ClusterTrack] = Field(default_factory=list, description="Sample tracks from cluster")
    audio_stats: Optional[Dict[str, Any]] = Field(None, description="Detailed audio feature statistics")
    
    class Config:
        from_attributes = True


class ClusterAnalysis(BaseModel):
    """Cluster analysis result"""
    cluster_id: int = Field(..., description="Cluster ID")
    analysis_type: str = Field(..., description="Type of analysis performed")
    results: Dict[str, Any] = Field(..., description="Analysis results")
    confidence_score: float = Field(..., description="Confidence in analysis results")
    timestamp: datetime = Field(..., description="Analysis timestamp")
    
    class Config:
        from_attributes = True 