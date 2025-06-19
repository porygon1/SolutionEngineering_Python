import pytest
from streamlit_app.components.search_optimization import (
    create_optimized_search_index, vectorized_search, get_autocomplete_suggestions
)

def test_create_optimized_search_index(sample_tracks_df, sample_artist_mapping):
    idx = create_optimized_search_index(sample_tracks_df, sample_artist_mapping)
    assert 'search_text' in idx.columns
    assert 'artist_name' in idx.columns
    assert idx.iloc[0]['artist_name'] == 'Artist A'

def test_vectorized_search(sample_tracks_df, sample_artist_mapping):
    idx = create_optimized_search_index(sample_tracks_df, sample_artist_mapping)
    results = vectorized_search('Song A', idx)
    assert not results.empty
    assert results.iloc[0]['name'] == 'Song A'

def test_get_autocomplete_suggestions(sample_tracks_df, sample_artist_mapping):
    idx = create_optimized_search_index(sample_tracks_df, sample_artist_mapping)
    suggestions = get_autocomplete_suggestions('Son', idx)
    assert any('Song' in s for s in suggestions) 