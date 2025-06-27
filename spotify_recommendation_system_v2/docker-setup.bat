@echo off
REM 🎵 Spotify Music Recommendation System v2 - Docker Setup Script (Windows)
REM This script sets up the complete Docker environment for the application

setlocal enabledelayedexpansion

echo 🎵 Setting up Spotify Music Recommendation System v2...

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed. Please install Docker first.
    exit /b 1
)

REM Check if Docker Compose is installed
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Compose is not installed. Please install Docker Compose first.
    exit /b 1
)

REM Create necessary directories
echo [INFO] Creating necessary directories...
if not exist "..\data\raw" mkdir "..\data\raw"
if not exist "..\data\processed" mkdir "..\data\processed"
if not exist "..\data\models" mkdir "..\data\models"
if not exist "backend\logs" mkdir "backend\logs"
if not exist "frontend\dist" mkdir "frontend\dist"

REM Create .env file if it doesn't exist
if not exist ".env" (
    echo [INFO] Creating .env file from template...
    copy "env.example" ".env"
    echo [WARNING] Please edit .env file with your specific configuration
)

goto :%1 2>nul || goto :help

:setup
echo [INFO] Setting up the environment...

echo [INFO] Pulling latest Docker images...
docker-compose pull

echo [INFO] Building Docker images...
docker-compose build --no-cache

echo [INFO] Starting database...
docker-compose up -d database

echo [INFO] Waiting for database to be ready...
timeout /t 10 /nobreak >nul

:wait_db
docker-compose exec database pg_isready -U spotify_user -d spotify_recommendations >nul 2>&1
if errorlevel 1 (
    echo [INFO] Waiting for database...
    timeout /t 5 /nobreak >nul
    goto :wait_db
)

echo [SUCCESS] Database is ready!
goto :eof

:models
echo [INFO] Preparing ML models...

REM Check if data files exist first
if not exist "..\data\raw\spotify_tracks.csv" (
    echo [ERROR] Required data file not found: ..\data\raw\spotify_tracks.csv
    echo [WARNING] Please ensure your data files are in the correct location before running setup
    exit /b 1
)

echo [INFO] Found required data files. Starting model generation...
echo [WARNING] This process may take 5-15 minutes depending on your system...

REM Run model preparation with verbose output
docker-compose --profile setup run --rm model-prep

REM Check if model preparation was successful
if exist "C:\tmp\model_prep_success" (
    echo [SUCCESS] Models prepared successfully!
    
    REM List generated models
    echo [INFO] Generated model files:
    if exist "..\data\models\*.pkl" (
        dir /b "..\data\models\*.pkl" 2>nul | findstr /c:"_" >nul
        if not errorlevel 1 (
            echo Model variants found in ..\data\models\
        )
    )
    
    exit /b 0
) else if exist "C:\tmp\model_prep_failure" (
    echo [ERROR] Model preparation failed!
    type "C:\tmp\model_prep_failure" 2>nul
    exit /b 1
) else (
    echo [ERROR] Model preparation status unknown!
    exit /b 1
)

:models-force
echo [INFO] Force regenerating all ML models...

REM Check if data files exist first
if not exist "..\data\raw\spotify_tracks.csv" (
    echo [ERROR] Required data file not found: ..\data\raw\spotify_tracks.csv
    echo [WARNING] Please ensure your data files are in the correct location
    exit /b 1
)

echo [WARNING] FORCE MODE: Will regenerate all models even if they exist
echo [WARNING] This process may take 10-20 minutes depending on your system...

REM Run model preparation with force flag
docker-compose --profile setup run --rm -e FORCE_REGENERATE=true model-prep

REM Check if model preparation was successful
if exist "C:\tmp\model_prep_success" (
    echo [SUCCESS] Models regenerated successfully!
    exit /b 0
) else (
    echo [ERROR] Model regeneration failed!
    type "C:\tmp\model_prep_failure" 2>nul
    exit /b 1
)

:models-check
echo [INFO] Checking model status...

REM Run model check without generation
docker-compose --profile setup run --rm model-prep python scripts/startup.py --check-only

if errorlevel 1 (
    echo [INFO] No models found or check failed
    exit /b 1
) else (
    echo [SUCCESS] Models exist and are accessible
    exit /b 0
)

:import
echo [INFO] Importing data...
if not exist "..\data\raw\spotify_tracks.csv" (
    echo [WARNING] Data file not found at ..\data\raw\spotify_tracks.csv
    echo [WARNING] Please ensure your data files are in the correct location
    exit /b 1
)

