"""
UI components package for the Spotify Music Recommendation System.
"""

from .track_cards import (
    create_spotify_track_card, display_simple_card, create_detailed_view,
    display_recommendations_with_cards
)
from .search_interface import (
    create_song_search_interface, create_advanced_search_interface,
    create_searchable_song_index, fuzzy_search_songs
)
from .audio_player import display_audio_player
from .notifications import (
    create_streamlit_notification, show_success_message, show_info_message,
    show_warning_message, show_error_message
)
from .dashboard import (
    create_logging_dashboard, create_app_footer, create_sidebar_controls,
    display_audio_preview_analysis, search_song_by_name
)

__all__ = [
    # Track cards
    'create_spotify_track_card',
    'display_simple_card', 
    'create_detailed_view',
    'display_recommendations_with_cards',
    
    # Search interface
    'create_song_search_interface',
    'create_advanced_search_interface',
    'create_searchable_song_index',
    'fuzzy_search_songs',
    
    # Audio player
    'display_audio_player',
    
    # Notifications
    'create_streamlit_notification',
    'show_success_message',
    'show_info_message',
    'show_warning_message',
    'show_error_message',
    
    # Dashboard
    'create_logging_dashboard',
    'create_app_footer',
    'create_sidebar_controls',
    'display_audio_preview_analysis',
    'search_song_by_name'
] 