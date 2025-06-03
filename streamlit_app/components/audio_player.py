"""
Audio player components for playing song previews.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any, Optional
from utils.data_utils import check_audio_url, get_artist_name


def display_audio_player(
    track_data: pd.Series, 
    title: str = "🎵 Audio Preview", 
    artist_mapping: Optional[Dict[str, str]] = None
) -> bool:
    """
    Display an audio player for a track with preview URL.
    
    Args:
        track_data (pd.Series): Track data
        title (str): Player title
        artist_mapping (Optional[Dict[str, str]]): Artist ID to name mapping
        
    Returns:
        bool: True if audio player was displayed, False otherwise
    """
    try:
        from logging_config import get_logger
        logger = get_logger()
        logger.debug(f"Displaying audio player for track: {track_data.get('name', 'Unknown')}")
    except:
        import logging
        logger = logging.getLogger(__name__)
    
    preview_url = track_data.get('preview_url', '')
    
    if check_audio_url(preview_url):
        st.markdown(f"### {title}")
        
        # Display track info with audio player
        artist_name = get_artist_name(track_data.get('artists_id', ''), artist_mapping)
        
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #1DB954, #1ed760);
            color: white;
            padding: 15px;
            border-radius: 10px;
            margin: 10px 0;
            box-shadow: 0 4px 12px rgba(29, 185, 84, 0.3);
        ">
            <h4 style="margin: 0 0 5px 0;">🎵 {track_data.get('name', 'Unknown Track')}</h4>
            <p style="margin: 0; opacity: 0.9;">👤 {artist_name}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Streamlit's built-in audio player
        st.audio(preview_url, format='audio/mp3')
        logger.info(f"Successfully displayed audio player for track: {track_data.get('name', 'Unknown')}")
        
        return True
    else:
        logger.debug(f"No audio preview available for track: {track_data.get('name', 'Unknown')}")
        st.warning(f"⚠️ No audio preview available for: **{track_data.get('name', 'Unknown Track')}**")
        return False 