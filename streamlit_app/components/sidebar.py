"""
Sidebar Navigation Component - Spotify-inspired Design
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Optional

def render_sidebar(app):
    """Render the main sidebar navigation"""
    
    with st.sidebar:
        # App branding
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0; margin-bottom: 2rem;">
            <h2 style="color: #1db954; margin: 0;">🎵 Spotify Music Recommendation</h2>
            <p style="color: #b3b3b3; margin: 0.5rem 0 0 0; font-size: 0.9rem;">
                AI-powered music recommendations using<br>advanced clustering algorithms 🎧
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Search section
        render_search_section(app)
        
        st.markdown("---")
        
        # Settings section
        render_settings_section(app)
        
        st.markdown("---")
        
        # Quick actions
        render_quick_actions(app)
        
        st.markdown("---")
        
        # API Status
        render_api_status(app)

def render_search_section(app):
    """Render the search section of the sidebar"""
    st.markdown("### 🔍 Search for a Song")
    st.markdown("**Enter song name or artist:**")
    
    search_query = st.text_input(
        "Search tracks",
        placeholder="Type song or artist name...",
        key="search_input",
        label_visibility="collapsed"
    )
    
    if search_query:
        # Perform search
        search_results = app.search_tracks(search_query)
        
        if search_results:
            st.session_state.search_results = search_results
            st.success(f"Found {len(search_results)} tracks")
        else:
            st.warning("No tracks found")
            st.session_state.search_results = []
        
        # Clear search button
        if st.button("🗑️ Clear Search", use_container_width=True):
            st.session_state.search_results = []
            st.rerun()
    
    elif st.session_state.search_results:
        # Show clear button if we have search results but no current query
        if st.button("🗑️ Clear Search", use_container_width=True):
            st.session_state.search_results = []
            st.rerun()

def render_settings_section(app):
    """Render the settings section"""
    st.markdown("### ⚙️ Settings")
    
    # Number of recommendations slider
    st.markdown("**Number of recommendations:**")
    num_recs = st.slider(
        "Number of recommendations",
        min_value=5,
        max_value=20,
        value=st.session_state.num_recommendations,
        key="recommendations_slider",
        label_visibility="collapsed"
    )
    
    if num_recs != st.session_state.num_recommendations:
        st.session_state.num_recommendations = num_recs
    
    # Recommendation type
    st.markdown("**Recommendation algorithm:**")
    rec_type = st.selectbox(
        "Recommendation algorithm",
        options=["cluster", "global"],
        index=0 if st.session_state.recommendation_type == "cluster" else 1,
        format_func=lambda x: "🎯 Cluster-based" if x == "cluster" else "🌍 Global similarity",
        key="rec_type_select",
        label_visibility="collapsed"
    )
    
    if rec_type != st.session_state.recommendation_type:
        st.session_state.recommendation_type = rec_type
    
    # Get Recommendations button
    if st.button(
        "🤖 Get Recommendations", 
        use_container_width=True,
        type="primary",
        disabled=st.session_state.selected_track_idx is None
    ):
        if st.session_state.selected_track_idx is not None:
            # Trigger recommendations generation
            st.session_state.recommendations = app.get_recommendations(
                st.session_state.selected_track_idx,
                st.session_state.num_recommendations,
                st.session_state.recommendation_type
            )
            st.success("Recommendations updated!")
        else:
            st.warning("Please select a track first")

def render_quick_actions(app):
    """Render quick action buttons"""
    st.markdown("### 🎯 Quick Discovery")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔥 Popular", use_container_width=True):
            # Generate new featured tracks from popular songs
            if not app.tracks_df.empty:
                popular_tracks = app.tracks_df.nlargest(12, 'popularity')
                st.session_state.featured_tracks = popular_tracks.index.tolist()
                st.session_state.search_results = []  # Clear search results
                st.rerun()
        
        if st.button("💃 Danceable", use_container_width=True):
            # Generate featured tracks from danceable songs
            if not app.tracks_df.empty:
                danceable_tracks = app.tracks_df.nlargest(12, 'danceability')
                st.session_state.featured_tracks = danceable_tracks.index.tolist()
                st.session_state.search_results = []
                st.rerun()
    
    with col2:
        if st.button("🎸 Energetic", use_container_width=True):
            # Generate featured tracks from energetic songs
            if not app.tracks_df.empty:
                energetic_tracks = app.tracks_df.nlargest(12, 'energy')
                st.session_state.featured_tracks = energetic_tracks.index.tolist()
                st.session_state.search_results = []
                st.rerun()
        
        if st.button("😌 Chill", use_container_width=True):
            # Generate featured tracks from chill songs (low energy, high valence)
            if not app.tracks_df.empty:
                chill_tracks = app.tracks_df[
                    (app.tracks_df['energy'] < 0.5) & 
                    (app.tracks_df['valence'] > 0.5)
                ].nlargest(12, 'popularity')
                
                if len(chill_tracks) >= 12:
                    st.session_state.featured_tracks = chill_tracks.index.tolist()
                else:
                    # Fallback to low energy tracks
                    low_energy = app.tracks_df.nsmallest(12, 'energy')
                    st.session_state.featured_tracks = low_energy.index.tolist()
                
                st.session_state.search_results = []
                st.rerun()
    
    # Refresh featured tracks
    if st.button("🔄 Refresh Featured", use_container_width=True):
        app.generate_featured_tracks()
        st.session_state.search_results = []  # Clear search results
        st.rerun()

def render_api_status(app):
    """Render API connection status"""
    st.markdown("### 📡 API Status")
    
    # Spotify API status
    if app.spotify_available:
        st.success("✅ Spotify API Connected")
        st.markdown("*Enhanced track info available*")
    else:
        st.error("❌ Spotify API Unavailable")
        st.markdown("*Limited features*")
    
    # Models status
    if app.models:
        st.success("✅ AI Models Loaded")
        
        model_details = []
        if app.models.get('hdbscan') is not None:
            model_details.append("HDBSCAN clustering")
        if app.models.get('knn') is not None:
            model_details.append("K-NN similarity")
        if app.models.get('embeddings') is not None:
            model_details.append("Audio embeddings")
        
        if model_details:
            st.markdown(f"*{', '.join(model_details)}*")
    else:
        st.error("❌ AI Models Missing")
        st.markdown("*Recommendations unavailable*")
    
    # Data status
    if not app.tracks_df.empty:
        st.info(f"📊 {len(app.tracks_df):,} tracks loaded")
    else:
        st.error("❌ No track data loaded")

def render_library_section(app):
    """Render library/playlist section (future enhancement)"""
    st.markdown("### 📚 Your Library")
    
    # Placeholder for user playlists/favorites
    st.markdown("*Feature coming soon...*")
    
    # Recent selections
    if hasattr(st.session_state, 'recent_tracks') and st.session_state.recent_tracks:
        st.markdown("**Recently Played:**")
        for track_idx in st.session_state.recent_tracks[-3:]:  # Show last 3
            if track_idx < len(app.tracks_df):
                track = app.tracks_df.iloc[track_idx]
                if st.button(
                    f"🎵 {track['name'][:20]}...",
                    key=f"recent_{track_idx}",
                    use_container_width=True
                ):
                    st.session_state.selected_track_idx = track_idx
                    st.session_state.current_track = track_idx
                    st.rerun()

# Additional styling for sidebar
SIDEBAR_CSS = """
<style>
.sidebar .sidebar-content {
    background: linear-gradient(180deg, #0c0c0c 0%, #1a1a1a 100%);
}

.sidebar .element-container {
    background: transparent;
}

.sidebar .stButton > button {
    background: linear-gradient(135deg, #2a2a2a, #1e1e1e);
    color: white;
    border: 1px solid rgba(29, 185, 84, 0.3);
    border-radius: 8px;
    transition: all 0.3s ease;
    font-size: 0.9rem;
}

.sidebar .stButton > button:hover {
    border-color: #1db954;
    background: linear-gradient(135deg, #1db954, #1ed760);
    transform: translateY(-1px);
}

.sidebar .stSelectbox > div > div {
    background: rgba(42, 42, 42, 0.8);
    border: 1px solid rgba(29, 185, 84, 0.3);
    border-radius: 8px;
}

.sidebar .stTextInput > div > div > input {
    background: rgba(42, 42, 42, 0.8);
    border: 1px solid rgba(29, 185, 84, 0.3);
    border-radius: 8px;
    color: white;
}

.sidebar .stSlider > div > div {
    background: rgba(42, 42, 42, 0.8);
}
</style>
""" 