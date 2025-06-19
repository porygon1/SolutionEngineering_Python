"""
Enhanced Caching System for Spotify Music Recommendation System
Provides optimized caching with memory management and performance monitoring
"""

import streamlit as st
import pandas as pd
import numpy as np
import time
import hashlib
import pickle
from typing import Any, Dict, List, Optional, Callable, Tuple
from functools import wraps
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class EnhancedCacheManager:
    """Enhanced cache manager with performance optimizations"""
    
    def __init__(self, max_cache_size: int = 100, default_ttl: int = 3600):
        self.max_cache_size = max_cache_size
        self.default_ttl = default_ttl
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'memory_usage': 0
        }
        
        # Initialize cache in session state if not exists
        if 'enhanced_cache' not in st.session_state:
            st.session_state.enhanced_cache = {}
        if 'cache_metadata' not in st.session_state:
            st.session_state.cache_metadata = {}
    
    def _generate_cache_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """Generate a unique cache key for function calls"""
        try:
            # Create a string representation of args and kwargs
            key_data = f"{func_name}_{str(args)}_{str(sorted(kwargs.items()))}"
            return hashlib.md5(key_data.encode()).hexdigest()
        except Exception as e:
            logger.warning(f"Error generating cache key: {e}")
            return f"{func_name}_{time.time()}"
    
    def _is_cache_valid(self, key: str) -> bool:
        """Check if cache entry is still valid"""
        if key not in st.session_state.cache_metadata:
            return False
        
        metadata = st.session_state.cache_metadata[key]
        expiry_time = metadata.get('timestamp', 0) + metadata.get('ttl', self.default_ttl)
        return time.time() < expiry_time
    
    def _evict_expired_entries(self):
        """Remove expired cache entries"""
        current_time = time.time()
        expired_keys = []
        
        for key, metadata in st.session_state.cache_metadata.items():
            expiry_time = metadata.get('timestamp', 0) + metadata.get('ttl', self.default_ttl)
            if current_time >= expiry_time:
                expired_keys.append(key)
        
        for key in expired_keys:
            self._remove_cache_entry(key)
            self.cache_stats['evictions'] += 1
    
    def _evict_lru_entries(self):
        """Remove least recently used entries if cache is full"""
        if len(st.session_state.enhanced_cache) <= self.max_cache_size:
            return
        
        # Sort by last access time
        sorted_entries = sorted(
            st.session_state.cache_metadata.items(),
            key=lambda x: x[1].get('last_access', 0)
        )
        
        # Remove oldest entries
        entries_to_remove = len(st.session_state.enhanced_cache) - self.max_cache_size + 1
        for i in range(entries_to_remove):
            key = sorted_entries[i][0]
            self._remove_cache_entry(key)
            self.cache_stats['evictions'] += 1
    
    def _remove_cache_entry(self, key: str):
        """Remove a cache entry and its metadata"""
        if key in st.session_state.enhanced_cache:
            del st.session_state.enhanced_cache[key]
        if key in st.session_state.cache_metadata:
            del st.session_state.cache_metadata[key]
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self._is_cache_valid(key):
            self.cache_stats['misses'] += 1
            return None
        
        # Update last access time
        st.session_state.cache_metadata[key]['last_access'] = time.time()
        self.cache_stats['hits'] += 1
        
        return st.session_state.enhanced_cache.get(key)
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache"""
        # Clean up expired entries first
        self._evict_expired_entries()
        self._evict_lru_entries()
        
        # Store the value
        st.session_state.enhanced_cache[key] = value
        st.session_state.cache_metadata[key] = {
            'timestamp': time.time(),
            'last_access': time.time(),
            'ttl': ttl or self.default_ttl,
            'size': self._estimate_size(value)
        }
    
    def _estimate_size(self, obj: Any) -> int:
        """Estimate memory size of an object"""
        try:
            if isinstance(obj, pd.DataFrame):
                return obj.memory_usage(deep=True).sum()
            elif isinstance(obj, (list, dict)):
                return len(pickle.dumps(obj))
            else:
                return len(str(obj))
        except Exception:
            return 1000  # Default estimate
    
    def clear(self):
        """Clear all cache entries"""
        st.session_state.enhanced_cache = {}
        st.session_state.cache_metadata = {}
        self.cache_stats = {'hits': 0, 'misses': 0, 'evictions': 0, 'memory_usage': 0}
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = (self.cache_stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        # Calculate memory usage
        memory_usage = sum(
            metadata.get('size', 0) 
            for metadata in st.session_state.cache_metadata.values()
        )
        
        return {
            'entries': len(st.session_state.enhanced_cache),
            'hits': self.cache_stats['hits'],
            'misses': self.cache_stats['misses'],
            'evictions': self.cache_stats['evictions'],
            'hit_rate': f"{hit_rate:.1f}%",
            'memory_usage_mb': f"{memory_usage / (1024*1024):.2f}",
            'max_size': self.max_cache_size
        }

# Global cache manager instance
cache_manager = EnhancedCacheManager()

def enhanced_cache(ttl: int = 3600, max_entries: int = 50):
    """
    Enhanced caching decorator with better performance and memory management
    
    Args:
        ttl: Time to live in seconds
        max_entries: Maximum number of entries for this function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = cache_manager._generate_cache_key(func.__name__, args, kwargs)
            
            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result
            
            # Execute function and cache result
            logger.debug(f"Cache miss for {func.__name__}, executing...")
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Cache the result
            cache_manager.set(cache_key, result, ttl)
            
            logger.info(f"Cached {func.__name__} (execution: {execution_time:.2f}s)")
            return result
        
        return wrapper
    return decorator

