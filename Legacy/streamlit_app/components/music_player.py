"""
Music Player Component - Spotify-inspired Player Interface
"""

import streamlit as st
import pandas as pd
import requests
from typing import Dict, Optional, List
import base64
from io import BytesIO
from PIL import Image
import plotly.graph_objects as go
from utils.data_utils import get_artist_name
from utils.formatting import format_duration

# Import get_album_cover from recommendations module
def get_album_cover(track, spotify_client):
    """Get album cover URL from recommendations module"""
    from .recommendations import get_album_cover as _get_album_cover
    return _get_album_cover(track, spotify_client)


def get_album_artwork(track_info: Dict, spotify_client=None) -> Optional[str]:
    """
    Get album artwork URL for a track.
    
    Args:
        track_info: Track information dictionary
        spotify_client: Optional Spotify API client
        
    Returns:
        URL to album artwork or None
    """
    # Try to get from Spotify API if available
    if spotify_client and track_info.get('id'):
        try:
            track = spotify_client.get_track_details(track_info['id'])
            if track.get('album', {}).get('images'):
                # Get the largest image (usually first)
                return track['album']['images'][0]['url']
        except Exception:
            pass
    
    # Fallback: try to get album artwork from album_id if available
    album_id = track_info.get('album_id')
    if album_id and spotify_client:
        try:
            album = spotify_client.get_album_details(album_id)
            if album.get('images'):
                return album['images'][0]['url']
        except Exception:
            pass
    
    return None


def create_album_cover_display(track_info: Dict, artist_name: str, spotify_client=None) -> str:
    """
    Create an album cover display with fallback options.
    
    Args:
        track_info: Track information
        artist_name: Artist name
        spotify_client: Optional Spotify client
        
    Returns:
        HTML string for album cover display
    """
    artwork_url = get_album_artwork(track_info, spotify_client)
    
    if artwork_url:
        return f"""
        <div class="album-cover-container">
            <img src="{artwork_url}" 
                 class="album-cover" 
                 style="width: 300px; height: 300px; border-radius: 15px; object-fit: cover; 
                        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);"
                 alt="Album cover for {track_info.get('name', 'Unknown')}"
                 onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
            <div class="album-cover-fallback" 
                 style="width: 300px; height: 300px; background: linear-gradient(135deg, #1db954, #1ed760); 
                        display: none; align-items: center; justify-content: center; 
                        border-radius: 15px; font-size: 4rem; color: white; flex-direction: column;">
                🎵
                <div style="font-size: 1rem; margin-top: 1rem; text-align: center; padding: 0 1rem;">
                    {track_info.get('name', 'Unknown Track')[:30]}
                </div>
            </div>
        </div>
        """
    else:
        # Create a beautiful gradient fallback with track info
        gradient_colors = [
            "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
            "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
            "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
            "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)",
            "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
            "linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)",
            "linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%)",
            "linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)"
        ]
        
        # Use track name hash to select consistent gradient
        track_hash = hash(track_info.get('name', '')) % len(gradient_colors)
        selected_gradient = gradient_colors[track_hash]
        
        return f"""
        <div class="album-cover-container">
            <div class="album-cover-fallback" 
                 style="width: 300px; height: 300px; background: {selected_gradient}; 
                        display: flex; align-items: center; justify-content: center; 
                        border-radius: 15px; color: white; flex-direction: column;
                        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);">
                <div style="font-size: 4rem; margin-bottom: 1rem;">🎵</div>
                <div style="font-size: 1rem; text-align: center; padding: 0 1rem; font-weight: 500;">
                    {track_info.get('name', 'Unknown Track')[:25]}{'...' if len(track_info.get('name', '')) > 25 else ''}
                </div>
                <div style="font-size: 0.8rem; opacity: 0.8; margin-top: 0.5rem;">
                    {artist_name[:20]}{'...' if len(artist_name) > 20 else ''}
                </div>
            </div>
        </div>
        """


