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

# Import utilities
from utils import (
    load_data, load_all_models, create_artist_mapping, get_artist_name,
    format_duration, get_key_name, get_mode_name, initialize_app_styles
)
from utils.recommendations import get_recommendations_within_cluster, get_global_recommendations

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
        self.initialize_session_state()
        self.setup_spotify_client()
        self.load_data()
    
    def setup_paths(self):
        """Setup data and model paths for Docker compatibility"""
        base_path = os.getenv('DATA_PATH', '/app/data')
        if not os.path.exists(base_path):
            base_path = os.getenv('DATA_PATH', 'data')
        
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
    
    def initialize_session_state(self):
        """Initialize session state for the app"""
        if 'current_track' not in st.session_state:
            st.session_state.current_track = None
        if 'featured_tracks' not in st.session_state:
            st.session_state.featured_tracks = []
        if 'recommendations' not in st.session_state:
            st.session_state.recommendations = []
        if 'search_results' not in st.session_state:
            st.session_state.search_results = []
        if 'selected_track_idx' not in st.session_state:
            st.session_state.selected_track_idx = None
        if 'num_recommendations' not in st.session_state:
            st.session_state.num_recommendations = 12
        if 'recommendation_type' not in st.session_state:
            st.session_state.recommendation_type = "cluster"
    
    def load_data(self):
        """Load music data and models"""
        try:
            self.tracks_df = load_data(self.TRACKS_CSV)
            self.artists_df = load_data(self.ARTISTS_CSV)
            self.artist_mapping = create_artist_mapping(self.artists_df)
            self.models = load_all_models(self.MODEL_PATHS)
            
            # Initialize featured tracks
            if not st.session_state.featured_tracks:
                self.generate_featured_tracks()
                
            logger.info(f"Data loaded - Tracks: {len(self.tracks_df)}, Artists: {len(self.artist_mapping)}")
            
        except Exception as e:
            st.error(f"❌ Error loading data: {e}")
            logger.error(f"Data loading error: {e}")
            self.tracks_df = pd.DataFrame()
            self.artists_df = pd.DataFrame()
            self.artist_mapping = {}
            self.models = {}
    
    def generate_featured_tracks(self):
        """Generate a selection of featured tracks"""
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
            st.session_state.featured_tracks = featured_indices[:12]
    
    def render_sidebar(self):
        """Render the left sidebar navigation"""
        from components.sidebar import render_sidebar
        render_sidebar(self)
    
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
        from components.track_grid import render_track_grid
        
        st.markdown("## 🎵 Featured Tracks")
        
        if st.session_state.featured_tracks and not self.tracks_df.empty:
            featured_tracks_data = self.tracks_df.iloc[st.session_state.featured_tracks]
            render_track_grid(
                featured_tracks_data, 
                self.artist_mapping, 
                self.spotify_client,
                grid_id="featured"
            )
        else:
            st.info("Loading featured tracks...")
    
    def render_recommendations(self):
        """Render recommendations if a track is selected"""
        if st.session_state.selected_track_idx is not None:
            from components.recommendations import render_recommendations_section
            
            st.markdown("---")
            st.markdown("## 🤖 AI Recommendations")
            
            render_recommendations_section(
                self.tracks_df,
                self.artist_mapping,
                self.models,
                st.session_state.selected_track_idx,
                self.spotify_client,
                st.session_state.num_recommendations,
                st.session_state.recommendation_type
            )
    
    def render_search_results(self):
        """Render search results if any"""
        if st.session_state.search_results:
            from components.track_grid import render_track_grid
            
            st.markdown("## 🔍 Search Results")
            search_df = pd.DataFrame(st.session_state.search_results)
            render_track_grid(
                search_df, 
                self.artist_mapping, 
                self.spotify_client,
                grid_id="search"
            )
    
    def render_now_playing(self):
        """Render the now playing section at the bottom"""
        if st.session_state.current_track is not None:
            from components.music_player import render_bottom_player
            
            track = self.tracks_df.iloc[st.session_state.current_track]
            render_bottom_player(track, self.artist_mapping, self.spotify_client)
    
    def search_tracks(self, query: str) -> List[Dict]:
        """Search for tracks based on query"""
        if not query or self.tracks_df.empty:
            return []
        
        query = query.lower()
        
        # Create search index
        search_df = self.tracks_df.copy()
        search_df['artist_name'] = search_df['artists_id'].apply(
            lambda x: get_artist_name(x, self.artist_mapping)
        )
        search_df['search_text'] = (
            search_df['name'].str.lower() + ' ' + 
            search_df['artist_name'].str.lower()
        )
        
        # Perform search
        mask = search_df['search_text'].str.contains(query, na=False)
        results = search_df[mask].sort_values('popularity', ascending=False)
        
        return results.head(20).to_dict('records')
    
    def get_recommendations(self, track_idx: int, n_recommendations: int = 12, rec_type: str = "cluster"):
        """Get recommendations for a track"""
        if not self.models or self.tracks_df.empty:
            return []
        
        try:
            if rec_type == "cluster" and self.models.get('labels') is not None:
                distances, indices = get_recommendations_within_cluster(
                    self.models['knn'], self.models['embeddings'], 
                    self.models['labels'], track_idx, n_neighbors=n_recommendations + 1
                )
            else:
                distances, indices = get_global_recommendations(
                    self.models['knn'], self.models['embeddings'], 
                    track_idx, n_neighbors=n_recommendations + 1
                )
            
            # Return recommendations (excluding the input track)
            rec_indices = indices[1:]  # Skip first one (input track)
            return self.tracks_df.iloc[rec_indices]
            
        except Exception as e:
            logger.error(f"Error getting recommendations: {e}")
            return pd.DataFrame()
    
    def run(self):
        """Main application runner"""
        logger.info("Starting Spotify-like Music Discovery App")
        
        if self.tracks_df.empty:
            st.error("❌ Could not load track data. Please check data files.")
            return
        
        # Custom CSS for Spotify-like layout
        st.markdown("""
        <style>
        .main .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
            max-width: 100%;
        }
        
        .spotify-header {
            text-align: center;
            padding: 1.5rem 0;
            background: linear-gradient(135deg, #1db954 0%, #1ed760 100%);
            border-radius: 15px;
            margin-bottom: 2rem;
            box-shadow: 0 8px 32px rgba(29, 185, 84, 0.3);
        }
        
        .spotify-header h1 {
            font-family: 'Poppins', sans-serif;
            font-size: 2.5rem;
            font-weight: 700;
            margin: 0;
            color: white;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .subtitle {
            font-size: 1rem;
            margin: 0.5rem 0 0 0;
            opacity: 0.9;
            color: white;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Render sidebar
        self.render_sidebar()
        
        # Main content area (no column wrapper to avoid nesting issues)
        # Render main header
        self.render_main_header()
        
        # Render search results if any
        self.render_search_results()
        
        # Render featured tracks if no search results
        if not st.session_state.search_results:
            self.render_featured_tracks()
        
        # Render recommendations if a track is selected
        self.render_recommendations()
        
        # Render now playing at the bottom (outside columns)
        self.render_now_playing()
        
        # Footer
        st.markdown("---")
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem; opacity: 0.7; font-size: 0.9rem;">
            <p>🎵 Spotify Music Recommendation | 🎧 {len(self.tracks_df):,} tracks loaded | 
            🤖 AI Models {'✅' if self.models else '❌'} | 
            🎼 Spotify API {'✅' if self.spotify_available else '❌'}</p>
        </div>
        """, unsafe_allow_html=True)


def main():
    """Main function to run the Spotify-like Music Discovery App"""
    app = SpotifyLikeApp()
    app.run()


if __name__ == "__main__":
    main() 