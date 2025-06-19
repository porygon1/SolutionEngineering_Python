"""
UI components package for Spotify Music Recommendation System
"""

# UI Components
from .sidebar import render_sidebar
from .track_grid import render_track_grid, render_track_list_view
from .music_player import render_bottom_player, get_album_artwork
from .recommendations import render_recommendations_section, render_compact_recommendations_section, get_album_cover

# Search Optimization
from .search_optimization import (
    create_optimized_search_index,
    vectorized_search,
    get_top_suggestions,
    create_genre_filters,
    apply_advanced_filters,
    get_autocomplete_suggestions,
    get_available_genres
)

__all__ = [
    # UI Components
    'render_sidebar',
    'render_track_grid',
    'render_track_list_view',
    'render_bottom_player',
    'render_recommendations_section',
    'render_compact_recommendations_section',
    'get_album_artwork',
    'get_album_cover',
    
    # Search Optimization
    'create_optimized_search_index',
    'vectorized_search',
    'get_top_suggestions',
    'create_genre_filters',
    'apply_advanced_filters',
    'get_autocomplete_suggestions',
    'get_available_genres'
] 