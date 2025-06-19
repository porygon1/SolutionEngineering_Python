"""
🎵 Spotify Music Recommendation - Modern Music Discovery System
AI-powered music recommendation system with Spotify Web API integration
"""

import streamlit as st
import pandas as pd
import numpy as np
import time
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging

# Import core utilities
from utils.data_utils import load_data, load_all_models, create_artist_mapping, get_artist_name
from utils.recommendations import get_recommendations_within_cluster, get_global_recommendations
from utils.analytics import UserAnalytics
from utils.formatting import format_duration, get_key_name, get_mode_name
from utils.styles import initialize_app_styles

# Import new state management and caching
from utils.state_manager import state_manager
from utils.enhanced_cache import (
    enhanced_cache, cached_search_operation, cached_recommendations,
    cached_data_processing, get_cache_statistics, cleanup_expired_caches
)
from utils.performance_monitor import (
    monitor_performance, track_user_interaction, render_performance_dashboard
)

# Import UI components
from components.sidebar import render_sidebar
from components.track_grid import render_track_grid, render_track_list_view
from components.recommendations import render_recommendations_section, render_compact_recommendations_section
from components.music_player import render_bottom_player
from components.search_optimization import (
    create_optimized_search_index,
    vectorized_search,
    get_top_suggestions,
    create_genre_filters,
    apply_advanced_filters,
    get_autocomplete_suggestions,
    get_available_genres
)

