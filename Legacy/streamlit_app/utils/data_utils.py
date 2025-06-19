"""
Data utilities for the Spotify Music Recommendation System.
Handles data loading, caching, and preprocessing.
"""

import streamlit as st
import pandas as pd
import numpy as np
import pickle
import os
import ast
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple


@st.cache_data
def load_data(file_path: str) -> pd.DataFrame:
    """
    Load and cache data from CSV file.
    
    Args:
        file_path (str): Path to the CSV file
        
    Returns:
        pd.DataFrame: Loaded dataframe
    """
    try:
        from logging_config import get_logger
        logger = get_logger()
        logger.info(f"Loading data from {file_path}")
        start_time = datetime.now()
        
        df = pd.read_csv(file_path)
        
        load_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Successfully loaded {len(df)} records from {file_path} in {load_time:.2f}s")
        
        return df
    except Exception as e:
        try:
            from logging_config import get_logger
            logger = get_logger()
            logger.error(f"Error loading data from {file_path}: {e}")
        except:
            pass
        st.error(f"Error loading data from {file_path}: {e}")
        return pd.DataFrame()


@st.cache_resource
def load_model(model_path: str) -> Optional[Any]:
    """
    Load and cache model from pickle file.
    
    Args:
        model_path (str): Path to the pickle file
        
    Returns:
        Optional[Any]: Loaded model or None if error
    """
    try:
        from logging_config import get_logger
        logger = get_logger()
        logger.info(f"Loading model from {model_path}")
        start_time = datetime.now()
        
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        
        load_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Successfully loaded model from {model_path} in {load_time:.2f}s")
        
        return model
    except Exception as e:
        try:
            from logging_config import get_logger
            logger = get_logger()
            logger.error(f"Error loading model from {model_path}: {e}")
        except:
            pass
        st.error(f"Error loading model from {model_path}: {e}")
        return None


@st.cache_resource
def load_all_models(model_paths: Dict[str, str]) -> Optional[Dict[str, Any]]:
    """
    Load all available recommendation models.
    
    Args:
        model_paths (Dict[str, str]): Dictionary mapping model names to file paths
        
    Returns:
        Optional[Dict[str, Any]]: Dictionary of loaded models or None if error
    """
    try:
        from logging_config import get_logger
        logger = get_logger()
        logger.info("Starting to load all models")
    except:
        import logging
        logger = logging.getLogger(__name__)
    
    models = {}
    
    # Check if models directory exists
    models_dir = Path(list(model_paths.values())[0]).parent
    if not models_dir.exists():
        logger.warning(f"Models directory does not exist: {models_dir}")
        return None
    
    for model_name, path in model_paths.items():
        if os.path.exists(path):
            models[model_name] = load_model(path)
            if models[model_name] is not None:
                logger.info(f"Successfully loaded model: {model_name}")
        else:
            logger.warning(f"Model {model_name} not found at {path}")
            st.warning(f"⚠️ Model {model_name} not found at {path}")
            models[model_name] = None
    
    successful_models = [name for name, model in models.items() if model is not None]
    logger.info(f"Loaded {len(successful_models)} models successfully: {successful_models}")
    
    return models


@st.cache_data
def create_artist_mapping(artists_df: pd.DataFrame) -> Dict[str, str]:
    """
    Create a mapping from artist ID to artist name.
    
    Args:
        artists_df (pd.DataFrame): Artists dataframe with 'id' and 'name' columns
        
    Returns:
        Dict[str, str]: Mapping from artist ID to name
    """
    try:
        from logging_config import get_logger
        logger = get_logger()
        logger.info("Creating artist mapping")
        logger.debug(f"Artists dataframe shape: {artists_df.shape}")
    except:
        import logging
        logger = logging.getLogger(__name__)
    
    if artists_df.empty:
        logger.warning("Artists dataframe is empty")
        return {}
    
    # Create mapping from id to name
    artist_mapping = {}
    if 'id' in artists_df.columns and 'name' in artists_df.columns:
        artist_mapping = dict(zip(artists_df['id'], artists_df['name']))
        logger.info(f"Created artist mapping with {len(artist_mapping)} entries")
    else:
        logger.error("Required columns 'id' or 'name' not found in artists dataframe")
    
    return artist_mapping