def create_audio_player_controls(track_info: Dict) -> str:
    """
    Create enhanced audio player controls.
    
    Args:
        track_info: Track information
        
    Returns:
        HTML for audio controls
    """
    preview_url = track_info.get('preview_url')
    
    if pd.notna(preview_url) and preview_url:
        return f"""
        <div class="audio-controls">
            <div style="display: flex; align-items: center; gap: 1rem;">
                <div class="now-playing">
                    <div class="sound-wave"></div>
                    <div class="sound-wave"></div>
                    <div class="sound-wave"></div>
                    <div class="sound-wave"></div>
                    <span style="margin-left: 0.5rem;">Preview Available</span>
                </div>
            </div>
        </div>
        """
    else:
        return """
        <div style="padding: 1rem; background: rgba(255, 255, 255, 0.1); border-radius: 10px; text-align: center;">
            <span style="opacity: 0.7;">🎵 No preview available</span>
        </div>
        """


def create_track_metadata_display(track_info: Dict, artist_name: str) -> str:
    """
    Create a rich metadata display for the track.
    
    Args:
        track_info: Track information
        artist_name: Artist name
        
    Returns:
        HTML for metadata display
    """
    def format_duration(duration_ms):
        if pd.isna(duration_ms) or duration_ms == 0:
            return "Unknown"
        duration_s = int(duration_ms / 1000)
        minutes = duration_s // 60
        seconds = duration_s % 60
        return f"{minutes}:{seconds:02d}"
    
    def get_key_name(key_number):
        key_map = {
            0: "C", 1: "C#", 2: "D", 3: "D#", 4: "E", 5: "F",
            6: "F#", 7: "G", 8: "G#", 9: "A", 10: "A#", 11: "B"
        }
        return key_map.get(int(key_number) if pd.notna(key_number) else 0, "Unknown")
    
    def get_mode_name(mode_number):
        return "Major" if mode_number == 1 else "Minor"
    
    # Calculate additional metrics
    popularity = track_info.get('popularity', 0)
    if popularity >= 80:
        popularity_badge = "🔥 Viral"
    elif popularity >= 60:
        popularity_badge = "⭐ Popular"
    elif popularity >= 40:
        popularity_badge = "✨ Known"
    else:
        popularity_badge = "💎 Hidden Gem"
    
    energy = track_info.get('energy', 0)
    if energy >= 0.8:
        energy_badge = "⚡ High Energy"
    elif energy >= 0.5:
        energy_badge = "🔋 Moderate Energy"
    else:
        energy_badge = "😌 Chill"
    
    valence = track_info.get('valence', 0)
    if valence >= 0.7:
        mood_badge = "😄 Happy"
    elif valence >= 0.4:
        mood_badge = "😐 Neutral"
    else:
        mood_badge = "😢 Sad"
    
    return f"""
    <div class="music-card">
        <h2 style="margin: 0 0 0.5rem 0; color: #ffffff;">{track_info.get('name', 'Unknown Track')}</h2>
        <h4 style="margin: 0 0 1.5rem 0; color: #1db954;">by {artist_name}</h4>
        
        <div style="margin: 1.5rem 0; display: flex; flex-wrap: wrap; gap: 0.5rem;">
            <span class="stat-badge">{popularity_badge} ({popularity}/100)</span>
            <span class="stat-badge">⏱️ {format_duration(track_info.get('duration_ms', 0))}</span>
            <span class="stat-badge">🎵 {get_key_name(track_info.get('key', 0))} {get_mode_name(track_info.get('mode', 0))}</span>
            <span class="stat-badge">🎼 {track_info.get('tempo', 0):.0f} BPM</span>
            <span class="stat-badge">{energy_badge}</span>
            <span class="stat-badge">{mood_badge}</span>
        </div>
        
        <div style="margin: 1.5rem 0;">
            <h5 style="color: #1db954; margin: 0 0 1rem 0;">Audio Characteristics</h5>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                <div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.3rem;">
                        <span>Danceability</span>
                        <span>{track_info.get('danceability', 0):.2f}</span>
                    </div>
                    <div class="feature-meter" style="--value: {track_info.get('danceability', 0) * 100}%;"></div>
                </div>
                <div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.3rem;">
                        <span>Energy</span>
                        <span>{track_info.get('energy', 0):.2f}</span>
                    </div>
                    <div class="feature-meter" style="--value: {track_info.get('energy', 0) * 100}%;"></div>
                </div>
                <div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.3rem;">
                        <span>Valence</span>
                        <span>{track_info.get('valence', 0):.2f}</span>
                    </div>
                    <div class="feature-meter" style="--value: {track_info.get('valence', 0) * 100}%;"></div>
                </div>
                <div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.3rem;">
                        <span>Acousticness</span>
                        <span>{track_info.get('acousticness', 0):.2f}</span>
                    </div>
                    <div class="feature-meter" style="--value: {track_info.get('acousticness', 0) * 100}%;"></div>
                </div>
            </div>
        </div>
    </div>
    """


