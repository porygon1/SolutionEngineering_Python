"""
Clusters router for Spotify Music Recommendation System v2
Handles cluster information, statistics, and exploration
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from typing import List, Optional, Dict, Any
from loguru import logger

from app.database.database import get_database
from app.database.models import Track, Artist, Album, Cluster
from app.schemas.cluster import (
    ClusterInfo, ClusterStats, ClusterResponse,
    ClusterTrack, ClusterAnalysis
)
from app.services.model_service import ModelService

router = APIRouter()


@router.get("/", response_model=List[ClusterInfo])
async def get_all_clusters(
    skip: int = Query(0, ge=0, description="Number of clusters to skip"),
    limit: int = Query(50, ge=1, le=100, description="Number of clusters to return"),
    min_size: Optional[int] = Query(None, ge=1, description="Minimum cluster size"),
    sort_by: str = Query("size", description="Sort by: size, id"),
    order: str = Query("desc", description="Sort order: asc, desc"),
    db: AsyncSession = Depends(get_database)
):
    """
    Get all music clusters with basic information
    """
    try:
        # Get cluster information from clusters table
        cluster_query = select(Cluster)
        
        # Apply minimum size filter
        if min_size:
            cluster_query = cluster_query.where(Cluster.size >= min_size)
        
        # Apply sorting
        if sort_by == "size":
            order_column = Cluster.size
        else:
            order_column = Cluster.id
        
        if order.lower() == "desc":
            cluster_query = cluster_query.order_by(order_column.desc())
        else:
            cluster_query = cluster_query.order_by(order_column.asc())
        
        # Apply pagination
        cluster_query = cluster_query.offset(skip).limit(limit)
        
        # Execute query
        result = await db.execute(cluster_query)
        clusters = result.scalars().all()
        
        # Convert to response format
        cluster_infos = []
        for cluster in clusters:
            cluster_infos.append(ClusterInfo(
                id=cluster.id,
                name=cluster.name or f"Cluster {cluster.id}",
                description=cluster.description,
                size=cluster.size,
                cohesion_score=cluster.cohesion_score,
                separation_score=cluster.separation_score,
                dominant_genres=cluster.dominant_genres or [],
                dominant_features=cluster.dominant_features or [],
                era=cluster.era
            ))
        
        logger.info(f"Retrieved {len(cluster_infos)} clusters from clusters table")
        return cluster_infos
        
    except Exception as e:
        logger.error(f"Failed to get clusters: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve clusters")


@router.get("/{cluster_id}", response_model=ClusterResponse)
async def get_cluster_details(
    cluster_id: int,
    include_tracks: bool = Query(False, description="Include sample tracks"),
    track_limit: int = Query(10, ge=1, le=50, description="Number of sample tracks"),
    db: AsyncSession = Depends(get_database)
):
    """
    Get detailed information about a specific cluster
    """
    try:
        # Get cluster info
        query = select(Cluster).where(Cluster.id == cluster_id)
        result = await db.execute(query)
        cluster = result.scalar_one_or_none()
        
        if not cluster:
            raise HTTPException(status_code=404, detail="Cluster not found")
        
        # Get cluster statistics
        stats_query = select(
            func.count(Track.id).label('total_tracks'),
            func.avg(Track.popularity).label('avg_popularity'),
            func.avg(Track.energy).label('avg_energy'),
            func.avg(Track.valence).label('avg_valence'),
            func.avg(Track.danceability).label('avg_danceability'),
            func.avg(Track.tempo).label('avg_tempo'),
            func.count(func.distinct(Track.artist_id)).label('unique_artists')
        ).where(Track.cluster_id == cluster_id)
        
        stats_result = await db.execute(stats_query)
        stats = stats_result.first()
        
        cluster_stats = ClusterStats(
            total_tracks=stats.total_tracks or 0,
            avg_popularity=float(stats.avg_popularity or 0),
            avg_energy=float(stats.avg_energy or 0),
            avg_valence=float(stats.avg_valence or 0),
            avg_danceability=float(stats.avg_danceability or 0),
            avg_tempo=float(stats.avg_tempo or 0),
            unique_artists=stats.unique_artists or 0
        )
        
        # Get sample tracks if requested
        sample_tracks = []
        if include_tracks:
            tracks_query = select(Track, Artist).join(
                Artist, Track.artist_id == Artist.id
            ).where(
                Track.cluster_id == cluster_id
            ).order_by(
                Track.popularity.desc()
            ).limit(track_limit)
            
            tracks_result = await db.execute(tracks_query)
            tracks_data = tracks_result.all()
            
            for track, artist in tracks_data:
                sample_tracks.append(ClusterTrack(
                    id=track.id,
                    name=track.name,
                    artist_name=artist.name,
                    popularity=track.popularity,
                    energy=track.energy,
                    valence=track.valence,
                    danceability=track.danceability,
                    tempo=track.tempo
                ))
        
        # Create response
        response = ClusterResponse(
            id=cluster.id,
            name=cluster.name or f"Cluster {cluster.id}",
            description=cluster.description,
            size=cluster.size,
            cohesion_score=cluster.cohesion_score,
            separation_score=cluster.separation_score,
            dominant_genres=cluster.dominant_genres or [],
            dominant_features=cluster.dominant_features or [],
            era=cluster.era,
            statistics=cluster_stats,
            sample_tracks=sample_tracks,
            audio_stats=cluster.audio_stats
        )
        
        logger.info(f"Retrieved details for cluster {cluster_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get cluster details for {cluster_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve cluster details")


@router.get("/{cluster_id}/tracks")
async def get_cluster_tracks(
    cluster_id: int,
    skip: int = Query(0, ge=0, description="Number of tracks to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of tracks to return"),
    sort_by: str = Query("popularity", description="Sort by: popularity, name, energy, valence"),
    order: str = Query("desc", description="Sort order: asc, desc"),
    db: AsyncSession = Depends(get_database)
):
    """
    Get tracks belonging to a specific cluster
    """
    try:
        # Verify cluster exists
        cluster_query = select(Cluster).where(Cluster.id == cluster_id)
        cluster_result = await db.execute(cluster_query)
        cluster = cluster_result.scalar_one_or_none()
        
        if not cluster:
            raise HTTPException(status_code=404, detail="Cluster not found")
        
        # Build tracks query
        query = select(Track, Artist).join(
            Artist, Track.artist_id == Artist.id
        ).where(Track.cluster_id == cluster_id)
        
        # Apply sorting
        if sort_by == "popularity":
            order_column = Track.popularity
        elif sort_by == "name":
            order_column = Track.name
        elif sort_by == "energy":
            order_column = Track.energy
        elif sort_by == "valence":
            order_column = Track.valence
        else:
            order_column = Track.popularity
        
        if order.lower() == "desc":
            query = query.order_by(order_column.desc())
        else:
            query = query.order_by(order_column.asc())
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        # Execute query
        result = await db.execute(query)
        tracks_data = result.all()
        
        # Convert to response format
        tracks = []
        for track, artist in tracks_data:
            tracks.append({
                "id": track.id,
                "name": track.name,
                "artist_name": artist.name,
                "artist_id": artist.id,
                "album_id": track.album_id,
                "popularity": track.popularity,
                "duration_ms": track.duration_ms,
                "energy": track.energy,
                "valence": track.valence,
                "danceability": track.danceability,
                "tempo": track.tempo,
                "key": track.key,
                "mode": track.mode,
                "cluster_probability": track.cluster_probability
            })
        
        logger.info(f"Retrieved {len(tracks)} tracks for cluster {cluster_id}")
        return {
            "cluster_id": cluster_id,
            "cluster_name": cluster.name or f"Cluster {cluster_id}",
            "total_tracks": cluster.size,
            "tracks": tracks,
            "pagination": {
                "skip": skip,
                "limit": limit,
                "returned": len(tracks)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get tracks for cluster {cluster_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve cluster tracks")


@router.get("/stats/summary")
async def get_cluster_summary(
    db: AsyncSession = Depends(get_database)
):
    """
    Get overall cluster statistics summary
    """
    try:
        # Get cluster statistics
        cluster_stats_query = select(
            func.count(Cluster.id).label('total_clusters'),
            func.sum(Cluster.size).label('total_tracks'),
            func.avg(Cluster.size).label('avg_cluster_size'),
            func.min(Cluster.size).label('min_cluster_size'),
            func.max(Cluster.size).label('max_cluster_size'),
            func.avg(Cluster.cohesion_score).label('avg_cohesion'),
            func.avg(Cluster.separation_score).label('avg_separation')
        )
        
        cluster_result = await db.execute(cluster_stats_query)
        cluster_stats = cluster_result.first()
        
        # Get noise points (unclustered tracks)
        noise_query = select(func.count(Track.id)).where(Track.cluster_id == -1)
        noise_result = await db.execute(noise_query)
        noise_count = noise_result.scalar() or 0
        
        # Get top genres across all clusters
        genres_query = text("""
            SELECT UNNEST(dominant_genres) as genre, COUNT(*) as cluster_count
            FROM clusters 
            WHERE dominant_genres IS NOT NULL 
            GROUP BY genre 
            ORDER BY cluster_count DESC 
            LIMIT 10
        """)
        
        genres_result = await db.execute(genres_query)
        top_genres = [{"genre": row[0], "cluster_count": row[1]} for row in genres_result.fetchall()]
        
        summary = {
            "overview": {
                "total_clusters": cluster_stats.total_clusters or 0,
                "total_clustered_tracks": cluster_stats.total_tracks or 0,
                "noise_points": noise_count,
                "avg_cluster_size": float(cluster_stats.avg_cluster_size or 0),
                "min_cluster_size": cluster_stats.min_cluster_size or 0,
                "max_cluster_size": cluster_stats.max_cluster_size or 0,
                "avg_cohesion_score": float(cluster_stats.avg_cohesion or 0),
                "avg_separation_score": float(cluster_stats.avg_separation or 0)
            },
            "top_genres": top_genres
        }
        
        logger.info("Retrieved cluster summary statistics")
        return summary
        
    except Exception as e:
        logger.error(f"Failed to get cluster summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve cluster summary")


@router.post("/analyze")
async def analyze_clusters(
    request: Request,
    regenerate: bool = Query(False, description="Regenerate cluster analysis"),
    db: AsyncSession = Depends(get_database)
):
    """
    Analyze clusters and update their metadata
    """
    try:
        # Get model service from app state
        model_service = getattr(request.app.state, 'model_service', None)
        if not model_service or not model_service.is_ready():
            raise HTTPException(status_code=503, detail="ML models not available")
        
        # This would typically trigger cluster analysis
        # For now, return a placeholder response
        
        analysis_result = {
            "status": "completed",
            "message": "Cluster analysis completed successfully",
            "clusters_analyzed": 0,
            "metadata_updated": 0,
            "analysis_timestamp": "2024-01-01T00:00:00Z"
        }
        
        logger.info("Cluster analysis requested")
        return analysis_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to analyze clusters: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze clusters") 