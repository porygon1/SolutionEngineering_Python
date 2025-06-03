"""
Track card components for displaying song information and recommendations.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional
from utils.data_utils import get_artist_name, format_duration, get_key_name, get_mode_name, check_audio_url


def get_comprehensive_track_info(track_data: pd.Series, artist_mapping: Dict[str, str]) -> Dict[str, Any]:
    """
    Get comprehensive track information for detailed view.
    
    Args:
        track_data (pd.Series): Track data
        artist_mapping (Dict[str, str]): Artist ID to name mapping
        
    Returns:
        Dict[str, Any]: Comprehensive track information
    """
    artist_name = get_artist_name(track_data.get('artists_id', ''), artist_mapping)
    
    # Basic information
    info = {
        'basic': {
            'Track Name': track_data.get('name', 'Unknown'),
            'Artist': artist_name,
            'Duration': format_duration(track_data.get('duration_ms', 0)),
            'Popularity': f"{track_data.get('popularity', 0)}/100",
            'Release Year': str(track_data.get('year', 'Unknown')) if pd.notna(track_data.get('year')) else 'Unknown'
        },
        'musical': {
            'Key': get_key_name(track_data.get('key')),
            'Mode': get_mode_name(track_data.get('mode')),
            'Time Signature': f"{int(track_data.get('time_signature', 4))}/4" if pd.notna(track_data.get('time_signature')) else 'Unknown',
            'Tempo': f"{int(track_data.get('tempo', 0))} BPM" if pd.notna(track_data.get('tempo')) else 'Unknown',
            'Loudness': f"{track_data.get('loudness', 0):.1f} dB" if pd.notna(track_data.get('loudness')) else 'Unknown'
        },
        'audio_features': {
            'Primary': {
                'Danceability': track_data.get('danceability', 0),
                'Energy': track_data.get('energy', 0),
                'Valence': track_data.get('valence', 0),
                'Acousticness': track_data.get('acousticness', 0)
            },
            'Secondary': {
                'Instrumentalness': track_data.get('instrumentalness', 0),
                'Liveness': track_data.get('liveness', 0),
                'Speechiness': track_data.get('speechiness', 0)
            }
        }
    }
    
    return info


def create_spotify_track_card(
    track_data: pd.Series, 
    similarity_score: Optional[float] = None, 
    artist_mapping: Optional[Dict[str, str]] = None, 
    show_audio: bool = True, 
    card_id: str = "card"
) -> Tuple[Dict[str, Any], List[str], str]:
    """
    Create an expandable Spotify-style track card with both compact and detailed views.
    
    Args:
        track_data (pd.Series): Track data
        similarity_score (Optional[float]): Similarity score for recommendations
        artist_mapping (Optional[Dict[str, str]]): Artist ID to name mapping
        show_audio (bool): Whether to show audio player
        card_id (str): Unique card identifier
        
    Returns:
        Tuple[Dict[str, Any], List[str], str]: Track info, stats items, and artist name
    """
    artist_name = get_artist_name(track_data.get('artists_id', ''), artist_mapping)
    
    # Get comprehensive track information
    track_info = get_comprehensive_track_info(track_data, artist_mapping)
    
    # Create compact stats items
    stats_items = []
    if not pd.isna(track_data.get('popularity')):
        popularity = int(track_data.get('popularity'))
        stats_items.append(f"🔥{popularity}")
    if not pd.isna(track_data.get('tempo')):
        tempo = int(track_data.get('tempo'))
        stats_items.append(f"♪{tempo}")
    
    key_name = get_key_name(track_data.get('key'))
    mode_name = get_mode_name(track_data.get('mode'))
    if key_name != "Unknown" and mode_name != "Unknown":
        stats_items.append(f"🎹{key_name}{mode_name[0]}")
    
    duration = format_duration(track_data.get('duration_ms', 0))
    if duration != "Unknown":
        stats_items.append(f"⏱️{duration}")
    
    return track_info, stats_items, artist_name


def display_simple_card(
    track_data: pd.Series, 
    track_info: Dict[str, Any], 
    stats_items: List[str], 
    artist_name: str, 
    similarity_score: Optional[float] = None, 
    show_audio: bool = True
) -> None:
    """
    Display a simplified card using Streamlit components.
    
    Args:
        track_data (pd.Series): Track data
        track_info (Dict[str, Any]): Comprehensive track information
        stats_items (List[str]): Quick stats items
        artist_name (str): Artist name
        similarity_score (Optional[float]): Similarity score
        show_audio (bool): Whether to show audio player
    """
    # Create a visually appealing card container
    with st.container():
        # Card header with gradient background
        st.markdown(f"""
        <div style="background: linear-gradient(90deg, #1DB954, #1ed760); 
                    padding: 12px; margin: 8px 0; border-radius: 8px;">
            <h4 style="color: white; margin: 0; font-size: 16px;">{track_data.get('name', 'Unknown Track')}</h4>
            <p style="color: rgba(255,255,255,0.9); margin: 4px 0 0 0; font-size: 12px;">by {artist_name}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Similarity score (if available)
        if similarity_score is not None:
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                st.metric("Similarity", f"{similarity_score:.3f}")
        
        # Quick stats in a clean layout
        if stats_items:
            st.markdown("**Stats:**")
            cols = st.columns(len(stats_items))
            for i, stat in enumerate(stats_items):
                with cols[i]:
                    st.info(stat)
        
        # Audio features with progress bars
        st.markdown("**Audio Features:**")
        features_data = []
        for feature, label in [
            ('danceability', 'Dance'),
            ('energy', 'Energy'), 
            ('valence', 'Happy'),
            ('acousticness', 'Acoustic')
        ]:
            value = track_data.get(feature, 0)
            if not pd.isna(value):
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.text(f"{label}:")
                with col2:
                    st.progress(value, text=f"{value:.2f}")
        
        # Audio player
        if show_audio:
            st.markdown("**🎧 Audio Preview:**")
            preview_url = track_data.get('preview_url', '')
            if check_audio_url(preview_url):
                st.audio(preview_url, format='audio/mpeg')
            else:
                st.warning("No audio preview available")


