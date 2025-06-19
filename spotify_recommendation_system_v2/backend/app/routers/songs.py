"""
API endpoints for song-related operations
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Query
from typing import List, Optional
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy import func, select, or_

from app.schemas.recommendation import Song
from app.database.database import get_database
from app.database.models import Track, Artist, Album

router = APIRouter()


def _track_to_song(track: Track) -> Song:
    """Convert a Track database object to a Song schema object"""
    # Extract album image URL from images JSON
    album_image_url = None
    if track.album and track.album.images:
        # Images are stored as JSON array, get the medium size (index 1) or first available
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
        album_image_url=album_image_url
    )


@router.get("/{song_id}", response_model=Song)
async def get_song(
    song_id: str,
    db: AsyncSession = Depends(get_database)
) -> Song:
    """Get detailed information about a specific song"""
    try:
        query = select(Track).options(
            joinedload(Track.artist),
            joinedload(Track.album)
        ).filter(Track.id == song_id)
        
        result = await db.execute(query)
        track = result.scalar_one_or_none()
        
        if not track:
            raise HTTPException(
                status_code=404,
                detail=f"Song with ID '{song_id}' not found"
            )
        
        song = _track_to_song(track)
        logger.info(f"🎵 Retrieved song: {song.name} by {song.artist}")
        return song
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting song {song_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving song: {str(e)}"
        )


@router.get("/", response_model=List[Song])
async def search_songs(
    q: str = Query(..., description="Search query for song name or artist"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    db: AsyncSession = Depends(get_database)
) -> List[Song]:
    """Search for songs by name or artist"""
    try:
        if len(q.strip()) < 2:
            raise HTTPException(
                status_code=400,
                detail="Search query must be at least 2 characters long"
            )
        
        # Search in both song names and artist names
        search_term = f"%{q.lower()}%"
        query = select(Track).options(
            joinedload(Track.artist),
            joinedload(Track.album)
        ).join(Artist).filter(
            or_(
                func.lower(Track.name).like(search_term),
                func.lower(Artist.name).like(search_term)
            )
        ).order_by(Track.popularity.desc()).limit(limit)
        
        result = await db.execute(query)
        tracks = result.scalars().all()
        
        songs = [_track_to_song(track) for track in tracks]
        
        logger.info(f"🔍 Search '{q}' returned {len(songs)} results from database")
        return songs
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error searching songs with query '{q}': {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error searching songs: {str(e)}"
        )


@router.get("/cluster/{cluster_id}", response_model=List[Song])
async def get_songs_in_cluster(
    cluster_id: int,
    limit: int = Query(50, ge=1, le=200, description="Maximum number of songs to return"),
    offset: int = Query(0, ge=0, description="Number of songs to skip"),
    db: AsyncSession = Depends(get_database)
) -> List[Song]:
    """Get songs from a specific cluster"""
    try:
        query = select(Track).options(
            joinedload(Track.artist),
            joinedload(Track.album)
        ).filter(
            Track.cluster_id == cluster_id
        ).order_by(
            Track.popularity.desc()
        ).offset(offset).limit(limit)
        
        result = await db.execute(query)
        tracks = result.scalars().all()
        
        if not tracks:
            raise HTTPException(
                status_code=404,
                detail=f"No songs found in cluster {cluster_id}"
            )
        
        songs = [_track_to_song(track) for track in tracks]
        
        logger.info(f"🎵 Retrieved {len(songs)} songs from cluster {cluster_id} from database")
        return songs
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting songs from cluster {cluster_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving cluster songs: {str(e)}"
        )


@router.get("/random/", response_model=List[Song])
async def get_random_songs(
    limit: int = Query(20, ge=1, le=100, description="Number of random songs"),
    cluster_id: Optional[int] = Query(None, description="Limit to specific cluster"),
    db: AsyncSession = Depends(get_database)
) -> List[Song]:
    """Get random songs, optionally from a specific cluster"""
    try:
        # Build query for random songs
        query = select(Track).options(
            joinedload(Track.artist),
            joinedload(Track.album)
        )
        
        # Filter by cluster if specified
        if cluster_id is not None:
            query = query.filter(Track.cluster_id == cluster_id)
        
        # Get random songs using SQL
        query = query.order_by(func.random()).limit(limit)
        result = await db.execute(query)
        tracks = result.scalars().all()
        
        if not tracks:
            raise HTTPException(
                status_code=404,
                detail=f"No songs found{f' in cluster {cluster_id}' if cluster_id else ''}"
            )
        
        songs = [_track_to_song(track) for track in tracks]
        
        cluster_info = f" from cluster {cluster_id}" if cluster_id is not None else ""
        logger.info(f"🎲 Retrieved {len(songs)} random REAL songs{cluster_info} from database")
        
        return songs
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting random songs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving random songs: {str(e)}"
        )


@router.get("/popular/", response_model=List[Song])
async def get_popular_songs(
    limit: int = Query(50, ge=1, le=200, description="Number of popular songs"),
    min_popularity: int = Query(70, ge=0, le=100, description="Minimum popularity score"),
    db: AsyncSession = Depends(get_database)
) -> List[Song]:
    """Get popular songs based on Spotify popularity scores"""
    try:
        # Query popular songs
        query = select(Track).options(
            joinedload(Track.artist),
            joinedload(Track.album)
        ).filter(
            Track.popularity >= min_popularity
        ).order_by(
            Track.popularity.desc()
        ).limit(limit)
        
        result = await db.execute(query)
        tracks = result.scalars().all()
        
        if not tracks:
            raise HTTPException(
                status_code=404,
                detail=f"No songs found with popularity >= {min_popularity}"
            )
        
        songs = [_track_to_song(track) for track in tracks]
        
        logger.info(f"🔥 Retrieved {len(songs)} popular REAL songs from database (min popularity: {min_popularity})")
        return songs
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting popular songs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving popular songs: {str(e)}"
        )


@router.get("/stats/overview")
async def get_songs_overview(
    db: AsyncSession = Depends(get_database)
) -> dict:
    """Get overview statistics about the song dataset"""
    try:
        # Basic count statistics
        total_songs_query = select(func.count(Track.id))
        unique_artists_query = select(func.count(func.distinct(Track.artist_id)))
        unique_albums_query = select(func.count(func.distinct(Track.album_id)))
        
        total_songs_result = await db.execute(total_songs_query)
        unique_artists_result = await db.execute(unique_artists_query)
        unique_albums_result = await db.execute(unique_albums_query)
        
        total_songs = total_songs_result.scalar()
        unique_artists = unique_artists_result.scalar()
        unique_albums = unique_albums_result.scalar()
        
        # Audio feature statistics
        audio_features = ['acousticness', 'danceability', 'energy', 'valence', 'tempo']
        feature_stats = {}
        
        for feature in audio_features:
            feature_column = getattr(Track, feature)
            stats_query = select(
                func.avg(feature_column).label('mean'),
                func.stddev(feature_column).label('std'),
                func.min(feature_column).label('min'),
                func.max(feature_column).label('max')
            )
            stats_result = await db.execute(stats_query)
            stats = stats_result.first()
            
            feature_stats[feature] = {
                'mean': float(stats.mean or 0),
                'std': float(stats.std or 0),
                'min': float(stats.min or 0),
                'max': float(stats.max or 0)
            }
        
        # Cluster statistics
        cluster_stats_query = select(
            Track.cluster_id,
            func.count(Track.id).label('count')
        ).group_by(Track.cluster_id)
        
        cluster_result = await db.execute(cluster_stats_query)
        cluster_counts = {row.cluster_id: row.count for row in cluster_result}
        
        cluster_stats = {
            'total_clusters': len(cluster_counts),
            'largest_cluster_size': max(cluster_counts.values()) if cluster_counts else 0,
            'smallest_cluster_size': min(cluster_counts.values()) if cluster_counts else 0,
            'average_cluster_size': sum(cluster_counts.values()) / len(cluster_counts) if cluster_counts else 0
        }
        
        # Popularity statistics
        popularity_stats_query = select(
            func.avg(Track.popularity).label('mean'),
            func.count().filter(Track.popularity >= 80).label('high'),
            func.count().filter((Track.popularity >= 50) & (Track.popularity < 80)).label('medium'),
            func.count().filter(Track.popularity < 50).label('low')
        )
        
        popularity_result = await db.execute(popularity_stats_query)
        pop_stats = popularity_result.first()
        
        popularity_stats = {
            'mean': float(pop_stats.mean or 0),
            'distribution': {
                'high (80-100)': pop_stats.high or 0,
                'medium (50-79)': pop_stats.medium or 0,
                'low (0-49)': pop_stats.low or 0
            }
        }
        
        return {
            'dataset_summary': {
                'total_songs': total_songs,
                'unique_artists': unique_artists,
                'unique_albums': unique_albums
            },
            'audio_features': feature_stats,
            'clustering': cluster_stats,
            'popularity': popularity_stats
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting songs overview: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving songs overview: {str(e)}"
        ) 