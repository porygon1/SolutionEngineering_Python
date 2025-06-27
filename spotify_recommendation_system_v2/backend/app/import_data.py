#!/usr/bin/env python3
"""
Data Import Script for Spotify Music Recommendation System v2
Imports CSV data into PostgreSQL database with proper normalization and validation
"""

import asyncio
import os
import sys
import json
import ast
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from loguru import logger
from pathlib import Path
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.dialects.postgresql import insert
from tqdm import tqdm

# Add the parent directory to the path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.database.database import get_database, create_tables, engine
from app.database.models import (
    Artist, Album, Track, AudioFeatures, LyricsFeatures,
    Cluster, Base
)


class DataImporter:
    """Main data importer class"""
    
    def __init__(self):
        self.batch_size = settings.IMPORT_BATCH_SIZE
        self.skip_duplicates = settings.IMPORT_SKIP_DUPLICATES
        self.validate_data = False  # Disabled strict validation since data should be complete
        
        # Adjust batch sizes to avoid PostgreSQL parameter limits (32767 max)
        # Audio features have ~13 columns, so 1000 records = 13k+ parameters
        self.audio_features_batch_size = min(500, self.batch_size)  # 500 * 13 = 6500 params
        self.lyrics_features_batch_size = min(200, self.batch_size)  # 200 * 15 = 3000 params 
        self.tracks_batch_size = min(300, self.batch_size)  # 300 * 20 = 6000 params
        
        # Enhanced statistics with constraint violations tracking
        self.stats = {
            'artists': {'imported': 0, 'skipped': 0, 'errors': 0},
            'albums': {'imported': 0, 'skipped': 0, 'errors': 0},
            'tracks': {'imported': 0, 'skipped': 0, 'errors': 0},
            'audio_features': {'imported': 0, 'skipped': 0, 'errors': 0},
            'lyrics_features': {'imported': 0, 'skipped': 0, 'errors': 0},
            'constraint_violations': 0,
            'null_replacements': 0,
            'outliers_capped': 0,
        }
        
        # EDA-based data quality thresholds
        self.constraints = {
            'tempo': {'min': 30, 'max': 300},
            'time_signature': {'min': 1, 'max': 7, 'default': 4},
            'duration_ms': {'min': 5000, 'max': 7200000},
            'popularity': {'min': 0, 'max': 100},
            'audio_features': {'min': 0.0, 'max': 1.0},
            'followers': {'min': 0},
            'total_tracks': {'min': 1, 'max': 100}
        }
    
    def safe_eval(self, value: str) -> Any:
        """Safely evaluate string representations of Python objects"""
        if pd.isna(value) or value == '' or value == 'nan':
            return None
        if isinstance(value, str):
            try:
                # Handle string representation of lists
                if value.startswith('[') and value.endswith(']'):
                    return ast.literal_eval(value)
                # Handle JSON-like strings - improved parsing
                elif value.startswith('{') and value.endswith('}'):
                    try:
                        return json.loads(value)
                    except json.JSONDecodeError:
                        # Try with ast.literal_eval for Python dict format
                        return ast.literal_eval(value)
                # Handle single-quoted dict strings
                elif "'" in value and ('{' in value or '[' in value):
                    return ast.literal_eval(value)
                return value
            except (ValueError, SyntaxError, json.JSONDecodeError):
                logger.debug(f"Could not parse value: {value[:100]}...")
                return value
        return value
    
    def clean_numeric_value(self, value: Any, default: Optional[float] = None) -> Optional[float]:
        """Clean and convert numeric values"""
        if pd.isna(value) or value == '' or value == 'nan':
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    
    def clean_integer_value(self, value: Any, min_val: int = None, max_val: int = None, 
                           default: Optional[int] = None) -> Optional[int]:
        """Clean integer values with optional bounds checking"""
        if pd.isna(value) or value == '' or value == 'nan':
            return default
        
        try:
            int_val = int(float(value))
            
            if min_val is not None and int_val < min_val:
                logger.debug(f"Value {int_val} below minimum {min_val}")
                self.stats['constraint_violations'] += 1
                return default
            
            if max_val is not None and int_val > max_val:
                logger.debug(f"Value {int_val} above maximum {max_val}, capping")
                self.stats['outliers_capped'] += 1
                return max_val
            
            return int_val
        except (ValueError, TypeError):
            self.stats['constraint_violations'] += 1
            return default

    def clean_tempo_value(self, value: Any) -> Optional[float]:
        """Clean and validate tempo values - less restrictive for complete data"""
        if pd.isna(value) or value == '' or value == 'nan':
            return None
        try:
            tempo = float(value)
            # Tempo must be positive (database constraint: tempo > 0)
            if tempo <= 0:
                logger.debug(f"Invalid tempo value: {tempo}, setting to None")
                self.stats['constraint_violations'] += 1
                return None
            
            # Only cap extremely unrealistic values
            if tempo > 1000:
                logger.debug(f"Capping tempo from {tempo} to 300")
                self.stats['outliers_capped'] += 1
                return 300.0
            
            # Accept all positive tempo values
            return tempo
        except (ValueError, TypeError):
            self.stats['constraint_violations'] += 1
            return None
    
    def clean_time_signature_value(self, value: Any) -> Optional[int]:
        """Clean and validate time signature values - enhanced based on EDA findings"""
        if pd.isna(value) or value == '' or value == 'nan':
            return self.constraints['time_signature']['default']
        try:
            time_sig = int(float(value))
            # Time signature must be between 1 and 7 (database constraint)
            if time_sig < self.constraints['time_signature']['min'] or time_sig > self.constraints['time_signature']['max']:
                logger.debug(f"Invalid time signature value: {time_sig}, setting to default")
                self.stats['constraint_violations'] += 1
                return self.constraints['time_signature']['default']
            return time_sig
        except (ValueError, TypeError):
            self.stats['constraint_violations'] += 1
            return self.constraints['time_signature']['default']
    
    def clean_string_value(self, value: Any, max_length: int = 255) -> Optional[str]:
        """Clean and validate string values"""
        if pd.isna(value) or value == '' or value == 'nan':
            return None
        str_value = str(value).strip()
        if len(str_value) == 0:
            return None
        return str_value[:max_length]
    
    def clean_array_value(self, value: Any) -> List[str]:
        """Clean and convert array values"""
        if pd.isna(value) or value == '' or value == 'nan':
            return []
        
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        
        if isinstance(value, str):
            # Try to parse as Python list
            parsed = self.safe_eval(value)
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]
            # If not a list, treat as single item
            return [value.strip()] if value.strip() else []
        
        return []
    
    def clean_audio_feature_value(self, value: Any, feature_name: str) -> Optional[float]:
        """Clean audio feature values (0-1 range) - less restrictive for complete data"""
        if pd.isna(value) or value == '' or value == 'nan':
            return None
        
        try:
            feature_val = float(value)
            # Only check for obvious errors, but keep all reasonable values
            if feature_val < -10 or feature_val > 10:  # Very liberal bounds
                logger.debug(f"Extreme {feature_name} value: {feature_val}, setting to None")
                self.stats['constraint_violations'] += 1
                return None
            return feature_val
        except (ValueError, TypeError):
            self.stats['constraint_violations'] += 1
            return None
    
    def clean_lyrics_feature_value(self, value: Any, feature_name: str) -> Optional[float]:
        """Clean lyrics feature values - keep valid data, handle -1 sentinel values"""
        if pd.isna(value) or value == '' or value == 'nan':
            return None
        
        try:
            if feature_name in ['n_sentences', 'n_words']:
                val = int(float(value))
                if val == -1:
                    logger.debug(f"Replacing -1 sentinel value in {feature_name} with None")
                    self.stats['null_replacements'] += 1
                    return None
                # Accept any non-negative value (more liberal)
                if val < 0:
                    logger.debug(f"Invalid negative {feature_name}: {val}, setting to None")
                    self.stats['constraint_violations'] += 1
                    return None
                return float(val)  # Return as float for consistency
            else:  # Float features like sentence_similarity, vocabulary_wealth
                val = float(value)
                if val == -1.0:
                    logger.debug(f"Replacing -1 sentinel value in {feature_name} with None")
                    self.stats['null_replacements'] += 1
                    return None
                
                # More liberal validation - only reject obviously wrong values
                if val < -10 or val > 10:
                    logger.debug(f"Extreme {feature_name} value: {val}, setting to None")
                    self.stats['constraint_violations'] += 1
                    return None
                
                return val
        except (ValueError, TypeError):
            self.stats['constraint_violations'] += 1
            return None
    
    def clean_popularity_value(self, value: Any) -> Optional[int]:
        """Clean popularity values - accept all reasonable values"""
        if pd.isna(value) or value == '' or value == 'nan':
            return None
        
        try:
            pop = int(float(value))
            # Only reject obviously invalid values
            if pop < 0:
                return 0
            if pop > 100:
                return 100
            return pop
        except (ValueError, TypeError):
            self.stats['constraint_violations'] += 1
            return None
    
    def clean_duration_value(self, value: Any) -> Optional[int]:
        """Clean duration values - accept all positive durations"""
        if pd.isna(value) or value == '' or value == 'nan':
            return None
        
        try:
            duration = int(float(value))
            # Only reject obviously invalid values (negative or zero)
            if duration <= 0:
                logger.debug(f"Invalid duration: {duration}ms, setting to None")
                self.stats['constraint_violations'] += 1
                return None
            # Accept all positive durations, even very long ones
            return duration
        except (ValueError, TypeError):
            self.stats['constraint_violations'] += 1
            return None
    
    def clean_total_tracks_value(self, value: Any) -> Optional[int]:
        """Clean total_tracks values with realistic bounds - enhanced based on EDA findings"""
        if pd.isna(value) or value == '' or value == 'nan':
            return None
        
        try:
            total = int(float(value))
            if total < self.constraints['total_tracks']['min']:
                logger.debug(f"Total tracks too low: {total}, setting to None")
                self.stats['constraint_violations'] += 1
                return None
            if total > self.constraints['total_tracks']['max']:
                logger.debug(f"Total tracks too high: {total}, capping to {self.constraints['total_tracks']['max']}")
                self.stats['outliers_capped'] += 1
                return self.constraints['total_tracks']['max']
            return total
        except (ValueError, TypeError):
            self.stats['constraint_violations'] += 1
            return None
    
    async def load_csv_data(self) -> Dict[str, pd.DataFrame]:
        """Load all CSV files"""
        logger.info("🔄 Loading CSV files...")
        
        csv_files = {
            'tracks': settings.get_data_path(settings.SPOTIFY_TRACKS_FILE),
            'artists': settings.get_data_path(settings.SPOTIFY_ARTISTS_FILE),
            'albums': settings.get_data_path(settings.SPOTIFY_ALBUMS_FILE),
            'audio_features': settings.get_data_path(settings.LOW_LEVEL_AUDIO_FEATURES_FILE),
            'lyrics_features': settings.get_data_path(settings.LYRICS_FEATURES_FILE),
        }
        
        dataframes = {}
        
        for name, file_path in csv_files.items():
            if not os.path.exists(file_path):
                logger.warning(f"⚠️ File not found: {file_path}")
                continue
                
            try:
                logger.info(f"📖 Loading {name} from {file_path}")
                df = pd.read_csv(file_path)
                logger.success(f"✅ Loaded {len(df)} rows from {name}")
                dataframes[name] = df
            except Exception as e:
                logger.error(f"❌ Failed to load {name}: {e}")
                
        return dataframes
    
    async def import_artists(self, df: pd.DataFrame, session) -> None:
        """Import artists data"""
        logger.info("🎵 Importing artists...")
        
        artists_data = []
        
        for _, row in tqdm(df.iterrows(), total=len(df), desc="Processing artists"):
            try:
                # Parse genres
                genres = self.clean_array_value(row.get('genres', []))
                
                artist_data = {
                    'id': self.clean_string_value(row['id'], 22),
                    'name': self.clean_string_value(row['name']),
                    'popularity': self.clean_popularity_value(row.get('artist_popularity')),
                    'followers': self.clean_integer_value(row.get('followers'), min_val=self.constraints['followers']['min']),
                    'genres': genres,
                    'spotify_type': self.clean_string_value(row.get('type', 'artist')),
                }
                
                # Validate required fields
                if not artist_data['id'] or not artist_data['name']:
                    self.stats['artists']['errors'] += 1
                    continue
                
                artists_data.append(artist_data)
                
                # Batch insert
                if len(artists_data) >= self.batch_size:
                    await self._bulk_insert_artists(session, artists_data)
                    artists_data = []
                    
            except Exception as e:
                logger.error(f"Error processing artist row: {e}")
                self.stats['artists']['errors'] += 1
        
        # Insert remaining data
        if artists_data:
            await self._bulk_insert_artists(session, artists_data)
    
    async def _bulk_insert_artists(self, session, artists_data: List[Dict]) -> None:
        """Bulk insert artists with proper conflict handling"""
        await self._generic_bulk_insert(session, artists_data, Artist, 'artists', 'id')
    
    async def import_albums(self, df: pd.DataFrame, session) -> None:
        """Import albums - import all data since it should be complete"""
        logger.info("💿 Importing albums...")
        
        albums_data = []
        
        for _, row in tqdm(df.iterrows(), total=len(df), desc="Processing albums"):
            try:
                # Get artist_id without strict validation
                artist_id = self.clean_string_value(row.get('artist_id'), 22)
                if not artist_id:
                    logger.debug(f"Skipping album {row.get('id')} - missing artist_id")
                    self.stats['albums']['errors'] += 1
                    continue
                
                # Parse complex fields with improved handling
                external_urls_raw = row.get('external_urls', '{}')
                external_urls = self.safe_eval(external_urls_raw)
                if external_urls_raw and not external_urls:
                    logger.debug(f"Failed to parse external_urls: {external_urls_raw[:100]}")
                
                images_raw = row.get('images', '[]')
                images = self.safe_eval(images_raw)
                if images_raw and not images:
                    logger.debug(f"Failed to parse images: {images_raw[:100]}")
                
                available_markets = self.clean_array_value(row.get('available_markets', []))
                
                album_data = {
                    'id': self.clean_string_value(row['id'], 22),
                    'name': self.clean_string_value(row.get('name'), 255),
                    'album_type': self.clean_string_value(row.get('album_type'), 50),
                    'release_date': self.clean_string_value(row.get('release_date'), 10),
                    'release_date_precision': self.clean_string_value(row.get('release_date_precision'), 10),
                    'total_tracks': self.clean_total_tracks_value(row.get('total_tracks')),
                    'available_markets': available_markets,
                    'external_urls': external_urls if external_urls else None,
                    'images': images if images else None,
                    'spotify_uri': self.clean_string_value(row.get('uri'), 255),
                    'spotify_href': self.clean_string_value(row.get('href'), 255),
                    'spotify_type': self.clean_string_value(row.get('type', 'album'), 50),
                    
                    # Foreign key
                    'artist_id': artist_id,
                }
                
                # Validate required fields
                if not album_data['id'] or not album_data['artist_id']:
                    self.stats['albums']['errors'] += 1
                    continue
                
                albums_data.append(album_data)
                
                # Batch insert
                if len(albums_data) >= self.batch_size:
                    await self._bulk_insert_albums(session, albums_data)
                    albums_data = []
                    
            except Exception as e:
                logger.error(f"Error processing album row: {e}")
                self.stats['albums']['errors'] += 1
        
        # Insert remaining data
        if albums_data:
            await self._bulk_insert_albums(session, albums_data)
    
    async def _bulk_insert_albums(self, session, albums_data: List[Dict]) -> None:
        """Bulk insert albums with proper conflict handling"""
        await self._generic_bulk_insert(session, albums_data, Album, 'albums', 'id')
    
    async def import_tracks(self, df: pd.DataFrame, session) -> None:
        """Import tracks - import all data since it should be complete"""
        logger.info("🎵 Importing tracks...")
        
        tracks_data = []
        
        for _, row in tqdm(df.iterrows(), total=len(df), desc="Processing tracks"):
            try:
                # Extract first artist ID from artists_id array
                artists_id_str = row.get('artists_id', '')
                artist_id = None
                
                if pd.notna(artists_id_str) and artists_id_str:
                    try:
                        # Parse the array string
                        if isinstance(artists_id_str, str) and artists_id_str.startswith('['):
                            artists_list = ast.literal_eval(artists_id_str)
                            if artists_list and len(artists_list) > 0:
                                artist_id = artists_list[0]  # Take first artist
                        else:
                            artist_id = str(artists_id_str)
                    except:
                        logger.warning(f"Could not parse artists_id: {artists_id_str}")
                        # Try to use the raw value if parsing fails
                        artist_id = str(artists_id_str) if artists_id_str else None
                
                # Get album_id without strict validation
                album_id = self.clean_string_value(row.get('album_id'), 22)
                
                if not artist_id:
                    logger.debug(f"Skipping track {row.get('id')} - missing artist_id")
                    self.stats['tracks']['errors'] += 1
                    continue
                
                track_data = {
                    'id': self.clean_string_value(row['id'], 22),
                    'name': self.clean_string_value(row.get('name'), 255),
                    'artist_id': artist_id,  # Use extracted first artist
                    'album_id': album_id,
                    'popularity': self.clean_popularity_value(row.get('popularity')),
                    'duration_ms': self.clean_duration_value(row.get('duration_ms')),
                    'track_number': self.clean_integer_value(row.get('track_number'), min_val=1),
                    'disc_number': self.clean_integer_value(row.get('disc_number'), min_val=1),
                    'explicit': bool(row.get('explicit', False)),
                    
                    # Audio features from Spotify API - enhanced validation
                    'acousticness': self.clean_audio_feature_value(row.get('acousticness'), 'acousticness'),
                    'danceability': self.clean_audio_feature_value(row.get('danceability'), 'danceability'),
                    'energy': self.clean_audio_feature_value(row.get('energy'), 'energy'),
                    'instrumentalness': self.clean_audio_feature_value(row.get('instrumentalness'), 'instrumentalness'),
                    'liveness': self.clean_audio_feature_value(row.get('liveness'), 'liveness'),
                    'loudness': self.clean_numeric_value(row.get('loudness')),  # Can be negative
                    'speechiness': self.clean_audio_feature_value(row.get('speechiness'), 'speechiness'),
                    'valence': self.clean_audio_feature_value(row.get('valence'), 'valence'),
                    'tempo': self.clean_tempo_value(row.get('tempo')),
                    
                    # Musical features
                    'key': self.clean_integer_value(row.get('key'), min_val=0, max_val=11),
                    'mode': self.clean_integer_value(row.get('mode'), min_val=0, max_val=1),
                    'time_signature': self.clean_time_signature_value(row.get('time_signature')),
                    
                    # URLs and metadata
                    'preview_url': self.clean_string_value(row.get('preview_url'), 255),
                    'spotify_uri': self.clean_string_value(row.get('uri'), 255),
                    'spotify_href': self.clean_string_value(row.get('href'), 255),
                    'track_href': self.clean_string_value(row.get('track_href'), 255),
                    'analysis_url': self.clean_string_value(row.get('analysis_url'), 255),
                    
                    # Additional metadata
                    'available_markets': self.clean_array_value(row.get('available_markets')),
                    'country': self.clean_string_value(row.get('country'), 5),
                    'playlist': self.clean_string_value(row.get('playlist'), 255),
                    'lyrics': row.get('lyrics') if pd.notna(row.get('lyrics')) else None,
                }
                
                # Validate required fields
                if not track_data['id'] or not track_data['artist_id']:
                    self.stats['tracks']['errors'] += 1
                    continue
                
                tracks_data.append(track_data)
                
                # Batch insert with smaller batch size
                if len(tracks_data) >= self.tracks_batch_size:
                    await self._bulk_insert_tracks(session, tracks_data)
                    tracks_data = []
                    
            except Exception as e:
                logger.error(f"Error processing track row: {e}")
                self.stats['tracks']['errors'] += 1
        
        # Insert remaining data
        if tracks_data:
            await self._bulk_insert_tracks(session, tracks_data)
    
    async def _bulk_insert_tracks(self, session, tracks_data: List[Dict]) -> None:
        """Bulk insert tracks with proper conflict handling"""
        await self._generic_bulk_insert(session, tracks_data, Track, 'tracks', 'id')
    
    async def import_audio_features(self, df: pd.DataFrame, session) -> None:
        """Import low-level audio features"""
        logger.info("🎵 Importing audio features...")
        
        audio_features_data = []
        
        for _, row in tqdm(df.iterrows(), total=len(df), desc="Processing audio features"):
            try:
                # Extract MEL features (128 columns)
                mel_features = []
                for i in range(1, settings.MEL_FEATURES_COUNT + 1):
                    col_name = f"MEL_{i}"
                    if col_name in row:
                        mel_features.append(self.clean_numeric_value(row[col_name], 0.0))
                
                # Extract MFCC features (48 columns)
                mfcc_features = []
                for i in range(1, settings.MFCC_FEATURES_COUNT + 1):
                    col_name = f"MFCC_{i}"
                    if col_name in row:
                        mfcc_features.append(self.clean_numeric_value(row[col_name], 0.0))
                
                audio_data = {
                    'track_id': self.clean_string_value(row['track_id'], 22),
                    
                    # Chroma features
                    'chroma_1': self.clean_numeric_value(row.get('Chroma_1')),
                    'chroma_2': self.clean_numeric_value(row.get('Chroma_2')),
                    'chroma_3': self.clean_numeric_value(row.get('Chroma_3')),
                    'chroma_4': self.clean_numeric_value(row.get('Chroma_4')),
                    'chroma_5': self.clean_numeric_value(row.get('Chroma_5')),
                    'chroma_6': self.clean_numeric_value(row.get('Chroma_6')),
                    'chroma_7': self.clean_numeric_value(row.get('Chroma_7')),
                    'chroma_8': self.clean_numeric_value(row.get('Chroma_8')),
                    'chroma_9': self.clean_numeric_value(row.get('Chroma_9')),
                    'chroma_10': self.clean_numeric_value(row.get('Chroma_10')),
                    'chroma_11': self.clean_numeric_value(row.get('Chroma_11')),
                    'chroma_12': self.clean_numeric_value(row.get('Chroma_12')),
                    
                    # MEL and MFCC as JSON arrays
                    'mel_features': mel_features if mel_features else None,
                    'mfcc_features': mfcc_features if mfcc_features else None,
                    
                    # Spectral contrast
                    'spectral_contrast_1': self.clean_numeric_value(row.get('Spectral_contrast_1')),
                    'spectral_contrast_2': self.clean_numeric_value(row.get('Spectral_contrast_2')),
                    'spectral_contrast_3': self.clean_numeric_value(row.get('Spectral_contrast_3')),
                    'spectral_contrast_4': self.clean_numeric_value(row.get('Spectral_contrast_4')),
                    'spectral_contrast_5': self.clean_numeric_value(row.get('Spectral_contrast_5')),
                    'spectral_contrast_6': self.clean_numeric_value(row.get('Spectral_contrast_6')),
                    'spectral_contrast_7': self.clean_numeric_value(row.get('Spectral_contrast_7')),
                    
                    # Tonnetz features
                    'tonnetz_1': self.clean_numeric_value(row.get('Tonnetz_1')),
                    'tonnetz_2': self.clean_numeric_value(row.get('Tonnetz_2')),
                    'tonnetz_3': self.clean_numeric_value(row.get('Tonnetz_3')),
                    'tonnetz_4': self.clean_numeric_value(row.get('Tonnetz_4')),
                    'tonnetz_5': self.clean_numeric_value(row.get('Tonnetz_5')),
                    'tonnetz_6': self.clean_numeric_value(row.get('Tonnetz_6')),
                    
                    # Additional features
                    'zcr': self.clean_numeric_value(row.get('ZCR')),
                    'entropy_energy': self.clean_numeric_value(row.get('entropy_energy')),
                    'spectral_bandwidth': self.clean_numeric_value(row.get('spectral_bandwith')),  # Note: typo in original CSV
                    'spectral_centroid': self.clean_numeric_value(row.get('spectral_centroid')),
                    'spectral_rolloff_max': self.clean_numeric_value(row.get('spectral_rollOff_max')),
                    'spectral_rolloff_min': self.clean_numeric_value(row.get('spectral_rollOff_min')),
                }
                
                # Validate required fields
                if not audio_data['track_id']:
                    self.stats['audio_features']['errors'] += 1
                    continue
                
                audio_features_data.append(audio_data)
                
                # Batch insert with smaller batch size to avoid parameter limits
                if len(audio_features_data) >= self.audio_features_batch_size:
                    await self._bulk_insert_audio_features(session, audio_features_data)
                    audio_features_data = []
                    
            except Exception as e:
                logger.error(f"Error processing audio features row: {e}")
                self.stats['audio_features']['errors'] += 1
        
        # Insert remaining data
        if audio_features_data:
            await self._bulk_insert_audio_features(session, audio_features_data)
    
    async def _bulk_insert_audio_features(self, session, audio_features_data: List[Dict]) -> None:
        """Bulk insert audio features with proper conflict handling"""
        await self._generic_bulk_insert(session, audio_features_data, AudioFeatures, 'audio_features', 'track_id')
    
    async def import_lyrics_features(self, df: pd.DataFrame, session) -> None:
        """Import lyrics features"""
        logger.info("📝 Importing lyrics features...")
        
        lyrics_features_data = []
        
        for _, row in tqdm(df.iterrows(), total=len(df), desc="Processing lyrics features"):
            try:
                lyrics_data = {
                    'track_id': self.clean_string_value(row['track_id'], 22),
                    'mean_syllables_word': self.clean_lyrics_feature_value(row.get('mean_syllables_word'), 'mean_syllables_word'),
                    'mean_words_sentence': self.clean_lyrics_feature_value(row.get('mean_words_sentence'), 'mean_words_sentence'),
                    'n_sentences': self.clean_lyrics_feature_value(row.get('n_sentences'), 'n_sentences'),
                    'n_words': self.clean_lyrics_feature_value(row.get('n_words'), 'n_words'),
                    'sentence_similarity': self.clean_lyrics_feature_value(row.get('sentence_similarity'), 'sentence_similarity'),
                    'vocabulary_wealth': self.clean_lyrics_feature_value(row.get('vocabulary_wealth'), 'vocabulary_wealth'),
                }
                
                # Validate required fields
                if not lyrics_data['track_id']:
                    self.stats['lyrics_features']['errors'] += 1
                    continue
                
                lyrics_features_data.append(lyrics_data)
                
                # Batch insert with smaller batch size to avoid parameter limits
                if len(lyrics_features_data) >= self.lyrics_features_batch_size:
                    await self._bulk_insert_lyrics_features(session, lyrics_features_data)
                    lyrics_features_data = []
                    
            except Exception as e:
                logger.error(f"Error processing lyrics features row: {e}")
                self.stats['lyrics_features']['errors'] += 1
        
        # Insert remaining data
        if lyrics_features_data:
            await self._bulk_insert_lyrics_features(session, lyrics_features_data)
    
    async def _bulk_insert_lyrics_features(self, session, lyrics_features_data: List[Dict]) -> None:
        """Bulk insert lyrics features with proper conflict handling"""
        await self._generic_bulk_insert(session, lyrics_features_data, LyricsFeatures, 'lyrics_features', 'track_id')
    
    async def check_existing_data(self, session) -> Dict[str, int]:
        """Check how much data already exists in the database"""
        existing_counts = {}
        
        try:
            # Count existing records in each table
            result = await session.execute(text("SELECT COUNT(*) FROM artists"))
            existing_counts['artists'] = result.scalar() or 0
            
            result = await session.execute(text("SELECT COUNT(*) FROM albums"))
            existing_counts['albums'] = result.scalar() or 0
            
            result = await session.execute(text("SELECT COUNT(*) FROM tracks"))
            existing_counts['tracks'] = result.scalar() or 0
            
            result = await session.execute(text("SELECT COUNT(*) FROM audio_features"))
            existing_counts['audio_features'] = result.scalar() or 0
            
            result = await session.execute(text("SELECT COUNT(*) FROM lyrics_features"))
            existing_counts['lyrics_features'] = result.scalar() or 0
            
        except Exception as e:
            logger.warning(f"Could not check existing data counts: {e}")
            # Return zeros if we can't check (tables might not exist yet)
            existing_counts = {
                'artists': 0, 'albums': 0, 'tracks': 0, 
                'audio_features': 0, 'lyrics_features': 0
            }
        
        return existing_counts

    async def should_skip_import(self, table_name: str, df: pd.DataFrame, existing_count: int) -> bool:
        """Determine if we should skip importing a table based on existing data"""
        if not self.skip_duplicates:
            return False
            
        df_count = len(df)
        
        # If we have significantly more data in DB than in CSV, something's wrong
        if existing_count > df_count * 1.1:  # 10% tolerance
            logger.warning(f"Database has more {table_name} ({existing_count}) than CSV ({df_count})")
            return False
        
        # If we have most of the data already, consider skipping
        if existing_count >= df_count * 0.95:  # 95% threshold
            logger.info(f"✅ {table_name} already ~95% imported ({existing_count}/{df_count}), skipping")
            return True
            
        logger.info(f"📊 {table_name}: {existing_count}/{df_count} records exist, continuing import")
        return False

    async def run_import(self) -> None:
        """Run the complete data import process with early termination logic"""
        logger.info("🚀 Starting data import process...")
        
        # Create tables
        logger.info("📋 Creating database tables...")
        await create_tables()
        
        # Load CSV data
        dataframes = await self.load_csv_data()
        
        if not dataframes:
            logger.error("❌ No data files found. Import aborted.")
            return
        
        # Check existing data and determine what needs to be imported
        async for session in get_database():
            try:
                # Check existing data counts
                logger.info("🔍 Checking existing data in database...")
                existing_counts = await self.check_existing_data(session)
                
                # Display current state
                logger.info("📊 Current database state:")
                for table, count in existing_counts.items():
                    logger.info(f"  {table}: {count:,} records")
                
                # Check if all data is already imported
                all_tables_complete = True
                for table_name, df in dataframes.items():
                    if not await self.should_skip_import(table_name, df, existing_counts.get(table_name, 0)):
                        all_tables_complete = False
                        break
                
                if all_tables_complete:
                    logger.success("🎉 All data already imported! No action needed.")
                    self.print_import_statistics()
                    return
                
                # Import data in order (respecting foreign key constraints)
                # Import artists first (no dependencies)
                if 'artists' in dataframes:
                    if not await self.should_skip_import('artists', dataframes['artists'], existing_counts.get('artists', 0)):
                        await self.import_artists(dataframes['artists'], session)
                    else:
                        self.stats['artists']['skipped'] = existing_counts.get('artists', 0)
                
                # Import albums (depends on artists)
                if 'albums' in dataframes:
                    if not await self.should_skip_import('albums', dataframes['albums'], existing_counts.get('albums', 0)):
                        await self.import_albums(dataframes['albums'], session)
                    else:
                        self.stats['albums']['skipped'] = existing_counts.get('albums', 0)
                
                # Import tracks (depends on artists and albums)
                if 'tracks' in dataframes:
                    if not await self.should_skip_import('tracks', dataframes['tracks'], existing_counts.get('tracks', 0)):
                        await self.import_tracks(dataframes['tracks'], session)
                    else:
                        self.stats['tracks']['skipped'] = existing_counts.get('tracks', 0)
                
                # Import related features (depends on tracks)
                if 'audio_features' in dataframes:
                    if not await self.should_skip_import('audio_features', dataframes['audio_features'], existing_counts.get('audio_features', 0)):
                        await self.import_audio_features(dataframes['audio_features'], session)
                    else:
                        self.stats['audio_features']['skipped'] = existing_counts.get('audio_features', 0)
                
                if 'lyrics_features' in dataframes:
                    if not await self.should_skip_import('lyrics_features', dataframes['lyrics_features'], existing_counts.get('lyrics_features', 0)):
                        await self.import_lyrics_features(dataframes['lyrics_features'], session)
                    else:
                        self.stats['lyrics_features']['skipped'] = existing_counts.get('lyrics_features', 0)
                
                break  # We only need one session for the whole import
                
            except Exception as e:
                logger.error(f"❌ Import failed: {e}")
                await session.rollback()
                raise
        
        # Print statistics
        self.print_import_statistics()
        
        logger.success("🎉 Data import completed successfully!")
    
    def print_import_statistics(self) -> None:
        """Print enhanced import statistics with data quality metrics"""
        logger.info("📊 Import Statistics:")
        logger.info("=" * 70)
        
        total_imported = 0
        total_skipped = 0
        total_errors = 0
        
        for table, stats in self.stats.items():
            if isinstance(stats, dict) and 'imported' in stats:
                imported = stats['imported']
                skipped = stats['skipped']
                errors = stats['errors']
                total_imported += imported
                total_skipped += skipped
                total_errors += errors
                
                logger.info(f"{table.capitalize():15} | Imported: {imported:8,} | Skipped: {skipped:8,} | Errors: {errors:6,}")
        
        logger.info("=" * 70)
        logger.info(f"{'Total':15} | Imported: {total_imported:8,} | Skipped: {total_skipped:8,} | Errors: {total_errors:6,}")
        
        # Enhanced data quality metrics
        logger.info("=" * 70)
        logger.info("📋 Data Quality Metrics:")
        logger.info(f"Constraint violations fixed: {self.stats['constraint_violations']:,}")
        logger.info(f"Null replacements (-1 → NULL): {self.stats['null_replacements']:,}")
        logger.info(f"Outliers capped: {self.stats['outliers_capped']:,}")
        
        total_quality_fixes = (self.stats['constraint_violations'] + 
                              self.stats['null_replacements'] + 
                              self.stats['outliers_capped'])
        logger.info(f"Total data quality fixes: {total_quality_fixes:,}")
        
        # Summary
        logger.info("=" * 70)
        if total_errors > 0:
            logger.warning(f"⚠️ {total_errors} errors occurred during import")
        
        if total_skipped > 0:
            logger.info(f"⏭️ {total_skipped} records were skipped (already exist)")
            
        if total_imported > 0:
            logger.success(f"✅ {total_imported} new records were imported")
        
        if total_quality_fixes > 0:
            logger.info(f"🔧 {total_quality_fixes} data quality issues were automatically fixed")

    async def _generic_bulk_insert(self, session, data_list: List[Dict], model_class, table_name: str, unique_column: str = 'id') -> None:
        """Generic bulk insert method with proper conflict handling"""
        try:
            if self.skip_duplicates:
                # Use ON CONFLICT DO NOTHING for bulk insert
                stmt = insert(model_class).values(data_list)
                stmt = stmt.on_conflict_do_nothing(index_elements=[unique_column])
                await session.execute(stmt)
                await session.commit()
                self.stats[table_name]['imported'] += len(data_list)
            else:
                # Regular bulk insert without conflict handling
                for item_data in data_list:
                    item = model_class(**item_data)
                    session.add(item)
                await session.commit()
                self.stats[table_name]['imported'] += len(data_list)
            
        except Exception as e:
            await session.rollback()
            logger.error(f"❌ Failed to insert {table_name} batch: {e}")
            
            # Individual insert fallback with proper conflict handling
            successful = 0
            for item_data in data_list:
                try:
                    if self.skip_duplicates:
                        # Check if item already exists before inserting
                        unique_value = item_data[unique_column]
                        existing = await session.get(model_class, unique_value)
                        if existing:
                            logger.debug(f"{table_name.capitalize()} {unique_value} already exists, skipping")
                            self.stats[table_name]['skipped'] += 1
                            continue
                    
                    item = model_class(**item_data)
                    session.add(item)
                    await session.commit()
                    successful += 1
                    
                except IntegrityError as ie:
                    await session.rollback()
                    if self.skip_duplicates and "duplicate key" in str(ie).lower():
                        logger.debug(f"Skipping duplicate {table_name} {item_data.get(unique_column, 'unknown')}")
                        self.stats[table_name]['skipped'] += 1
                    else:
                        logger.debug(f"Failed to insert {table_name} {item_data.get(unique_column, 'unknown')}: {ie}")
                        self.stats[table_name]['errors'] += 1
                except Exception as individual_error:
                    await session.rollback()
                    logger.debug(f"Failed to insert {table_name} {item_data.get(unique_column, 'unknown')}: {individual_error}")
                    self.stats[table_name]['errors'] += 1
            
            logger.info(f"Salvaged {successful}/{len(data_list)} {table_name} from failed batch")
            self.stats[table_name]['imported'] += successful


async def main():
    """Main function"""
    logger.info("🎵 Spotify Music Recommendation System v2 - Data Import")
    logger.info("=" * 60)
    
    try:
        importer = DataImporter()
        await importer.run_import()
        
    except KeyboardInterrupt:
        logger.warning("⚠️ Import interrupted by user")
    except Exception as e:
        logger.error(f"❌ Import failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 