def create_lyrics_display(track_info: Dict) -> Optional[str]:
    """
    Create a beautiful lyrics display if lyrics are available.
    
    Args:
        track_info: Track information
        
    Returns:
        HTML for lyrics display or None
    """
    lyrics = track_info.get('lyrics')
    
    if pd.notna(lyrics) and lyrics.strip():
        # Clean up lyrics
        cleaned_lyrics = lyrics.replace('\n', '<br>').replace('\r', '')
        
        # Estimate reading time (average reading speed: 200 words per minute)
        word_count = len(lyrics.split())
        reading_time = max(1, round(word_count / 200))
        
        return f"""
        <div style="margin: 2rem 0;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                <h5 style="color: #1db954; margin: 0;">📝 Song Lyrics</h5>
                <small style="opacity: 0.7;">~{reading_time} min read</small>
            </div>
            <div class="lyrics-container">
                {cleaned_lyrics}
            </div>
        </div>
        """
    
    return None


def create_enhanced_audio_visualization(track_info: Dict) -> go.Figure:
    """
    Create an enhanced audio features visualization.
    
    Args:
        track_info: Track information
        
    Returns:
        Plotly figure
    """
    # Main audio features
    features = {
        'Danceability': track_info.get('danceability', 0),
        'Energy': track_info.get('energy', 0),
        'Valence': track_info.get('valence', 0),
        'Acousticness': track_info.get('acousticness', 0),
        'Instrumentalness': track_info.get('instrumentalness', 0),
        'Liveness': track_info.get('liveness', 0),
        'Speechiness': track_info.get('speechiness', 0)
    }
    
    # Create radar chart
    fig = go.Figure()
    
    # Add main trace
    fig.add_trace(go.Scatterpolar(
        r=list(features.values()),
        theta=list(features.keys()),
        fill='toself',
        name='Audio Features',
        line=dict(color='#1db954', width=3),
        fillcolor='rgba(29, 185, 84, 0.3)',
        hovertemplate='<b>%{theta}</b><br>Value: %{r:.2f}<extra></extra>'
    ))
    
    # Add average line for reference
    avg_values = [0.5] * len(features)
    fig.add_trace(go.Scatterpolar(
        r=avg_values,
        theta=list(features.keys()),
        line=dict(color='rgba(255, 255, 255, 0.3)', width=1, dash='dash'),
        name='Average',
        showlegend=False,
        hoverinfo='skip'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1],
                gridcolor='rgba(255, 255, 255, 0.2)',
                linecolor='rgba(255, 255, 255, 0.3)',
                tickfont=dict(color='white', size=10),
                showticklabels=True
            ),
            angularaxis=dict(
                gridcolor='rgba(255, 255, 255, 0.2)',
                linecolor='rgba(255, 255, 255, 0.3)',
                tickfont=dict(color='white', size=12)
            ),
            bgcolor='rgba(0,0,0,0)'
        ),
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white', size=12),
        height=450,
        title=dict(
            text="🎵 Audio Features Profile",
            x=0.5,
            font=dict(color='white', size=16)
        )
    )
    
    return fig


