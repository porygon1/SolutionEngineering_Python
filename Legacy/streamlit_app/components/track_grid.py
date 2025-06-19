"""
Track Grid Component - Spotify-inspired Track Display
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Optional
from utils.formatting import format_duration, get_key_name, get_mode_name
from utils.data_utils import get_artist_name
from .music_player import get_album_artwork

def render_track_grid(
    tracks_df: pd.DataFrame,
    artist_mapping: Dict[str, str],
    spotify_client: Optional[object] = None,
    grid_id: str = "default",
    cols: int = 4,
    nested: bool = False
):
    """Render tracks in a responsive grid layout"""
    
    if tracks_df.empty:
        st.info("No tracks to display")
        return

    # Display tracks in grid
    for i in range(0, len(tracks_df), cols):
        row_tracks = tracks_df.iloc[i:i+cols]
        columns = st.columns(cols)
        
        for idx, (_, track) in enumerate(row_tracks.iterrows()):
            if idx < len(columns):
                with columns[idx]:
                    render_enhanced_track_card(track, artist_mapping, spotify_client, grid_id, idx + i, nested=nested)

def render_enhanced_track_card(track, artist_mapping, spotify_client, grid_id, track_idx, nested=False):
    """Render an enhanced track card with prominent similarity score display"""
    
    # Get similarity score if this is a recommendation
    similarity_score = track.get('similarity_score', track.get('score', None))
    is_recommendation = similarity_score is not None
    
    # Create a container with custom styling
    with st.container():
        # Add custom CSS for this specific card
        if is_recommendation:
            st.markdown(f"""
            <style>
            .track-card-{grid_id}-{track_idx} {{
                background: linear-gradient(135deg, #1e1e1e 0%, #2a2a2a 100%);
                border: 2px solid #1db954;
                border-radius: 12px;
                padding: 16px;
                margin-bottom: 16px;
                box-shadow: 0 6px 20px rgba(29, 185, 84, 0.3);
                position: relative;
            }}
            </style>
            """, unsafe_allow_html=True)
            
            # Similarity score badge at the top
            st.markdown(f"""
            <div style="text-align: center; margin-bottom: 8px;">
                <span style="background: linear-gradient(45deg, #1db954, #1ed760); 
                           color: white; padding: 6px 12px; border-radius: 20px; 
                           font-weight: bold; font-size: 13px;
                           box-shadow: 0 2px 8px rgba(29, 185, 84, 0.4);">
                    🎯 {similarity_score:.1%} Match
                </span>
            </div>
            """, unsafe_allow_html=True)
    
        # Album cover with better fallback
        album_image_url = None
        if spotify_client:
            try:
                enhanced_track_info = get_enhanced_track_info(track, spotify_client)
                if enhanced_track_info and enhanced_track_info.get('album', {}).get('images'):
                    album_image_url = enhanced_track_info['album']['images'][0]['url']
            except Exception as e:
                pass
        
        if album_image_url:
            st.image(album_image_url, use_container_width=True)
        else:
            # Enhanced placeholder with track-specific colors
            energy = track.get('energy', 0.5)
            valence = track.get('valence', 0.5)
            danceability = track.get('danceability', 0.5)
            
            # Generate colors based on audio features
            hue1 = int(energy * 360)
            hue2 = int(valence * 360)
            saturation = int(50 + danceability * 50)
            
            placeholder_html = f"""
            <div style="width: 100%; height: 200px; 
                        background: linear-gradient(135deg, 
                            hsl({hue1}, {saturation}%, 45%) 0%, 
                            hsl({hue2}, {saturation}%, 35%) 100%);
                        border-radius: 8px; display: flex; align-items: center; 
                        justify-content: center; color: white; font-size: 2rem;
                        margin-bottom: 12px;">
                🎵
            </div>
            """
            st.markdown(placeholder_html, unsafe_allow_html=True)
        
        # Track Information Section
        track_name = track.get('name', 'Unknown Track')
        artist_name = get_artist_name(track, artist_mapping)
        
        # Truncate long names
        if len(track_name) > 25:
            track_name = track_name[:22] + "..."
        if len(artist_name) > 20:
            artist_name = artist_name[:17] + "..."
        
        # Display track name and artist
        if is_recommendation:
            st.markdown(f"**:green[{track_name}]**")
        else:
            st.markdown(f"**{track_name}**")
        st.markdown(f"*{artist_name}*")
        
        # Audio Features Visualization (especially for recommendations)
        if is_recommendation:
            st.markdown("**🎵 Audio Features:**")
            
            # Create mini feature bars using Streamlit progress bars
            features = ['energy', 'danceability', 'valence', 'acousticness']
            feature_labels = ['Energy', 'Dance', 'Mood', 'Acoustic']
            
            if not nested:
                for feature, label in zip(features, feature_labels):
                    value = track.get(feature, 0)
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.progress(value, text=label)
                    with col2:
                        st.markdown(f"**{int(value * 100)}%**")
            else:
                # Simplified version for nested context
                for feature, label in zip(features, feature_labels):
                    value = track.get(feature, 0)
                    st.progress(value, text=f"{label}: {int(value * 100)}%")
        
        # Track Stats - avoid nested columns in nested context
        if not nested:
            col1, col2 = st.columns(2)
            with col1:
                popularity = track.get('popularity', 0)
                st.metric("Popularity", f"{popularity}")
            
            with col2:
                # Fix the year issue - extract from available data sources
                year = None
                
                # Since there's no direct year field in the dataset, try to get it from Spotify API
                if spotify_client:
                    try:
                        enhanced_track_info = get_enhanced_track_info(track, spotify_client)
                        if enhanced_track_info and enhanced_track_info.get('album', {}).get('release_date'):
                            release_date = enhanced_track_info['album']['release_date']
                            if len(release_date) >= 4 and release_date[:4].isdigit():
                                year = release_date[:4]
                    except:
                        pass
                
                # If no year from API, try to extract from track name or other fields
                if not year:
                    # Try to extract year from track name (some tracks have year in parentheses)
                    track_name = track.get('name', '')
                    import re
                    year_match = re.search(r'\((\d{4})\)', str(track_name))
                    if year_match:
                        year = year_match.group(1)
                    else:
                        # Try to extract from album_id or other fields if they contain year info
                        album_id = track.get('album_id', '')
                        if album_id and isinstance(album_id, str):
                            year_match = re.search(r'(\d{4})', album_id)
                            if year_match:
                                year = year_match.group(1)
                
                # Display year or fallback
                if year and year.isdigit() and 1900 <= int(year) <= 2030:
                    st.metric("Year", str(year))
                else:
                    st.metric("Year", "Unknown")
        else:
            # Simplified layout for nested context
            popularity = track.get('popularity', 0)
            st.markdown(f"**Popularity:** {popularity}")
            
            # Simplified year display
            year = "Unknown"
            if spotify_client:
                try:
                    enhanced_track_info = get_enhanced_track_info(track, spotify_client)
                    if enhanced_track_info and enhanced_track_info.get('album', {}).get('release_date'):
                        release_date = enhanced_track_info['album']['release_date']
                        if len(release_date) >= 4 and release_date[:4].isdigit():
                            year = release_date[:4]
                except:
                    pass
            st.markdown(f"**Year:** {year}")
        
        # Action Buttons - avoid nested columns in nested context
        if not nested:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("▶️ Play", key=f"play_{grid_id}_{track_idx}", use_container_width=True):
                    # Set as current track
                    st.session_state.current_track = track_idx
                    st.session_state.selected_track_idx = track_idx
                    st.rerun()
            
            with col2:
                if st.button("🎯 Similar", key=f"similar_{grid_id}_{track_idx}", use_container_width=True):
                    # Set for recommendations
                    st.session_state.selected_track_idx = track_idx
                    st.rerun()
        else:
            # Simplified buttons for nested context
            if st.button("▶️ Play", key=f"play_{grid_id}_{track_idx}", use_container_width=True):
                # Set as current track
                st.session_state.current_track = track_idx
                st.session_state.selected_track_idx = track_idx
                st.rerun()
            
            if st.button("🎯 Similar", key=f"similar_{grid_id}_{track_idx}", use_container_width=True):
                # Set for recommendations
                st.session_state.selected_track_idx = track_idx
                st.rerun()

def render_track_list_view(
    tracks_df: pd.DataFrame,
    artist_mapping: Dict[str, str],
    spotify_client: Optional[object] = None,
    list_id: str = "default"
):
    """Render a list view of tracks"""
    if tracks_df.empty:
        st.info("No tracks to display")
        return

    # Display tracks in list
    for _, track in tracks_df.iterrows():
        render_track_card(track, artist_mapping, spotify_client, list_id, is_list=True)

def render_track_card(
    track: pd.Series,
    artist_mapping: Dict[str, str],
    spotify_client: Optional[object] = None,
    container_id: str = "default",
    is_list: bool = False
):
    """Render a single track card"""
    # Get track details
    track_name = track['name']
    artist_id = track['artists_id']
    artist_name = get_artist_name(artist_id, artist_mapping)
    duration = format_duration(track['duration_ms'])
    
    # Create card container
    with st.container():
        # Track info
        st.markdown(f"**{track_name}**")
        st.markdown(f"*{artist_name}*")
        
        # Additional details
        if not is_list:
            st.markdown(f"Duration: {duration}")
            if 'key' in track:
                st.markdown(f"Key: {get_key_name(track['key'])} {get_mode_name(track['mode'])}")
        
        # Play button
        if st.button("▶️ Play", key=f"play_{container_id}_{track.name}"):
            st.session_state.current_track = track.name
            if spotify_client:
                # Handle Spotify playback if client is available
                pass

def render_compact_audio_features(track):
    """Render compact audio features visualization"""
    
    # Get key audio features
    features = {
        '🎵 Energy': track.get('energy', 0),
        '💃 Dance': track.get('danceability', 0),
        '😊 Mood': track.get('valence', 0),
        '🎤 Speech': track.get('speechiness', 0)
    }
    
    # Create compact feature bars
    feature_html = "<div class='feature-container'>"
    
    for feature_name, value in features.items():
        percentage = int(value * 100)
        color = get_feature_color(feature_name, value)
        
        feature_html += f"""
        <div class="feature-row">
            <span class="feature-label">{feature_name}</span>
            <div class="feature-bar-container">
                <div class="feature-bar-fill" style="width: {percentage}%"></div>
            </div>
            <span class="feature-value">{percentage}%</span>
        </div>
        """
    
    feature_html += "</div>"
    st.markdown(feature_html, unsafe_allow_html=True)

def get_feature_color(feature_name, value):
    """Get color for audio feature based on value"""
    if '🎵 Energy' in feature_name:
        return f"hsl({int(value * 60)}, 70%, 50%)"  # Green to yellow
    elif '💃 Dance' in feature_name:
        return f"hsl({int(180 + value * 60)}, 70%, 50%)"  # Cyan to blue
    elif '😊 Mood' in feature_name:
        return f"hsl({int(value * 120)}, 70%, 50%)"  # Red to green
    else:
        return f"hsl({int(value * 300)}, 70%, 50%)"  # Purple spectrum

def get_enhanced_track_info(track, spotify_client):
    """Get enhanced track information from Spotify API"""
    if not spotify_client:
        return None
    
    # Try to get Spotify ID from track data
    spotify_id = None
    
    # Method 1: Direct ID field
    if 'id' in track and track['id'] and not pd.isna(track['id']):
        spotify_id = str(track['id']).strip()
    
    # Method 2: Extract from URI
    elif 'uri' in track and track['uri'] and not pd.isna(track['uri']):
        uri = str(track['uri']).strip()
        if uri.startswith('spotify:track:'):
            spotify_id = uri.split(':')[-1]
    
    if spotify_id:
        try:
            # Use the correct method name from the Spotify client
            return spotify_client.get_track_details(spotify_id)
        except Exception as e:
            print(f"Error fetching track details: {e}")
            return None
    
    return None

def show_track_details(track, artist_mapping, spotify_client):
    """Show detailed track information"""
    
    # Create a modal-like display using expander
    with st.expander(f"🎵 Track Details: {track.get('name', 'Unknown')}", expanded=True):
        
        # Try to get album cover
        if spotify_client:
            track_details = get_enhanced_track_info(track, spotify_client)
            if track_details:
                album_images = track_details.get('album', {}).get('images', [])
                if album_images:
                    st.image(album_images[0]['url'], width=200)
        
        # Basic track info
        st.markdown("**Track Information:**")
        st.write(f"**Name:** {track.get('name', 'Unknown')}")
        st.write(f"**Artist:** {get_artist_name(track.get('artists_id', ''), artist_mapping)}")
        st.write(f"**Duration:** {format_duration(track.get('duration_ms', 0))}")
        st.write(f"**Popularity:** {track.get('popularity', 0)}%")
        st.write(f"**Year:** {track.get('year', 'Unknown')}")
        
        # Audio features
        st.markdown("**Audio Features:**")
        features = [
            ('Energy', track.get('energy', 0)),
            ('Danceability', track.get('danceability', 0)),
            ('Valence', track.get('valence', 0)),
            ('Acousticness', track.get('acousticness', 0)),
            ('Instrumentalness', track.get('instrumentalness', 0)),
            ('Liveness', track.get('liveness', 0)),
            ('Speechiness', track.get('speechiness', 0))
        ]
        
        for feature_name, value in features:
            st.write(f"**{feature_name}:** {value:.3f}")

def render_track_list_view(tracks_df, artist_mapping, spotify_client, list_id="list"):
    """Render tracks in a list view (alternative to grid)"""
    
    if tracks_df.empty:
        st.info("No tracks to display")
        return
    
    for idx, (_, track) in enumerate(tracks_df.iterrows()):
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([1, 3, 2, 1, 1])
            
            with col1:
                # Preview button
                if st.button("▶️", key=f"listpreview_{list_id}_{idx}", help="Preview track"):
                    st.session_state.current_track = track.name if hasattr(track, 'name') else idx
                    st.rerun()
            
            with col2:
                # Track name and artist
                track_name = track.get('name', 'Unknown Track')
                artist_name = get_artist_name(track.get('artists_id', ''), artist_mapping)
                
                st.markdown(f"""
                <div class="track-list-item">
                    <div class="track-list-title">{track_name}</div>
                    <div class="track-list-artist">{artist_name}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                # Duration and popularity
                duration = format_duration(track.get('duration_ms', 0))
                popularity = track.get('popularity', 0)
                year = track.get('year', 'Unknown')
                
                st.markdown(f"""
                <div class="track-list-details">
                    {year} • {duration}<br>
                    {popularity}% popularity
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                # Get recommendations button
                if st.button("🎯", key=f"listrec_{list_id}_{idx}", help="Get similar tracks"):
                    st.session_state.selected_track_idx = track.name if hasattr(track, 'name') else idx
                    st.rerun()
            
            with col5:
                # Info button
                if st.button("ℹ️", key=f"listinfo_{list_id}_{idx}", help="Track details"):
                    show_track_details(track, artist_mapping, spotify_client)
            
            st.markdown("---") 