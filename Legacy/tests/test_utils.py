import pytest
from streamlit_app.utils import (
    create_artist_mapping, get_artist_name, format_duration, get_key_name, get_mode_name
)

def test_create_artist_mapping(sample_tracks_df):
    artists_df = sample_tracks_df[['artists_id']].copy()
    artists_df['name'] = ['Artist A', 'Artist B']
    mapping = create_artist_mapping(artists_df)
    assert mapping['1'] == 'Artist A'
    assert mapping['2'] == 'Artist B'

def test_get_artist_name(sample_artist_mapping):
    assert get_artist_name('1', sample_artist_mapping) == 'Artist A'
    assert get_artist_name('2', sample_artist_mapping) == 'Artist B'
    assert get_artist_name('3', sample_artist_mapping) == 'Unknown Artist'

def test_format_duration():
    assert format_duration(200000) == '3:20'
    assert format_duration(180000) == '3:00'

def test_get_key_name():
    assert get_key_name(0) == 'C'
    assert get_key_name(1) == 'C# / Db'

def test_get_mode_name():
    assert get_mode_name(1) == 'Major'
    assert get_mode_name(0) == 'Minor' 