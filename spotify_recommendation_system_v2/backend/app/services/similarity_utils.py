"""
Similarity Utilities - Helper functions for converting distances to similarity scores
"""

import numpy as np
from typing import List, Tuple, Optional
import math


def distance_to_similarity(distance: float, method: str = "exponential", scale_factor: float = 1.0) -> float:
    """
    Convert distance to similarity score (0-1 range, higher = more similar)
    
    Args:
        distance (float): Distance value (lower = more similar)
        method (str): Conversion method ('exponential', 'inverse', 'gaussian', 'linear')
        scale_factor (float): Scaling factor for the conversion
    
    Returns:
        float: Similarity score between 0 and 1
    """
    if distance < 0:
        distance = 0
    
    if method == "exponential":
        # Exponential decay: similarity = exp(-distance * scale_factor)
        # Good for distance values in range [0, 2-3]
        return math.exp(-distance * scale_factor)
    
    elif method == "inverse":
        # Inverse: similarity = 1 / (1 + distance * scale_factor)
        # Good for any distance range, asymptotically approaches 0
        return 1.0 / (1.0 + distance * scale_factor)
    
    elif method == "gaussian":
        # Gaussian: similarity = exp(-(distance^2) / (2 * scale_factor^2))
        # Good for distance values where you want sharp dropoff
        return math.exp(-(distance ** 2) / (2 * (scale_factor ** 2)))
    
    elif method == "linear":
        # Linear: similarity = max(0, 1 - distance / scale_factor)
        # Good when you know the maximum expected distance
        return max(0.0, 1.0 - (distance / scale_factor))
    
    else:
        raise ValueError(f"Unknown similarity method: {method}")


def normalize_distances_to_similarities(distances: List[float], method: str = "exponential") -> List[float]:
    """
    Convert a list of distances to normalized similarity scores
    
    Args:
        distances (List[float]): List of distance values
        method (str): Conversion method
    
    Returns:
        List[float]: List of similarity scores between 0 and 1
    """
    if not distances:
        return []
    
    distances = np.array(distances)
    
    # Auto-determine scale factor based on distance distribution
    if method == "linear":
        # For linear, use max distance as scale factor
        scale_factor = max(distances) if max(distances) > 0 else 1.0
    elif method == "exponential":
        # For exponential, use median distance for good spread
        scale_factor = 1.0 / np.median(distances) if np.median(distances) > 0 else 1.0
    elif method == "inverse":
        # For inverse, use median distance
        scale_factor = 1.0 / np.median(distances) if np.median(distances) > 0 else 1.0
    elif method == "gaussian":
        # For gaussian, use standard deviation
        scale_factor = np.std(distances) if np.std(distances) > 0 else 1.0
    else:
        scale_factor = 1.0
    
    similarities = [distance_to_similarity(d, method, scale_factor) for d in distances]
    
    # Additional normalization to ensure good spread
    similarities = np.array(similarities)
    if similarities.max() > similarities.min():
        # Normalize to 0-1 range while preserving relative ordering
        similarities = (similarities - similarities.min()) / (similarities.max() - similarities.min())
    
    return similarities.tolist()


def get_optimal_similarity_method(model_type: str, feature_type: str = "audio") -> str:
    """
    Get the optimal similarity conversion method for a given model type
    
    Args:
        model_type (str): Type of model (e.g., 'hdbscan', 'lyrics', 'knn')
        feature_type (str): Type of features (e.g., 'audio', 'lyrics', 'combined')
    
    Returns:
        str: Recommended similarity method
    """
    # Mapping of model types to optimal similarity methods
    method_mapping = {
        "hdbscan": "exponential",      # HDBSCAN distances usually in 0-2 range
        "lyrics": "inverse",           # Lyrics distances can vary widely
        "knn": "exponential",          # KNN distances usually well-behaved
        "cosine": "linear",            # Cosine distances are in 0-2 range
        "euclidean": "exponential",    # Euclidean distances need exponential decay
        "svd": "inverse",              # SVD features can have varying scales
    }
    
    # Default to exponential for unknown types
    return method_mapping.get(model_type.lower(), "exponential")


class SimilarityScoreCalculator:
    """
    Class for calculating and caching similarity scores with different methods
    """
    
    def __init__(self, default_method: str = "exponential"):
        self.default_method = default_method
        self._cache = {}
    
    def calculate_similarities(
        self, 
        distances: List[float], 
        model_type: str = None,
        method: str = None
    ) -> List[float]:
        """
        Calculate similarity scores from distances with caching
        
        Args:
            distances: List of distance values
            model_type: Type of model for method selection
            method: Specific method to use (overrides model_type)
        
        Returns:
            List of similarity scores
        """
        # Create cache key
        cache_key = (tuple(distances), model_type, method)
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Determine method
        if method is None:
            if model_type:
                method = get_optimal_similarity_method(model_type)
            else:
                method = self.default_method
        
        # Calculate similarities
        similarities = normalize_distances_to_similarities(distances, method)
        
        # Cache result
        self._cache[cache_key] = similarities
        
        return similarities
    
    def add_similarity_scores(
        self, 
        recommendations: List[dict], 
        model_type: str = None
    ) -> List[dict]:
        """
        Add similarity scores to recommendation dictionaries
        
        Args:
            recommendations: List of recommendation dicts with 'distance' field
            model_type: Type of model for method selection
        
        Returns:
            Updated recommendations with 'similarity_score' field
        """
        if not recommendations:
            return recommendations
        
        # Extract distances
        distances = [rec.get('distance', rec.get('similarity_score', 0.0)) for rec in recommendations]
        
        # Calculate similarities
        similarities = self.calculate_similarities(distances, model_type)
        
        # Add to recommendations
        for i, rec in enumerate(recommendations):
            rec['similarity_score'] = similarities[i]
            # Keep original distance for reference
            if 'distance' not in rec:
                rec['distance'] = distances[i]
        
        return recommendations
    
    def clear_cache(self):
        """Clear the similarity calculation cache"""
        self._cache.clear()


# Global calculator instance
similarity_calculator = SimilarityScoreCalculator() 