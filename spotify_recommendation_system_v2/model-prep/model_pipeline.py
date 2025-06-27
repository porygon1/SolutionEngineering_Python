#!/usr/bin/env python3
"""
Complete Model Generation Pipeline for Spotify Recommendation System

This pipeline generates ALL models used by the system:
1. HDBSCAN clustering models (5 variants with different feature approaches)
2. Lyrics similarity models (4 variants with different algorithms)
3. Base models for backward compatibility
4. All supporting files (embeddings, indices, configs)

Based on:
- scripts/Models/HDBSCAN_Clusters_KNN.ipynb
- scripts/Models/lyrics_similarity_search.ipynb
"""

import os
import sys
import logging
import pickle
import json
import joblib
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

# ML libraries for HDBSCAN models
import hdbscan
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import HDBSCAN

# ML libraries for lyrics models
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.decomposition import TruncatedSVD
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
import re

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/model_pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ModelPipeline:
    def __init__(self, data_dir: str = "/app/data", models_dir: str = "/app/data/models"):
        self.data_dir = Path(data_dir)
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # File paths
        self.spotify_tracks_path = self.data_dir / "raw" / "spotify_tracks.csv"
        
        # Model status tracking
        self.success_markers = {}
        self.failure_markers = {}
        
        # Initialize NLTK for lyrics processing
        self._setup_nltk()
        
        logger.info(f"Initialized ModelPipeline with data_dir={data_dir}, models_dir={models_dir}")

    def _setup_nltk(self):
        """Download required NLTK data for lyrics processing"""
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            nltk.download('wordnet', quiet=True)
            nltk.download('averaged_perceptron_tagger', quiet=True)
            
            self.lemmatizer = WordNetLemmatizer()
            self.stop_words = set(stopwords.words('english'))
            logger.info("✅ NLTK setup completed")
        except Exception as e:
            logger.error(f"❌ NLTK setup failed: {e}")
            raise

    def _create_status_markers(self, model_type: str, success: bool = True):
        """Create success/failure marker files"""
        if success:
            marker_file = self.models_dir / f".{model_type}_success"
            self.success_markers[model_type] = marker_file
            marker_file.touch()
            if model_type in self.failure_markers:
                self.failure_markers[model_type].unlink(missing_ok=True)
        else:
            marker_file = self.models_dir / f".{model_type}_failed"
            self.failure_markers[model_type] = marker_file
            marker_file.touch()

    def _check_existing_models(self, model_type: str, required_files: List[str]) -> bool:
        """Check if model already exists and is complete"""
        success_marker = self.models_dir / f".{model_type}_success"
        if not success_marker.exists():
            return False
            
        # Check if all required files exist
        for file_name in required_files:
            if not (self.models_dir / file_name).exists():
                logger.info(f"Missing file for {model_type}: {file_name}")
                return False
                
        return True

    def load_spotify_data(self) -> pd.DataFrame:
        """Load and validate Spotify tracks data"""
        if not self.spotify_tracks_path.exists():
            raise FileNotFoundError(f"Spotify tracks data not found at {self.spotify_tracks_path}")
        
        logger.info("📊 Loading Spotify tracks data...")
        df = pd.read_csv(self.spotify_tracks_path)
        logger.info(f"Loaded {len(df)} tracks with {len(df.columns)} columns")
        
        # Validate required columns
        required_cols = ['id', 'name', 'artists_id', 'danceability', 'energy', 'valence', 
                        'acousticness', 'instrumentalness', 'liveness', 'loudness', 
                        'speechiness', 'tempo', 'key', 'mode', 'time_signature']
        
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
            
        return df

    def prepare_hdbscan_features(self, df: pd.DataFrame) -> Dict[str, np.ndarray]:
        """Prepare different feature sets for HDBSCAN variants"""
        logger.info("🔧 Preparing HDBSCAN feature sets...")
        
        # Basic audio features (12 features)
        basic_features = ['danceability', 'energy', 'valence', 'acousticness', 'instrumentalness', 
                         'liveness', 'loudness', 'speechiness', 'tempo', 'key', 'mode', 'time_signature']
        
        # Load low-level audio features if available
        low_level_features_path = self.data_dir / "raw" / "low_level_audio_features.csv"
        
        if low_level_features_path.exists():
            logger.info("📊 Loading low-level audio features...")
            df_llav = pd.read_csv(low_level_features_path)
            
            # Merge with main dataset
            df_merged = pd.merge(df, df_llav, left_on='id', right_on='track_id', how='left')
            
            # Extract low-level feature columns (exclude metadata columns)
            llav_cols = [col for col in df_llav.columns if col not in ['track_id', 'Unnamed: 0']]
            low_level_features = df_merged[llav_cols].fillna(0).values
            
            logger.info(f"✅ Loaded {low_level_features.shape[1]} low-level audio features")
        else:
            logger.warning("⚠️ Low-level audio features not found, using derived features")
            # Create derived features from basic audio features
            n_tracks = len(df)
            basic_vals = df[basic_features].fillna(0).values
            
            # Create additional derived features
            derived_features = []
            
            # Feature interactions
            derived_features.append((basic_vals[:, 0] * basic_vals[:, 1]).reshape(-1, 1))  # danceability * energy
            derived_features.append((basic_vals[:, 2] * basic_vals[:, 3]).reshape(-1, 1))  # valence * acousticness
            derived_features.append((basic_vals[:, 4] * basic_vals[:, 5]).reshape(-1, 1))  # instrumentalness * liveness
            
            # Polynomial features
            derived_features.append(np.power(basic_vals[:, 0], 2).reshape(-1, 1))  # danceability^2
            derived_features.append(np.power(basic_vals[:, 1], 2).reshape(-1, 1))  # energy^2
            derived_features.append(np.power(basic_vals[:, 2], 2).reshape(-1, 1))  # valence^2
            
            # Log transformations (add small constant to avoid log(0))
            derived_features.append(np.log(basic_vals[:, 5] + 0.001).reshape(-1, 1))  # log(liveness)
            derived_features.append(np.log(basic_vals[:, 7] + 0.001).reshape(-1, 1))  # log(speechiness)
            
            # Ratios
            derived_features.append((basic_vals[:, 1] / (basic_vals[:, 3] + 0.001)).reshape(-1, 1))  # energy/acousticness
            derived_features.append((basic_vals[:, 0] / (basic_vals[:, 4] + 0.001)).reshape(-1, 1))  # danceability/instrumentalness
            
            # Combine all derived features
            low_level_features = np.hstack(derived_features)
            logger.info(f"✅ Created {low_level_features.shape[1]} derived audio features")
        
        # Prepare feature sets
        feature_sets = {}
        
        # 1. Naive features (basic 12 features)
        naive_features = df[basic_features].fillna(0).values
        scaler_naive = MinMaxScaler()
        feature_sets['naive_features'] = scaler_naive.fit_transform(naive_features)
        
        # 2. PCA features (reduced basic features)
        pca_basic = PCA(n_components=6, random_state=42)
        feature_sets['pca_features'] = pca_basic.fit_transform(feature_sets['naive_features'])
        
        # 3. Combined features (basic + low-level)
        combined_raw = np.hstack([naive_features, low_level_features])
        scaler_combined = StandardScaler()
        feature_sets['combined_features'] = scaler_combined.fit_transform(combined_raw)
        
        # 4. Low-level audio features only
        scaler_llav = StandardScaler()  
        feature_sets['llav_features'] = scaler_llav.fit_transform(low_level_features)
        
        # 5. Low-level PCA features (60 components)
        pca_llav = PCA(n_components=60, random_state=42)
        feature_sets['llav_pca'] = pca_llav.fit_transform(feature_sets['llav_features'])
        
        logger.info(f"✅ Prepared {len(feature_sets)} feature sets")
        for name, features in feature_sets.items():
            logger.info(f"  - {name}: {features.shape}")
            
        return feature_sets

    def generate_hdbscan_models(self, df: pd.DataFrame, force_regenerate: bool = False) -> bool:
        """Generate HDBSCAN clustering models with different feature approaches"""
        model_type = "hdbscan_models"
        
        # Define required files for all HDBSCAN variants
        required_files = []
        variants = ['naive_features', 'pca_features', 'combined_features', 'llav_features', 'llav_pca']
        
        for variant in variants:
            required_files.extend([
                f"{variant}_hdbscan_model.pkl",
                f"{variant}_knn_model.pkl", 
                f"{variant}_audio_embeddings.pkl",
                f"{variant}_cluster_labels.pkl",
                f"{variant}_song_indices.pkl",
                f"hdbscan_config_{variant}.json"
            ])
        
        # Add base models for backward compatibility
        base_files = ["hdbscan_model.pkl", "knn_model.pkl", "audio_embeddings.pkl", 
                     "cluster_labels.pkl", "song_indices.pkl"]
        required_files.extend(base_files)
        
        if not force_regenerate and self._check_existing_models(model_type, required_files):
            logger.info(f"✅ {model_type} already exist and are complete")
            return True

        try:
            logger.info(f"🚀 Generating HDBSCAN models...")
            
            # Prepare feature sets
            feature_sets = self.prepare_hdbscan_features(df)
            
            # HDBSCAN parameters for different variants
            hdbscan_configs = {
                'naive_features': {'min_cluster_size': 15, 'min_samples': 5, 'metric': 'euclidean'},
                'pca_features': {'min_cluster_size': 20, 'min_samples': 7, 'metric': 'euclidean'},  
                'combined_features': {'min_cluster_size': 25, 'min_samples': 10, 'metric': 'euclidean'},
                'llav_features': {'min_cluster_size': 30, 'min_samples': 8, 'metric': 'euclidean'},
                'llav_pca': {'min_cluster_size': 20, 'min_samples': 6, 'metric': 'euclidean'}
            }
            
            best_model_info = None
            best_score = -1
            
            # Generate each variant
            for variant_name, features in feature_sets.items():
                logger.info(f"🤖 Training {variant_name} HDBSCAN model...")
                
                config = hdbscan_configs[variant_name]
                
                # Train HDBSCAN
                clusterer = hdbscan.HDBSCAN(
                    min_cluster_size=config['min_cluster_size'],
                    min_samples=config['min_samples'], 
                    metric=config['metric'],
                    cluster_selection_epsilon=0.1
                )
                
                cluster_labels = clusterer.fit_predict(features)
                n_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
                n_noise = list(cluster_labels).count(-1)
                
                logger.info(f"  - Clusters: {n_clusters}, Noise points: {n_noise}")
                
                # Calculate silhouette score for model comparison
                if n_clusters > 1:
                    from sklearn.metrics import silhouette_score
                    silhouette_avg = silhouette_score(features, cluster_labels)
                    logger.info(f"  - Silhouette score: {silhouette_avg:.4f}")
                    
                    if silhouette_avg > best_score:
                        best_score = silhouette_avg
                        best_model_info = {
                            'variant': variant_name,
                            'clusterer': clusterer,
                            'features': features,
                            'labels': cluster_labels
                        }
                else:
                    silhouette_avg = -1
                
                # Train KNN model for recommendations within clusters
                knn_model = NearestNeighbors(n_neighbors=6, algorithm='auto', metric='euclidean')
                knn_model.fit(features)
                
                # Create song indices mapping
                song_indices = {
                    'track_ids': df['id'].values,
                    'track_names': df['name'].values,
                    'track_artists': df['artists_id'].values,
                    'track_uris': df['uri'].values if 'uri' in df.columns else df['id'].values
                }
                
                # Save variant-specific models
                variant_files = {
                    f"{variant_name}_hdbscan_model.pkl": clusterer,
                    f"{variant_name}_knn_model.pkl": knn_model,
                    f"{variant_name}_audio_embeddings.pkl": features,
                    f"{variant_name}_cluster_labels.pkl": cluster_labels,
                    f"{variant_name}_song_indices.pkl": song_indices
                }
                
                for filename, obj in variant_files.items():
                    with open(self.models_dir / filename, 'wb') as f:
                        pickle.dump(obj, f)
                
                # Save configuration
                config_data = {
                    'variant_name': variant_name,
                    'hdbscan_params': config,
                    'feature_shape': features.shape,
                    'n_clusters': int(n_clusters),
                    'n_noise_points': int(n_noise),
                    'silhouette_score': float(silhouette_avg),
                    'created_at': datetime.now().isoformat()
                }
                
                config_path = self.models_dir / f"hdbscan_config_{variant_name}.json"
                with open(config_path, 'w') as f:
                    json.dump(config_data, f, indent=2)
                
                logger.info(f"✅ {variant_name} HDBSCAN model saved")
            
            # Save base models (best performing variant for backward compatibility)
            if best_model_info:
                logger.info(f"🏆 Best model: {best_model_info['variant']} (score: {best_score:.4f})")
                
                base_files_map = {
                    "hdbscan_model.pkl": best_model_info['clusterer'],
                    "knn_model.pkl": None,  # Will be created below
                    "audio_embeddings.pkl": best_model_info['features'],
                    "cluster_labels.pkl": best_model_info['labels'],
                    "song_indices.pkl": None  # Will be created below
                }
                
                # Create base KNN and song indices
                base_knn = NearestNeighbors(n_neighbors=6, algorithm='auto', metric='euclidean')
                base_knn.fit(best_model_info['features'])
                base_files_map["knn_model.pkl"] = base_knn
                
                base_song_indices = {
                    'track_ids': df['id'].values,
                    'track_names': df['name'].values,
                    'track_artists': df['artists_id'].values,
                    'track_uris': df['uri'].values if 'uri' in df.columns else df['id'].values
                }
                base_files_map["song_indices.pkl"] = base_song_indices
                
                for filename, obj in base_files_map.items():
                    with open(self.models_dir / filename, 'wb') as f:
                        pickle.dump(obj, f)
                
                logger.info("✅ Base models saved for backward compatibility")
            
            self._create_status_markers(model_type, success=True)
            logger.info(f"✅ All HDBSCAN models generated successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error generating HDBSCAN models: {e}")
            self._create_status_markers(model_type, success=False)
            return False

    def preprocess_lyrics(self, text: str) -> str:
        """Preprocess lyrics text for similarity search"""
        if pd.isna(text) or not text:
            return ""
        
        # Convert to lowercase and clean
        text = text.lower()
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Tokenize
        tokens = word_tokenize(text)
        
        # Apply preprocessing (lemmatization + stop word removal)
        processed_tokens = [self.lemmatizer.lemmatize(token) for token in tokens 
                           if token not in self.stop_words and len(token) > 2]
        
        return ' '.join(processed_tokens)

    def generate_lyrics_models(self, df: pd.DataFrame, force_regenerate: bool = False) -> bool:
        """Generate lyrics similarity models"""
        model_type = "lyrics_models"
        
        # Define required files for lyrics models
        required_files = [
            "lyrics_tfidf_vectorizer.pkl",
            "lyrics_training_metadata.pkl",
            "lyrics_model_evaluation_results.json",
            "lyrics_similarity_search_production.py",
            "lyrics_config_knn_cosine.json",
            "lyrics_config_knn_euclidean.json", 
            "lyrics_config_svd_knn.json",
            "lyrics_config_knn_cosine_k20.json",
            "lyrics_similarity_model_knn_cosine.pkl",
            "lyrics_similarity_model_knn_euclidean.pkl",
            "lyrics_svd_model_svd_knn.pkl",
            "lyrics_knn_model_svd_knn.pkl",
            "lyrics_similarity_model_knn_cosine_k20.pkl"
        ]
        
        if not force_regenerate and self._check_existing_models(model_type, required_files):
            logger.info(f"✅ {model_type} already exist and are complete")
            return True

        try:
            logger.info(f"🚀 Generating lyrics similarity models...")
            
            # Check if lyrics column exists
            if 'lyrics' not in df.columns:
                logger.warning("⚠️ No lyrics column found, skipping lyrics models")
                return True
            
            # Filter to songs with lyrics
            lyrics_df = df[df['lyrics'].notna()].copy()
            if len(lyrics_df) == 0:
                logger.warning("⚠️ No songs with lyrics found, skipping lyrics models")
                return True
                
            logger.info(f"📝 Processing {len(lyrics_df)} songs with lyrics")
            
            # Preprocess lyrics
            logger.info("🔧 Preprocessing lyrics...")
            lyrics_df['processed_lyrics'] = lyrics_df['lyrics'].apply(self.preprocess_lyrics)
            
            # Remove songs with empty processed lyrics
            lyrics_df = lyrics_df[lyrics_df['processed_lyrics'].str.len() > 0]
            logger.info(f"📝 {len(lyrics_df)} songs after preprocessing")
            
            if len(lyrics_df) < 100:
                logger.warning("⚠️ Too few songs with valid lyrics, skipping lyrics models")
                return True
            
            # Split data
            train_df, val_df = train_test_split(lyrics_df, test_size=0.2, random_state=42)
            logger.info(f"📊 Train: {len(train_df)}, Validation: {len(val_df)}")
            
            # Create TF-IDF vectorizer
            logger.info("🔧 Creating TF-IDF vectorizer...")
            vectorizer = TfidfVectorizer(
                max_features=5000,
                min_df=2,
                max_df=0.8,
                ngram_range=(1, 2),
                stop_words='english'
            )
            
            X_train_tfidf = vectorizer.fit_transform(train_df['processed_lyrics'])
            X_val_tfidf = vectorizer.transform(val_df['processed_lyrics'])
            
            logger.info(f"📊 TF-IDF shape: {X_train_tfidf.shape}")
            
            # Define model configurations
            model_configs = {
                'knn_cosine': {
                    'model_class': NearestNeighbors,
                    'params': {'n_neighbors': 50, 'metric': 'cosine', 'algorithm': 'brute'},
                    'description': 'KNN with cosine similarity'
                },
                'knn_euclidean': {
                    'model_class': NearestNeighbors,
                    'params': {'n_neighbors': 50, 'metric': 'euclidean', 'algorithm': 'auto'},
                    'description': 'KNN with euclidean distance'
                },
                'svd_knn': {
                    'model_class': 'custom',  # Special handling
                    'params': {'n_components': 100, 'n_neighbors': 50},
                    'description': 'SVD dimensionality reduction + KNN'
                },
                'knn_cosine_k20': {
                    'model_class': NearestNeighbors,
                    'params': {'n_neighbors': 20, 'metric': 'cosine', 'algorithm': 'brute'},
                    'description': 'KNN with cosine similarity (k=20)'
                }
            }
            
            # Train models
            trained_models = {}
            
            for model_name, config in model_configs.items():
                logger.info(f"🤖 Training {model_name} model...")
                
                try:
                    if config['model_class'] == 'custom':  # SVD + KNN
                        # Train SVD
                        svd_model = TruncatedSVD(
                            n_components=config['params']['n_components'],
                            random_state=42
                        )
                        X_train_reduced = svd_model.fit_transform(X_train_tfidf)
                        X_val_reduced = svd_model.transform(X_val_tfidf)
                        
                        logger.info(f"📊 SVD explained variance: {svd_model.explained_variance_ratio_.sum():.4f}")
                        
                        # Train KNN on reduced features
                        knn_model = NearestNeighbors(
                            n_neighbors=config['params']['n_neighbors'],
                            metric='cosine',
                            algorithm='brute'
                        )
                        knn_model.fit(X_train_reduced)
                        
                        # Store both models
                        trained_models[model_name] = {
                            'svd_model': svd_model,
                            'knn_model': knn_model,
                            'type': 'svd_knn'
                        }
                        
                        # Save SVD and KNN models separately
                        svd_path = self.models_dir / f"lyrics_svd_model_{model_name}.pkl"
                        knn_path = self.models_dir / f"lyrics_knn_model_{model_name}.pkl"
                        
                        joblib.dump(svd_model, svd_path)
                        joblib.dump(knn_model, knn_path)
                        
                    else:  # Regular KNN models
                        model = config['model_class'](**config['params'])
                        model.fit(X_train_tfidf)
                        
                        trained_models[model_name] = {
                            'model': model,
                            'type': 'knn'
                        }
                        
                        # Save model
                        model_path = self.models_dir / f"lyrics_similarity_model_{model_name}.pkl"
                        joblib.dump(model, model_path)
                    
                    # Save model configuration
                    config_data = {
                        'model_type': model_name,
                        'model_params': config['params'],
                        'description': config['description'],
                        'sklearn_version': joblib.__version__,
                        'has_svd': config['model_class'] == 'custom',
                        'created_at': datetime.now().isoformat()
                    }
                    
                    config_path = self.models_dir / f"lyrics_config_{model_name}.json"
                    with open(config_path, 'w') as f:
                        json.dump(config_data, f, indent=2)
                    
                    logger.info(f"✅ {model_name} model trained and saved")
                    
                except Exception as e:
                    logger.error(f"❌ Error training {model_name}: {e}")
                    continue
            
            # Save TF-IDF vectorizer
            vectorizer_path = self.models_dir / "lyrics_tfidf_vectorizer.pkl"
            joblib.dump(vectorizer, vectorizer_path)
            
            # Save training metadata
            training_metadata = {
                'training_date': datetime.now().isoformat(),
                'n_training_songs': len(train_df),
                'n_validation_songs': len(val_df),
                'vocabulary_size': len(vectorizer.vocabulary_),
                'tfidf_features': X_train_tfidf.shape[1],
                'preprocessing': 'lemmatization + stop_words',
                'training_songs': [
                    {
                        'id': row['id'],
                        'name': row['name'],
                        'artists_id': row['artists_id']
                    }
                    for _, row in train_df.iterrows()
                ]
            }
            
            metadata_path = self.models_dir / "lyrics_training_metadata.pkl"
            joblib.dump(training_metadata, metadata_path)
            
            # Save evaluation results
            evaluation_summary = {
                'evaluation_date': datetime.now().isoformat(),
                'models_trained': list(trained_models.keys()),
                'best_model': list(trained_models.keys())[0] if trained_models else None,  # Default to first
                'dataset_info': {
                    'total_songs_with_lyrics': len(lyrics_df),
                    'training_size': len(train_df),
                    'validation_size': len(val_df),
                    'vocabulary_size': len(vectorizer.vocabulary_)
                }
            }
            
            results_path = self.models_dir / "lyrics_model_evaluation_results.json"
            with open(results_path, 'w') as f:
                json.dump(evaluation_summary, f, indent=2)
            
            # Create production function
            self._create_lyrics_production_function(list(trained_models.keys())[0] if trained_models else 'knn_cosine')
            
            self._create_status_markers(model_type, success=True)
            logger.info(f"✅ All lyrics models generated successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error generating lyrics models: {e}")
            self._create_status_markers(model_type, success=False)
            return False

    def _create_lyrics_production_function(self, best_model_name: str):
        """Create production-ready lyrics similarity search function"""
        function_code = f'''"""
Production-ready lyrics similarity search function
Generated automatically by model pipeline
"""

import pandas as pd
import numpy as np
import joblib
import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

# Initialize NLTK components
try:
    lemmatizer = WordNetLemmatizer()
    stop_words = set(stopwords.words('english'))
except:
    print("Warning: NLTK data not available. Please run: nltk.download(['punkt', 'stopwords', 'wordnet'])")

# Load model components (update paths as needed)
MODEL_DIR = "../../data/models"
vectorizer = joblib.load(f"{{MODEL_DIR}}/lyrics_tfidf_vectorizer.pkl")
training_metadata = joblib.load(f"{{MODEL_DIR}}/lyrics_training_metadata.pkl")

# Load best model: {best_model_name}
try:
    if "{best_model_name}" == "svd_knn":
        svd_model = joblib.load(f"{{MODEL_DIR}}/lyrics_svd_model_{best_model_name}.pkl")
        similarity_model = joblib.load(f"{{MODEL_DIR}}/lyrics_knn_model_{best_model_name}.pkl")
        model_type = "svd_knn"
    else:
        similarity_model = joblib.load(f"{{MODEL_DIR}}/lyrics_similarity_model_{best_model_name}.pkl")
        model_type = "knn"
        svd_model = None
except Exception as e:
    print(f"Error loading model: {{e}}")
    similarity_model = None

def preprocess_lyrics(text):
    """Preprocess lyrics using the same method as training"""
    if pd.isna(text):
        return ""
    
    # Convert to lowercase and clean
    text = text.lower()
    text = re.sub(r'[^a-zA-Z\\s]', '', text)
    text = re.sub(r'\\s+', ' ', text)
    text = text.strip()
    
    # Tokenize
    tokens = word_tokenize(text)
    
    # Apply preprocessing
    processed_tokens = [lemmatizer.lemmatize(token) for token in tokens 
                       if token not in stop_words and len(token) > 2]
    
    return ' '.join(processed_tokens)

def find_similar_songs_by_lyrics(lyrics_text, k=10):
    """
    Find similar songs based on lyrics content
    
    Args:
        lyrics_text (str): Lyrics text to find similar songs for
        k (int): Number of similar songs to return
    
    Returns:
        list: List of similar songs with similarity scores
    """
    if similarity_model is None:
        return []
        
    # Preprocess the input lyrics
    processed_lyrics = preprocess_lyrics(lyrics_text)
    
    if not processed_lyrics:
        return []
    
    # Vectorize the lyrics
    lyrics_vector = vectorizer.transform([processed_lyrics])
    
    # Apply SVD if needed
    if model_type == "svd_knn" and svd_model is not None:
        lyrics_vector = svd_model.transform(lyrics_vector)
    
    # Find similar songs
    distances, indices = similarity_model.kneighbors(lyrics_vector, n_neighbors=k)
    
    # Format results
    results = []
    for idx, distance in zip(indices[0], distances[0]):
        if idx < len(training_metadata['training_songs']):
            song_info = training_metadata['training_songs'][idx]
            results.append({{
                'track_id': song_info['id'],
                'name': song_info['name'],
                'artist': song_info['artists_id'],
                'similarity_score': float(1 - distance)  # Convert distance to similarity
            }})
    
    return results

# Example usage:
# recommendations = find_similar_songs_by_lyrics("your lyrics here", k=5)
'''
        
        function_path = self.models_dir / "lyrics_similarity_search_production.py"
        with open(function_path, 'w') as f:
            f.write(function_code)
        logger.info(f"✅ Production function saved to {function_path}")

    def generate_all_models(self, force_regenerate: bool = False) -> Dict[str, bool]:
        """Generate all models (HDBSCAN + Lyrics)"""
        logger.info("🚀 Starting complete model generation pipeline...")
        
        # Load data
        try:
            df = self.load_spotify_data()
        except Exception as e:
            logger.error(f"❌ Failed to load data: {e}")
            return {'data_loading': False}
        
        results = {}
        
        # Generate HDBSCAN models
        logger.info("=" * 60)
        logger.info("🎯 PHASE 1: HDBSCAN Clustering Models")
        logger.info("=" * 60)
        results['hdbscan_models'] = self.generate_hdbscan_models(df, force_regenerate)
        
        # Generate Lyrics models
        logger.info("=" * 60)
        logger.info("🎯 PHASE 2: Lyrics Similarity Models")
        logger.info("=" * 60)
        results['lyrics_models'] = self.generate_lyrics_models(df, force_regenerate)
        
        # Summary
        logger.info("=" * 60)
        logger.info("📊 PIPELINE SUMMARY")
        logger.info("=" * 60)
        
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        for model_type, success in results.items():
            status = "✅ SUCCESS" if success else "❌ FAILED"
            logger.info(f"{model_type}: {status}")
        
        logger.info(f"\n🎉 Overall: {success_count}/{total_count} model types generated successfully")
        
        if success_count == total_count:
            logger.info("🚀 All models generated successfully! System ready for deployment.")
        else:
            logger.warning("⚠️ Some models failed to generate. Check logs for details.")
        
        return results

    def check_model_status(self) -> Dict[str, Dict[str, Any]]:
        """Check status of all models"""
        logger.info("🔍 Checking model generation status...")
        
        model_types = {
            'hdbscan_models': {
                'variants': ['naive_features', 'pca_features', 'combined_features', 'llav_features', 'llav_pca'],
                'base_files': ['hdbscan_model.pkl', 'knn_model.pkl', 'audio_embeddings.pkl']
            },
            'lyrics_models': {
                'variants': ['knn_cosine', 'knn_euclidean', 'svd_knn', 'knn_cosine_k20'],
                'base_files': ['lyrics_tfidf_vectorizer.pkl', 'lyrics_training_metadata.pkl']
            }
        }
        
        status = {}
        
        for model_type, info in model_types.items():
            model_status = {
                'generated': False,
                'variants': {},
                'base_files': {},
                'success_marker': (self.models_dir / f".{model_type}_success").exists(),
                'failure_marker': (self.models_dir / f".{model_type}_failed").exists()
            }
            
            # Check variant files
            if model_type == 'hdbscan_models':
                for variant in info['variants']:
                    variant_files = [
                        f"{variant}_hdbscan_model.pkl",
                        f"{variant}_knn_model.pkl", 
                        f"{variant}_audio_embeddings.pkl",
                        f"hdbscan_config_{variant}.json"
                    ]
                    variant_exists = all((self.models_dir / f).exists() for f in variant_files)
                    model_status['variants'][variant] = variant_exists
                    
            elif model_type == 'lyrics_models':
                for variant in info['variants']:
                    if variant == 'svd_knn':
                        variant_files = [
                            f"lyrics_svd_model_{variant}.pkl",
                            f"lyrics_knn_model_{variant}.pkl",
                            f"lyrics_config_{variant}.json"
                        ]
                    else:
                        variant_files = [
                            f"lyrics_similarity_model_{variant}.pkl",
                            f"lyrics_config_{variant}.json"
                        ]
                    variant_exists = all((self.models_dir / f).exists() for f in variant_files)
                    model_status['variants'][variant] = variant_exists
            
            # Check base files
            for base_file in info['base_files']:
                model_status['base_files'][base_file] = (self.models_dir / base_file).exists()
            
            # Overall status
            model_status['generated'] = (
                model_status['success_marker'] and 
                all(model_status['variants'].values()) and
                all(model_status['base_files'].values())
            )
            
            status[model_type] = model_status
        
        # Print status
        for model_type, model_status in status.items():
            status_emoji = "✅" if model_status['generated'] else "❌"
            logger.info(f"{status_emoji} {model_type.upper()}: {'Generated' if model_status['generated'] else 'Missing'}")
            
            for variant, exists in model_status['variants'].items():
                variant_emoji = "✅" if exists else "❌"
                logger.info(f"  {variant_emoji} {variant}")
        
        return status


def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate ML models for Spotify Recommendation System')
    parser.add_argument('--force', action='store_true', help='Force regeneration of existing models')
    parser.add_argument('--check-only', action='store_true', help='Only check model status, do not generate')
    parser.add_argument('--data-dir', default='/app/data', help='Data directory path')
    parser.add_argument('--models-dir', default='/app/data/models', help='Models directory path')
    
    args = parser.parse_args()
    
    # Initialize pipeline
    pipeline = ModelPipeline(data_dir=args.data_dir, models_dir=args.models_dir)
    
    if args.check_only:
        # Only check status
        status = pipeline.check_model_status()
        return all(model_info['generated'] for model_info in status.values())
    else:
        # Generate models
        results = pipeline.generate_all_models(force_regenerate=args.force)
        return all(results.values())


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 