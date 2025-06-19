"""
Health check endpoints
"""

from fastapi import APIRouter, Request, HTTPException
from datetime import datetime
import psutil
import os
from loguru import logger

router = APIRouter()


@router.get("/")
async def health_check(request: Request):
    """Basic health check endpoint"""
    try:
        model_service = getattr(request.app.state, 'model_service', None)
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "Spotify Recommendation System v2",
            "version": "2.0.0",
            "models_loaded": model_service is not None
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Service unhealthy")


@router.get("/detailed")
async def detailed_health_check(request: Request):
    """Detailed health check with system metrics"""
    try:
        model_service = getattr(request.app.state, 'model_service', None)
        
        # System metrics
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        health_data = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "Spotify Recommendation System v2",
            "version": "2.0.0",
            "uptime_seconds": 0,  # Would track actual uptime in production
            "system": {
                "cpu_percent": psutil.cpu_percent(),
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": (disk.used / disk.total) * 100
                }
            },
            "models": {
                "loaded": model_service is not None,
                "stats": await model_service.get_stats() if model_service else None
            }
        }
        
        return health_data
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check error: {str(e)}")


@router.get("/ready")
async def readiness_check(request: Request):
    """Readiness check - ensures service is ready to handle requests"""
    try:
        model_service = getattr(request.app.state, 'model_service', None)
        
        if not model_service:
            raise HTTPException(status_code=503, detail="Models not loaded")
        
        # Verify models are properly loaded
        stats = await model_service.get_stats()
        if not all(stats.get('models_loaded', {}).values()):
            raise HTTPException(status_code=503, detail="Some models not loaded")
        
        return {
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat(),
            "models_status": stats.get('models_loaded', {}),
            "total_songs": stats.get('total_songs', 0)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service not ready: {str(e)}")


@router.get("/live")
async def liveness_check():
    """Liveness check - basic ping to ensure service is running"""
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
        "pid": os.getpid()
    } 