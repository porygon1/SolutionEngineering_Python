"""
🎵 Spotify Music Recommendation System v2 - FastAPI Backend
AI-powered music recommendation using HDBSCAN clustering and KNN
"""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import time
from loguru import logger
import sys
import os

from app.config import settings
from app.database.database import init_database, close_database, create_tables
from app.routers import recommendations, health, songs, clusters
from app.services.model_service import ModelService
from app.middleware.logging import LoggingMiddleware
from app.middleware.performance import PerformanceMiddleware


# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    format=settings.LOG_FORMAT,
    level=settings.LOG_LEVEL,
    colorize=True
)

# Add file logging
log_file = os.path.join(os.path.dirname(__file__), "../logs/app.log")
os.makedirs(os.path.dirname(log_file), exist_ok=True)
logger.add(
    log_file,
    format=settings.LOG_FORMAT,
    level=settings.LOG_LEVEL,
    rotation="10 MB",
    retention="7 days",
    compression="zip"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    Handles startup and shutdown events
    """
    # Startup
    logger.info("🚀 Starting Spotify Music Recommendation System v2...")
    
    try:
        # Initialize database connection
        logger.info("🔌 Connecting to database...")
        await init_database()
        
        # Create tables if they don't exist
        logger.info("📋 Ensuring database tables exist...")
        await create_tables()
        
        # Initialize ML models using trained HDBSCAN and KNN models
        logger.info("🧠 Loading trained ML models...")
        model_service = ModelService()
        
        try:
            await model_service.initialize()
            logger.success("✅ Trained ML models loaded successfully")
        except Exception as e:
            logger.error(f"❌ Failed to load trained models: {e}")
            logger.warning("⚠️ Starting without trained models - using fallback recommendations")
        
        app.state.model_service = model_service
        
        logger.success("🎉 Application startup completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🔌 Shutting down application...")
    
    try:
        # Close database connection
        await close_database()
        logger.info("📡 Database connection closed")
        
        # Cleanup ML models
        if hasattr(app.state, 'model_service'):
            app.state.model_service.cleanup()
            logger.info("🧠 ML models cleaned up")
        
        logger.success("✅ Application shutdown completed")
        
    except Exception as e:
        logger.error(f"❌ Shutdown error: {e}")


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V2_STR}/openapi.json",
    docs_url=f"{settings.API_V2_STR}/docs",
    redoc_url=f"{settings.API_V2_STR}/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure this properly in production
)

# Add custom middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(PerformanceMiddleware)

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time header to all responses"""
    start_time = time.time()
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        # Log slow requests
        if process_time > 1.0:
            logger.warning(f"Slow request: {request.method} {request.url.path} took {process_time:.2f}s")
        
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"Request failed: {request.method} {request.url.path} after {process_time:.2f}s - {e}")
        raise


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    logger.warning(f"HTTP {exc.status_code}: {exc.detail} - {request.method} {request.url.path}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url.path),
            "method": request.method,
            "timestamp": time.time()
        }
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Handle generic exceptions"""
    logger.error(f"Unhandled exception: {exc} - {request.method} {request.url.path}")
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "path": str(request.url.path),
            "method": request.method,
            "timestamp": time.time()
        }
    )


# Include routers
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(recommendations.router, prefix=f"{settings.API_V2_STR}/recommendations", tags=["Recommendations"])
app.include_router(songs.router, prefix=f"{settings.API_V2_STR}/songs", tags=["Songs"])
app.include_router(clusters.router, prefix=f"{settings.API_V2_STR}/clusters", tags=["Clusters"])


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "🎵 Welcome to Spotify Music Recommendation System v2",
        "version": settings.VERSION,
        "description": settings.DESCRIPTION,
        "docs_url": f"{settings.API_V2_STR}/docs",
        "health_check": "/health",
        "database": "PostgreSQL",
        "ml_algorithm": "HDBSCAN + KNN",
        "status": "running"
    }


# API status endpoint
@app.get(f"{settings.API_V2_STR}/status")
async def api_status():
    """API status endpoint"""
    try:
        # Check if model service is available
        model_service = getattr(app.state, 'model_service', None)
        model_status = "loaded" if model_service and model_service.is_ready() else "not_loaded"
        
        return {
            "status": "healthy",
            "version": settings.VERSION,
            "models": model_status,
            "database": "connected",
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True
    ) 