def render_bottom_player(track, artist_mapping, spotify_client):
    """Render the fixed bottom player using Streamlit components"""
    
    # Create a container for the player
    with st.container():
        st.markdown("---")
        st.markdown("### 🎵 Now Playing")
        
        # Player layout
        col1, col2, col3 = st.columns([2, 3, 2])
        
        with col1:
            # Album cover and track info
            render_player_track_info(track, artist_mapping, spotify_client)
        
        with col2:
            # Player controls
            render_player_controls(track)
        
        with col3:
            # Volume and additional controls
            render_player_volume_controls(track, spotify_client)

def get_album_cover_html(track, spotify_client):
    """Get album cover HTML with fallback"""
    
    album_image_url = get_album_cover(track, spotify_client)
    
    if album_image_url:
        return f'<img src="{album_image_url}" class="album-cover" alt="Album cover">'
    else:
        # Create gradient placeholder
        energy = track.get('energy', 0.5)
        valence = track.get('valence', 0.5)
        color_intensity = int(255 * energy)
        
        return f"""
        <div class="album-cover" style="
            background: linear-gradient(135deg, 
                rgba({color_intensity}, 185, 84, 0.8), 
                rgba({color_intensity//2}, 100, 150, 0.6));
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 1.5rem;
        ">
            🎵
        </div>
        """

def render_player_track_info(track, artist_mapping, spotify_client):
    """Render track info section of the player"""
    
    # Get track information
    track_name = track.get('name', 'Unknown Track')
    artist_name = get_artist_name(track.get('artists_id', ''), artist_mapping)
    
    # Try to get album cover
    album_image_url = get_album_cover_small(track, spotify_client)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        if album_image_url:
            st.image(album_image_url, width=60)
        else:
            # Small placeholder
            st.markdown("""
            <div style="
                width: 60px;
                height: 60px;
                background: linear-gradient(135deg, #1db954, #1ed760);
                border-radius: 8px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 1.5rem;
            ">🎵</div>
            """, unsafe_allow_html=True)
    
    with col2:
        # Track info
        st.markdown(f"""
        <div style="padding: 0.5rem 0;">
            <div style="color: white; font-weight: 500; font-size: 0.9rem;">
                {track_name[:30]}{'...' if len(track_name) > 30 else ''}
            </div>
            <div style="color: #b3b3b3; font-size: 0.8rem;">
                {artist_name[:25]}{'...' if len(artist_name) > 25 else ''}
            </div>
        </div>
        """, unsafe_allow_html=True)

def render_player_controls(track):
    """Render player control buttons"""
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("⏮️", key="prev_track", help="Previous"):
            # Previous track logic (placeholder)
            st.info("Previous track")
    
    with col2:
        # Play/Pause button
        is_playing = st.session_state.get('is_playing', False)
        
        if is_playing:
            if st.button("⏸️", key="pause_track", help="Pause"):
                st.session_state.is_playing = False
                st.rerun()
        else:
            if st.button("▶️", key="play_track", help="Play"):
                st.session_state.is_playing = True
                st.rerun()
    
    with col3:
        if st.button("⏭️", key="next_track", help="Next"):
            # Next track logic (placeholder)
            st.info("Next track")
    
    with col4:
        # Shuffle button
        shuffle_enabled = st.session_state.get('shuffle_enabled', False)
        
        if shuffle_enabled:
            if st.button("🔀", key="shuffle_off", help="Disable Shuffle"):
                st.session_state.shuffle_enabled = False
                st.rerun()
        else:
            if st.button("🔀", key="shuffle_on", help="Enable Shuffle"):
                st.session_state.shuffle_enabled = True
                st.rerun()
    
    with col5:
        # Repeat button
        repeat_enabled = st.session_state.get('repeat_enabled', False)
        
        if repeat_enabled:
            if st.button("🔁", key="repeat_off", help="Disable Repeat"):
                st.session_state.repeat_enabled = False
                st.rerun()
        else:
            if st.button("🔁", key="repeat_on", help="Enable Repeat"):
                st.session_state.repeat_enabled = True
                st.rerun()
    
    # Progress bar
    render_progress_bar(track)

