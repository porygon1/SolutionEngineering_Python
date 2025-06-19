"""
Cache utilities for optimizing performance.
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Any, Dict, List, Optional
import time
from functools import wraps

def cache_with_timeout(timeout: int = 3600):
    """
    Decorator to cache function results with a timeout.
    
    Args:
        timeout: Cache timeout in seconds (default: 1 hour)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create a unique key based on function name and arguments
            key = f"{func.__name__}_{str(args)}_{str(kwargs)}"
            
            # Check if we have a cached result
            if key in st.session_state:
                cached_result, timestamp = st.session_state[key]
                if time.time() - timestamp < timeout:
                    return cached_result
            
            # If no cache or expired, call the function
            result = func(*args, **kwargs)
            
            # Cache the result
            st.session_state[key] = (result, time.time())
            return result
        return wrapper
    return decorator

@st.cache_data(ttl=3600)
def cache_dataframe(df: pd.DataFrame, key: str) -> pd.DataFrame:
    """
    Cache a DataFrame with a timeout.
    
    Args:
        df: DataFrame to cache
        key: Unique key for caching
        
    Returns:
        Cached DataFrame
    """
    return df.copy()

@st.cache_data(ttl=3600)
def cache_numpy_array(arr: np.ndarray, key: str) -> np.ndarray:
    """
    Cache a NumPy array with a timeout.
    
    Args:
        arr: Array to cache
        key: Unique key for caching
        
    Returns:
        Cached array
    """
    return arr.copy()

@st.cache_data(ttl=3600)
def cache_dict(d: Dict, key: str) -> Dict:
    """
    Cache a dictionary with a timeout.
    
    Args:
        d: Dictionary to cache
        key: Unique key for caching
        
    Returns:
        Cached dictionary
    """
    return d.copy()

def clear_cache():
    """Clear all cached data"""
    for key in list(st.session_state.keys()):
        if key.startswith('_cached_'):
            del st.session_state[key]

def get_cache_stats() -> Dict[str, int]:
    """
    Get statistics about cached data.
    
    Returns:
        Dictionary with cache statistics
    """
    stats = {
        'total_cached_items': 0,
        'cached_dataframes': 0,
        'cached_arrays': 0,
        'cached_dicts': 0
    }
    
    for key in st.session_state.keys():
        if key.startswith('_cached_'):
            stats['total_cached_items'] += 1
            value = st.session_state[key]
            
            if isinstance(value, pd.DataFrame):
                stats['cached_dataframes'] += 1
            elif isinstance(value, np.ndarray):
                stats['cached_arrays'] += 1
            elif isinstance(value, dict):
                stats['cached_dicts'] += 1
    
    return stats 