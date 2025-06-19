"""
Utilities package for Spotify Music Recommendation System
"""

# Core utilities
from .data_utils import load_data, load_all_models, create_artist_mapping, get_artist_name
from .formatting import format_duration, get_key_name, get_mode_name
from .styles import initialize_app_styles

# State management
from .state_manager import AppStateManager, state_manager

# Enhanced caching
from .enhanced_cache import (
    EnhancedCacheManager, enhanced_cache, cache_manager,
    cached_search_operation, cached_recommendations, cached_data_processing,
    cached_genre_analysis, cached_audio_features_analysis,
    optimize_dataframe_memory, chunk_dataframe_processing,
    clear_all_caches, get_cache_statistics, cleanup_expired_caches
)

# Performance monitoring
from .performance_monitor import (
    PerformanceMonitor, performance_monitor, monitor_performance,
    track_user_interaction, get_performance_dashboard_data,
    optimize_memory, render_performance_dashboard
)

# Recommendation utilities
from .recommendations import get_recommendations_within_cluster, get_global_recommendations

# Analytics
from .analytics import UserAnalytics

# Legacy caching (for backward compatibility)
from .cache_utils import cache_with_timeout, cache_dataframe, get_cache_stats

# Search optimization (moved to components)
from components.search_optimization import (
    create_optimized_search_index,
    vectorized_search,
    get_top_suggestions,
    create_genre_filters,
    apply_advanced_filters,
    get_autocomplete_suggestions,
    get_available_genres
)

# Music player utilities (moved to components)
from components.music_player import get_album_artwork
from components.recommendations import get_album_cover

__all__ = [
    # Core utilities
    'load_data',
    'load_all_models',
    'create_artist_mapping',
    'get_artist_name',
    'format_duration',
    'get_key_name',
    'get_mode_name',
    'initialize_app_styles',
    
    # State management
    'AppStateManager',
    'state_manager',
    
    # Enhanced caching
    'EnhancedCacheManager',
    'enhanced_cache',
    'cache_manager',
    'cached_search_operation',
    'cached_recommendations',
    'cached_data_processing',
    'cached_genre_analysis',
    'cached_audio_features_analysis',
    'optimize_dataframe_memory',
    'chunk_dataframe_processing',
    'clear_all_caches',
    'get_cache_statistics',
    'cleanup_expired_caches',
    
    # Recommendation utilities
    'get_recommendations_within_cluster',
    'get_global_recommendations',
    
    # Analytics
    'UserAnalytics',
    
    # Legacy caching
    'cache_with_timeout',
    'cache_dataframe',
    'get_cache_stats',
    
    # Search optimization
    'create_optimized_search_index',
    'vectorized_search',
    'get_top_suggestions',
    'create_genre_filters',
    'apply_advanced_filters',
    'get_autocomplete_suggestions',
    'get_available_genres',
    
    # Music player
    'get_album_artwork',
    'get_album_cover',
    
    # Performance monitoring
    'PerformanceMonitor',
    'performance_monitor',
    'monitor_performance',
    'track_user_interaction',
    'get_performance_dashboard_data',
    'optimize_memory',
    'render_performance_dashboard'
] 