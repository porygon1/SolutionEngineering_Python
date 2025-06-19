import pytest
import numpy as np
from streamlit_app.utils.recommendations import get_recommendations_within_cluster, get_global_recommendations

class DummyKNN:
    def kneighbors(self, X, n_neighbors=2):
        return np.array([[0.1, 0.2]]), np.array([[0, 1]])

def test_get_recommendations_within_cluster(sample_embeddings):
    knn = DummyKNN()
    labels = np.array([0, 0])
    distances, indices = get_recommendations_within_cluster(knn, sample_embeddings, labels, 0, n_neighbors=2)
    assert distances is not None
    assert indices is not None
    assert len(indices) == 2

def test_get_global_recommendations(sample_embeddings):
    knn = DummyKNN()
    distances, indices = get_global_recommendations(knn, sample_embeddings, 0, n_neighbors=2)
    assert distances is not None
    assert indices is not None
    assert len(indices) == 2 