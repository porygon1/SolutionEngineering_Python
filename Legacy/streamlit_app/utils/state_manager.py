"""
Centralized State Management for Spotify Music Recommendation System
Handles all session state operations safely and efficiently
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Optional, Any, Callable
import logging

logger = logging.getLogger(__name__)

class AppStateManager:
    """Centralized state management for the Spotify app"""
    
    # Default values for all session state variables
    DEFAULT_STATE = {
        # Track and playback state
        'current_track': None,
        'selected_track_idx': None,
        'is_playing': False,
        'shuffle_enabled': False,
        'repeat_enabled': False,
        'track_position': 0,
        'volume': 70,
        
        # Content state
        'featured_tracks': [],
        'recommendations': [],
        'search_results': [],
        'search_suggestions': [],
        'recent_tracks': [],
        
        # UI state
        'view_mode': "Grid",
        'sort_by': "Relevance",
        'num_recommendations': 12,
        'recommendation_type': "cluster",
        
        # Search and filter state
        'search_query': "",
        'filters': {
            'year_range': (1950, 2024),
            'genres': [],
            'danceability': (0.0, 1.0),
            'energy': (0.0, 1.0),
            'popularity': (0, 100)
        },
        
        # Analytics state
        'search_history': [],
        'recommendation_clicks': [],
        'play_history': [],
        
        # Cache state
        'last_search_time': 0,
        'last_recommendation_time': 0,
    }
    
    def __init__(self):
        """Initialize the state manager"""
        self.initialize_all_state()
    
    def initialize_all_state(self):
        """Initialize all session state variables with default values"""
        for key, default_value in self.DEFAULT_STATE.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
                logger.debug(f"Initialized session state: {key}")
    
    def get_state(self, key: str, default: Any = None) -> Any:
        """Safely get a session state value"""
        return st.session_state.get(key, default or self.DEFAULT_STATE.get(key))
    
    def set_state(self, key: str, value: Any, callback: Optional[Callable] = None):
        """Safely set a session state value with optional callback"""
        try:
            st.session_state[key] = value
            if callback:
                callback(key, value)
            logger.debug(f"Updated session state: {key}")
        except Exception as e:
            logger.error(f"Error setting session state {key}: {e}")
    
    def update_track_state(self, track_idx: Optional[int], is_playing: bool = False, 
                          is_selected: bool = False):
        """Update track-related state safely"""
        try:
            if track_idx is not None:
                if is_selected:
                    st.session_state.selected_track_idx = track_idx
                else:
                    st.session_state.current_track = track_idx
                
                st.session_state.is_playing = is_playing
                
                # Update recent tracks
                recent = st.session_state.get('recent_tracks', [])
                if track_idx not in recent:
                    recent.append(track_idx)
                    # Keep only last 10 tracks
                    st.session_state.recent_tracks = recent[-10:]
                
                logger.info(f"Updated track state: idx={track_idx}, playing={is_playing}")
        except Exception as e:
            logger.error(f"Error updating track state: {e}")
    
    def update_search_state(self, query: str, results: List[Dict], 
                           suggestions: Optional[List[str]] = None):
        """Update search-related state safely"""
        try:
            st.session_state.search_query = query
            st.session_state.search_results = results
            
            if suggestions:
                st.session_state.search_suggestions = suggestions
            
            # Update search history
            history = st.session_state.get('search_history', [])
            if query and query not in [h.get('query', '') for h in history]:
                history.append({
                    'query': query,
                    'results_count': len(results),
                    'timestamp': pd.Timestamp.now()
                })
                st.session_state.search_history = history[-20:]  # Keep last 20
            
            logger.info(f"Updated search state: query='{query}', results={len(results)}")
        except Exception as e:
            logger.error(f"Error updating search state: {e}")
    
    def update_filter_state(self, filters: Dict[str, Any]):
        """Update filter state safely"""
        try:
            current_filters = st.session_state.get('filters', {})
            current_filters.update(filters)
            st.session_state.filters = current_filters
            logger.debug(f"Updated filter state: {filters}")
        except Exception as e:
            logger.error(f"Error updating filter state: {e}")
    
    def update_ui_state(self, **kwargs):
        """Update UI-related state safely"""
        try:
            for key, value in kwargs.items():
                if key in ['view_mode', 'sort_by', 'num_recommendations', 'recommendation_type']:
                    st.session_state[key] = value
            logger.debug(f"Updated UI state: {kwargs}")
        except Exception as e:
            logger.error(f"Error updating UI state: {e}")
    
    def clear_search_state(self):
        """Clear search-related state"""
        try:
            st.session_state.search_query = ""
            st.session_state.search_results = []
            st.session_state.search_suggestions = []
            logger.info("Cleared search state")
        except Exception as e:
            logger.error(f"Error clearing search state: {e}")
    
    def clear_recommendations(self):
        """Clear recommendation state"""
        try:
            st.session_state.recommendations = []
            st.session_state.selected_track_idx = None
            logger.info("Cleared recommendations")
        except Exception as e:
            logger.error(f"Error clearing recommendations: {e}")
    
    def get_analytics_data(self) -> Dict[str, Any]:
        """Get analytics data safely"""
        return {
            'search_history': st.session_state.get('search_history', []),
            'recommendation_clicks': st.session_state.get('recommendation_clicks', []),
            'play_history': st.session_state.get('play_history', []),
            'recent_tracks': st.session_state.get('recent_tracks', [])
        }
    
    def cleanup_old_state(self, max_age_hours: int = 24):
        """Clean up old state data to prevent memory bloat"""
        try:
            current_time = pd.Timestamp.now()
            cutoff_time = current_time - pd.Timedelta(hours=max_age_hours)
            
            # Helper function to safely get timestamp
            def safe_get_timestamp(item, default_time):
                timestamp = item.get('timestamp', default_time)
                if isinstance(timestamp, str):
                    try:
                        return pd.Timestamp(timestamp)
                    except:
                        return default_time
                elif isinstance(timestamp, pd.Timestamp):
                    return timestamp
                else:
                    return default_time
            
            # Clean search history
            history = st.session_state.get('search_history', [])
            st.session_state.search_history = [
                h for h in history 
                if safe_get_timestamp(h, current_time) > cutoff_time
            ]
            
            # Clean recommendation clicks
            clicks = st.session_state.get('recommendation_clicks', [])
            st.session_state.recommendation_clicks = [
                c for c in clicks 
                if safe_get_timestamp(c, current_time) > cutoff_time
            ]
            
            # Clean play history
            plays = st.session_state.get('play_history', [])
            st.session_state.play_history = [
                p for p in plays 
                if safe_get_timestamp(p, current_time) > cutoff_time
            ]
            
            logger.info("Cleaned up old state data")
        except Exception as e:
            logger.error(f"Error cleaning up state: {e}")
    
    def reset_to_defaults(self):
        """Reset all state to default values"""
        try:
            for key, default_value in self.DEFAULT_STATE.items():
                st.session_state[key] = default_value
            logger.info("Reset all state to defaults")
        except Exception as e:
            logger.error(f"Error resetting state: {e}")
    
    def get_state_summary(self) -> Dict[str, Any]:
        """Get a summary of current state for debugging"""
        return {
            'current_track': st.session_state.get('current_track'),
            'selected_track_idx': st.session_state.get('selected_track_idx'),
            'search_results_count': len(st.session_state.get('search_results', [])),
            'recommendations_count': len(st.session_state.get('recommendations', [])),
            'featured_tracks_count': len(st.session_state.get('featured_tracks', [])),
            'view_mode': st.session_state.get('view_mode'),
            'is_playing': st.session_state.get('is_playing'),
            'search_query': st.session_state.get('search_query', '')[:50] + '...' if len(st.session_state.get('search_query', '')) > 50 else st.session_state.get('search_query', '')
        }

# Global instance
state_manager = AppStateManager() 