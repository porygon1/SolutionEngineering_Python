"""
UI components package for Spotify Music Recommendation.
Spotify-inspired modular components for the music recommendation system.
"""

# Core components for the Spotify-like interface
try:
    from .sidebar import render_sidebar
except ImportError:
    render_sidebar = None

try:
    from .track_grid import render_track_grid, render_track_card, render_track_list_view
except ImportError:
    render_track_grid = None
    render_track_card = None
    render_track_list_view = None

try:
    from .music_player import render_bottom_player, render_mini_player
except ImportError:
    render_bottom_player = None
    render_mini_player = None

try:
    from .recommendations import render_recommendations_section, generate_recommendations
except ImportError:
    render_recommendations_section = None
    generate_recommendations = None

# Legacy components (for backward compatibility)
try:
    from .music_player import render_complete_music_player
except ImportError:
    render_complete_music_player = None

try:
    from .recommendation_cards import (
        render_enhanced_recommendations_grid,
        create_recommendation_comparison_chart,
        create_recommendation_insights
    )
except ImportError:
    render_enhanced_recommendations_grid = None
    create_recommendation_comparison_chart = None
    create_recommendation_insights = None

__all__ = [
    # Main Spotify-like components
    'render_sidebar',
    'render_track_grid',
    'render_track_card', 
    'render_track_list_view',
    'render_bottom_player',
    'render_mini_player',
    'render_recommendations_section',
    'generate_recommendations',
    
    # Legacy components (backward compatibility)
    'render_complete_music_player',
    'render_enhanced_recommendations_grid',
    'create_recommendation_comparison_chart',
    'create_recommendation_insights'
] 