def create_detailed_view(track_info: Dict[str, Any]) -> None:
    """
    Create detailed information view for expanded cards using Streamlit components.
    
    Args:
        track_info (Dict[str, Any]): Comprehensive track information
    """
    # Basic Information Section
    st.markdown("#### 📋 Basic Information")
    
    # Create a clean data display using columns
    basic_col1, basic_col2 = st.columns(2)
    
    basic_items = list(track_info['basic'].items())
    mid_point = len(basic_items) // 2
    
    with basic_col1:
        for label, value in basic_items[:mid_point]:
            st.text(f"{label}: {value}")
    
    with basic_col2:
        for label, value in basic_items[mid_point:]:
            st.text(f"{label}: {value}")
    
    st.markdown("---")
    
    # Musical Information Section
    st.markdown("#### 🎼 Musical Properties")
    
    musical_col1, musical_col2 = st.columns(2)
    
    musical_items = list(track_info['musical'].items())
    mid_point = len(musical_items) // 2
    
    with musical_col1:
        for label, value in musical_items[:mid_point]:
            st.text(f"{label}: {value}")
    
    with musical_col2:
        for label, value in musical_items[mid_point:]:
            st.text(f"{label}: {value}")
    
    st.markdown("---")
    
    # Primary Audio Features
    st.markdown("#### 🎵 Primary Audio Features")
    
    primary_features = track_info['audio_features']['Primary']
    for feature_name, value in primary_features.items():
        if not pd.isna(value):
            col1, col2, col3 = st.columns([2, 3, 1])
            
            with col1:
                st.text(feature_name)
            
            with col2:
                st.progress(value)
            
            with col3:
                st.text(f"{value:.3f}")
    
    st.markdown("---")
    
    # Advanced Audio Features
    st.markdown("#### 🔧 Advanced Audio Features")
    
    secondary_features = track_info['audio_features']['Secondary']
    for feature_name, value in secondary_features.items():
        if not pd.isna(value):
            col1, col2, col3 = st.columns([2, 3, 1])
            
            with col1:
                st.text(feature_name)
            
            with col2:
                st.progress(value)
            
            with col3:
                st.text(f"{value:.3f}")