def get_artist_name(track_or_artist_id, artist_mapping: Dict[str, str]) -> str:
    """
    Get artist name from track data or artist ID using the mapping.
    
    Args:
        track_or_artist_id: Track data (dict/Series) or artist ID (str)
        artist_mapping (Dict[str, str]): Mapping from ID to name
        
    Returns:
        str: Artist name(s) or "Unknown Artist"
    """
    if artist_mapping is None:
        return "Unknown Artist"
    
    # Handle pandas Series or dict (track data)
    if isinstance(track_or_artist_id, (pd.Series, dict)):
        # Extract artist ID from track data
        artist_id = track_or_artist_id.get('artists_id', track_or_artist_id.get('artist_id', ''))
    else:
        # Direct artist ID
        artist_id = track_or_artist_id
    
    # Check for empty or null values
    if pd.isna(artist_id) or artist_id == '' or artist_id is None:
        return "Unknown Artist"
    
    try:
        # Handle string representation of Python list format like "['3mxJuHRn2ZWD5OofvJtDZY']"
        if isinstance(artist_id, str) and artist_id.startswith('[') and artist_id.endswith(']'):
            # Parse the string as a Python list
            artist_ids = ast.literal_eval(artist_id)
        elif isinstance(artist_id, str) and ',' in artist_id:
            # Handle comma-separated IDs
            artist_ids = [aid.strip() for aid in artist_id.split(',')]
        else:
            # Single artist ID
            artist_ids = [str(artist_id)]
        
        # Get names for all artist IDs
        artist_names = []
        for aid in artist_ids:
            if aid and str(aid) in artist_mapping:
                name = artist_mapping[str(aid)]
                # Ensure the name is a string and not None
                if name and isinstance(name, str):
                    artist_names.append(name)
                else:
                    artist_names.append(f"Unknown ({aid})")
            else:
                artist_names.append(f"Unknown ({aid})")
        
        # Ensure we have at least one name and all are strings
        if not artist_names:
            return "Unknown Artist"
        
        # Filter out any None values and ensure all are strings
        valid_names = [str(name) for name in artist_names if name is not None]
        
        result = ", ".join(valid_names) if valid_names else "Unknown Artist"
        return result
        
    except (ValueError, SyntaxError, TypeError) as e:
        # If parsing fails, return a safe fallback
        try:
            from logging_config import get_logger
            logger = get_logger()
            logger.debug(f"Error parsing artist ID {artist_id}: {e}")
        except:
            pass
        return "Unknown Artist"


def format_duration(duration_ms: float) -> str:
    """
    Format duration from milliseconds to MM:SS format.
    
    Args:
        duration_ms (float): Duration in milliseconds
        
    Returns:
        str: Formatted duration string
    """
    if pd.isna(duration_ms) or duration_ms == 0:
        return "Unknown"
    
    try:
        duration_seconds = int(duration_ms) // 1000
        minutes = duration_seconds // 60
        seconds = duration_seconds % 60
        return f"{minutes}:{seconds:02d}"
    except Exception:
        return "Unknown"


def get_key_name(key_number: float) -> str:
    """
    Convert key number to musical key name.
    
    Args:
        key_number (float): Musical key as number (0-11)
        
    Returns:
        str: Musical key name
    """
    if pd.isna(key_number):
        return "Unknown"
    
    key_map = {
        0: "C", 1: "C#", 2: "D", 3: "D#", 4: "E", 5: "F",
        6: "F#", 7: "G", 8: "G#", 9: "A", 10: "A#", 11: "B"
    }
    return key_map.get(int(key_number), "Unknown")


def get_mode_name(mode_number: float) -> str:
    """
    Convert mode number to mode name.
    
    Args:
        mode_number (float): Mode as number (0=Minor, 1=Major)
        
    Returns:
        str: Mode name
    """
    if pd.isna(mode_number):
        return "Unknown"
    return "Major" if int(mode_number) == 1 else "Minor"


def check_audio_url(url: str) -> bool:
    """
    Check if an audio URL is valid and accessible.
    
    Args:
        url (str): Audio URL to check
        
    Returns:
        bool: True if URL is valid, False otherwise
    """
    if pd.isna(url) or url == '' or url == 'None' or url is None:
        return False
    
    try:
        url_str = str(url)
        # Check if it's a valid HTTP URL format and from Spotify domains
        is_valid = (url_str.startswith('http') and 
                   ('spotify' in url_str or 'scdn.co' in url_str))
        return is_valid
    except Exception:
        return False 