def render_progress_bar(track):
    """Render a simulated progress bar"""
    
    # Get track duration
    duration_ms = track.get('duration_ms', 180000)  # Default 3 minutes
    duration_seconds = duration_ms / 1000
    
    # Simulate current position (for demo purposes)
    current_position = st.session_state.get('track_position', 0)
    
    col1, col2, col3 = st.columns([1, 8, 1])
    
    with col1:
        # Current time
        current_time = format_duration(current_position * 1000)
        st.markdown(f"<div class='time-display'>{current_time}</div>", 
                   unsafe_allow_html=True)
    
    with col2:
        # Progress slider
        progress = st.slider(
            "Track progress", 
            min_value=0, 
            max_value=int(duration_seconds),
            value=current_position,
            key="progress_slider",
            label_visibility="collapsed"
        )
        
        if progress != current_position:
            st.session_state.track_position = progress
    
    with col3:
        # Total duration
        total_time = format_duration(duration_ms)
        st.markdown(f"<div class='time-display'>{total_time}</div>", 
                   unsafe_allow_html=True)

def render_player_volume_controls(track, spotify_client):
    """Render volume and additional controls using Streamlit components"""
    
    st.markdown("**Controls**")
    
    # Volume control
    volume = st.slider(
        "Volume",
        min_value=0,
        max_value=100,
        value=st.session_state.get('volume', 75),
        key="volume_slider",
        label_visibility="collapsed"
    )
    
    if volume != st.session_state.get('volume', 75):
        st.session_state.volume = volume
    
    # Additional controls
    col1, col2 = st.columns(2)
    
    with col1:
        # Like/Save button
        is_liked = st.session_state.get(f'liked_{track.get("name", "")}', False)
        
        if is_liked:
            if st.button("💚", key="unlike_track", help="Remove from Liked"):
                st.session_state[f'liked_{track.get("name", "")}'] = False
                st.rerun()
        else:
            if st.button("🤍", key="like_track", help="Add to Liked"):
                st.session_state[f'liked_{track.get("name", "")}'] = True
                st.rerun()
    
    with col2:
        # More options
        if st.button("⋯", key="more_options", help="More options"):
            st.info("More options coming soon!")

def render_track_options(track, spotify_client):
    """Render additional track options"""
    
    with st.expander("🎵 Track Options", expanded=True):
        
        # Use vertical layout instead of columns to avoid nesting
        st.markdown("**Playback Options:**")
        
        if st.button("▶️ Preview Track", use_container_width=True, key="preview_track"):
            track_idx = track.name if hasattr(track, 'name') else st.session_state.current_track
            st.session_state.current_track = track_idx
            st.success("Now previewing track!")
            st.rerun()
        
        st.markdown("**Recommendation Options:**")
        
        if st.button("🎯 Get Similar Tracks", use_container_width=True, key="get_similar"):
            # Set this track for recommendations
            track_idx = track.name if hasattr(track, 'name') else st.session_state.current_track
            st.session_state.selected_track_idx = track_idx
            st.success("Getting recommendations for this track!")
            st.rerun()
        
        st.markdown("**Other Options:**")
        
        if st.button("📋 Add to Playlist", use_container_width=True, key="add_playlist"):
            st.info("Playlist feature coming soon!")
        
        if st.button("📤 Share Track", use_container_width=True, key="share_track"):
            # Get Spotify URL
            spotify_url = get_spotify_url(track, spotify_client)
            if spotify_url:
                st.code(spotify_url)
                st.success("Spotify URL copied above!")
            else:
                st.warning("Spotify URL not available")
        
        if st.button("ℹ️ Track Info", use_container_width=True, key="track_info"):
            render_detailed_track_info(track, spotify_client)

def render_detailed_track_info(track, spotify_client):
    """Render detailed track information"""
    
    st.markdown("#### 🎵 Track Details")
    
    # Basic info
    track_name = track.get('name', 'Unknown Track')
    duration = format_duration(track.get('duration_ms', 0))
    popularity = track.get('popularity', 0)
    year = track.get('year', 'Unknown')
    
    st.markdown(f"""
    **Track:** {track_name}  
    **Duration:** {duration}  
    **Popularity:** {popularity}%  
    **Year:** {year}  
    """)
    
    # Audio features
    st.markdown("#### 🎚️ Audio Features")
    
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
        percentage = int(value * 100)
        st.markdown(f"**{feature_name}:** {percentage}%")

