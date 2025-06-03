"""
Dashboard components for system monitoring and administrative features.
"""

import streamlit as st
import os
from typing import Dict, Any
import pandas as pd


def create_logging_dashboard() -> None:
    """Create a logging dashboard in the sidebar."""
    try:
        from logging_config import get_log_stats, get_logger, log_user_action, log_performance
        logger = get_logger()
        ADVANCED_LOGGING = True
    except ImportError:
        ADVANCED_LOGGING = False
    
    if ADVANCED_LOGGING:
        with st.sidebar.expander("📊 Logging Dashboard", expanded=False):
            st.markdown("#### System Logging Status")
            
            # Get logging statistics
            log_stats = get_log_stats()
            
            # Display key metrics
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Log Level", log_stats.get('log_level', 'INFO'))
                st.metric("Handlers", log_stats.get('handlers', 0))
            
            with col2:
                st.metric("File Logging", "✅" if log_stats.get('file_logging_enabled') else "❌")
                st.metric("Performance", "✅" if log_stats.get('performance_logging_enabled') else "❌")
            
            # Log files information
            if log_stats.get('log_files'):
                st.markdown("#### 📁 Log Files")
                for log_file in log_stats['log_files'][:5]:  # Show top 5 files
                    file_size = log_file.get('size_mb', 0)
                    st.text(f"{log_file['name']}: {file_size:.2f} MB")
            
            # Environment variables
            st.markdown("#### ⚙️ Configuration")
            env_vars = [
                ('LOG_LEVEL', os.getenv('LOG_LEVEL', 'INFO')),
                ('ENABLE_FILE_LOGGING', os.getenv('ENABLE_FILE_LOGGING', 'true')),
                ('ENABLE_PERFORMANCE_LOGGING', os.getenv('ENABLE_PERFORMANCE_LOGGING', 'true')),
                ('ENABLE_JSON_LOGGING', os.getenv('ENABLE_JSON_LOGGING', 'false'))
            ]
            
            for env_var, value in env_vars:
                st.text(f"{env_var}: {value}")
            
            # Quick actions
            st.markdown("#### 🎛️ Quick Actions")
            if st.button("📝 Log Test Message", use_container_width=True):
                logger.info("Test message from logging dashboard")
                log_user_action("test_log_message", {"source": "dashboard"})
                st.success("Test message logged!")
            
            if st.button("📊 Log Performance Test", use_container_width=True):
                import time
                start = time.time()
                time.sleep(0.1)  # Simulate work
                duration = time.time() - start
                log_performance("test_operation", duration, {"test": True})
                st.success(f"Performance test logged: {duration:.3f}s")
    
    else:
        with st.sidebar.expander("📊 Basic Logging Info", expanded=False):
            st.info("Using basic logging configuration")
            st.text("Install advanced logging for more features")


def create_app_footer(
    tracks_count: int, 
    artists_count: int, 
    models_count: int, 
    spotify_connected: bool = False
) -> None:
    """
    Create footer with app statistics.
    
    Args:
        tracks_count (int): Number of tracks loaded
        artists_count (int): Number of artists
        models_count (int): Number of models loaded
        spotify_connected (bool): Whether Spotify API is connected
    """
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Tracks", f"{tracks_count:,}")
    with col2:
        st.metric("Artists", f"{artists_count:,}")
    with col3:
        st.metric("Models Loaded", models_count)
    with col4:
        if spotify_connected:
            st.metric("API Status", "✅ Connected")
        else:
            st.metric("API Status", "❌ Offline")


def create_sidebar_controls(
    spotify_client: Any = None,
    enable_audio_settings: bool = True
) -> Dict[str, Any]:
    """
    Create sidebar controls and return configuration.
    
    Args:
        spotify_client: Spotify API client
        enable_audio_settings (bool): Whether to show audio settings
        
    Returns:
        Dict[str, Any]: Configuration settings
    """
    st.sidebar.header("🎛️ Recommendation Controls")
    
    # Add logging dashboard to sidebar
    create_logging_dashboard()
    
    config = {}
    
    # Spotify API Status in sidebar
    if spotify_client:
        with st.sidebar.expander("🎵 Spotify API Status"):
            try:
                from spotify_api_client import display_spotify_api_status
                api_connected = display_spotify_api_status(spotify_client)
                if api_connected:
                    st.success("Enhanced features enabled!")
                    config['spotify_connected'] = True
                else:
                    st.info("Basic features only")
                    config['spotify_connected'] = False
            except ImportError:
                st.warning("Spotify API client not available")
                config['spotify_connected'] = False
    else:
        config['spotify_connected'] = False
    
    # Audio Settings
    if enable_audio_settings:
        with st.sidebar.expander("🔊 Audio Settings"):
            st.markdown("**Audio Preview Information:**")
            st.info("🎵 30-second previews from Spotify")
            st.markdown("- Click ▶️ to play audio previews")
            st.markdown("- Compare selected song with recommendations")
            st.markdown("- Some tracks may not have preview URLs")
            
            config['auto_play'] = st.checkbox("🎯 Focus on audio comparison", value=True, 
                                   help="Expand recommendations with audio for easy comparison")
            
            # Enhanced features toggle
            if spotify_client:
                config['enable_enhanced'] = st.checkbox("🚀 Enable enhanced Spotify features", value=True,
                                            help="Show artist info, album details, and discography (limited due to recent API changes)")
            else:
                config['enable_enhanced'] = False
    
    # Recommendation settings
    config['n_recommendations'] = st.sidebar.slider(
        "Number of Recommendations", 
        min_value=3, 
        max_value=10, 
        value=5
    )
    
    return config 


