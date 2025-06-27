#!/bin/bash

# 🎵 Spotify Music Recommendation System v2 - Docker Setup Script
# This script sets up the complete Docker environment for the application

set -e  # Exit on any error

echo "🎵 Setting up Spotify Music Recommendation System v2..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p ../data/{raw,processed,models}
mkdir -p backend/logs
mkdir -p frontend/dist

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    print_status "Creating .env file from template..."
    cp env.example .env
    print_warning "Please edit .env file with your specific configuration"
fi

# Function to run setup profile
setup_environment() {
    print_status "Setting up the environment..."
    
    # Pull latest images
    print_status "Pulling latest Docker images..."
    docker-compose pull
    
    # Build images
    print_status "Building Docker images..."
    docker-compose build --no-cache
    
    # Start database first
    print_status "Starting database..."
    docker-compose up -d database
    
    # Wait for database to be ready
    print_status "Waiting for database to be ready..."
    sleep 10
    
    # Check database health
    until docker-compose exec database pg_isready -U spotify_user -d spotify_recommendations; do
        print_status "Waiting for database..."
        sleep 5
    done
    
    print_success "Database is ready!"
}

# Function to prepare models
prepare_models() {
    print_status "Preparing ML models..."
    
    # Check if data files exist first
    if [ ! -f "../data/raw/spotify_tracks.csv" ]; then
        print_error "Required data file not found: ../data/raw/spotify_tracks.csv"
        print_warning "Please ensure your data files are in the correct location before running setup"
        return 1
    fi
    
    print_status "Found required data files. Starting model generation..."
    print_warning "This process may take 5-15 minutes depending on your system..."
    
    # Run model preparation with verbose output
    docker-compose --profile setup run --rm model-prep
    
    # Check if model preparation was successful
    if [ -f "/tmp/model_prep_success" ]; then
        print_success "Models prepared successfully!"
        
        # List generated models
        print_status "Generated model files:"
        if [ -d "../data/models" ]; then
            ls -la ../data/models/*.pkl 2>/dev/null | head -10
            echo "..."
            echo "Total model files: $(ls -1 ../data/models/*.pkl 2>/dev/null | wc -l)"
        fi
        
        return 0
    elif [ -f "/tmp/model_prep_failure" ]; then
        print_error "Model preparation failed!"
        print_error "Error: $(cat /tmp/model_prep_failure 2>/dev/null || echo 'Unknown error')"
        return 1
    else
        print_error "Model preparation status unknown!"
        return 1
    fi
}

# Function to import data
import_data() {
    print_status "Importing data..."
    
    # Check if data files exist
    if [ ! -f "../data/raw/spotify_tracks.csv" ]; then
        print_warning "Data file not found at ../data/raw/spotify_tracks.csv"
        print_warning "Please ensure your data files are in the correct location"
        return 1
    fi
    
    # Run data import
    docker-compose --profile setup run --rm data-import
    
    if [ $? -eq 0 ]; then
        print_success "Data imported successfully!"
    else
        print_error "Data import failed!"
        return 1
    fi
}

# Function to start services
start_services() {
    print_status "Starting all services..."
    
    # Start main services
    docker-compose up -d backend frontend
    
    # Wait a bit for services to start
    sleep 10
    
    # Check service health
    print_status "Checking service health..."
    
    # Check backend health
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        print_success "Backend is healthy!"
    else
        print_warning "Backend health check failed"
    fi
    
    # Check frontend
    if curl -f http://localhost:8501 > /dev/null 2>&1; then
        print_success "Frontend is accessible!"
    else
        print_warning "Frontend accessibility check failed"
    fi
}

# Function to start development environment
start_development() {
    print_status "Starting development environment..."
    
    # Start with development profile
    docker-compose --profile development up -d backend frontend-dev
    
    print_success "Development environment started!"
    print_status "Backend: http://localhost:8000"
    print_status "Frontend (Dev): http://localhost:5173"
    print_status "API Docs: http://localhost:8000/api/v2/docs"
}

# Function to start production environment
start_production() {
    print_status "Starting production environment..."
    
    # Start with production profile
    docker-compose --profile production up -d
    
    print_success "Production environment started!"
    print_status "Application: http://localhost:80"
    print_status "Backend API: http://localhost:8000"
    print_status "Frontend: http://localhost:8501"
}

# Function to show logs
show_logs() {
    echo "📋 Showing logs for all services..."
    docker-compose logs -f
}

# Function to stop all services
stop_services() {
    print_status "Stopping all services..."
    docker-compose down
    print_success "All services stopped!"
}

# Function to clean up
cleanup() {
    print_status "Cleaning up Docker resources..."
    
    # Stop and remove containers
    docker-compose down -v
    
    # Remove unused images
    docker image prune -f
    
    # Remove unused volumes (be careful with this)
    read -p "Remove Docker volumes? This will delete all data! (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose down -v --remove-orphans
        docker volume prune -f
        print_success "Cleanup completed!"
    else
        print_status "Volumes preserved."
    fi
}

# Function to show status
show_status() {
    echo "📊 Docker Services Status:"
    docker-compose ps
    echo ""
    echo "📈 Resource Usage:"
    docker stats --no-stream
}

# Main menu
case "${1:-help}" in
    "setup")
        setup_environment
        ;;
    "models")
        prepare_models
        ;;
    "import")
        import_data
        ;;
    "start")
        start_services
        ;;
    "dev")
        start_development
        ;;
    "prod")
        start_production
        ;;
    "full")
        setup_environment
        prepare_models
        import_data
        start_services
        ;;
    "logs")
        show_logs
        ;;
    "stop")
        stop_services
        ;;
    "status")
        show_status
        ;;
    "cleanup")
        cleanup
        ;;
    "help"|*)
        echo "🎵 Spotify Music Recommendation System v2 - Docker Setup"
        echo ""
        echo "Usage: $0 [COMMAND]"
        echo ""
        echo "Commands:"
        echo "  setup     - Set up the environment (build images, start database)"
        echo "  models    - Prepare ML models"
        echo "  import    - Import data into database"
        echo "  start     - Start main services (backend + frontend)"
        echo "  dev       - Start development environment"
        echo "  prod      - Start production environment"
        echo "  full      - Complete setup (setup + models + import + start)"
        echo "  logs      - Show logs for all services"
        echo "  stop      - Stop all services"
        echo "  status    - Show status of all services"
        echo "  cleanup   - Clean up Docker resources"
        echo "  help      - Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0 full           # Complete setup and start"
        echo "  $0 dev            # Start development environment"
        echo "  $0 setup && $0 models && $0 start  # Step by step setup"
        ;;
esac 