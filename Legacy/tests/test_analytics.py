import pytest
import tempfile
import os
from streamlit_app.utils.analytics import UserAnalytics

def test_track_and_get_popular_searches(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        analytics = UserAnalytics(data_path=tmpdir)
        analytics.track_search('test query', 2, {'genre': 'pop'})
        analytics._save_search_history()
        popular = analytics.get_popular_searches()
        assert 'test query' in popular

def test_track_and_get_recommendation_insights(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        analytics = UserAnalytics(data_path=tmpdir)
        analytics.track_recommendation_click(0, 1, 'cluster', 0.1)
        analytics._save_recommendation_clicks()
        insights = analytics.get_recommendation_insights()
        assert 'total_clicks' in insights 