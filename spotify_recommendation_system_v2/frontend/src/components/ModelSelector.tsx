import React from 'react';

interface ModelSelectorProps {
  selectedModels: string[];
  onModelChange: (models: string[]) => void;
  availableModels?: string[];
  disabled?: boolean;
}

const MODEL_INFO = {
  cluster: {
    name: 'Audio Clustering',
    description: 'Recommendations based on audio features and HDBSCAN clustering',
    icon: '🎵',
    color: '#1DB954'
  },
  hdbscan_knn: {
    name: 'HDBSCAN + KNN',
    description: 'Advanced clustering with trained audio feature embeddings',
    icon: '🔬',
    color: '#8B5CF6'
  },
  // HDBSCAN Advanced Models
  hdbscan_naive_features: {
    name: 'HDBSCAN Naive',
    description: 'Basic audio features with HDBSCAN clustering',
    icon: '🎯',
    color: '#9333EA'
  },
  hdbscan_pca_features: {
    name: 'HDBSCAN PCA',
    description: 'PCA-reduced audio features with HDBSCAN',
    icon: '📊',
    color: '#7C3AED'
  },
  hdbscan_llav_features: {
    name: 'HDBSCAN Low-Level',
    description: 'Detailed low-level audio features with HDBSCAN',
    icon: '🔍',
    color: '#6D28D9'
  },
  hdbscan_llav_pca: {
    name: 'HDBSCAN Low-Level PCA',
    description: 'Low-level audio features + PCA (best performance)',
    icon: '⭐',
    color: '#5B21B6'
  },
  hdbscan_combined_features: {
    name: 'HDBSCAN Combined',
    description: 'Combined basic and low-level features with HDBSCAN',
    icon: '🔀',
    color: '#4C1D95'
  },
  // Lyrics Models
  lyrics: {
    name: 'Lyrics Similarity',
    description: 'Recommendations based on lyrical content and themes',
    icon: '📝',
    color: '#FF6B6B'
  },
  knn_cosine: {
    name: 'KNN Cosine',
    description: 'Lyrics similarity using cosine distance',
    icon: '📐',
    color: '#EC4899'
  },
  knn_cosine_k20: {
    name: 'KNN Cosine K20',
    description: 'Lyrics similarity with K=20 neighbors',
    icon: '🔢',
    color: '#F97316'
  },
  knn_euclidean: {
    name: 'KNN Euclidean',
    description: 'Lyrics similarity using Euclidean distance',
    icon: '📏',
    color: '#EF4444'
  },
  svd_knn: {
    name: 'SVD + KNN',
    description: 'Dimensionality reduction with KNN for lyrics',
    icon: '🧮',
    color: '#A855F7'
  },
  artist_based: {
    name: 'Similar Artists',
    description: 'More songs by artists you already like',
    icon: '🎤',
    color: '#F59E0B'
  },
  genre_based: {
    name: 'Genre-Based',
    description: 'Songs from similar genres and musical styles',
    icon: '🎶',
    color: '#10B981'
  },
  global: {
    name: 'Global',
    description: 'Recommendations from the entire dataset',
    icon: '🌍',
    color: '#4ECDC4'
  },
  hybrid: {
    name: 'Hybrid',
    description: 'Combined approach using multiple features',
    icon: '🔀',
    color: '#45B7D1'
  }
};

const ModelSelector: React.FC<ModelSelectorProps> = ({
  selectedModels,
  onModelChange,
  availableModels = [
    'cluster', 'hdbscan_knn', 
    'hdbscan_naive_features', 'hdbscan_pca_features', 'hdbscan_llav_features', 'hdbscan_llav_pca', 'hdbscan_combined_features',
    'lyrics', 'knn_cosine', 'knn_cosine_k20', 'knn_euclidean', 'svd_knn',
    'artist_based', 'genre_based', 'global', 'hybrid'
  ],
  disabled = false
}) => {
  const handleModelToggle = (modelType: string) => {
    if (disabled) return;
    
    if (selectedModels.includes(modelType)) {
      // Remove model
      onModelChange(selectedModels.filter(m => m !== modelType));
    } else {
      // Add model
      onModelChange([...selectedModels, modelType]);
    }
  };

  return (
    <div className="model-selector">
      <h3 className="text-lg font-semibold mb-4">Select Recommendation Models</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {availableModels.map((modelType) => {
          const modelInfo = MODEL_INFO[modelType as keyof typeof MODEL_INFO] || {
            name: modelType.charAt(0).toUpperCase() + modelType.slice(1).replace(/_/g, ' '),
            description: `${modelType} recommendation model`,
            icon: '🎯',
            color: '#6B7280'
          };
          const isSelected = selectedModels.includes(modelType);
          
          return (
            <div
              key={modelType}
              className={`
                model-card p-4 border-2 rounded-lg cursor-pointer transition-all duration-200
                ${isSelected 
                  ? 'border-blue-500 bg-blue-50 shadow-lg' 
                  : 'border-gray-200 bg-white hover:border-gray-300'
                }
                ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
              `}
              onClick={() => handleModelToggle(modelType)}
              style={{
                borderColor: isSelected ? modelInfo?.color : undefined,
                backgroundColor: isSelected ? `${modelInfo?.color}10` : undefined
              }}
            >
              <div className="flex items-start space-x-3">
                <div className="text-2xl">{modelInfo?.icon}</div>
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <h4 className="font-semibold text-gray-800">
                      {modelInfo?.name}
                    </h4>
                    {isSelected && (
                      <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                    )}
                  </div>
                  <p className="text-sm text-gray-600 mt-1">
                    {modelInfo?.description}
                  </p>
                  <div className="mt-2 flex flex-wrap gap-1">
                    {(modelType === 'hdbscan_knn' || modelType === 'artist_based' || modelType === 'genre_based') && (
                      <span className="inline-block px-2 py-1 text-xs bg-purple-100 text-purple-700 rounded-full">
                        {modelType === 'hdbscan_knn' ? 'Advanced' : 'New!'}
                      </span>
                    )}
                    {modelType.startsWith('hdbscan_') && modelType !== 'hdbscan_knn' && (
                      <span className="inline-block px-2 py-1 text-xs bg-violet-100 text-violet-700 rounded-full">
                        HDBSCAN
                      </span>
                    )}
                    {modelType === 'hdbscan_llav_pca' && (
                      <span className="inline-block px-2 py-1 text-xs bg-yellow-100 text-yellow-700 rounded-full">
                        Best Performance
                      </span>
                    )}
                    {(modelType.startsWith('knn_') || modelType.startsWith('svd_') || modelType === 'lyrics') && (
                      <span className="inline-block px-2 py-1 text-xs bg-pink-100 text-pink-700 rounded-full">
                        Lyrics
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
      
      {selectedModels.length === 0 && (
        <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
          <p className="text-sm text-yellow-700">
            ⚠️ Please select at least one recommendation model
          </p>
        </div>
      )}
      
      {selectedModels.length > 1 && (
        <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-sm text-blue-700">
            🔍 {selectedModels.length} models selected - you'll be able to compare their results!
          </p>
        </div>
      )}
    </div>
  );
};

export default ModelSelector; 