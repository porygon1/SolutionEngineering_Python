"""
Track Grid Component - Spotify-inspired Track Display
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Optional
from utils import get_artist_name, format_duration

def render_track_grid(tracks_df, artist_mapping, spotify_client, grid_id="tracks", cols=4):
    """Render tracks in a grid layout similar to Spotify"""
    
    if tracks_df.empty:
        st.info("No tracks to display")
        return
    
    # Ensure we're working with a DataFrame
    if isinstance(tracks_df, dict):
        tracks_df = pd.DataFrame([tracks_df])
    elif isinstance(tracks_df, list):
        tracks_df = pd.DataFrame(tracks_df)
    
    # Create grid layout
    track_cols = st.columns(cols)
    
    for idx, (_, track) in enumerate(tracks_df.iterrows()):
        col_idx = idx % cols
        
        with track_cols[col_idx]:
            render_track_card(track, artist_mapping, spotify_client, f"{grid_id}_{idx}")

def render_track_card(track, artist_mapping, spotify_client, card_key):
    """Render individual track card"""
    
    # Get track information
    track_name = track.get('name', 'Unknown Track')
    artist_name = get_artist_name(track.get('artists_id', ''), artist_mapping)
    duration = format_duration(track.get('duration_ms', 0))
    popularity = track.get('popularity', 0)
    
    # Truncate long names
    display_name = track_name[:25] + "..." if len(track_name) > 25 else track_name
    display_artist = artist_name[:20] + "..." if len(artist_name) > 20 else artist_name
    
    # Container for the track card
    with st.container():
        # Get enhanced track info from Spotify API if available
        album_image_url = None
        spotify_url = None
        
        if spotify_client:
            try:
                track_details = get_enhanced_track_info(track, spotify_client)
                if track_details:
                    album_images = track_details.get('album', {}).get('images', [])
                    if album_images:
                        album_image_url = album_images[0]['url']  # Largest image
                    
                    external_urls = track_details.get('external_urls', {})
                    spotify_url = external_urls.get('spotify')
            except Exception as e:
                st.write(f"Error fetching enhanced info: {e}")
        
        # Album cover or placeholder
        if album_image_url:
            st.image(album_image_url, width=200, use_container_width=True)
        else:
            # Placeholder image with gradient based on track features
            energy = track.get('energy', 0.5)
            valence = track.get('valence', 0.5)
            color_intensity = int(255 * energy)
            color_hue = "green" if valence > 0.5 else "blue"
            
            placeholder_html = f"""
            <div style="
                width: 100%;
                height: 200px;
                background: linear-gradient(135deg, 
                    rgba({color_intensity}, 185, 84, 0.8), 
                    rgba({color_intensity//2}, 100, 150, 0.6));
                border-radius: 12px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 2rem;
                margin-bottom: 1rem;
                box-shadow: 0 4px 16px rgba(0,0,0,0.3);
            ">
                🎵
            </div>
            """
            st.markdown(placeholder_html, unsafe_allow_html=True)
        
        # Track information
        st.markdown(f"""
        <div style="padding: 0.5rem 0;">
            <h4 style="margin: 0; color: white; font-size: 1rem; font-weight: 600;">
                {display_name}
            </h4>
            <p style="margin: 0.25rem 0; color: #b3b3b3; font-size: 0.9rem;">
                {display_artist}
            </p>
            <p style="margin: 0; color: #b3b3b3; font-size: 0.8rem;">
                {duration} • {popularity}% popularity
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Interactive buttons using vertical layout to avoid nesting issues
        if st.button("▶️ Play", key=f"play_{card_key}", help="Play", use_container_width=True):
            # Set as current track
            if hasattr(track, 'name'):  # pandas Series
                track_idx = track.name
            else:  # dict
                # Find the track index in the dataframe
                track_idx = None
                # This is a fallback - ideally we'd pass the index
            
            st.session_state.current_track = track_idx
            st.session_state.selected_track_idx = track_idx
            st.success(f"Now playing: {display_name}")
            st.rerun()
        
        # Spotify link button
        if spotify_url:
            st.markdown(f'''
            <a href="{spotify_url}" target="_blank" style="text-decoration: none; display: block; width: 100%;">
                <div style="
                    background: #1db954;
                    color: white;
                    padding: 0.5rem;
                    border-radius: 6px;
                    text-align: center;
                    margin: 0.25rem 0;
                    transition: background 0.2s;
                    cursor: pointer;
                ">🎵 Open in Spotify</div>
            </a>
            ''', unsafe_allow_html=True)
        
        if st.button("ℹ️ More Info", key=f"info_{card_key}", help="Track Details", use_container_width=True):
            # Show track details in sidebar or modal
            show_track_details(track, artist_mapping, spotify_client)
        
        # Audio features visualization (compact)
        render_compact_audio_features(track)
        
        st.markdown("---")

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
    feature_html = "<div style='margin: 0.5rem 0;'>"
    
    for feature_name, value in features.items():
        percentage = int(value * 100)
        color = get_feature_color(feature_name, value)
        
        feature_html += f"""
        <div style="display: flex; align-items: center; margin: 0.2rem 0;">
            <span style="color: #b3b3b3; font-size: 0.7rem; width: 60px; overflow: hidden;">
                {feature_name}
            </span>
            <div style="
                flex: 1;
                height: 4px;
                background: #333;
                border-radius: 2px;
                margin: 0 0.5rem;
                overflow: hidden;
            ">
                <div style="
                    width: {percentage}%;
                    height: 100%;
                    background: {color};
                    transition: width 0.3s ease;
                "></div>
            </div>
            <span style="color: #b3b3b3; font-size: 0.7rem; width: 30px;">
                {percentage}%
            </span>
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
            col1, col2, col3, col4 = st.columns([1, 3, 2, 1])
            
            with col1:
                # Small album cover or play button
                if st.button("▶️", key=f"listplay_{list_id}_{idx}"):
                    st.session_state.current_track = track.name if hasattr(track, 'name') else idx
                    st.session_state.selected_track_idx = track.name if hasattr(track, 'name') else idx
                    st.rerun()
            
            with col2:
                # Track name and artist
                track_name = track.get('name', 'Unknown Track')
                artist_name = get_artist_name(track.get('artists_id', ''), artist_mapping)
                
                st.markdown(f"""
                <div style="padding: 0.5rem 0;">
                    <div style="color: white; font-weight: 500;">{track_name}</div>
                    <div style="color: #b3b3b3; font-size: 0.9rem;">{artist_name}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                # Duration and popularity
                duration = format_duration(track.get('duration_ms', 0))
                popularity = track.get('popularity', 0)
                st.markdown(f"""
                <div style="color: #b3b3b3; font-size: 0.9rem; padding: 0.5rem 0;">
                    {duration}<br>
                    {popularity}% popularity
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                # Actions
                if st.button("ℹ️", key=f"listinfo_{list_id}_{idx}"):
                    show_track_details(track, artist_mapping, spotify_client)
        
        st.markdown("---") 