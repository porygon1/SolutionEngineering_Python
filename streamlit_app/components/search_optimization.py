"""
Optimized search utilities for better performance with large datasets.
"""

import pandas as pd
import numpy as np
from typing import List, Tuple, Dict, Optional
import streamlit as st


@st.cache_data
def create_optimized_search_index(tracks_df: pd.DataFrame, artist_mapping: Dict[str, str]) -> pd.DataFrame:
    """
    Create an optimized search index using vectorized operations.
    
    Args:
        tracks_df: DataFrame with track information
        artist_mapping: Mapping from artist ID to name
        
    Returns:
        Optimized search index DataFrame
    """
    # Create a copy to avoid modifying original
    search_index = tracks_df.copy()
    
    # Vectorized artist name mapping
    search_index['artist_name'] = search_index['artists_id'].apply(
        lambda x: get_artist_name_optimized(x, artist_mapping)
    )
    
    # Create combined search text using vectorized operations
    search_index['search_text'] = (
        search_index['name'].fillna('').astype(str).str.lower() + ' ' +
        search_index['artist_name'].fillna('').astype(str).str.lower()
    )
    
    # Create display name
    search_index['display_name'] = (
        search_index['name'].astype(str) + ' - ' + search_index['artist_name'].astype(str)
    )
    
    return search_index


def get_artist_name_optimized(artist_id: str, artist_mapping: Dict[str, str]) -> str:
    """Optimized artist name retrieval."""
    if pd.isna(artist_id) or not artist_id or not artist_mapping:
        return "Unknown Artist"
    
    try:
        # Handle list format
        if isinstance(artist_id, str) and artist_id.startswith('['):
            import ast
            artist_ids = ast.literal_eval(artist_id)
            if isinstance(artist_ids, list) and artist_ids:
                return artist_mapping.get(artist_ids[0], "Unknown Artist")
        
        # Handle single ID
        return artist_mapping.get(str(artist_id), "Unknown Artist")
    except:
        return "Unknown Artist"


@st.cache_data
def vectorized_search(search_term: str, search_index: pd.DataFrame, max_results: int = 50) -> pd.DataFrame:
    """
    Perform vectorized search for better performance.
    
    Args:
        search_term: Search query
        search_index: Search index DataFrame
        max_results: Maximum number of results
        
    Returns:
        Filtered and scored results
    """
    if not search_term or len(search_term.strip()) < 2:
        return pd.DataFrame()
    
    search_term = search_term.lower().strip()
    search_words = search_term.split()
    
    # Vectorized scoring using pandas operations
    search_index = search_index.copy()
    
    # Initialize score column
    search_index['score'] = 0.0
    
    # Exact match scoring (vectorized)
    exact_match_mask = search_index['search_text'].str.contains(search_term, na=False, regex=False)
    search_index.loc[exact_match_mask, 'score'] += 100
    
    # Song name start matching
    song_start_mask = search_index['name'].str.lower().str.startswith(search_term, na=False)
    search_index.loc[song_start_mask, 'score'] += 90
    
    # Artist name start matching
    artist_start_mask = search_index['artist_name'].str.lower().str.startswith(search_term, na=False)
    search_index.loc[artist_start_mask, 'score'] += 80
    
    # Word-by-word matching (vectorized)
    for word in search_words:
        # General word match
        word_match_mask = search_index['search_text'].str.contains(word, na=False, regex=False)
        search_index.loc[word_match_mask, 'score'] += 25
        
        # Song name word match bonus
        song_word_mask = search_index['name'].str.lower().str.contains(word, na=False, regex=False)
        search_index.loc[song_word_mask, 'score'] += 15
        
        # Artist name word match bonus
        artist_word_mask = search_index['artist_name'].str.lower().str.contains(word, na=False, regex=False)
        search_index.loc[artist_word_mask, 'score'] += 10
    
    # Popularity bonus (vectorized)
    popularity_mask = search_index['popularity'].notna()
    search_index.loc[popularity_mask, 'score'] += search_index.loc[popularity_mask, 'popularity'] * 0.2
    
    # Filter results with score > 0 and sort
    results = search_index[search_index['score'] > 0].copy()
    results = results.sort_values('score', ascending=False).head(max_results)
    
    return results.drop('score', axis=1)


def get_top_suggestions(search_index: pd.DataFrame, n: int = 10) -> List[str]:
    """
    Get top song suggestions based on popularity (vectorized).
    
    Args:
        search_index: Search index DataFrame
        n: Number of suggestions
        
    Returns:
        List of popular song suggestions
    """
    # Vectorized popularity-based suggestions
    top_songs = search_index.nlargest(n, 'popularity', keep='first')
    return top_songs['display_name'].tolist()


@st.cache_data
def create_genre_filters(tracks_df: pd.DataFrame) -> Dict[str, List[str]]:
    """
    Create genre-based filters using vectorized operations.
    
    Args:
        tracks_df: Tracks DataFrame
        
    Returns:
        Dictionary of genre filters
    """
    filters = {}
    
    # Extract unique genres (if genre column exists)
    if 'genre' in tracks_df.columns:
        genres = tracks_df['genre'].dropna().unique().tolist()
        filters['genres'] = sorted(genres)
    
    # Extract year ranges
    if 'year' in tracks_df.columns:
        years = tracks_df['year'].dropna()
        if len(years) > 0:
            min_year, max_year = int(years.min()), int(years.max())
            filters['year_range'] = (min_year, max_year)
    
    # Extract popularity ranges
    if 'popularity' in tracks_df.columns:
        popularity = tracks_df['popularity'].dropna()
        if len(popularity) > 0:
            filters['popularity_range'] = (float(popularity.min()), float(popularity.max()))
    
    return filters


def apply_advanced_filters(search_index: pd.DataFrame, 
                          year_range: Optional[Tuple[int, int]] = None,
                          popularity_min: Optional[float] = None,
                          genre: Optional[str] = None) -> pd.DataFrame:
    """
    Apply advanced filters using vectorized operations.
    
    Args:
        search_index: Search index DataFrame
        year_range: Tuple of (min_year, max_year)
        popularity_min: Minimum popularity threshold
        genre: Genre filter
        
    Returns:
        Filtered DataFrame
    """
    filtered_df = search_index.copy()
    
    # Year filter (vectorized)
    if year_range and 'year' in filtered_df.columns:
        min_year, max_year = year_range
        year_mask = (filtered_df['year'] >= min_year) & (filtered_df['year'] <= max_year)
        filtered_df = filtered_df[year_mask]
    
    # Popularity filter (vectorized)
    if popularity_min is not None and 'popularity' in filtered_df.columns:
        popularity_mask = filtered_df['popularity'] >= popularity_min
        filtered_df = filtered_df[popularity_mask]
    
    # Genre filter (vectorized)
    if genre and 'genre' in filtered_df.columns:
        genre_mask = filtered_df['genre'].str.contains(genre, na=False, case=False)
        filtered_df = filtered_df[genre_mask]
    
    return filtered_df 