docker-compose --profile setup run --rm data-import
if errorlevel 1 (
    echo [ERROR] Data import failed!
    exit /b 1
)
echo [SUCCESS] Data imported successfully!
goto :eof

:start
echo [INFO] Starting all services...
docker-compose up -d backend frontend

timeout /t 10 /nobreak >nul

echo [INFO] Checking service health...
curl -f http://localhost:8000/health >nul 2>&1
if not errorlevel 1 (
    echo [SUCCESS] Backend is healthy!
) else (
    echo [WARNING] Backend health check failed
)

curl -f http://localhost:8501 >nul 2>&1
if not errorlevel 1 (
    echo [SUCCESS] Frontend is accessible!
) else (
    echo [WARNING] Frontend accessibility check failed
)
goto :eof

:dev
echo [INFO] Starting development environment...
docker-compose --profile development up -d backend frontend-dev

echo [SUCCESS] Development environment started!
echo [INFO] Backend: http://localhost:8000
echo [INFO] Frontend (Dev): http://localhost:5173
echo [INFO] API Docs: http://localhost:8000/api/v2/docs
goto :eof

:prod
echo [INFO] Starting production environment...
docker-compose --profile production up -d

echo [SUCCESS] Production environment started!
echo [INFO] Application: http://localhost:80
echo [INFO] Backend API: http://localhost:8000
echo [INFO] Frontend: http://localhost:8501
goto :eof

:full
call :setup
if errorlevel 1 exit /b 1
call :models
if errorlevel 1 exit /b 1
call :import
if errorlevel 1 exit /b 1
call :start
goto :eof

:full-force
echo [WARNING] Full setup with forced model regeneration
call :setup
if errorlevel 1 exit /b 1
call :models-force
if errorlevel 1 exit /b 1
call :import
if errorlevel 1 exit /b 1
call :start
goto :eof

:logs
echo 📋 Showing logs for all services...
docker-compose logs -f
goto :eof

:stop
echo [INFO] Stopping all services...
docker-compose down
echo [SUCCESS] All services stopped!
goto :eof

:status
echo 📊 Docker Services Status:
docker-compose ps
echo.
echo 📈 Resource Usage:
docker stats --no-stream

echo.
echo 📊 Model Status:
call :models-check
goto :eof

:cleanup
echo [INFO] Cleaning up Docker resources...
docker-compose down -v
docker image prune -f

set /p cleanup_volumes="Remove Docker volumes? This will delete all data! (y/N): "
if /i "!cleanup_volumes!"=="y" (
    docker-compose down -v --remove-orphans
    docker volume prune -f
    
    REM Clean up temp files
    if exist "C:\tmp\model_prep_success" del "C:\tmp\model_prep_success" >nul 2>&1
    if exist "C:\tmp\model_prep_failure" del "C:\tmp\model_prep_failure" >nul 2>&1
    
    echo [SUCCESS] Cleanup completed!
) else (
    echo [INFO] Volumes preserved.
)
goto :eof

:help
echo 🎵 Spotify Music Recommendation System v2 - Docker Setup
echo.
echo Usage: %0 [COMMAND]
echo.
echo Commands:
echo   setup         - Set up the environment (build images, start database)
echo   models        - Prepare ML models (incremental - only missing ones)
echo   models-force  - Force regenerate all ML models
echo   models-check  - Check status of existing models
echo   import        - Import data into database
echo   start         - Start main services (backend + frontend)
echo   dev           - Start development environment
echo   prod          - Start production environment
echo   full          - Complete setup (setup + models + import + start)
echo   full-force    - Complete setup with forced model regeneration
echo   logs          - Show logs for all services
echo   stop          - Stop all services
echo   status        - Show status of all services and models
echo   cleanup       - Clean up Docker resources
echo   help          - Show this help message
echo.
echo Examples:
echo   %0 full           # Complete setup and start
echo   %0 models-check   # Check if models exist
echo   %0 models-force   # Force regenerate all models
echo   %0 dev            # Start development environment
echo   %0 setup ^&^& %0 models ^&^& %0 start  # Step by step setup
echo.
echo Production Features:
echo   - Incremental model generation (only creates missing models)
echo   - Force regeneration option for updates
echo   - Status checking for existing models
echo   - Comprehensive error handling and logging
goto :eof 