def create_audio_preview_analysis(tracks_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyze audio preview availability statistics in the dataset.
    
    Args:
        tracks_df (pd.DataFrame): Tracks dataframe
        
    Returns:
        Dict[str, Any]: Audio preview statistics
    """
    from utils.data_utils import check_audio_url
    
    total_tracks = len(tracks_df)
    
    # Check preview URL availability
    valid_urls = 0
    invalid_patterns = {
        'null_values': 0,
        'empty_strings': 0,
        'none_strings': 0,
        'invalid_format': 0
    }
    
    for _, track in tracks_df.iterrows():
        preview_url = track.get('preview_url', '')
        
        if pd.isna(preview_url):
            invalid_patterns['null_values'] += 1
        elif preview_url == '':
            invalid_patterns['empty_strings'] += 1
        elif preview_url == 'None':
            invalid_patterns['none_strings'] += 1
        elif not check_audio_url(preview_url):
            invalid_patterns['invalid_format'] += 1
        else:
            valid_urls += 1
    
    # Calculate percentages
    coverage_percentage = (valid_urls / total_tracks) * 100 if total_tracks > 0 else 0
    
    # Find examples of songs with and without previews
    has_preview = tracks_df[tracks_df['preview_url'].apply(check_audio_url)]
    no_preview = tracks_df[~tracks_df['preview_url'].apply(check_audio_url)]
    
    stats = {
        'total_tracks': total_tracks,
        'valid_previews': valid_urls,
        'invalid_previews': total_tracks - valid_urls,
        'coverage_percentage': coverage_percentage,
        'invalid_patterns': invalid_patterns,
        'examples_with_preview': has_preview.head(3)[['name', 'artists_id', 'popularity']].to_dict('records') if not has_preview.empty else [],
        'examples_without_preview': no_preview.head(3)[['name', 'artists_id', 'popularity']].to_dict('records') if not no_preview.empty else []
    }
    
    return stats


def display_audio_preview_analysis(tracks_df: pd.DataFrame):
    """
    Display audio preview analysis in the sidebar.
    
    Args:
        tracks_df (pd.DataFrame): Tracks dataframe
    """
    with st.sidebar.expander("📊 Audio Preview Statistics", expanded=False):
        stats = create_audio_preview_analysis(tracks_df)
        
        st.markdown("#### 🎵 Preview Availability")
        
        # Main statistics
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Tracks", f"{stats['total_tracks']:,}")
            st.metric("Valid Previews", f"{stats['valid_previews']:,}")
        
        with col2:
            st.metric("Coverage", f"{stats['coverage_percentage']:.1f}%")
            st.metric("Missing", f"{stats['invalid_previews']:,}")
        
        # Breakdown of missing preview reasons
        st.markdown("#### 🚨 Missing Preview Breakdown")
        for pattern, count in stats['invalid_patterns'].items():
            percentage = (count / stats['total_tracks']) * 100 if stats['total_tracks'] > 0 else 0
            st.text(f"{pattern.replace('_', ' ').title()}: {count:,} ({percentage:.1f}%)")
        
        # Examples
        if stats['examples_without_preview']:
            st.markdown("#### ❌ Example Songs Without Previews")
            for example in stats['examples_without_preview']:
                st.text(f"• {example['name']}")
        
        if stats['examples_with_preview']:
            st.markdown("#### ✅ Example Songs With Previews")
            for example in stats['examples_with_preview']:
                st.text(f"• {example['name']}")


def search_song_by_name(tracks_df: pd.DataFrame, song_name: str) -> pd.DataFrame:
    """
    Search for songs by name and return details including preview URL status.
    
    Args:
        tracks_df (pd.DataFrame): Tracks dataframe
        song_name (str): Song name to search for
        
    Returns:
        pd.DataFrame: Matching songs with preview URL analysis
    """
    from utils.data_utils import check_audio_url
    
    # Case-insensitive search
    matches = tracks_df[tracks_df['name'].str.contains(song_name, case=False, na=False)].copy()
    
    if not matches.empty:
        # Add preview URL status
        matches['has_preview'] = matches['preview_url'].apply(check_audio_url)
        matches['preview_status'] = matches['preview_url'].apply(
            lambda x: 'Valid' if check_audio_url(x) else 
                     'Null' if pd.isna(x) else 
                     'Empty' if x == '' else 
                     'None String' if x == 'None' else 
                     'Invalid Format'
        )
    
    return matches 