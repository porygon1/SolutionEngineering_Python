"""
API endpoints for music recommendations using HDBSCAN + KNN
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from typing import List, Optional
import time
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy import func, select
import random

from app.schemas.recommendation import (
    RecommendationRequest, 
    RecommendationResponse,
    PreferenceRequest,
    PreferenceResponse,
    UserFeedback,
    Song,
    ClusterUsed,
    ModelComparisonRequest,
    ModelComparisonResponse,
    ModelComparisonResult
)
from app.database.database import get_database
from app.database.models import Track, Artist, Album
from app.services.model_service import ModelService
from app.config import settings


router = APIRouter()


def get_model_service(request: Request) -> ModelService:
    """Dependency to get the model service from app state"""
    return request.app.state.model_service


def _track_to_song(track: Track, similarity_score: float = None) -> Song:
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
        album_image_url=album_image_url,
        similarity_score=similarity_score
    )


@router.post("/", response_model=RecommendationResponse)
async def get_recommendations(
    request: RecommendationRequest,
    db: AsyncSession = Depends(get_database),
    model_service: ModelService = Depends(get_model_service)
) -> RecommendationResponse:
    """
    Get song recommendations based on liked songs using trained HDBSCAN + KNN models
    
    This endpoint uses actual trained ML models for high-quality recommendations:
    1. Uses KNN to find similar songs based on audio features
    2. Includes similarity scores for each recommendation
    3. Falls back to database clustering if trained models aren't available
    """
    start_time = time.time()
    
    try:
        logger.info(f"🎵 Processing recommendation request: {len(request.liked_song_ids)} liked songs, type: {request.recommendation_type}")
        
        # Try to use trained models first
        if model_service.is_ready():
            if request.recommendation_type == "lyrics":
                logger.info("📝 Using lyrics similarity model for recommendations")
                response = await model_service.get_lyrics_recommendations(request, db)
                return response
            elif request.recommendation_type == "hdbscan_knn":
                logger.info("🎯 Using trained HDBSCAN + KNN models for recommendations")
                response = await model_service.get_recommendations_with_similarity(request, db)
                response.recommendation_type = "hdbscan_knn"
                return response
            else:
                logger.info("🤖 Using trained HDBSCAN + KNN models for recommendations (default)")
                response = await model_service.get_recommendations_with_similarity(request, db)
                return response
        
        # Fallback to database-only recommendations
        logger.warning("⚠️ Trained models not available, using database fallback")
        
        # Validate that liked songs exist in our dataset
        valid_song_ids = []
        liked_songs_query = select(Track).options(
            joinedload(Track.artist),
            joinedload(Track.album)
        ).filter(Track.id.in_(request.liked_song_ids))
        
        result = await db.execute(liked_songs_query)
        liked_tracks = result.scalars().all()
        
        if not liked_tracks:
            raise HTTPException(
                status_code=404,
                detail="None of the provided song IDs were found in our dataset"
            )
        
        valid_song_ids = [track.id for track in liked_tracks]
        logger.info(f"✅ Found {len(valid_song_ids)} valid songs out of {len(request.liked_song_ids)} requested")
        
        # Get clusters from liked songs
        clusters_used = []
        cluster_ids = set()
        
        for track in liked_tracks:
            if track.cluster_id is not None and track.cluster_id != -1:
                cluster_ids.add(track.cluster_id)
                clusters_used.append(ClusterUsed(
                    cluster_id=track.cluster_id,
                    size=0,  # We'll update this later
                    source_song=track.id
                ))
        
        if not cluster_ids:
            # If no valid clusters, fall back to popular songs
            logger.warning("⚠️ No valid clusters found, falling back to popular songs")
            popular_query = select(Track).options(
                joinedload(Track.artist),
                joinedload(Track.album)
            ).filter(
                Track.popularity >= 50,
                ~Track.id.in_(valid_song_ids)  # Exclude already liked songs
            ).order_by(Track.popularity.desc()).limit(request.n_recommendations)
            
            result = await db.execute(popular_query)
            recommendation_tracks = result.scalars().all()
        else:
            # Get recommendations from the same clusters
            recommendations_query = select(Track).options(
                joinedload(Track.artist),
                joinedload(Track.album)
            ).filter(
                Track.cluster_id.in_(cluster_ids),
                ~Track.id.in_(valid_song_ids)  # Exclude already liked songs
            ).order_by(
                Track.popularity.desc()
            ).limit(request.n_recommendations * 3)  # Get more to allow for diversity
            
            result = await db.execute(recommendations_query)
            all_recommendations = result.scalars().all()
            
            # Add some diversity by shuffling and taking the top N
            recommendation_tracks = list(all_recommendations)
            random.shuffle(recommendation_tracks)
            recommendation_tracks = recommendation_tracks[:request.n_recommendations]
        
        # Convert to Song objects
        recommendations = [_track_to_song(track) for track in recommendation_tracks]
        
        # Update cluster sizes
        for cluster_used in clusters_used:
            count_query = select(func.count(Track.id)).filter(Track.cluster_id == cluster_used.cluster_id)
            count_result = await db.execute(count_query)
            cluster_used.size = count_result.scalar() or 0
        
        # Create response
        processing_time = (time.time() - start_time) * 1000
        response = RecommendationResponse(
            recommendations=recommendations,
            recommendation_type=request.recommendation_type,
            clusters_used=clusters_used,
            total_found=len(recommendations),
            processing_time_ms=processing_time
        )
        
        logger.success(f"✅ Generated {len(response.recommendations)} recommendations in {processing_time:.1f}ms")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        logger.error(f"❌ Error generating recommendations: {e} (took {processing_time:.1f}ms)")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating recommendations: {str(e)}"
        )


@router.post("/preferences", response_model=PreferenceResponse)
async def get_song_preferences(
    request: PreferenceRequest,
    db: AsyncSession = Depends(get_database)
) -> PreferenceResponse:
    """
    Get song suggestions for initial preference selection
    
    This endpoint helps users discover songs to like based on their stated preferences.
    It returns a diverse set of songs that match the given criteria.
    """
    try:
        logger.info(f"🎯 Getting preference suggestions based on: {request}")
        
        # Build query based on preferences
        query = select(Track).options(
            joinedload(Track.artist),
            joinedload(Track.album)
        )
        
        filters = []
        
        # Filter by popularity range if specified
        if request.popularity_range:
            min_pop, max_pop = request.popularity_range
            filters.append(Track.popularity >= min_pop)
            filters.append(Track.popularity <= max_pop)
        
        # Apply audio feature filters if specified
        if request.audio_features:
            for feature, value in request.audio_features.items():
                if hasattr(Track, feature):
                    # Use a range around the target value (±0.2)
                    filters.append(getattr(Track, feature) >= value - 0.2)
                    filters.append(getattr(Track, feature) <= value + 0.2)
        
        # Add filters to query
        if filters:
            query = query.filter(*filters)
        
        # Add minimum popularity to ensure quality
        query = query.filter(Track.popularity >= 30)
        
        # Limit results for performance
        query = query.limit(200)
        
        result = await db.execute(query)
        all_tracks = result.scalars().all()
        
        if not all_tracks:
            # Fallback to popular songs if no matches
            logger.warning("⚠️ No songs match preferences, falling back to popular songs")
            fallback_query = select(Track).options(
                joinedload(Track.artist),
                joinedload(Track.album)
            ).filter(Track.popularity >= 60).order_by(Track.popularity.desc()).limit(50)
            
            result = await db.execute(fallback_query)
            all_tracks = result.scalars().all()
        
        # Sample songs from different clusters for diversity
        suggested_songs = []
        cluster_samples = {}
        cluster_counts = {}
        
        # Group by cluster
        for track in all_tracks:
            cluster_id = track.cluster_id
            if cluster_id not in cluster_samples:
                cluster_samples[cluster_id] = []
            cluster_samples[cluster_id].append(track)
        
        # Sample up to 3 songs per cluster
        for cluster_id, tracks in cluster_samples.items():
            sample_size = min(3, len(tracks))
            sampled_tracks = random.sample(tracks, sample_size)
            
            for track in sampled_tracks:
                song = _track_to_song(track)
                suggested_songs.append(song)
                cluster_counts[cluster_id] = len(tracks)
                
                if len(suggested_songs) >= 50:  # Limit total suggestions
                    break
            
            if len(suggested_songs) >= 50:
                break
        
        # Shuffle the results to mix clusters
        random.shuffle(suggested_songs)
        
        response = PreferenceResponse(
            suggested_songs=suggested_songs[:30],  # Return top 30
            total_available=len(all_tracks),
            categories=cluster_counts
        )
        
        logger.success(f"✅ Generated {len(response.suggested_songs)} preference suggestions")
        return response
        
    except Exception as e:
        logger.error(f"❌ Error getting preferences: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting song preferences: {str(e)}"
        )


@router.post("/feedback")
async def submit_feedback(
    feedback: UserFeedback,
    db: AsyncSession = Depends(get_database)
) -> JSONResponse:
    """
    Submit user feedback on recommendations
    
    This endpoint collects user feedback to improve future recommendations.
    Feedback is logged and can be used for model retraining.
    """
    try:
        logger.info(f"📝 Received feedback: {feedback.feedback_type} for song {feedback.song_id}")
        
        # Validate song exists
        song_query = select(Track).options(
            joinedload(Track.artist),
            joinedload(Track.album)
        ).filter(Track.id == feedback.song_id)
        
        result = await db.execute(song_query)
        track = result.scalar_one_or_none()
        
        if not track:
            raise HTTPException(
                status_code=404,
                detail=f"Song ID not found: {feedback.song_id}"
            )
        
        song = _track_to_song(track)
        
        # Log feedback (in production, save to database)
        feedback_data = {
            "timestamp": time.time(),
            "recommendation_id": feedback.recommendation_id,
            "song_id": feedback.song_id,
            "song_name": song.name,
            "song_artist": song.artist,
            "feedback_type": feedback.feedback_type,
            "rating": feedback.rating,
            "comment": feedback.comment,
            "cluster_id": song.cluster_id
        }
        
        logger.info(f"Feedback logged: {feedback_data}")
        
        return JSONResponse(
            content={
                "message": "Feedback received successfully",
                "feedback_id": f"fb_{int(time.time())}_{feedback.song_id[:8]}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error submitting feedback: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error submitting feedback: {str(e)}"
        )


@router.get("/similar/{song_id}", response_model=RecommendationResponse)
async def get_similar_songs(
    song_id: str,
    n_recommendations: int = 12,
    recommendation_type: str = "cluster",
    db: AsyncSession = Depends(get_database)
) -> RecommendationResponse:
    """
    Get songs similar to a specific song
    
    Convenience endpoint that wraps the main recommendation API
    for single-song similarity queries.
    """
    try:
        # Validate song exists
        song_query = select(Track).options(
            joinedload(Track.artist),
            joinedload(Track.album)
        ).filter(Track.id == song_id)
        
        result = await db.execute(song_query)
        track = result.scalar_one_or_none()
        
        if not track:
            raise HTTPException(
                status_code=404,
                detail=f"Song ID not found: {song_id}"
            )
        
        song = _track_to_song(track)
        
        # Create recommendation request
        request = RecommendationRequest(
            liked_song_ids=[song_id],
            n_recommendations=n_recommendations,
            recommendation_type=recommendation_type
        )
        
        # Get recommendations using the main endpoint
        response = await get_recommendations(request, db)
        
        logger.info(f"🎵 Found {len(response.recommendations)} similar songs to {song.name}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting similar songs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting similar songs: {str(e)}"
        )


@router.post("/compare", response_model=ModelComparisonResponse)
async def compare_recommendation_models(
    request: ModelComparisonRequest,
    db: AsyncSession = Depends(get_database),
    model_service: ModelService = Depends(get_model_service)
) -> ModelComparisonResponse:
    """
    Compare different recommendation models side-by-side
    
    This endpoint allows users to see results from multiple recommendation
    approaches (cluster-based, lyrics-based, etc.) for the same input songs.
    """
    start_time = time.time()
    
    try:
        logger.info(f"🔄 Comparing {len(request.models_to_compare)} models for {len(request.liked_song_ids)} songs")
        
        # Get query songs information
        query_songs_query = select(Track).options(
            joinedload(Track.artist),
            joinedload(Track.album)
        ).filter(Track.id.in_(request.liked_song_ids))
        
        result = await db.execute(query_songs_query)
        query_tracks = result.scalars().all()
        query_songs = [_track_to_song(track) for track in query_tracks]
        
        if not query_songs:
            raise HTTPException(
                status_code=404,
                detail="None of the provided song IDs were found in our dataset"
            )
        
        # Run each model and collect results
        comparison_results = []
        
        for model_type in request.models_to_compare:
            model_start_time = time.time()
            
            try:
                # Create individual recommendation request
                rec_request = RecommendationRequest(
                    liked_song_ids=request.liked_song_ids,
                    n_recommendations=request.n_recommendations,
                    recommendation_type=model_type
                )
                
                # Get recommendations from the specific model
                if model_type == "lyrics" and model_service.lyrics_service.is_ready():
                    response = await model_service.get_lyrics_recommendations(rec_request, db)
                elif model_type in ["svd_knn", "knn_cosine", "knn_cosine_k20", "knn_euclidean"] and model_service.lyrics_service.is_ready():
                    # Handle specific lyrics model variants by switching model first
                    if model_type != model_service.lyrics_service.get_current_model_info().get('model_name'):
                        switch_result = model_service.lyrics_service.switch_model(model_type)
                        if not switch_result.get('success'):
                            logger.warning(f"Failed to switch to lyrics model {model_type}, using current model")
                    response = await model_service.get_lyrics_recommendations(rec_request, db)
                elif model_type == "hdbscan_knn" and model_service.is_ready():
                    response = await model_service.get_recommendations_with_similarity(rec_request, db)
                    response.recommendation_type = "hdbscan_knn"
                elif model_type.startswith("hdbscan_") and model_service.hdbscan_service.is_ready():
                    # Extract the actual model name from the type (e.g., "hdbscan_naive_features" -> "naive_features")
                    hdbscan_model_name = model_type.replace("hdbscan_", "")
                    response = await model_service.get_hdbscan_recommendations(rec_request, db, hdbscan_model_name)
                elif model_type == "artist_based":
                    response = await get_artist_based_recommendations(rec_request, db)
                elif model_type == "genre_based":
                    response = await get_genre_based_recommendations(rec_request, db)
                elif model_type == "cluster" and model_service.is_ready():
                    response = await model_service.get_recommendations_with_similarity(rec_request, db)
                elif model_type == "global":
                    response = await get_global_recommendations(rec_request, db)
                elif model_type == "hybrid":
                    response = await get_hybrid_recommendations(rec_request, db, model_service)
                else:
                    # Fallback to database-only recommendations
                    response = await get_recommendations(rec_request, db, model_service)
                
                model_processing_time = (time.time() - model_start_time) * 1000
                
                comparison_results.append(ModelComparisonResult(
                    model_type=model_type,
                    recommendations=response.recommendations,
                    processing_time_ms=model_processing_time,
                    total_found=response.total_found,
                    error=None
                ))
                
                logger.info(f"✅ {model_type} model: {len(response.recommendations)} recommendations in {model_processing_time:.1f}ms")
                
            except Exception as model_error:
                model_processing_time = (time.time() - model_start_time) * 1000
                logger.error(f"❌ {model_type} model failed: {model_error}")
                
                comparison_results.append(ModelComparisonResult(
                    model_type=model_type,
                    recommendations=[],
                    processing_time_ms=model_processing_time,
                    total_found=0,
                    error=str(model_error)
                ))
        
        total_processing_time = (time.time() - start_time) * 1000
        
        response = ModelComparisonResponse(
            query_songs=query_songs,
            results=comparison_results,
            total_processing_time_ms=total_processing_time
        )
        
        successful_models = len([r for r in comparison_results if r.error is None])
        logger.success(f"✅ Model comparison complete: {successful_models}/{len(request.models_to_compare)} models succeeded in {total_processing_time:.1f}ms")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        total_processing_time = (time.time() - start_time) * 1000
        logger.error(f"❌ Error comparing models: {e} (took {total_processing_time:.1f}ms)")
        raise HTTPException(
            status_code=500,
            detail=f"Error comparing recommendation models: {str(e)}"
        )


@router.get("/stats")
async def get_recommendation_stats(
    db: AsyncSession = Depends(get_database)
) -> dict:
    """Get recommendation system statistics"""
    try:
        # Get basic statistics from database
        total_songs_query = select(func.count(Track.id))
        total_clusters_query = select(func.count(func.distinct(Track.cluster_id))).filter(Track.cluster_id != -1)
        
        total_songs_result = await db.execute(total_songs_query)
        total_clusters_result = await db.execute(total_clusters_query)
        
        total_songs = total_songs_result.scalar()
        total_clusters = total_clusters_result.scalar()
        
        stats = {
            "total_songs": total_songs,
            "total_clusters": total_clusters,
            "avg_songs_per_cluster": total_songs / total_clusters if total_clusters > 0 else 0,
            "recommendation_types": ["cluster", "hdbscan_knn", "lyrics", "artist_based", "genre_based", "global", "hybrid"]
        }
        
        return {
            "status": "healthy",
            "statistics": stats,
            "endpoints": {
                "recommendations": "/api/v2/recommendations/",
                "preferences": "/api/v2/recommendations/preferences",
                "similar": "/api/v2/recommendations/similar/{song_id}",
                "feedback": "/api/v2/recommendations/feedback",
                "compare": "/api/v2/recommendations/compare"
            }
        }
    except Exception as e:
        logger.error(f"❌ Error getting stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting statistics: {str(e)}"
        )


@router.get("/models/available")
async def get_available_models(
    model_service: ModelService = Depends(get_model_service)
) -> dict:
    """Get list of all available recommendation models"""
    try:
        all_models = []
        current_models = {}
        
        # Add HDBSCAN + KNN model (main clustering model)
        if model_service.is_ready():
            all_models.append("hdbscan_knn")
            current_models["hdbscan_knn"] = {
                "model_name": "hdbscan_knn",
                "model_type": "clustering",
                "description": "HDBSCAN clustering + KNN for audio feature similarity",
                "is_ready": True,
                "features": "audio_features",
                "algorithm": "HDBSCAN + KNN"
            }
        
        # Add traditional cluster-based model
        all_models.append("cluster")
        current_models["cluster"] = {
            "model_name": "cluster",
            "model_type": "clustering",
            "description": "Traditional cluster-based recommendations",
            "is_ready": True,
            "features": "audio_features",
            "algorithm": "Database Clustering"
        }
        
        # Add new recommendation strategies
        all_models.extend(["artist_based", "genre_based"])
        current_models["artist_based"] = {
            "model_name": "artist_based",
            "model_type": "content_based",
            "description": "Recommendations based on similar artists",
            "is_ready": True,
            "features": "artist_similarity",
            "algorithm": "Artist Matching"
        }
        current_models["genre_based"] = {
            "model_name": "genre_based",
            "model_type": "content_based", 
            "description": "Recommendations based on audio feature similarity",
            "is_ready": True,
            "features": "audio_features",
            "algorithm": "Feature Similarity"
        }
        
        # Add lyrics similarity models
        if hasattr(model_service, 'lyrics_service') and model_service.lyrics_service:
            lyrics_models = model_service.lyrics_service.get_available_models()
            current_lyrics_model = model_service.lyrics_service.get_current_model_info()
            
            all_models.extend(lyrics_models)
            
            # Add current lyrics model info
            if current_lyrics_model and "model_name" in current_lyrics_model:
                current_models["lyrics_current"] = current_lyrics_model
        
        # Add HDBSCAN similarity models
        if hasattr(model_service, 'hdbscan_service') and model_service.hdbscan_service:
            hdbscan_models = model_service.hdbscan_service.get_available_models()
            current_hdbscan_model = model_service.hdbscan_service.get_current_model_info()
            
            # Prefix HDBSCAN models to distinguish them
            prefixed_hdbscan_models = [f"hdbscan_{model}" for model in hdbscan_models]
            all_models.extend(prefixed_hdbscan_models)
            
            # Add current HDBSCAN model info
            if current_hdbscan_model and "model_name" in current_hdbscan_model:
                current_models["hdbscan_current"] = current_hdbscan_model
            
        # Add additional strategy models
        all_models.extend(["global", "hybrid"])
        current_models["global"] = {
            "model_name": "global",
            "model_type": "popularity",
            "description": "Global popular recommendations",
            "is_ready": True,
            "features": "popularity",
            "algorithm": "Popularity Ranking"
        }
        current_models["hybrid"] = {
            "model_name": "hybrid",
            "model_type": "ensemble",
            "description": "Hybrid approach combining multiple methods",
            "is_ready": True,
            "features": "multiple",
            "algorithm": "Ensemble Method"
        }
        
        # Determine the primary model for recommendations
        primary_model = None
        if model_service.is_ready():
            primary_model = current_models.get("hdbscan_knn")
        elif hasattr(model_service, 'lyrics_service') and model_service.lyrics_service.is_ready():
            primary_model = current_models.get("lyrics_current")
        
        return {
            "available_models": all_models,
            "current_model": primary_model,
            "all_models": current_models,
            "total_available": len(all_models),
            "hdbscan_ready": model_service.is_ready(),
            "lyrics_ready": hasattr(model_service, 'lyrics_service') and model_service.lyrics_service.is_ready(),
            "hdbscan_advanced_ready": hasattr(model_service, 'hdbscan_service') and model_service.hdbscan_service.is_ready()
        }
        
    except Exception as e:
        logger.error(f"Error getting available models: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting available models: {e}")


@router.post("/models/switch/{model_name}")
async def switch_model(
    model_name: str,
    model_service: ModelService = Depends(get_model_service)
) -> dict:
    """Switch to a different similarity model (lyrics or HDBSCAN)"""
    try:
        logger.info(f"🔄 Attempting to switch to model: {model_name}")
        
        # Determine model type based on model name prefix
        if model_name.startswith('hdbscan_'):
            logger.info(f"🔬 Detected HDBSCAN model request: {model_name}")
            
            # HDBSCAN model switching
            if not hasattr(model_service, 'hdbscan_service') or not model_service.hdbscan_service:
                logger.error("❌ HDBSCAN service not initialized")
                raise HTTPException(status_code=503, detail="HDBSCAN service not initialized")
            
            logger.info("✅ HDBSCAN service found, calling switch_model")
            result = model_service.hdbscan_service.switch_model(model_name)
            
            if result.get("success"):
                logger.success(f"✅ Successfully switched to HDBSCAN model: {model_name}")
                return {
                    "message": f"Successfully switched to HDBSCAN model: {model_name}",
                    "model_info": result.get("info", {}),
                    "model_type": "hdbscan",
                    "switch_time": time.time()
                }
            else:
                logger.error(f"❌ HDBSCAN model switch failed: {result.get('error')}")
                raise HTTPException(
                    status_code=400, 
                    detail=f"Failed to switch model: {result.get('error', 'Unknown error')}"
                )
        else:
            logger.info(f"📝 Detected lyrics model request: {model_name}")
            
            # Lyrics model switching
            if not hasattr(model_service, 'lyrics_service') or not model_service.lyrics_service:
                logger.error("❌ Lyrics service not initialized")
                raise HTTPException(status_code=503, detail="Lyrics service not initialized")
                
            logger.info("✅ Lyrics service found, calling switch_model")
            result = model_service.lyrics_service.switch_model(model_name)
            
            if result.get("success"):
                logger.success(f"✅ Successfully switched to lyrics model: {model_name}")
                return {
                    "message": f"Successfully switched to lyrics model: {model_name}",
                    "model_info": result.get("info", {}),
                    "model_type": "lyrics",
                    "switch_time": time.time()
                }
            else:
                logger.error(f"❌ Lyrics model switch failed: {result.get('error')}")
                raise HTTPException(
                    status_code=400, 
                    detail=f"Failed to switch model: {result.get('error', 'Unknown error')}"
                )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error switching to model {model_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Error switching model: {e}")


@router.get("/models/current")
async def get_current_model_info(
    model_service: ModelService = Depends(get_model_service)
) -> dict:
    """Get information about the currently loaded lyrics similarity model"""
    try:
        if hasattr(model_service, 'lyrics_service') and model_service.lyrics_service:
            model_info = model_service.lyrics_service.get_current_model_info()
            return {
                "status": "loaded",
                "model_info": model_info,
                "is_ready": model_service.lyrics_service.is_ready()
            }
        else:
            return {
                "status": "not_initialized",
                "model_info": {},
                "is_ready": False
            }
    except Exception as e:
        logger.error(f"Error getting current model info: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting model info: {e}")


@router.post("/artist-based", response_model=RecommendationResponse)
async def get_artist_based_recommendations(
    request: RecommendationRequest,
    db: AsyncSession = Depends(get_database)
) -> RecommendationResponse:
    """
    Get recommendations based on similar artists from liked songs
    """
    start_time = time.time()
    
    try:
        logger.info(f"🎤 Getting artist-based recommendations for {len(request.liked_song_ids)} songs")
        
        # Get liked songs and their artists
        liked_songs_query = select(Track).options(
            joinedload(Track.artist),
            joinedload(Track.album)
        ).filter(Track.id.in_(request.liked_song_ids))
        
        result = await db.execute(liked_songs_query)
        liked_tracks = result.scalars().all()
        
        if not liked_tracks:
            raise HTTPException(status_code=404, detail="No valid songs found")
        
        # Get unique artists from liked songs
        artist_ids = list(set([track.artist.id for track in liked_tracks if track.artist]))
        
        # Find more songs by these artists (excluding already liked songs)
        artist_songs_query = select(Track).options(
            joinedload(Track.artist),
            joinedload(Track.album)
        ).filter(
            Track.artist_id.in_(artist_ids),
            ~Track.id.in_(request.liked_song_ids)
        ).order_by(Track.popularity.desc()).limit(request.n_recommendations * 2)
        
        result = await db.execute(artist_songs_query)
        artist_songs = result.scalars().all()
        
        # Add some randomization and limit to requested count
        recommendations = list(artist_songs)
        random.shuffle(recommendations)
        recommendations = recommendations[:request.n_recommendations]
        
        # Convert to Song objects with artist similarity scores
        song_recommendations = []
        liked_artist_ids = set([track.artist.id for track in liked_tracks if track.artist])
        
        for track in recommendations:
            # Calculate similarity based on how many liked artists this track's artist matches
            if track.artist and track.artist.id in liked_artist_ids:
                # Full match for same artist - use percentage score (0-100)
                similarity = 85 + (track.popularity / 10)  # Base 85% + popularity bonus
            else:
                # Partial match based on genre similarity or other factors
                similarity = 30 + (track.popularity / 10)  # Lower base score for different artists
            
            # Ensure score stays within 0-100 range
            similarity = min(100, max(0, similarity))
            song_recommendations.append(_track_to_song(track, similarity))
        
        # Sort by similarity descending (higher is better for artist matching)
        song_recommendations.sort(key=lambda x: x.similarity_score, reverse=True)
        
        processing_time = (time.time() - start_time) * 1000
        
        return RecommendationResponse(
            recommendations=song_recommendations,
            recommendation_type="artist_based",
            clusters_used=[],
            total_found=len(song_recommendations),
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"❌ Error getting artist-based recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/genre-based", response_model=RecommendationResponse)
async def get_genre_based_recommendations(
    request: RecommendationRequest,
    db: AsyncSession = Depends(get_database)
) -> RecommendationResponse:
    """
    Get recommendations based on audio feature similarity (genre-like)
    """
    start_time = time.time()
    
    try:
        logger.info(f"🎵 Getting genre-based recommendations for {len(request.liked_song_ids)} songs")
        
        # Get liked songs and calculate average audio features
        liked_songs_query = select(Track).options(
            joinedload(Track.artist),
            joinedload(Track.album)
        ).filter(Track.id.in_(request.liked_song_ids))
        
        result = await db.execute(liked_songs_query)
        liked_tracks = result.scalars().all()
        
        if not liked_tracks:
            raise HTTPException(status_code=404, detail="No valid songs found")
        
        # Calculate average audio features
        features = ['energy', 'valence', 'danceability', 'acousticness', 'tempo']
        avg_features = {}
        
        for feature in features:
            values = [getattr(track, feature) for track in liked_tracks if getattr(track, feature) is not None]
            if values:
                avg_features[feature] = sum(values) / len(values)
        
        # Find songs with similar audio features
        # This is a simplified approach - in production you'd use more sophisticated similarity
        recommendations_query = select(Track).options(
            joinedload(Track.artist),
            joinedload(Track.album)
        ).filter(
            ~Track.id.in_(request.liked_song_ids)
        )
        
        # Add basic feature filtering if we have averages
        if 'energy' in avg_features:
            energy_range = 0.2
            recommendations_query = recommendations_query.filter(
                Track.energy.between(
                    max(0, avg_features['energy'] - energy_range),
                    min(1, avg_features['energy'] + energy_range)
                )
            )
        
        if 'valence' in avg_features:
            valence_range = 0.2
            recommendations_query = recommendations_query.filter(
                Track.valence.between(
                    max(0, avg_features['valence'] - valence_range),
                    min(1, avg_features['valence'] + valence_range)
                )
            )
        
        recommendations_query = recommendations_query.order_by(Track.popularity.desc()).limit(request.n_recommendations * 2)
        
        result = await db.execute(recommendations_query)
        similar_tracks = result.scalars().all()
        
        # Add randomization and limit
        recommendations = list(similar_tracks)
        random.shuffle(recommendations)
        recommendations = recommendations[:request.n_recommendations]
        
        # Convert to Song objects with feature similarity scores
        song_recommendations = []
        for track in recommendations:
            # Calculate similarity based on audio features
            similarity = 0.0
            feature_count = 0
            
            for feature in features:
                if feature in avg_features and getattr(track, feature) is not None:
                    avg_val = avg_features[feature]
                    track_val = getattr(track, feature)
                    
                    # Calculate normalized difference (closer to 0 means more similar)
                    if avg_val != 0:
                        diff = abs(track_val - avg_val) / abs(avg_val)
                        # Convert to similarity (1 - normalized_difference)
                        feature_similarity = max(0, 1 - diff)
                    else:
                        feature_similarity = 1.0 if track_val == 0 else 0.0
                    
                    similarity += feature_similarity
                    feature_count += 1
            
            # Average similarity across features and convert to percentage (0-100)
            if feature_count > 0:
                similarity = (similarity / feature_count) * 100  # Convert to percentage
                # Add popularity bonus
                similarity = min(100, similarity + (track.popularity / 10))
            else:
                similarity = track.popularity  # Fallback to popularity as percentage
            
            # Ensure score stays within 0-100 range
            similarity = min(100, max(0, similarity))
            song_recommendations.append(_track_to_song(track, similarity))
        
        # Sort by similarity descending (higher is better for genre matching)
        song_recommendations.sort(key=lambda x: x.similarity_score, reverse=True)
        
        processing_time = (time.time() - start_time) * 1000
        
        return RecommendationResponse(
            recommendations=song_recommendations,
            recommendation_type="genre_based",
            clusters_used=[],
            total_found=len(song_recommendations),
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"❌ Error getting genre-based recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/hdbscan-knn", response_model=RecommendationResponse)
async def get_hdbscan_knn_recommendations(
    request: RecommendationRequest,
    db: AsyncSession = Depends(get_database),
    model_service: ModelService = Depends(get_model_service)
) -> RecommendationResponse:
    """
    Get recommendations using HDBSCAN + KNN models directly
    This endpoint forces the use of trained models if available
    """
    if not model_service.is_ready():
        raise HTTPException(
            status_code=503,
            detail="Trained HDBSCAN + KNN models are not available"
        )
    
    response = await model_service.get_recommendations_with_similarity(request, db)
    response.recommendation_type = "hdbscan_knn"
    return response


async def get_global_recommendations(
    request: RecommendationRequest,
    db: AsyncSession
) -> RecommendationResponse:
    """
    Get globally popular recommendations regardless of user preferences
    Based on overall song popularity and trending metrics
    """
    start_time = time.time()
    
    try:
        logger.info(f"🌍 Getting global popular recommendations")
        
        # Get globally popular songs with diversity
        popular_query = select(Track).options(
            joinedload(Track.artist),
            joinedload(Track.album)
        ).filter(
            Track.popularity >= 60,  # High popularity threshold
            ~Track.id.in_(request.liked_song_ids)  # Exclude already liked songs
        ).order_by(
            Track.popularity.desc(),
            func.random()  # Add some randomness for diversity
        ).limit(request.n_recommendations * 2)  # Get more for filtering
        
        result = await db.execute(popular_query)
        all_recommendations = result.scalars().all()
        
        # Add some diversity by mixing high and medium popularity
        high_pop = [t for t in all_recommendations if t.popularity >= 80]
        medium_pop = [t for t in all_recommendations if 60 <= t.popularity < 80]
        
        # Mix the results for diversity
        recommendations = []
        high_idx = medium_idx = 0
        
        for i in range(min(request.n_recommendations, len(all_recommendations))):
            if i % 3 == 0 and medium_idx < len(medium_pop):
                # Every 3rd song from medium popularity for diversity
                recommendations.append(medium_pop[medium_idx])
                medium_idx += 1
            elif high_idx < len(high_pop):
                recommendations.append(high_pop[high_idx])
                high_idx += 1
            elif medium_idx < len(medium_pop):
                recommendations.append(medium_pop[medium_idx])
                medium_idx += 1
        
        # Convert to Song objects with popularity-based similarity scores
        song_recommendations = []
        for track in recommendations:
            # Use popularity as base score and add some randomness for diversity
            similarity = track.popularity + random.uniform(-10, 10)  # Use popularity as percentage with variance
            # Ensure score stays within 0-100 range
            similarity = min(100, max(0, similarity))
            song_recommendations.append(_track_to_song(track, similarity))
        
        # Sort by similarity descending (higher is better for global popularity)
        song_recommendations.sort(key=lambda x: x.similarity_score, reverse=True)
        
        processing_time = (time.time() - start_time) * 1000
        
        response = RecommendationResponse(
            recommendations=song_recommendations,
            recommendation_type="global",
            clusters_used=[],
            total_found=len(song_recommendations),
            processing_time_ms=processing_time
        )
        
        logger.success(f"✅ Generated {len(song_recommendations)} global recommendations in {processing_time:.1f}ms")
        return response
        
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        logger.error(f"❌ Error generating global recommendations: {e} (took {processing_time:.1f}ms)")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating global recommendations: {str(e)}"
        )


async def get_hybrid_recommendations(
    request: RecommendationRequest,
    db: AsyncSession,
    model_service: ModelService
) -> RecommendationResponse:
    """
    Get hybrid recommendations combining multiple approaches
    Blends cluster-based, popularity-based, and content-based recommendations
    """
    start_time = time.time()
    
    try:
        logger.info(f"🔀 Getting hybrid recommendations combining multiple approaches")
        
        all_recommendations = []
        weights = {
            'cluster': 0.4,      # 40% cluster-based
            'popularity': 0.3,   # 30% popularity-based  
            'content': 0.3       # 30% content-based (genre/artist)
        }
        
        # 1. Get cluster-based recommendations (if available)
        cluster_recs = []
        if model_service.is_ready():
            try:
                cluster_request = RecommendationRequest(
                    liked_song_ids=request.liked_song_ids,
                    n_recommendations=int(request.n_recommendations * weights['cluster'] * 2),
                    recommendation_type="cluster"
                )
                cluster_response = await model_service.get_recommendations_with_similarity(cluster_request, db)
                cluster_recs = [(song, song.similarity_score or 0.0, 'cluster') for song in cluster_response.recommendations]
            except Exception as e:
                logger.warning(f"Cluster recommendations failed in hybrid: {e}")
        
        # 2. Get popularity-based recommendations
        popularity_recs = []
        try:
            pop_request = RecommendationRequest(
                liked_song_ids=request.liked_song_ids,
                n_recommendations=int(request.n_recommendations * weights['popularity'] * 2),
                recommendation_type="global"
            )
            pop_response = await get_global_recommendations(pop_request, db)
            popularity_recs = [(song, song.similarity_score or 0.0, 'popularity') for song in pop_response.recommendations]
        except Exception as e:
            logger.warning(f"Popularity recommendations failed in hybrid: {e}")
        
        # 3. Get content-based recommendations (artist similarity)
        content_recs = []
        try:
            content_request = RecommendationRequest(
                liked_song_ids=request.liked_song_ids,
                n_recommendations=int(request.n_recommendations * weights['content'] * 2),
                recommendation_type="artist_based"
            )
            content_response = await get_artist_based_recommendations(content_request, db)
            content_recs = [(song, song.similarity_score or 0.0, 'content') for song in content_response.recommendations]
        except Exception as e:
            logger.warning(f"Content recommendations failed in hybrid: {e}")
        
        # Combine and weight the recommendations
        all_recs = cluster_recs + popularity_recs + content_recs
        
        # Calculate hybrid scores
        song_scores = {}
        for song, score, source in all_recs:
            if song.id not in song_scores:
                song_scores[song.id] = {
                    'song': song,
                    'scores': {'cluster': 0, 'popularity': 0, 'content': 0},
                    'count': {'cluster': 0, 'popularity': 0, 'content': 0}
                }
            
            song_scores[song.id]['scores'][source] = max(song_scores[song.id]['scores'][source], score)
            song_scores[song.id]['count'][source] += 1
        
        # Calculate final hybrid scores
        final_recommendations = []
        for song_id, data in song_scores.items():
            song = data['song']
            scores = data['scores']
            
            # Weighted hybrid score (convert to percentage)
            hybrid_score = (
                scores['cluster'] * weights['cluster'] +
                scores['popularity'] * weights['popularity'] +
                scores['content'] * weights['content']
            )
            
            # Boost songs that appear in multiple methods (percentage bonus)
            diversity_bonus = len([s for s in scores.values() if s > 0]) * 5  # 5% bonus per method
            final_score = min(100, hybrid_score + diversity_bonus)  # Keep within 0-100 range
            
            song.similarity_score = final_score
            final_recommendations.append((song, final_score))
        
        # Sort by hybrid score and take top N
        final_recommendations.sort(key=lambda x: x[1], reverse=True)
        recommendations = [song for song, _ in final_recommendations[:request.n_recommendations]]
        
        processing_time = (time.time() - start_time) * 1000
        
        response = RecommendationResponse(
            recommendations=recommendations,
            recommendation_type="hybrid",
            clusters_used=[],
            total_found=len(recommendations),
            processing_time_ms=processing_time
        )
        
        logger.success(f"✅ Generated {len(recommendations)} hybrid recommendations in {processing_time:.1f}ms")
        return response
        
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        logger.error(f"❌ Error generating hybrid recommendations: {e} (took {processing_time:.1f}ms)")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating hybrid recommendations: {str(e)}"
        )