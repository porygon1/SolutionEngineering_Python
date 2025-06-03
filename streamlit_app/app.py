"""
Spotify Music Recommendation System - Refactored Main Application

A modern, modular implementation of the music recommendation system using
HDBSCAN clustering and KNN-based song discovery.
"""

import streamlit as st
import pandas as pd
import numpy as np
import os
import time
from datetime import datetime
from pathlib import Path

# Import modular components
from utils import (
    initialize_app_styles,
    load_data, load_all_models, create_artist_mapping, get_artist_name
)
from utils.recommendations import get_recommendations_within_cluster, get_global_recommendations
from components import (
    create_searchable_song_index, create_song_search_interface, create_advanced_search_interface,
    create_spotify_track_card, display_simple_card, display_recommendations_with_cards,
    display_audio_player, show_success_message, show_info_message, show_warning_message,
    create_sidebar_controls, create_app_footer, display_audio_preview_analysis, search_song_by_name
)

# Set page configuration
st.set_page_config(
    page_title="🎵 Spotify Music Recommendation System",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize logging
try:
    from logging_config import (
        setup_logging, get_logger, log_user_action, log_performance, 
        log_recommendation_generation
    )
    logger = setup_logging()
    ADVANCED_LOGGING = True
    logger.info("Advanced logging system initialized")
except ImportError:
    import logging
    import sys
    from pathlib import Path
    
    # Fallback to basic logging
    def setup_basic_logging():
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(log_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log")
            ]
        )
        return logging.getLogger(__name__)
    
    logger = setup_basic_logging()
    ADVANCED_LOGGING = False
    
    # Fallback functions
    def log_user_action(action, details=None):
        logger.info(f"User action: {action} - {details}")
    def log_performance(operation, duration, details=None):
        logger.info(f"Performance: {operation} - {duration:.3f}s - {details}")
    def log_recommendation_generation(method, song_idx, num_recommendations, processing_time, details=None):
        logger.info(f"Recommendations: {method} - song {song_idx} - {num_recommendations} recs - {processing_time:.3f}s")

logger.info("Streamlit app started - page configuration set")

# Initialize custom styles
initialize_app_styles()

# Initialize Spotify API client
SPOTIFY_API_AVAILABLE = False
spotify_client = None
try:
    from spotify_api_client import create_spotify_client, display_enhanced_track_info
    SPOTIFY_API_AVAILABLE = True
    logger.info("Spotify API client available")
    
    spotify_client = create_spotify_client()
    if spotify_client:
        logger.info("Spotify API client initialized successfully")
        log_user_action("spotify_client_initialized", {"success": True})
    else:
        logger.warning("Spotify API client initialization returned None")
except ImportError as e:
    logger.warning(f"Spotify API client not available: {e}")
    st.warning("Spotify API client not available. Enhanced features disabled.")


