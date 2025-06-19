import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
import numpy as np

@pytest.fixture(autouse=True)
def patch_streamlit(monkeypatch):
    mock_st = MagicMock()
    monkeypatch.setitem(__import__('sys').modules, 'streamlit', mock_st)
    yield mock_st

@pytest.fixture
def sample_tracks_df():
    return pd.DataFrame({
        'name': ['Song A', 'Song B'],
        'artists_id': ['1', '2'],
        'popularity': [80, 60],
        'year': [2020, 2021],
        'danceability': [0.8, 0.6],
        'energy': [0.7, 0.5],
        'genre': ['pop', 'rock'],
        'duration_ms': [200000, 180000]
    })

@pytest.fixture
def sample_artist_mapping():
    return {'1': 'Artist A', '2': 'Artist B'}

@pytest.fixture
def sample_embeddings():
    return np.array([[0.1, 0.2], [0.2, 0.3]]) 