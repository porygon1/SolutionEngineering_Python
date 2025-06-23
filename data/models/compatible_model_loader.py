"""
Compatible Model Loader for Backend Service
Handles the new individual model file format
"""

import os
import joblib
import json
import numpy as np
from typing import List, Tuple, Optional

class CompatibleLyricsSimilarityModel:
    """Model loader that handles individual model files"""

    def __init__(self, models_dir: str, model_name: str = None):
        self.models_dir = models_dir
        self.model_name = model_name
        self.vectorizer = None
        self.model = None
        self.svd_model = None
        self.config = None
        self.metadata = None

    def load_model(self, model_name: str = None):
        """Load a specific model by name"""
        if model_name:
            self.model_name = model_name

        if not self.model_name:
            raise ValueError("Model name must be specified")

        # Load vectorizer (shared by all models)
        vectorizer_path = os.path.join(self.models_dir, "lyrics_tfidf_vectorizer.pkl")
        self.vectorizer = joblib.load(vectorizer_path)

        # Load model configuration
        config_path = os.path.join(self.models_dir, f"lyrics_config_{self.model_name}.json")
        with open(config_path, 'r') as f:
            self.config = json.load(f)

        # Load the actual model(s)
        if self.config.get('has_svd', False):
            # Load SVD + KNN models separately
            svd_path = os.path.join(self.models_dir, f"lyrics_svd_model_{self.model_name}.pkl")
            knn_path = os.path.join(self.models_dir, f"lyrics_knn_model_{self.model_name}.pkl")

            self.svd_model = joblib.load(svd_path)
            self.model = joblib.load(knn_path)
        else:
            # Load direct model
            model_path = os.path.join(self.models_dir, f"lyrics_similarity_model_{self.model_name}.pkl")
            self.model = joblib.load(model_path)

        # Load metadata
        metadata_path = os.path.join(self.models_dir, "lyrics_training_metadata.pkl")
        self.metadata = joblib.load(metadata_path)

        return self

    def find_similar(self, query_vector, k: int = 10) -> Tuple[List[int], List[float]]:
        """Find similar songs using the loaded model"""
        if self.config.get('has_svd', False):
            # Transform using SVD first
            query_reduced = self.svd_model.transform(query_vector)
            distances, indices = self.model.kneighbors(query_reduced, n_neighbors=k)
        else:
            distances, indices = self.model.kneighbors(query_vector, n_neighbors=k)

        # Return actual distances instead of converting to similarities
        return indices[0].tolist(), distances[0].tolist()

    def preprocess_lyrics(self, text: str) -> str:
        """Preprocess lyrics using the same method as training"""
        import re
        import nltk
        from nltk.corpus import stopwords
        from nltk.stem import WordNetLemmatizer
        from nltk.tokenize import word_tokenize

        if not text:
            return ""

        # Basic cleaning
        text = text.lower()
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()

        # Tokenize and process based on training method
        try:
            tokens = word_tokenize(text)
            lemmatizer = WordNetLemmatizer()
            stop_words = set(stopwords.words('english'))

            processed_tokens = [lemmatizer.lemmatize(token) for token in tokens 
                              if token not in stop_words and len(token) > 2]

            return ' '.join(processed_tokens)
        except:
            # Fallback to basic processing
            tokens = text.split()
            return ' '.join([token for token in tokens if len(token) > 2])

    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        models = []
        for filename in os.listdir(self.models_dir):
            if filename.startswith('lyrics_config_') and filename.endswith('.json'):
                model_name = filename.replace('lyrics_config_', '').replace('.json', '')
                models.append(model_name)
        return models

    def get_model_info(self) -> dict:
        """Get information about the loaded model"""
        if not self.config:
            return {}

        return {
            'model_name': self.model_name,
            'model_type': self.config.get('model_type'),
            'has_svd': self.config.get('has_svd', False),
            'sklearn_version': self.config.get('sklearn_version'),
            'parameters': self.config.get('model_params', {}),
            'vocabulary_size': len(self.vectorizer.vocabulary_) if self.vectorizer else 0
        }

# Example usage:
# loader = CompatibleLyricsSimilarityModel("/path/to/models")
# available_models = loader.get_available_models()
# loader.load_model("svd_knn")  # or any available model
# query_vector = loader.vectorizer.transform([processed_lyrics])
# indices, similarities = loader.find_similar(query_vector, k=10)
