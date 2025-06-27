#!/usr/bin/env python3
"""
Model Preparation Startup Script
Handles the initialization and execution of the model generation pipeline
"""

import os
import sys
import time
import argparse
from pathlib import Path
from loguru import logger

# Add parent directory to path
sys.path.append('/app')

def check_prerequisites():
    """Check if all prerequisites are met"""
    logger.info("🔍 Checking prerequisites...")
    
    # Check data directory
    data_path = Path(os.environ.get('DATA_PATH', '/app/data'))
    raw_data_path = data_path / 'raw'
    
    if not raw_data_path.exists():
        logger.error(f"❌ Raw data directory not found: {raw_data_path}")
        return False
    
    # Check required files
    required_files = ['spotify_tracks.csv']
    optional_files = ['low_level_audio_features.csv', 'lyrics_features.csv']
    
    missing_required = []
    for file in required_files:
        if not (raw_data_path / file).exists():
            missing_required.append(file)
    
    if missing_required:
        logger.error(f"❌ Missing required files: {missing_required}")
        return False
    
    # Check optional files
    available_optional = []
    for file in optional_files:
        if (raw_data_path / file).exists():
            available_optional.append(file)
            file_size = (raw_data_path / file).stat().st_size / (1024 * 1024)  # MB
            logger.info(f"📄 {file}: {file_size:.1f}MB")
    
    logger.info(f"✅ Required files: {required_files}")
    logger.info(f"📄 Available optional files: {available_optional}")
    
    return True

def setup_directories():
    """Setup necessary directories"""
    logger.info("📁 Setting up directories...")
    
    directories = [
        Path(os.environ.get('MODELS_PATH', '/app/models')),
        Path(os.environ.get('DATA_PATH', '/app/data')) / 'processed',
        Path('/app/logs')
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True) 
        logger.info(f"✅ Directory ready: {directory}")

def check_existing_models():
    """Check what models already exist"""
    models_path = Path(os.environ.get('MODELS_PATH', '/app/models'))
    
    if not models_path.exists():
        logger.info("📂 Models directory doesn't exist yet")
        return False
    
    pkl_files = list(models_path.glob("*.pkl"))
    json_files = list(models_path.glob("*.json"))
    
    if pkl_files or json_files:
        logger.info(f"📊 Found existing files:")
        logger.info(f"  📄 PKL files: {len(pkl_files)}")
        logger.info(f"  📄 JSON files: {len(json_files)}")
        
        # Show some examples
        for file in sorted(pkl_files)[:5]:
            size_mb = file.stat().st_size / (1024 * 1024)
            logger.info(f"    {file.name} ({size_mb:.1f}MB)")
        
        if len(pkl_files) > 5:
            logger.info(f"    ... and {len(pkl_files) - 5} more")
            
        return True
    else:
        logger.info("📂 No existing model files found")
        return False

def main():
    """Main startup function"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Model Preparation Service')
    parser.add_argument('--force', action='store_true', 
                       help='Force regeneration of all models')
    parser.add_argument('--check-only', action='store_true',
                       help='Only check status, don\'t generate models')
    
    args = parser.parse_args()
    
    logger.info("🚀 Starting Model Preparation Service...")
    
    if args.force:
        logger.warning("⚡ FORCE MODE: Will regenerate all models")
        # Set environment variable for pipeline
        os.environ['FORCE_REGENERATE'] = 'true'
    
    try:
        # Setup
        setup_directories()
        
        # Check prerequisites
        if not check_prerequisites():
            logger.error("❌ Prerequisites not met. Exiting...")
            sys.exit(1)
        
        # Check existing models
        has_existing = check_existing_models()
        
        if args.check_only:
            logger.info("📊 Status check completed")
            if has_existing:
                logger.info("✅ Models exist")
                sys.exit(0)
            else:
                logger.info("❌ No models found")
                sys.exit(1)
        
        if has_existing and not args.force:
            logger.info("🎯 Some models may already exist - will only generate missing ones")
        
        # Import and run pipeline
        logger.info("🔧 Starting model generation pipeline...")
        from model_pipeline import main as run_pipeline
        
        start_time = time.time()
        run_pipeline()
        end_time = time.time()
        
        duration = end_time - start_time
        logger.success(f"✅ Model generation completed in {duration:.2f} seconds")
        
        # Final status check
        final_check = check_existing_models()
        if final_check:
            logger.success("🎉 Model preparation service completed successfully!")
            
            # Create success marker with metadata
            success_marker = Path("/tmp/model_prep_success")
            metadata = {
                'completion_time': time.time(),
                'duration_seconds': duration,
                'force_mode': args.force
            }
            success_marker.write_text(f"Success at {time.ctime()}\nDuration: {duration:.2f}s\nForce: {args.force}")
        else:
            logger.error("❌ Model generation completed but no models found!")
            sys.exit(1)
        
    except KeyboardInterrupt:
        logger.warning("⚠️ Model preparation interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"❌ Model preparation failed: {e}")
        
        # Create failure marker
        failure_marker = Path("/tmp/model_prep_failure")
        failure_marker.write_text(f"Failed at {time.ctime()}\nError: {str(e)}")
        
        sys.exit(1)

if __name__ == "__main__":
    main() 