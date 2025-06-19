"""
Advanced Logging Configuration for Spotify Recommendation System

This module provides comprehensive logging setup with:
- Multiple log levels and handlers
- File rotation
- Structured logging
- Performance monitoring
- Error tracking
- Environment-based configuration
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
import json
from typing import Dict, Any
import traceback

class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging with JSON output option"""
    
    def __init__(self, include_json=False):
        self.include_json = include_json
        super().__init__()
    
    def format(self, record):
        # Standard formatted message
        if not self.include_json:
            return super().format(record)
        
        # JSON structured output
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'message': record.getMessage(),
            'thread': record.thread,
            'process': record.process
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields
        if hasattr(record, 'extra_data'):
            log_entry['extra'] = record.extra_data
        
        return json.dumps(log_entry)

class PerformanceFilter(logging.Filter):
    """Filter to add performance metrics to log records"""
    
    def filter(self, record):
        # Add performance context if available
        if hasattr(record, 'duration'):
            record.msg = f"[{record.duration:.3f}s] {record.msg}"
        return True

class SpotifyRecommendationLogger:
    """Advanced logging setup for the Spotify Recommendation System"""
    
    def __init__(self, app_name="spotify_recommender"):
        self.app_name = app_name
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        
        # Configuration from environment
        self.log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        self.enable_file_logging = os.getenv('ENABLE_FILE_LOGGING', 'true').lower() == 'true'
        self.enable_json_logging = os.getenv('ENABLE_JSON_LOGGING', 'false').lower() == 'true'
        self.enable_performance_logging = os.getenv('ENABLE_PERFORMANCE_LOGGING', 'true').lower() == 'true'
        self.max_log_files = int(os.getenv('MAX_LOG_FILES', '30'))
        self.max_log_size_mb = int(os.getenv('MAX_LOG_SIZE_MB', '50'))
        
        self.logger = None
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup comprehensive logging configuration"""
        # Create root logger
        self.logger = logging.getLogger(self.app_name)
        self.logger.setLevel(getattr(logging, self.log_level, logging.INFO))
        
        # Clear existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Create formatters
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(module)s.%(funcName)s:%(lineno)d - %(process)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        json_formatter = StructuredFormatter(include_json=True)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.INFO)
        if self.enable_performance_logging:
            console_handler.addFilter(PerformanceFilter())
        self.logger.addHandler(console_handler)
        
        if self.enable_file_logging:
            # Main application log with rotation
            app_log_file = self.log_dir / f"{self.app_name}.log"
            app_handler = logging.handlers.RotatingFileHandler(
                app_log_file,
                maxBytes=self.max_log_size_mb * 1024 * 1024,
                backupCount=self.max_log_files
            )
            app_handler.setFormatter(file_formatter)
            app_handler.setLevel(logging.DEBUG)
            if self.enable_performance_logging:
                app_handler.addFilter(PerformanceFilter())
            self.logger.addHandler(app_handler)
            
            # Error-only log
            error_log_file = self.log_dir / f"{self.app_name}_errors.log"
            error_handler = logging.handlers.RotatingFileHandler(
                error_log_file,
                maxBytes=self.max_log_size_mb * 1024 * 1024,
                backupCount=self.max_log_files
            )
            error_handler.setFormatter(file_formatter)
            error_handler.setLevel(logging.ERROR)
            self.logger.addHandler(error_handler)
            
            # Performance log (if enabled)
            if self.enable_performance_logging:
                perf_log_file = self.log_dir / f"{self.app_name}_performance.log"
                perf_handler = logging.handlers.RotatingFileHandler(
                    perf_log_file,
                    maxBytes=self.max_log_size_mb * 1024 * 1024,
                    backupCount=self.max_log_files
                )
                perf_handler.setFormatter(file_formatter)
                perf_handler.setLevel(logging.DEBUG)
                perf_handler.addFilter(self._create_performance_filter())
                self.logger.addHandler(perf_handler)
            
            # JSON structured log (if enabled)
            if self.enable_json_logging:
                json_log_file = self.log_dir / f"{self.app_name}_structured.json"
                json_handler = logging.handlers.RotatingFileHandler(
                    json_log_file,
                    maxBytes=self.max_log_size_mb * 1024 * 1024,
                    backupCount=self.max_log_files
                )
                json_handler.setFormatter(json_formatter)
                json_handler.setLevel(logging.DEBUG)
                self.logger.addHandler(json_handler)
    
    def _create_performance_filter(self):
        """Create filter for performance-related logs"""
        class PerfFilter(logging.Filter):
            def filter(self, record):
                # Only log messages containing performance indicators
                return any(keyword in record.getMessage().lower() for keyword in 
                          ['loading', 'loaded', 'processing', 'generated', 'time', 'duration', 'ms', 'seconds'])
        return PerfFilter()
    
    def get_logger(self, name=None):
        """Get a logger instance"""
        if name:
            return logging.getLogger(f"{self.app_name}.{name}")
        return self.logger
    
    def log_user_action(self, action: str, details: Dict[str, Any] = None):
        """Log user actions with structured data"""
        logger = self.get_logger("user_actions")
        extra_data = {
            'action_type': 'user_interaction',
            'action': action,
            'timestamp': datetime.now().isoformat()
        }
        if details:
            extra_data.update(details)
        
        # Create a log record with extra data
        record = logging.LogRecord(
            name=logger.name,
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg=f"User action: {action}",
            args=(),
            exc_info=None
        )
        record.extra_data = extra_data
        logger.handle(record)
    
    def log_performance(self, operation: str, duration: float, details: Dict[str, Any] = None):
        """Log performance metrics"""
        logger = self.get_logger("performance")
        extra_data = {
            'operation_type': 'performance',
            'operation': operation,
            'duration_seconds': duration,
            'timestamp': datetime.now().isoformat()
        }
        if details:
            extra_data.update(details)
        
        record = logging.LogRecord(
            name=logger.name,
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg=f"Performance: {operation} completed in {duration:.3f}s",
            args=(),
            exc_info=None
        )
        record.duration = duration
        record.extra_data = extra_data
        logger.handle(record)
    
    def log_spotify_api_call(self, endpoint: str, success: bool, response_time: float = None, details: Dict[str, Any] = None):
        """Log Spotify API calls"""
        logger = self.get_logger("spotify_api")
        level = logging.INFO if success else logging.WARNING
        
        extra_data = {
            'api_type': 'spotify',
            'endpoint': endpoint,
            'success': success,
            'timestamp': datetime.now().isoformat()
        }
        
        if response_time:
            extra_data['response_time_seconds'] = response_time
        
        if details:
            extra_data.update(details)
        
        message = f"Spotify API {endpoint}: {'SUCCESS' if success else 'FAILED'}"
        if response_time:
            message += f" ({response_time:.3f}s)"
        
        record = logging.LogRecord(
            name=logger.name,
            level=level,
            pathname="",
            lineno=0,
            msg=message,
            args=(),
            exc_info=None
        )
        record.extra_data = extra_data
        if response_time:
            record.duration = response_time
        logger.handle(record)
    
    def log_recommendation_generation(self, method: str, song_idx: int, num_recommendations: int, 
                                    processing_time: float, details: Dict[str, Any] = None):
        """Log recommendation generation events"""
        logger = self.get_logger("recommendations")
        
        extra_data = {
            'recommendation_type': method,
            'input_song_index': song_idx,
            'num_recommendations': num_recommendations,
            'processing_time_seconds': processing_time,
            'timestamp': datetime.now().isoformat()
        }
        
        if details:
            extra_data.update(details)
        
        record = logging.LogRecord(
            name=logger.name,
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg=f"Generated {num_recommendations} {method} recommendations for song {song_idx} in {processing_time:.3f}s",
            args=(),
            exc_info=None
        )
        record.duration = processing_time
        record.extra_data = extra_data
        logger.handle(record)
    
    def get_log_stats(self):
        """Get logging statistics"""
        stats = {
            'log_directory': str(self.log_dir),
            'log_level': self.log_level,
            'file_logging_enabled': self.enable_file_logging,
            'json_logging_enabled': self.enable_json_logging,
            'performance_logging_enabled': self.enable_performance_logging,
            'handlers': len(self.logger.handlers),
            'log_files': []
        }
        
        if self.log_dir.exists():
            for log_file in self.log_dir.glob("*.log*"):
                stats['log_files'].append({
                    'name': log_file.name,
                    'size_mb': log_file.stat().st_size / (1024 * 1024),
                    'modified': datetime.fromtimestamp(log_file.stat().st_mtime).isoformat()
                })
        
        return stats

# Global logger instance
_logger_instance = None

def get_logger(name=None):
    """Get the global logger instance"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = SpotifyRecommendationLogger()
    return _logger_instance.get_logger(name)

