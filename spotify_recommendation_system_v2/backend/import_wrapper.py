#!/usr/bin/env python3
"""
Import Wrapper Script for Spotify Music Recommendation System v2
Provides better error handling and prevents infinite loops
"""

import asyncio
import sys
import os
import signal
import time
from loguru import logger
from pathlib import Path

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.import_data import main as import_main


class ImportWrapper:
    """Wrapper class for safe import execution"""
    
    def __init__(self):
        self.max_retries = 3
        self.retry_delay = 60  # seconds
        self.lock_file = Path("/tmp/spotify_import.lock")
        self.success_file = Path("/tmp/spotify_import_success.flag")
        
    def create_lock_file(self):
        """Create a lock file to prevent concurrent imports"""
        try:
            self.lock_file.write_text(str(os.getpid()))
            logger.info(f"Created lock file: {self.lock_file}")
        except Exception as e:
            logger.error(f"Could not create lock file: {e}")
            
    def remove_lock_file(self):
        """Remove the lock file"""
        try:
            if self.lock_file.exists():
                self.lock_file.unlink()
                logger.info(f"Removed lock file: {self.lock_file}")
        except Exception as e:
            logger.error(f"Could not remove lock file: {e}")
            
    def check_if_already_running(self):
        """Check if another import process is already running"""
        if self.lock_file.exists():
            try:
                pid_str = self.lock_file.read_text().strip()
                pid = int(pid_str)
                
                # Check if process is still running
                try:
                    os.kill(pid, 0)  # Signal 0 just checks if process exists
                    logger.warning(f"Import process already running with PID {pid}")
                    return True
                except OSError:
                    # Process doesn't exist, remove stale lock file
                    logger.info("Removing stale lock file")
                    self.lock_file.unlink()
                    
            except (ValueError, FileNotFoundError):
                # Invalid lock file, remove it
                try:
                    self.lock_file.unlink()
                except:
                    pass
                    
        return False
        
    def check_if_already_completed(self):
        """Check if import was already completed successfully"""
        if self.success_file.exists():
            try:
                timestamp = self.success_file.stat().st_mtime
                import_time = time.ctime(timestamp)
                logger.info(f"✅ Import already completed successfully at {import_time}")
                logger.info("To force re-import, delete the success flag file:")
                logger.info(f"   rm {self.success_file}")
                return True
            except Exception as e:
                logger.warning(f"Could not read success file: {e}")
                
        return False
        
    def mark_success(self):
        """Mark the import as successful"""
        try:
            self.success_file.write_text(f"Import completed successfully at {time.ctime()}")
            logger.info(f"Created success flag: {self.success_file}")
        except Exception as e:
            logger.error(f"Could not create success flag: {e}")
            
    def cleanup(self):
        """Cleanup on exit"""
        self.remove_lock_file()
        
    def signal_handler(self, signum, frame):
        """Handle termination signals gracefully"""
        logger.warning(f"Received signal {signum}, cleaning up...")
        self.cleanup()
        sys.exit(1)
        
    async def run_import_with_retries(self):
        """Run the import with retry logic"""
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"🚀 Starting import attempt {attempt}/{self.max_retries}")
                
                # Run the actual import
                await import_main()
                
                # If we get here, import was successful
                logger.success("🎉 Import completed successfully!")
                self.mark_success()
                return True
                
            except KeyboardInterrupt:
                logger.warning("⚠️ Import interrupted by user")
                return False
                
            except Exception as e:
                logger.error(f"❌ Import attempt {attempt} failed: {e}")
                
                if attempt < self.max_retries:
                    logger.info(f"⏳ Waiting {self.retry_delay} seconds before retry...")
                    await asyncio.sleep(self.retry_delay)
                else:
                    logger.error(f"❌ All {self.max_retries} import attempts failed")
                    return False
                    
        return False
        
    async def run(self):
        """Main execution method"""
        logger.info("🎵 Spotify Music Recommendation System v2 - Import Wrapper")
        logger.info("=" * 70)
        
        # Setup signal handlers
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        
        try:
            # Check if already completed
            if self.check_if_already_completed():
                return True
                
            # Check if already running
            if self.check_if_already_running():
                logger.error("❌ Import process already running, exiting")
                return False
                
            # Create lock file
            self.create_lock_file()
            
            # Run the import
            success = await self.run_import_with_retries()
            
            return success
            
        finally:
            self.cleanup()


async def main():
    """Main function"""
    wrapper = ImportWrapper()
    success = await wrapper.run()
    
    if success:
        logger.success("✅ Import wrapper completed successfully")
        sys.exit(0)
    else:
        logger.error("❌ Import wrapper failed")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 