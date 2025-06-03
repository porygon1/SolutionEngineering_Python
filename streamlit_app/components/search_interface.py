"""
Search interface components for finding and selecting songs.
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from utils.data_utils import get_artist_name, format_duration


def create_searchable_song_index(tracks_df: pd.DataFrame, artist_mapping: Dict[str, str]) -> pd.DataFrame:
    """
    Create a searchable index for songs with artist names resolved.
    
    Args:
        tracks_df (pd.DataFrame): Tracks dataframe
        artist_mapping (Dict[str, str]): Artist ID to name mapping
        
    Returns:
        pd.DataFrame: Searchable index dataframe
    """
    try:
        from logging_config import get_logger
        logger = get_logger()
        logger.info("Creating searchable song index")
    except:
        import logging
        logger = logging.getLogger(__name__)
    
    from datetime import datetime
    start_time = datetime.now()
    
    search_index = tracks_df[['name', 'artists_id', 'popularity']].copy()
    
    # Add resolved artist names
    search_index['artist_name'] = search_index['artists_id'].apply(
        lambda x: get_artist_name(x, artist_mapping)
    )
    
    # Create searchable text combining song name and artist
    search_index['search_text'] = (
        search_index['name'].astype(str) + " " + 
        search_index['artist_name'].astype(str)
    ).str.lower()
    
    # Create display name for dropdown
    search_index['display_name'] = (
        search_index['name'].astype(str) + " - " + 
        search_index['artist_name'].astype(str)
    )
    
    processing_time = (datetime.now() - start_time).total_seconds()
    logger.info(f"Created searchable index with {len(search_index)} tracks in {processing_time:.2f}s")
    
    return search_index


def fuzzy_search_songs(search_term: str, search_index: pd.DataFrame, max_results: int = 50) -> pd.DataFrame:
    """
    Perform fuzzy search on songs with scoring.
    
    Args:
        search_term (str): Search term
        search_index (pd.DataFrame): Searchable index
        max_results (int): Maximum number of results
        
    Returns:
        pd.DataFrame: Search results dataframe
    """
    try:
        from logging_config import get_logger
        logger = get_logger()
        logger.debug(f"Performing fuzzy search for term: '{search_term}', max_results: {max_results}")
    except:
        import logging
        logger = logging.getLogger(__name__)
    
    if not search_term or len(search_term.strip()) < 2:
        logger.debug("Search term too short, returning default results")
        return search_index.head(max_results)
    
    search_term = search_term.lower().strip()
    
    # Split search term into words for better matching
    search_words = search_term.split()
    
    # Calculate relevance scores
    scores = []
    for idx, row in search_index.iterrows():
        search_text = row['search_text']
        score = 0
        
        # Exact match gets highest score
        if search_term in search_text:
            score += 100
            
        # Bonus for matching at start of song name or artist
        song_name_lower = row['name'].lower()
        artist_name_lower = row['artist_name'].lower()
        
        if song_name_lower.startswith(search_term):
            score += 80
        elif artist_name_lower.startswith(search_term):
            score += 70
            
        # Word-by-word matching
        for word in search_words:
            if word in search_text:
                score += 20
                if word in song_name_lower:
                    score += 10  # Bonus for song name match
                if word in artist_name_lower:
                    score += 8   # Bonus for artist match
        
        # Popularity bonus (scaled)
        popularity = row.get('popularity', 0)
        if pd.notna(popularity):
            score += popularity * 0.1
            
        scores.append((idx, score))
    
    # Sort by score and return top results
    scores.sort(key=lambda x: x[1], reverse=True)
    top_indices = [idx for idx, score in scores[:max_results] if score > 0]
    
    result_count = len(top_indices)
    logger.debug(f"Fuzzy search returned {result_count} results for '{search_term}'")
    
    return search_index.loc[top_indices]


def create_song_search_interface(tracks_df: pd.DataFrame, search_index: pd.DataFrame) -> Optional[int]:
    """
    Create enhanced song search interface.
    
    Args:
        tracks_df (pd.DataFrame): Tracks dataframe
        search_index (pd.DataFrame): Searchable index
        
    Returns:
        Optional[int]: Selected song index or None
    """
    try:
        from logging_config import get_logger, log_user_action
        logger = get_logger()
        logger.debug("Creating song search interface")
    except:
        import logging
        logger = logging.getLogger(__name__)
        def log_user_action(*args, **kwargs): pass
    
    st.sidebar.markdown("### 🎵 Song Search & Selection")
    
    # Search input with help text
    search_term = st.sidebar.text_input(
        "🔍 Search for songs:",
        placeholder="Enter song name, artist, or both...",
        help="Search by song title, artist name, or both. Try 'Bohemian Rhapsody', 'Queen', or 'Queen Bohemian'"
    )
    
    # Log user search activity
    if search_term:
        logger.info(f"User search: '{search_term}'")
    
    # Search results
    if search_term and len(search_term.strip()) >= 2:
        with st.sidebar.container():
            st.markdown("**🔎 Search Results:**")
            
            # Perform search
            search_results = fuzzy_search_songs(search_term, search_index, max_results=50)
            
            if not search_results.empty:
                # Show number of results
                st.caption(f"Found {len(search_results)} matches")
                
                # Create options for selectbox
                search_options = []
                for idx, row in search_results.head(20).iterrows():  # Limit to top 20 for UI
                    popularity_indicator = "🔥" if row.get('popularity', 0) > 70 else "⭐" if row.get('popularity', 0) > 40 else ""
                    option_text = f"{row['display_name']} {popularity_indicator}"
                    search_options.append((option_text, idx))
                
                # Selection dropdown
                if search_options:
                    selected_option = st.sidebar.selectbox(
                        "Select a song:",
                        options=[opt[0] for opt in search_options],
                        key="song_search_select"
                    )
                    
                    # Get the selected index
                    selected_idx = next(opt[1] for opt in search_options if opt[0] == selected_option)
                    
                    # Log user selection
                    selected_song = tracks_df.loc[selected_idx]
                    logger.info(f"User selected song: '{selected_song['name']}' by {search_index.loc[selected_idx, 'artist_name']}")
                    log_user_action("song_selected_from_search", {
                        "song_name": selected_song['name'],
                        "search_term": search_term
                    })
                    
                    # Show preview of selected song
                    with st.sidebar.expander("📖 Song Preview", expanded=False):
                        st.write(f"**Song:** {selected_song['name']}")
                        st.write(f"**Artist:** {search_index.loc[selected_idx, 'artist_name']}")
                        if 'popularity' in selected_song and pd.notna(selected_song['popularity']):
                            st.write(f"**Popularity:** {selected_song['popularity']}/100")
                        if 'duration_ms' in selected_song and pd.notna(selected_song['duration_ms']):
                            duration = format_duration(selected_song['duration_ms'])
                            st.write(f"**Duration:** {duration}")
                    
                    return selected_idx
                else:
                    st.sidebar.warning("No valid search results found.")
                    return None
            else:
                st.sidebar.warning(f"No songs found matching '{search_term}'")
                st.sidebar.info("💡 Try searching with different keywords or check spelling")
                return None
    
    elif search_term and len(search_term.strip()) < 2:
        st.sidebar.info("Please enter at least 2 characters to search")
        return None
    
    else:
        # No search term - show popular songs and random option
        st.sidebar.markdown("**🎲 Quick Options:**")
        
        col1, col2 = st.sidebar.columns(2)
        
        with col1:
            if st.button("🎲 Random Song", use_container_width=True):
                random_idx = np.random.randint(0, len(tracks_df))
                logger.info(f"User selected random song at index: {random_idx}")
                log_user_action("random_song_selected", {"song_index": random_idx})
                return random_idx
        
        with col2:
            if st.button("🔥 Popular Song", use_container_width=True):
                # Get a random popular song (popularity > 60)
                popular_songs = search_index[search_index['popularity'] > 60]
                if not popular_songs.empty:
                    selected_idx = popular_songs.sample(1).index[0]
                    logger.info(f"User selected popular song at index: {selected_idx}")
                    log_user_action("popular_song_selected", {"song_index": selected_idx})
                    return selected_idx
                else:
                    random_idx = np.random.randint(0, len(tracks_df))
                    logger.info(f"No popular songs found, selected random at index: {random_idx}")
                    log_user_action("fallback_random_song", {"song_index": random_idx})
                    return random_idx
        
        # Show some popular suggestions
        with st.sidebar.expander("💡 Song Suggestions", expanded=False):
            popular_songs = search_index.nlargest(10, 'popularity')
            st.markdown("**Popular tracks to try:**")
            for _, row in popular_songs.head(5).iterrows():
                if st.button(f"🎵 {row['name'][:20]}{'...' if len(row['name']) > 20 else ''}", 
                           key=f"suggest_{row.name}", use_container_width=True):
                    logger.info(f"User selected suggested song: '{row['name']}'")
                    log_user_action("suggested_song_selected", {
                        "song_name": row['name'],
                        "song_index": row.name
                    })
                    return row.name
        
        return None


def create_advanced_search_interface(search_index: pd.DataFrame) -> Optional[int]:
    """
    Create advanced search filters.
    
    Args:
        search_index (pd.DataFrame): Searchable index
        
    Returns:
        Optional[int]: Selected song index from filters or None
    """
    try:
        from logging_config import log_user_action
        def log_user_action(*args, **kwargs): pass
    except:
        def log_user_action(*args, **kwargs): pass
    
    with st.sidebar.expander("🔧 Advanced Search Filters", expanded=False):
        st.markdown("**Filter by popularity:**")
        popularity_range = st.slider(
            "Popularity Range",
            min_value=0,
            max_value=100,
            value=(0, 100),
            help="Filter songs by their popularity score"
        )
        
        # Artist filter
        st.markdown("**Filter by artist (partial name):**")
        artist_filter = st.text_input(
            "Artist contains:",
            placeholder="e.g., Beatles, Taylor",
            help="Show only songs from artists containing this text"
        )
        
        # Apply filters
        filtered_index = search_index.copy()
        
        # Apply popularity filter
        filtered_index = filtered_index[
            (filtered_index['popularity'] >= popularity_range[0]) & 
            (filtered_index['popularity'] <= popularity_range[1])
        ]
        
        # Apply artist filter
        if artist_filter:
            filtered_index = filtered_index[
                filtered_index['artist_name'].str.contains(artist_filter, case=False, na=False)
            ]
        
        # Show filter results
        if len(filtered_index) != len(search_index):
            st.info(f"Filters applied: {len(filtered_index):,} of {len(search_index):,} songs match")
            
            if len(filtered_index) > 0:
                # Quick select from filtered results
                if st.button("🎲 Random from Filtered", use_container_width=True):
                    selected_idx = filtered_index.sample(1).index[0]
                    log_user_action("filtered_random_selected", {
                        "popularity_range": popularity_range,
                        "artist_filter": artist_filter,
                        "song_index": selected_idx
                    })
                    return selected_idx
        
        return None 