def setup_logging():
    """Setup logging and return the main logger"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = SpotifyRecommendationLogger()
    return _logger_instance.get_logger()

def log_user_action(action: str, details: Dict[str, Any] = None):
    """Convenience function for logging user actions"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = SpotifyRecommendationLogger()
    _logger_instance.log_user_action(action, details)

def log_performance(operation: str, duration: float, details: Dict[str, Any] = None):
    """Convenience function for logging performance metrics"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = SpotifyRecommendationLogger()
    _logger_instance.log_performance(operation, duration, details)

def log_spotify_api_call(endpoint: str, success: bool, response_time: float = None, details: Dict[str, Any] = None):
    """Convenience function for logging Spotify API calls"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = SpotifyRecommendationLogger()
    _logger_instance.log_spotify_api_call(endpoint, success, response_time, details)

def log_recommendation_generation(method: str, song_idx: int, num_recommendations: int, 
                                processing_time: float, details: Dict[str, Any] = None):
    """Convenience function for logging recommendation generation"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = SpotifyRecommendationLogger()
    _logger_instance.log_recommendation_generation(method, song_idx, num_recommendations, processing_time, details)

def get_log_stats():
    """Get logging statistics"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = SpotifyRecommendationLogger()
    return _logger_instance.get_log_stats() 