@enhanced_cache(ttl=1800, max_entries=20)  # 30 minutes
def cached_search_operation(query: str, search_index: pd.DataFrame, 
                           filters: Dict[str, Any]) -> List[Dict]:
    """Cached search operation"""
    from components.search_optimization import vectorized_search, apply_advanced_filters
    
    # Perform vectorized search
    initial_results = vectorized_search(query, search_index)
    
    # Apply filters with proper parameters
    filtered_results = apply_advanced_filters(
        initial_results,
        year_range=filters.get('year_range'),
        popularity_min=filters.get('popularity', (0, 100))[0] if filters.get('popularity') else None,
        genre=filters.get('genres', [None])[0] if filters.get('genres') else None
    )
    
    # Convert DataFrame to list of dictionaries
    return filtered_results.to_dict('records')

@enhanced_cache(ttl=3600, max_entries=30)  # 1 hour
def cached_recommendations(track_idx: int, tracks_df: pd.DataFrame, 
                          _models: Dict, num_recommendations: int, 
                          recommendation_type: str) -> List[Dict]:
    """Cached recommendation generation (models prefixed with _ to avoid hashing)"""
    from utils.recommendations import get_recommendations_within_cluster, get_global_recommendations
    
    try:
        if recommendation_type == "cluster" and _models.get('labels') is not None:
            distances, indices = get_recommendations_within_cluster(
                _models['knn'], _models['embeddings'], 
                _models['labels'], track_idx, 
                n_neighbors=num_recommendations + 1
            )
        else:
            distances, indices = get_global_recommendations(
                _models['knn'], _models['embeddings'], 
                track_idx, 
                n_neighbors=num_recommendations + 1
            )
        
        if indices is not None:
            # Return recommendations (excluding the input track)
            rec_indices = indices[1:]  # Skip first one (input track)
            recommendations_df = tracks_df.iloc[rec_indices]
            return recommendations_df.to_dict('records')
        else:
            return []
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in cached_recommendations: {e}")
        return []

@enhanced_cache(ttl=7200, max_entries=10)  # 2 hours
def cached_data_processing(data_path: str, processing_type: str) -> pd.DataFrame:
    """Cached data processing operations"""
    if processing_type == "tracks":
        return pd.read_csv(data_path)
    elif processing_type == "artists":
        return pd.read_csv(data_path)
    else:
        raise ValueError(f"Unknown processing type: {processing_type}")

@enhanced_cache(ttl=1800, max_entries=15)  # 30 minutes
def cached_genre_analysis(tracks_df: pd.DataFrame) -> Dict[str, Any]:
    """Cached genre analysis"""
    # Extract unique genres
    all_genres = []
    for genres in tracks_df['genres'].dropna():
        if isinstance(genres, str):
            all_genres.extend([g.strip() for g in genres.split(',')])
        elif isinstance(genres, list):
            all_genres.extend(genres)
    
    genre_counts = pd.Series(all_genres).value_counts()
    
    return {
        'top_genres': genre_counts.head(20).to_dict(),
        'total_genres': len(genre_counts),
        'genre_distribution': genre_counts.describe().to_dict()
    }

@enhanced_cache(ttl=900, max_entries=25)  # 15 minutes
def cached_audio_features_analysis(tracks_df: pd.DataFrame, 
                                  feature_columns: List[str]) -> Dict[str, Any]:
    """Cached audio features analysis"""
    analysis = {}
    
    for feature in feature_columns:
        if feature in tracks_df.columns:
            feature_data = tracks_df[feature].dropna()
            analysis[feature] = {
                'mean': float(feature_data.mean()),
                'std': float(feature_data.std()),
                'min': float(feature_data.min()),
                'max': float(feature_data.max()),
                'median': float(feature_data.median())
            }
    
    return analysis

def optimize_dataframe_memory(df: pd.DataFrame) -> pd.DataFrame:
    """Optimize DataFrame memory usage"""
    optimized_df = df.copy()
    
    for col in optimized_df.columns:
        col_type = optimized_df[col].dtype
        
        if col_type != 'object':
            c_min = optimized_df[col].min()
            c_max = optimized_df[col].max()
            
            if str(col_type)[:3] == 'int':
                if c_min > np.iinfo(np.int8).min and c_max < np.iinfo(np.int8).max:
                    optimized_df[col] = optimized_df[col].astype(np.int8)
                elif c_min > np.iinfo(np.int16).min and c_max < np.iinfo(np.int16).max:
                    optimized_df[col] = optimized_df[col].astype(np.int16)
                elif c_min > np.iinfo(np.int32).min and c_max < np.iinfo(np.int32).max:
                    optimized_df[col] = optimized_df[col].astype(np.int32)
            
            elif str(col_type)[:5] == 'float':
                if c_min > np.finfo(np.float32).min and c_max < np.finfo(np.float32).max:
                    optimized_df[col] = optimized_df[col].astype(np.float32)
    
    return optimized_df

def chunk_dataframe_processing(df: pd.DataFrame, chunk_size: int = 1000, 
                              processing_func: Callable = None) -> pd.DataFrame:
    """Process large DataFrames in chunks"""
    if processing_func is None:
        return df
    
    chunks = []
    for i in range(0, len(df), chunk_size):
        chunk = df.iloc[i:i + chunk_size]
        processed_chunk = processing_func(chunk)
        chunks.append(processed_chunk)
    
    return pd.concat(chunks, ignore_index=True)

# Utility functions for cache management
def clear_all_caches():
    """Clear all caches"""
    cache_manager.clear()
    logger.info("All caches cleared")

def get_cache_statistics() -> Dict[str, Any]:
    """Get comprehensive cache statistics"""
    return cache_manager.get_stats()

def cleanup_expired_caches():
    """Clean up expired cache entries"""
    cache_manager._evict_expired_entries()
    logger.info("Expired cache entries cleaned up") 