# Set page config for wide layout
st.set_page_config(
    page_title="🎵 Spotify Music Recommendation",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize custom styles from external CSS file
initialize_app_styles()

class SpotifyLikeApp:
    """Spotify-inspired Music Discovery Application"""
    
    def __init__(self):
        self.setup_paths()
        # Use centralized state management instead of manual initialization
        self.state_manager = state_manager
        self.setup_spotify_client()
        self.load_data()
        self.analytics = UserAnalytics()
        
        # Clean up expired caches on startup
        cleanup_expired_caches()
    
    def setup_paths(self):
        """Setup data and model paths for Docker compatibility"""
        base_path = os.getenv('DATA_PATH', '/app/data')
        if not os.path.exists(base_path):
            # For local development, use the correct relative path from Legacy/streamlit_app to data
            base_path = os.getenv('DATA_PATH', '../../data')
        
        self.DATA_PATH = base_path
        self.RAW_DATA_PATH = os.path.join(self.DATA_PATH, "raw")
        self.MODELS_PATH = os.path.join(self.DATA_PATH, "models")
        
        self.TRACKS_CSV = os.path.join(self.RAW_DATA_PATH, "spotify_tracks.csv")
        self.ARTISTS_CSV = os.path.join(self.RAW_DATA_PATH, "spotify_artists.csv")
        
        self.MODEL_PATHS = {
            "hdbscan": os.path.join(self.MODELS_PATH, "hdbscan_model.pkl"),
            "knn": os.path.join(self.MODELS_PATH, "knn_model.pkl"),
            "embeddings": os.path.join(self.MODELS_PATH, "audio_embeddings.pkl"),
            "labels": os.path.join(self.MODELS_PATH, "cluster_labels.pkl"),
            "song_indices": os.path.join(self.MODELS_PATH, "song_indices.pkl")
        }
        
        logger.info(f"Data paths configured - BASE: {base_path}")
    
    def setup_spotify_client(self):
        """Setup Spotify API client if available"""
        self.spotify_client = None
        self.spotify_available = False
        
        try:
            from spotify_api_client import create_spotify_client
            self.spotify_client = create_spotify_client()
            if self.spotify_client:
                self.spotify_available = True
                logger.info("Spotify API client initialized successfully")
            else:
                logger.warning("Spotify API client initialization returned None")
        except ImportError as e:
            logger.info(f"Spotify API client not available: {e}")
        except Exception as e:
            logger.warning(f"Error initializing Spotify client: {e}")
    
    @enhanced_cache(ttl=3600)
    @monitor_performance()
    def load_data(self):
        """Load music data and models with enhanced caching"""
        try:
            # Use cached data processing
            self.tracks_df = cached_data_processing(self.TRACKS_CSV, 'tracks')
            self.artists_df = cached_data_processing(self.ARTISTS_CSV, 'artists')
            
            # Extract first artist id for each track (handle string or list)
            def extract_first_artist_id(artists_id):
                if isinstance(artists_id, str):
                    # If comma-separated string, take the first
                    return artists_id.split(',')[0].strip()
                elif isinstance(artists_id, list) and artists_id:
                    return artists_id[0]
                return None
            self.tracks_df['main_artist_id'] = self.tracks_df['artists_id'].apply(extract_first_artist_id)
            
            # Join tracks with artists data for genres
            self.tracks_df = self.tracks_df.merge(
                self.artists_df[['id', 'genres']],
                left_on='main_artist_id',
                right_on='id',
                how='left',
                suffixes=('', '_artist')
            )
            
            self.artist_mapping = create_artist_mapping(self.artists_df)
            self.models = load_all_models(self.MODEL_PATHS)
            
            # Initialize optimized search index
            self.search_index = create_optimized_search_index(self.tracks_df, self.artist_mapping)
            
            # Initialize featured tracks using state manager
            if not self.state_manager.get_state('featured_tracks'):
                self.generate_featured_tracks()
                
            logger.info(f"Data loaded - Tracks: {len(self.tracks_df)}, Artists: {len(self.artist_mapping)}")
            
        except Exception as e:
            st.error(f"❌ Error loading data: {e}")
            logger.error(f"Data loading error: {e}")
            self.tracks_df = pd.DataFrame()
            self.artists_df = pd.DataFrame()
            self.artist_mapping = {}
            self.models = {}
            self.search_index = pd.DataFrame()
    
    def generate_featured_tracks(self):
        """Generate a selection of featured tracks using state manager"""
        if not self.tracks_df.empty:
            # Select diverse featured tracks
            popular_tracks = self.tracks_df.nlargest(20, 'popularity')
            danceable_tracks = self.tracks_df.nlargest(10, 'danceability')
            energetic_tracks = self.tracks_df.nlargest(10, 'energy')
            
            # Combine and shuffle
            featured_indices = list(set(
                list(popular_tracks.index[:8]) + 
                list(danceable_tracks.index[:4]) + 
                list(energetic_tracks.index[:4])
            ))
            
            np.random.shuffle(featured_indices)
            self.state_manager.set_state('featured_tracks', featured_indices[:12])
    
    def render_sidebar(self):
        """Render the left sidebar navigation (no search bar)"""
        render_sidebar(self, show_search=False)
    
    def render_main_header(self):
        """Render the main application header"""
        st.markdown("""
        <div class="spotify-header">
            <h1>🎵 Spotify Music Recommendation</h1>
            <p class="subtitle">Powered by HDBSCAN + K-means clustering with audio feature analysis</p>
        </div>
        """, unsafe_allow_html=True)
    
    def render_featured_tracks(self):
        """Render the featured tracks grid"""
        st.markdown("## 🎵 Featured Tracks")
        
        if self.state_manager.get_state('featured_tracks') and not self.tracks_df.empty:
            featured_tracks_data = self.tracks_df.iloc[self.state_manager.get_state('featured_tracks')]
            render_track_grid(
                featured_tracks_data, 
                self.artist_mapping, 
                self.spotify_client,
                grid_id="featured"
            )
        else:
            st.info("Loading featured tracks...")
    
    def on_search_suggestion_click(self, suggestion):
        """Callback for search suggestion clicks using state manager"""
        self.state_manager.update_search_state(suggestion, [], [])
        self.perform_search(suggestion)
    
    def on_filter_change(self):
        """Callback for filter changes using state manager"""
        current_query = self.state_manager.get_state('search_query')
        if current_query:
            self.perform_search(current_query)
    
    @monitor_performance()
    def perform_search(self, query):
        """Perform search with current filters using enhanced caching"""
        try:
            # Track user interaction
            track_user_interaction('search', query=query, query_length=len(query))
            
            # Get current filters from state manager
            current_filters = self.state_manager.get_state('filters')
            
            # Use cached search operation
            filtered_results = cached_search_operation(
                query, 
                self.search_index, 
                current_filters
            )
            
            # Update state using state manager
            self.state_manager.update_search_state(query, filtered_results)
            
            # Track search analytics
            self.analytics.track_search(query, len(filtered_results), current_filters)
            
        except Exception as e:
            logger.error(f"Error performing search: {e}")
            st.error(f"Search error: {e}")
    
    def render_search_section(self):
        """Render enhanced search section with auto-complete using state manager"""
        st.markdown("### 🔍 Search Music")
        
        # Get current search query from state
        current_query = self.state_manager.get_state('search_query', '')
        
        # Search input with auto-complete - use callback to avoid session state modification
        search_query = st.text_input(
            "Search tracks or artists",
            value=current_query,
            placeholder="Type to search...",
            key="main_search_input",
            label_visibility="collapsed"
        )
        
        # Only perform search if query changed
        if search_query != current_query and search_query:
            track_user_interaction('search_input', query=search_query)
            self.perform_search(search_query)
        
        # Show auto-complete suggestions
        if search_query and len(search_query) >= 2:
            suggestions = get_autocomplete_suggestions(search_query, self.search_index)
            if suggestions:
                st.markdown("**Suggestions:**")
                # Display suggestions in one row
                suggestion_cols = st.columns(len(suggestions))
                for i, suggestion in enumerate(suggestions):
                    with suggestion_cols[i]:
                        if st.button(suggestion, key=f"sugg_{i}_{suggestion}", use_container_width=True):
                            # Track suggestion click
                            track_user_interaction('suggestion_click', suggestion=suggestion)
                            # Use rerun instead of direct state modification
                            st.query_params.search = suggestion
                            st.rerun()
        
        # Advanced filters using state manager
        with st.expander("🔍 Advanced Filters", expanded=False):
            col1, col2 = st.columns(2)
            
            current_filters = self.state_manager.get_state('filters')
            
            with col1:
                # Year range filter
                year_range = st.slider(
                    "Release Year",
                    min_value=1950,
                    max_value=2024,
                    value=current_filters['year_range'],
                    key="year_range_filter"
                )
                
                # Genre filter
                genres = st.multiselect(
                    "Genres",
                    options=get_available_genres(self.tracks_df),
                    default=current_filters['genres'],
                    key="genre_filter"
                )
            
            with col2:
                # Audio feature filters
                danceability = st.slider(
                    "Danceability", 
                    0.0, 1.0, 
                    value=current_filters['danceability'],
                    key="danceability_filter"
                )
                energy = st.slider(
                    "Energy", 
                    0.0, 1.0, 
                    value=current_filters['energy'],
                    key="energy_filter"
                )
                popularity = st.slider(
                    "Popularity", 
                    0, 100, 
                    value=current_filters['popularity'],
                    key="popularity_filter"
                )
            
            # Update filters if they changed
            new_filters = {
                'year_range': year_range,
                'genres': genres,
                'danceability': danceability,
                'energy': energy,
                'popularity': popularity
            }
            
            if new_filters != current_filters:
                track_user_interaction('filter_change', filters=new_filters)
                self.state_manager.update_filter_state(new_filters)
                if search_query:
                    self.perform_search(search_query)
    
    @monitor_performance()
    def render_search_results(self):
        """Render enhanced search results using state manager"""
        search_results = self.state_manager.get_state('search_results')
        
        if search_results is not None and len(search_results) > 0:
            st.markdown("## 🔍 Search Results")
            
            # Results summary
            st.markdown(f"Found {len(search_results)} tracks")
            
            # View options using state manager
            current_view_mode = self.state_manager.get_state('view_mode')
            view_mode = st.radio(
                "View Mode",
                ["Grid", "List"],
                index=0 if current_view_mode == "Grid" else 1,
                horizontal=True,
                key="view_mode_radio"
            )
            
            # Sort options using state manager
            current_sort_by = self.state_manager.get_state('sort_by')
            sort_by = st.selectbox(
                "Sort by",
                ["Relevance", "Popularity", "Year", "Duration"],
                index=["Relevance", "Popularity", "Year", "Duration"].index(current_sort_by),
                key="sort_by_select"
            )
            
            # Update UI state if changed
            if view_mode != current_view_mode or sort_by != current_sort_by:
                track_user_interaction('ui_change', view_mode=view_mode, sort_by=sort_by)
                self.state_manager.update_ui_state(view_mode=view_mode, sort_by=sort_by)
            
            # Convert results to DataFrame for sorting
            results_df = pd.DataFrame(search_results)
            
            # Apply sorting
            if sort_by == "Popularity":
                results_df = results_df.sort_values('popularity', ascending=False)
            elif sort_by == "Year":
                results_df = results_df.sort_values('year', ascending=False)
            elif sort_by == "Duration":
                results_df = results_df.sort_values('duration_ms', ascending=False)
            # Relevance is already sorted by score
            
            # Render results - check if we're in a nested context
            has_recommendations = self.state_manager.get_state('selected_track_idx') is not None
            show_full_recommendations = st.session_state.get('show_full_recommendations', False)
            is_nested = has_recommendations and not show_full_recommendations
            
            if view_mode == "Grid":
                render_track_grid(
                    results_df,
                    self.artist_mapping,
                    self.spotify_client,
                    grid_id="search",
                    nested=is_nested
                )
            else:
                render_track_list_view(
                    results_df,
                    self.artist_mapping,
                    self.spotify_client,
                    list_id="search"
                )
    
    @monitor_performance()
    def render_recommendations(self):
        """Render recommendations with analytics tracking using state manager"""
        selected_track_idx = self.state_manager.get_state('selected_track_idx')
        
        if selected_track_idx is not None:
            # Use cached recommendations
            num_recommendations = self.state_manager.get_state('num_recommendations')
            recommendation_type = self.state_manager.get_state('recommendation_type')
            
            try:
                recommendations = cached_recommendations(
                    selected_track_idx,
                    self.tracks_df,
                    self.models,
                    num_recommendations,
                    recommendation_type
                )
                
                render_recommendations_section(
                    self.tracks_df,
                    self.artist_mapping,
                    self.models,
                    selected_track_idx,
                    self.spotify_client,
                    num_recommendations,
                    recommendation_type
                )
            except Exception as e:
                logger.error(f"Error rendering recommendations: {e}")
                st.error(f"Recommendation error: {e}")
    
    @monitor_performance()
    def render_compact_recommendations(self):
        """Render compact recommendations optimized for column layout using state manager"""
        selected_track_idx = self.state_manager.get_state('selected_track_idx')
        
        if selected_track_idx is not None:
            # Use cached recommendations
            num_recommendations = min(8, self.state_manager.get_state('num_recommendations'))  # Limit to 8 for compact view
            recommendation_type = self.state_manager.get_state('recommendation_type')
            
            try:
                recommendations = cached_recommendations(
                    selected_track_idx,
                    self.tracks_df,
                    self.models,
                    num_recommendations,
                    recommendation_type
                )
                
                render_compact_recommendations_section(
                    self.tracks_df,
                    self.artist_mapping,
                    self.models,
                    selected_track_idx,
                    self.spotify_client,
                    num_recommendations,
                    recommendation_type
                )
            except Exception as e:
                logger.error(f"Error rendering compact recommendations: {e}")
                st.error(f"Compact recommendation error: {e}")
    
    def render_now_playing(self):
        """Render the now playing section with analytics using state manager"""
        current_track = self.state_manager.get_state('current_track')
        
        if current_track is not None:
            try:
                track = self.tracks_df.iloc[current_track]
                
                # Track play duration (keep for analytics, but don't pass to player)
                def on_play_end(duration):
                    self.analytics.track_play(current_track, duration)
                
                # Remove on_play_end argument from the call
                render_bottom_player(track, self.artist_mapping, self.spotify_client)
            except Exception as e:
                logger.error(f"Error rendering now playing: {e}")
    
    def render_analytics_dashboard(self):
        """Render analytics dashboard in sidebar using enhanced cache stats"""
        with st.sidebar:
            st.markdown("### 📊 Analytics & Performance")
            
            # Tabs for different analytics
            tab1, tab2 = st.tabs(["📈 Cache & Search", "🚀 Performance"])
            
            with tab1:
                # Enhanced cache statistics
                cache_stats = get_cache_statistics()
                st.markdown("**Enhanced Cache Statistics:**")
                st.json(cache_stats)
                
                # Popular searches from state manager
                analytics_data = self.state_manager.get_analytics_data()
                search_history = analytics_data.get('search_history', [])
                
                if search_history:
                    st.markdown("**Recent Searches:**")
                    for search in search_history[-5:]:  # Show last 5
                        query = search.get('query', 'Unknown')
                        count = search.get('results_count', 0)
                        st.markdown(f"- {query} ({count} results)")
                
                # State summary for debugging
                if st.checkbox("Show Debug Info"):
                    state_summary = self.state_manager.get_state_summary()
                    st.markdown("**State Summary:**")
                    st.json(state_summary)
            
            with tab2:
                # Performance monitoring dashboard
                render_performance_dashboard()
    
    @monitor_performance()
    def run(self):
        """Main application runner with enhanced error handling and improved layout"""
        logger.info("Starting Spotify-like Music Discovery App")
        
        # Track app start
        track_user_interaction('app_start')
        
        # Handle URL parameters for search
        if 'search' in st.query_params:
            search_param = st.query_params.search
            current_query = self.state_manager.get_state('search_query')
            if search_param != current_query:
                track_user_interaction('url_search', query=search_param)
                self.perform_search(search_param)
        
        if self.tracks_df.empty:
            st.error("❌ Could not load track data. Please check data files.")
            return
        
        # Render sidebar with analytics
        self.render_sidebar()
        self.render_analytics_dashboard()
        
        # Main content area with padding for fixed player
        st.markdown('<div class="main-content">', unsafe_allow_html=True)
        
        # Render main header
        self.render_main_header()
        
        # Check if we have recommendations to show
        selected_track_idx = self.state_manager.get_state('selected_track_idx')
        has_recommendations = selected_track_idx is not None
        show_full_recommendations = st.session_state.get('show_full_recommendations', False)
        
        # Create layout based on whether we have recommendations
        if has_recommendations and not show_full_recommendations:
            # Split layout: Main content on left, Recommendations on right
            main_col, rec_col = st.columns([2, 1])
            
            with main_col:
                st.markdown("### 🎵 Music Discovery")
                # Render enhanced search
                self.render_search_section()
                
                # Render search results if any
                search_results = self.state_manager.get_state('search_results')
                if search_results is not None and len(search_results) > 0:
                    self.render_search_results()
                else:
                    # Show a condensed version of featured tracks
                    self.render_condensed_featured_tracks()
            
            with rec_col:
                # Render compact recommendations in the right column
                self.render_compact_recommendations()
        elif has_recommendations and show_full_recommendations:
            # Full width layout for detailed recommendations
            # Add button to go back to split view
            if st.button("◀️ Back to Split View", type="secondary"):
                st.session_state.show_full_recommendations = False
                st.rerun()
            
            # Render full recommendations
            self.render_recommendations()
            
            # Clear the flag after rendering
            if st.button("🎵 Continue Browsing", use_container_width=True):
                st.session_state.show_full_recommendations = False
                st.rerun()
        else:
            # Full width layout when no recommendations
            # Render enhanced search
            self.render_search_section()
            
            # Render search results if any
            search_results = self.state_manager.get_state('search_results')
            if search_results is not None and len(search_results) > 0:
                self.render_search_results()
            else:
                # Render featured tracks if no search results
                self.render_featured_tracks()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Render now playing at the bottom (fixed position)
        self.render_now_playing()
        
        # Footer
        self.render_footer()
        
        # Cleanup old state periodically (every 100 runs)
        if np.random.randint(0, 100) == 0:
            self.state_manager.cleanup_old_state()
    
    def render_condensed_featured_tracks(self):
        """Render a condensed version of featured tracks for split layout"""
        st.markdown("#### 🎵 Featured Tracks")
        
        if self.state_manager.get_state('featured_tracks') and not self.tracks_df.empty:
            # Show only 6 tracks in condensed view
            featured_indices = self.state_manager.get_state('featured_tracks')[:6]
            featured_tracks_data = self.tracks_df.iloc[featured_indices]
            
            # Render in a more compact grid (2 columns instead of 3-4)
            render_track_grid(
                featured_tracks_data, 
                self.artist_mapping, 
                self.spotify_client,
                grid_id="featured_condensed",
                cols=2,
                nested=True
            )
            
            # Add button to view all featured tracks
            if st.button("🎵 View All Featured Tracks", use_container_width=True):
                # Clear recommendations to show full featured tracks
                self.state_manager.set_state('selected_track_idx', None)
                st.rerun()
        else:
            st.info("Loading featured tracks...")

    def render_footer(self):
        """Render the app footer"""
        st.markdown("""
        <div class="app-footer">
            <p>Built with ❤️ using Streamlit and Spotify API</p>
        </div>
        """, unsafe_allow_html=True)


def main():
    """Main function to run the Spotify-like Music Discovery App"""
    app = SpotifyLikeApp()
    app.run()


if __name__ == "__main__":
    main() 