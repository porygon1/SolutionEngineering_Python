"""
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
vectorizer = joblib.load(f"{MODEL_DIR}/lyrics_tfidf_vectorizer.pkl")
training_metadata = joblib.load(f"{MODEL_DIR}/lyrics_training_metadata.pkl")

# Load best model: knn_cosine
try:
    if "knn_cosine" == "svd_knn":
        svd_model = joblib.load(f"{MODEL_DIR}/lyrics_svd_model_knn_cosine.pkl")
        similarity_model = joblib.load(f"{MODEL_DIR}/lyrics_knn_model_knn_cosine.pkl")
        model_type = "svd_knn"
    else:
        similarity_model = joblib.load(f"{MODEL_DIR}/lyrics_similarity_model_knn_cosine.pkl")
        model_type = "knn"
        svd_model = None
except Exception as e:
    print(f"Error loading model: {e}")
    similarity_model = None

def preprocess_lyrics(text):
    """Preprocess lyrics using the same method as training"""
    if pd.isna(text):
        return ""
    
    # Convert to lowercase and clean
    text = text.lower()
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
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
            results.append({
                'track_id': song_info['id'],
                'name': song_info['name'],
                'artist': song_info['artists_id'],
                'similarity_score': float(1 - distance)  # Convert distance to similarity
            })
    
    return results

# Example usage:
# recommendations = find_similar_songs_by_lyrics("your lyrics here", k=5)
