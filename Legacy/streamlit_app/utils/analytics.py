"""
Analytics utilities for tracking user interactions and improving recommendations.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
import json
import os

class UserAnalytics:
    def __init__(self, data_path: str = "data/analytics"):
        self.data_path = data_path
        self._ensure_analytics_dir()
        
    def _ensure_analytics_dir(self):
        """Ensure analytics directory exists"""
        os.makedirs(self.data_path, exist_ok=True)
    
    def track_search(self, query: str, results_count: int, filters: Optional[Dict] = None):
        """Track search queries and results"""
        if 'search_history' not in st.session_state:
            st.session_state.search_history = []
            
        st.session_state.search_history.append({
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'results_count': results_count,
            'filters': filters
        })
        
        # Save to file periodically
        if len(st.session_state.search_history) >= 10:
            self._save_search_history()
    
    def track_recommendation_click(self, track_idx: int, recommendation_idx: int, 
                                 rec_type: str, distance: float):
        """Track when users click on recommendations"""
        if 'recommendation_clicks' not in st.session_state:
            st.session_state.recommendation_clicks = []
            
        st.session_state.recommendation_clicks.append({
            'timestamp': datetime.now().isoformat(),
            'track_idx': track_idx,
            'recommendation_idx': recommendation_idx,
            'rec_type': rec_type,
            'distance': distance
        })
        
        # Save to file periodically
        if len(st.session_state.recommendation_clicks) >= 10:
            self._save_recommendation_clicks()
    
    def track_play(self, track_idx: int, duration: float):
        """Track when users play tracks"""
        if 'play_history' not in st.session_state:
            st.session_state.play_history = []
            
        st.session_state.play_history.append({
            'timestamp': datetime.now().isoformat(),
            'track_idx': track_idx,
            'duration': duration
        })
        
        # Save to file periodically
        if len(st.session_state.play_history) >= 10:
            self._save_play_history()
    
    def _save_search_history(self):
        """Save search history to file"""
        if not st.session_state.search_history:
            return
            
        file_path = os.path.join(self.data_path, 'search_history.json')
        with open(file_path, 'a') as f:
            for entry in st.session_state.search_history:
                f.write(json.dumps(entry) + '\n')
        st.session_state.search_history = []
    
    def _save_recommendation_clicks(self):
        """Save recommendation clicks to file"""
        if not st.session_state.recommendation_clicks:
            return
            
        file_path = os.path.join(self.data_path, 'recommendation_clicks.json')
        with open(file_path, 'a') as f:
            for entry in st.session_state.recommendation_clicks:
                f.write(json.dumps(entry) + '\n')
        st.session_state.recommendation_clicks = []
    
    def _save_play_history(self):
        """Save play history to file"""
        if not st.session_state.play_history:
            return
            
        file_path = os.path.join(self.data_path, 'play_history.json')
        with open(file_path, 'a') as f:
            for entry in st.session_state.play_history:
                f.write(json.dumps(entry) + '\n')
        st.session_state.play_history = []
    
    def get_popular_searches(self, limit: int = 10) -> List[Dict]:
        """Get most popular search queries"""
        try:
            file_path = os.path.join(self.data_path, 'search_history.json')
            if not os.path.exists(file_path):
                return []
                
            searches = []
            with open(file_path, 'r') as f:
                for line in f:
                    searches.append(json.loads(line))
            
            # Count search frequencies
            search_counts = pd.DataFrame(searches)['query'].value_counts()
            return search_counts.head(limit).to_dict()
        except:
            return []
    
    def get_recommendation_insights(self) -> Dict:
        """Get insights about recommendation effectiveness"""
        try:
            file_path = os.path.join(self.data_path, 'recommendation_clicks.json')
            if not os.path.exists(file_path):
                return {}
                
            clicks = []
            with open(file_path, 'r') as f:
                for line in f:
                    clicks.append(json.loads(line))
            
            if not clicks:
                return {}
                
            df = pd.DataFrame(clicks)
            return {
                'total_clicks': len(df),
                'avg_distance': df['distance'].mean(),
                'rec_type_distribution': df['rec_type'].value_counts().to_dict()
            }
        except:
            return {} 