def display_recommendations_with_cards(
    tracks_df: pd.DataFrame, 
    rec_indices: Optional[List[int]], 
    rec_distances: Optional[List[float]], 
    title: str, 
    description: str, 
    artist_mapping: Dict[str, str], 
    spotify_client: Any = None, 
    enable_enhanced: bool = False
) -> None:
    """
    Display recommendations as expandable cards in a grid layout with optional Spotify API enhancements.
    
    Args:
        tracks_df (pd.DataFrame): Tracks dataframe
        rec_indices (Optional[List[int]]): Recommendation indices
        rec_distances (Optional[List[float]]): Recommendation distances
        title (str): Section title
        description (str): Section description
        artist_mapping (Dict[str, str]): Artist ID to name mapping
        spotify_client (Any): Spotify API client
        enable_enhanced (bool): Whether to enable enhanced features
    """
    try:
        from logging_config import get_logger
        logger = get_logger()
        logger.info(f"Displaying recommendations: {title}")
        logger.debug(f"Number of recommendations: {len(rec_indices) if rec_indices is not None else 0}")
    except:
        import logging
        logger = logging.getLogger(__name__)
    
    st.markdown(f"<div class='feature-set-header'><h4>{title}</h4></div>", unsafe_allow_html=True)
    st.markdown(f"*{description}*")
    
    if rec_indices is None or rec_distances is None:
        logger.error("Unable to generate recommendations - indices or distances are None")
        st.error("Unable to generate recommendations")
        return
    
    # Skip the first result if it's the same song
    start_idx = 1 if len(rec_indices) > 1 and rec_indices[0] == tracks_df.index[0] else 0
    
    # Display recommendations using columns for grid layout
    recommendations_to_show = list(zip(rec_indices[start_idx:], rec_distances[start_idx:]))[:5]
    
    # Create grid layout with columns
    num_cols = min(3, len(recommendations_to_show))
    if len(recommendations_to_show) > 0:
        # Display in rows of up to 3 cards
        for row_start in range(0, len(recommendations_to_show), num_cols):
            row_recs = recommendations_to_show[row_start:row_start + num_cols]
            cols = st.columns(len(row_recs))
            
            for col_idx, (idx, distance) in enumerate(row_recs):
                with cols[col_idx]:
                    rec_song = tracks_df.iloc[idx]
                    similarity_score = 1 - distance
                    rec_num = row_start + col_idx + 1
                    
                    logger.debug(f"Displaying recommendation #{rec_num}: {rec_song.get('name', 'Unknown')} (similarity: {similarity_score:.3f})")
                    
                    # Create the recommendation header
                    st.markdown(f"""
                    <div class="recommendation-header">#{rec_num} Recommendation</div>
                    """, unsafe_allow_html=True)
                
                    # Get track info and display compact card
                    track_info, stats_items, artist_name = create_spotify_track_card(
                        rec_song, 
                        similarity_score, 
                        artist_mapping, 
                        show_audio=True, 
                        card_id=f"rec_{rec_num}"
                    )
                    
                    # Display the compact card using proper rendering
                    display_simple_card(rec_song, track_info, stats_items, artist_name, similarity_score, show_audio=True)
                    
                    # Add expandable detailed view
                    with st.expander(f"📊 Detailed Analysis #{rec_num}", expanded=False):
                        create_detailed_view(track_info)
                        
                        # Enhanced Spotify features for recommendations
                        if spotify_client and enable_enhanced:
                            st.markdown("---")
                            st.markdown("#### 🎵 Enhanced Spotify Features")
                            st.info("💡 Limited enhanced features available - artist info, album details, and discography")
                            # Note: Avoiding nested expanders by providing info instead of full display
                        
                        # Additional insights
                        st.markdown("---")
                        st.markdown("#### 🎯 Why This Song Was Recommended")
                        
                        # Calculate feature similarities for explanation
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("**🎵 Audio Similarity Breakdown:**")
                            features_for_comparison = ['danceability', 'energy', 'valence', 'acousticness']
                            for feature in features_for_comparison:
                                value = rec_song.get(feature, 0)
                                if not pd.isna(value):
                                    st.markdown(f"- **{feature.title()}**: {value:.3f}")
                        
                        with col2:
                            st.markdown("**📈 Track Metrics:**")
                            st.markdown(f"- **Similarity Score**: {similarity_score:.3f}")
                            st.markdown(f"- **Popularity Rank**: {rec_song.get('popularity', 'N/A')}/100")
                            if not pd.isna(rec_song.get('tempo')):
                                st.markdown(f"- **Tempo**: {int(rec_song.get('tempo'))} BPM")
                            if not pd.isna(rec_song.get('loudness')):
                                st.markdown(f"- **Loudness**: {rec_song.get('loudness'):.1f} dB") 