def get_album_cover_small(track, spotify_client):
    """Get small album cover for player"""
    
    if not spotify_client:
        return None
    
    try:
        # Get Spotify ID
        spotify_id = None
        
        if 'id' in track and track['id'] and not pd.isna(track['id']):
            spotify_id = str(track['id']).strip()
        elif 'uri' in track and track['uri'] and not pd.isna(track['uri']):
            uri = str(track['uri']).strip()
            if uri.startswith('spotify:track:'):
                spotify_id = uri.split(':')[-1]
        
        if spotify_id:
            track_details = spotify_client.get_track_details(spotify_id)
            
            if track_details:
                album_images = track_details.get('album', {}).get('images', [])
                if album_images:
                    # Return smallest image for player
                    return album_images[-1]['url'] if len(album_images) > 1 else album_images[0]['url']
    except Exception as e:
        pass
    
    return None

def get_spotify_url(track, spotify_client):
    """Get Spotify URL for sharing"""
    
    if not spotify_client:
        return None
    
    try:
        # Get Spotify ID
        spotify_id = None
        
        if 'id' in track and track['id'] and not pd.isna(track['id']):
            spotify_id = str(track['id']).strip()
        elif 'uri' in track and track['uri'] and not pd.isna(track['uri']):
            uri = str(track['uri']).strip()
            if uri.startswith('spotify:track:'):
                spotify_id = uri.split(':')[-1]
        
        if spotify_id:
            track_details = spotify_client.get_track_details(spotify_id)
            
            if track_details:
                external_urls = track_details.get('external_urls', {})
                return external_urls.get('spotify')
    except Exception as e:
        pass
    
    return None

def render_complete_music_player(track, artist_name, spotify_client):
    """Render a complete music player interface (legacy function for compatibility)"""
    
    # This is the old function - redirect to new bottom player
    render_bottom_player(track, {}, spotify_client)

def render_mini_player(track, artist_mapping):
    """Render a minimal player for sidebar or compact view"""
    
    if track is None:
        return
    
    track_name = track.get('name', 'Unknown Track')
    artist_name = get_artist_name(track.get('artists_id', ''), artist_mapping)
    
    st.markdown(f"""
    <div style="
        background: rgba(29, 185, 84, 0.1);
        border-radius: 8px;
        padding: 0.5rem;
        margin: 0.5rem 0;
        border-left: 3px solid #1db954;
    ">
        <div style="color: white; font-weight: 500; font-size: 0.9rem;">
            🎵 {track_name[:25]}{'...' if len(track_name) > 25 else ''}
        </div>
        <div style="color: #b3b3b3; font-size: 0.8rem;">
            {artist_name[:20]}{'...' if len(artist_name) > 20 else ''}
        </div>
    </div>
    """, unsafe_allow_html=True) 

def render_player_controls(current_track):
    """Render the music player controls"""
    
    # Create player controls HTML
    controls_html = f"""
    <div class="player-controls">
        <div class="player-controls-left">
            <div class="album-cover">
                {f'<img src="{current_track["album"]["images"][0]["url"]}" alt="Album Cover">' if current_track.get('album', {}).get('images') else 
                '<div class="album-cover-placeholder"><span class="album-cover-text">No Cover</span></div>'}
            </div>
            <div class="track-info">
                <div class="track-title">{current_track['name']}</div>
                <div class="track-artist">{current_track['artists'][0]['name']}</div>
            </div>
        </div>
        <div class="player-controls-center">
            <div class="time-display">{format_time(current_time)}</div>
            <div class="progress-slider">
                <input type="range" min="0" max="100" value="{progress}" class="slider" id="progress-slider">
            </div>
            <div class="time-display">{format_time(duration)}</div>
        </div>
        <div class="player-controls-right">
            <div class="volume-controls">
                <span class="volume-icon">🔊</span>
                <input type="range" min="0" max="100" value="{volume}" class="slider" id="volume-slider">
            </div>
        </div>
    </div>
    """
    
    st.markdown(controls_html, unsafe_allow_html=True) 