class SpotifyRecommendationApp:
    """Main application class for the Spotify Music Recommendation System."""
    
    def __init__(self):
        """Initialize the application with configuration and paths."""
        self.setup_paths()
        self.initialize_session_state()
    
    def setup_paths(self):
        """Setup data and model paths."""
        self.DATA_PATH = "/app/data"
        self.RAW_DATA_PATH = os.path.join(self.DATA_PATH, "raw")
        self.MODELS_PATH = os.path.join(self.DATA_PATH, "models")
        
        # File paths
        self.TRACKS_CSV = os.path.join(self.RAW_DATA_PATH, "spotify_tracks.csv")
        self.ARTISTS_CSV = os.path.join(self.RAW_DATA_PATH, "spotify_artists.csv")
        self.AUDIO_CSV = os.path.join(self.RAW_DATA_PATH, "low_level_audio_features.csv")
        
        # Model paths
        self.MODEL_PATHS = {
            "hdbscan": os.path.join(self.MODELS_PATH, "hdbscan_model.pkl"),
            "knn": os.path.join(self.MODELS_PATH, "knn_model.pkl"),
            "embeddings": os.path.join(self.MODELS_PATH, "audio_embeddings.pkl"),
            "labels": os.path.join(self.MODELS_PATH, "cluster_labels.pkl"),
            "song_indices": os.path.join(self.MODELS_PATH, "song_indices.pkl")
        }
        
        logger.info(f"Data paths configured - DATA_PATH: {self.DATA_PATH}")
        logger.debug(f"Model paths: {self.MODEL_PATHS}")
    
    def initialize_session_state(self):
        """Initialize session state variables."""
        if 'notifications_dismissed' not in st.session_state:
            st.session_state['notifications_dismissed'] = {}
    
    def load_application_data(self):
        """Load all required data for the application."""
        logger.info("Loading application data")
        data_load_start = time.time()
        
        # Load tracks data
        with st.spinner("Loading track data..."):
            tracks_df = load_data(self.TRACKS_CSV)
            
        if tracks_df.empty:
            logger.error("Cannot load track data - tracks_df is empty")
            st.error("Cannot load track data. Please ensure the data files are available.")
            return None, None, None, None
        
        # Load artists data
        with st.spinner("Loading artist data..."):
            artists_df = load_data(self.ARTISTS_CSV)
            artist_mapping = create_artist_mapping(artists_df)
            
        if not artist_mapping:
            logger.warning("Could not load artist mapping")
            st.warning("Could not load artist mapping. Artist names may not display correctly.")
        else:
            show_success_message(f"Loaded {len(artist_mapping):,} artist mappings", "👥")
        
        # Create searchable index
        with st.spinner("Creating search index..."):
            search_index = create_searchable_song_index(tracks_df, artist_mapping)
        
        show_info_message(f"Search index created with {len(search_index):,} searchable tracks", "🔍")
        
        # Load models
        with st.spinner("Loading recommendation models..."):
            models = load_all_models(self.MODEL_PATHS)
            
        data_load_time = time.time() - data_load_start
        log_performance("application_data_loading", data_load_time, {
            "tracks_count": len(tracks_df),
            "artists_count": len(artist_mapping),
            "search_index_size": len(search_index)
        })
        
        if models is None:
            logger.error("Cannot load models - models is None")
            st.error("Cannot load models. Please ensure the models are exported to the data/models directory.")
            st.info("Run the HDBSCAN notebook to generate the required models.")
            return tracks_df, artist_mapping, search_index, None
        
        # Check essential models
        essential_models = ['knn', 'embeddings']
        missing_models = [m for m in essential_models if models.get(m) is None]
        
        if missing_models:
            logger.error(f"Missing essential models: {missing_models}")
            st.error(f"Missing essential models: {missing_models}")
            st.info("Please ensure all required models are exported from the HDBSCAN notebook.")
            return tracks_df, artist_mapping, search_index, None
        
        # Show success notification for models
        available_models = [name for name, model in models.items() if model is not None]
        show_success_message(
            f"Successfully loaded {len(available_models)} recommendation models: {', '.join(available_models)}", 
            "🤖"
        )
        
        return tracks_df, artist_mapping, search_index, models
    
    def create_sidebar_interface(self, tracks_df, search_index):
        """Create the sidebar interface and return configuration and selected song."""
        # Create sidebar controls
        config = create_sidebar_controls(spotify_client, enable_audio_settings=True)
        
        # Audio preview analysis
        display_audio_preview_analysis(tracks_df)
        
        # Diagnostic search for troubleshooting
        with st.sidebar.expander("🔍 Song Diagnostics", expanded=False):
            st.markdown("**Search for specific songs to check preview status:**")
            search_term = st.text_input("Song name (e.g., 'Blood'):", key="diagnostic_search")
            
            if search_term:
                matches = search_song_by_name(tracks_df, search_term)
                if not matches.empty:
                    st.markdown(f"**Found {len(matches)} songs matching '{search_term}':**")
                    for _, song in matches.head(5).iterrows():
                        st.text(f"🎵 {song['name']}")
                        st.text(f"   Preview: {song['preview_status']}")
                        if not song['has_preview']:
                            preview_url = song.get('preview_url', 'N/A')
                            st.text(f"   URL: {str(preview_url)[:30]}...")
                        st.text("---")
                else:
                    st.info(f"No songs found matching '{search_term}'")
        
        # Enhanced song search interface
        selected_idx = create_song_search_interface(tracks_df, search_index)
        
        # Advanced search filters
        filtered_search_result = create_advanced_search_interface(search_index)
        if filtered_search_result is not None and selected_idx is None:
            selected_idx = filtered_search_result
        
        # Fallback to first song if no selection
        if selected_idx is None:
            selected_idx = 0
            logger.info("No song selected by user, using default (index 0)")
            st.sidebar.info("💡 Using first song as default. Try searching above!")
        
        logger.info(f"Selected song index: {selected_idx}")
        log_user_action("song_selected", {
            "song_index": selected_idx,
            "song_name": tracks_df.iloc[selected_idx].get('name', 'Unknown')
        })
        
        return config, selected_idx
    
    def display_selected_song(self, selected_song, artist_mapping, config):
        """Display information about the selected song."""
        artist_name = get_artist_name(selected_song.get('artists_id', ''), artist_mapping)
        
        st.markdown("---")
        st.markdown("## 🎵 Selected Song")
        
        # Create two columns for selected song display
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"### **{selected_song['name']}**")
            st.markdown(f"**Artist:** {artist_name}")
            
            # Song details
            if not pd.isna(selected_song.get('popularity')):
                st.markdown(f"**Popularity:** {selected_song['popularity']}/100")
            if not pd.isna(selected_song.get('duration_ms')):
                from utils.data_utils import format_duration
                duration = format_duration(selected_song['duration_ms'])
                st.markdown(f"**Duration:** {duration}")
            
            # Audio features preview
            features_col1, features_col2 = st.columns(2)
            with features_col1:
                if not pd.isna(selected_song.get('danceability')):
                    st.metric("Danceability", f"{selected_song['danceability']:.3f}")
                if not pd.isna(selected_song.get('energy')):
                    st.metric("Energy", f"{selected_song['energy']:.3f}")
            with features_col2:
                if not pd.isna(selected_song.get('valence')):
                    st.metric("Valence", f"{selected_song['valence']:.3f}")
                if not pd.isna(selected_song.get('acousticness')):
                    st.metric("Acousticness", f"{selected_song['acousticness']:.3f}")
        
        with col2:
            # Audio player for selected song
            display_audio_player(selected_song, "🎧 Preview:", artist_mapping)
            
            # Enhanced Spotify features for selected song
            if spotify_client and config.get('enable_enhanced', False):
                st.markdown("**🎵 Enhanced Info:**")
                if st.button("View Enhanced Details", key="enhanced_selected"):
                    if SPOTIFY_API_AVAILABLE:
                        display_enhanced_track_info(spotify_client, selected_song)
    
    def generate_and_display_recommendations(self, models, tracks_df, selected_idx, config, artist_mapping):
        """Generate and display recommendations using both cluster-based and global methods."""
        st.markdown("---")
        st.markdown("## 🎯 Music Recommendations")
        
        n_recommendations = config.get('n_recommendations', 5)
        enable_enhanced = config.get('enable_enhanced', False)
        
        # Create tabs for different recommendation types
        if models.get('labels') is not None:
            tab1, tab2 = st.tabs(["🎵 Cluster-Based", "🌐 Global Similarity"])
            
            with tab1:
                st.markdown("### Similar Songs from Same Musical Cluster")
                
                # Generate cluster-based recommendations
                cluster_distances, cluster_indices = get_recommendations_within_cluster(
                    models['knn'], 
                    models['embeddings'], 
                    models['labels'], 
                    selected_idx, 
                    n_neighbors=n_recommendations + 1
                )
                
                if cluster_distances is not None and cluster_indices is not None:
                    display_recommendations_with_cards(
                        tracks_df, 
                        cluster_indices, 
                        cluster_distances,
                        "🎵 Cluster-Based Recommendations",
                        f"Songs from the same musical cluster as '{tracks_df.iloc[selected_idx]['name']}'",
                        artist_mapping,
                        spotify_client,
                        enable_enhanced
                    )
                else:
                    st.error("Could not generate cluster-based recommendations")
            
            with tab2:
                st.markdown("### Similar Songs from Entire Dataset")
                
                # Generate global recommendations
                global_distances, global_indices = get_global_recommendations(
                    models['knn'], 
                    models['embeddings'], 
                    selected_idx, 
                    n_neighbors=n_recommendations + 1
                )
                
                if global_distances is not None and global_indices is not None:
                    display_recommendations_with_cards(
                        tracks_df, 
                        global_indices, 
                        global_distances,
                        "🌐 Global Similarity Recommendations",
                        f"Most similar songs to '{tracks_df.iloc[selected_idx]['name']}' from entire dataset",
                        artist_mapping,
                        spotify_client,
                        enable_enhanced
                    )
                else:
                    st.error("Could not generate global recommendations")
        
        else:
            # Only global recommendations if cluster labels not available
            st.markdown("### 🌐 Similar Songs")
            
            global_distances, global_indices = get_global_recommendations(
                models['knn'], 
                models['embeddings'], 
                selected_idx, 
                n_neighbors=n_recommendations + 1
            )
            
            if global_distances is not None and global_indices is not None:
                display_recommendations_with_cards(
                    tracks_df, 
                    global_indices, 
                    global_distances,
                    "🎵 Music Recommendations",
                    f"Songs most similar to '{tracks_df.iloc[selected_idx]['name']}'",
                    artist_mapping,
                    spotify_client,
                    enable_enhanced
                )
            else:
                st.error("Could not generate recommendations")
    
    def run(self):
        """Main application entry point."""
        logger.info("Starting main application function")
        app_start_time = time.time()
        
        # Page title
        st.title("🎵 Spotify Music Recommendation System")
        st.markdown("**HDBSCAN Clustering with KNN-Based Song Discovery**")
        
        # Load application data
        tracks_df, artist_mapping, search_index, models = self.load_application_data()
        
        if tracks_df is None or models is None:
            return  # Exit if critical data couldn't be loaded
        
        # Create sidebar interface
        config, selected_idx = self.create_sidebar_interface(tracks_df, search_index)
        
        # Display selected song information
        selected_song = tracks_df.iloc[selected_idx]
        self.display_selected_song(selected_song, artist_mapping, config)
        
        # Generate and display recommendations
        self.generate_and_display_recommendations(models, tracks_df, selected_idx, config, artist_mapping)
        
        # Create footer with statistics
        available_models = [name for name, model in models.items() if model is not None]
        create_app_footer(
            tracks_count=len(tracks_df),
            artists_count=len(artist_mapping),
            models_count=len(available_models),
            spotify_connected=config.get('spotify_connected', False)
        )
        
        # Log total app initialization time
        app_init_time = time.time() - app_start_time
        log_performance("application_initialization", app_init_time, {
            "spotify_available": spotify_client is not None,
            "models_loaded": len(available_models),
            "tracks_loaded": len(tracks_df)
        })


def main():
    """Main function to run the Spotify Music Recommendation System."""
    app = SpotifyRecommendationApp()
    app.run()


if __name__ == "__main__":
    main() 