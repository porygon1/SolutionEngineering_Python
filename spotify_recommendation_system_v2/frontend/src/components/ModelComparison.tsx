import React, { useState, useEffect } from 'react';
import { apiService, ModelComparisonResponse, ModelComparisonResult, Song } from '../services/api';
import SongCard from './SongCard';
import ModelSelector from './ModelSelector';

interface ModelComparisonProps {
  initialSongs?: Song[];
  onSongSelect?: (song: Song) => void;
}

const ModelComparison: React.FC<ModelComparisonProps> = ({
  initialSongs = [],
  onSongSelect
}) => {
  const [selectedModels, setSelectedModels] = useState<string[]>(['hdbscan_knn', 'lyrics']);
  const [availableModels, setAvailableModels] = useState<string[]>(['cluster', 'hdbscan_knn', 'lyrics', 'artist_based', 'genre_based', 'global', 'hybrid']);
  const [comparisonResults, setComparisonResults] = useState<ModelComparisonResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [likedSongs, setLikedSongs] = useState<Song[]>(initialSongs);

  // Fetch available models on component mount
  useEffect(() => {
    const fetchAvailableModels = async () => {
      try {
        const modelsResponse = await apiService.recommendations.getAvailableModels();
        if (modelsResponse.available_models && modelsResponse.available_models.length > 0) {
          setAvailableModels(modelsResponse.available_models);
        }
      } catch (err) {
        console.error('Failed to fetch available models:', err);
        // Keep the default models if fetch fails
      }
    };

    fetchAvailableModels();
  }, []);

  const handleCompareModels = async () => {
    if (selectedModels.length === 0) {
      setError('Please select at least one model');
      return;
    }

    if (likedSongs.length === 0) {
      setError('Please select at least one song to get recommendations');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await apiService.recommendations.compare({
        liked_song_ids: likedSongs.map(s => s.id),
        models_to_compare: selectedModels,
        n_recommendations: 10
      });

      setComparisonResults(response);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to compare models');
      console.error('Model comparison error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const addLikedSong = (song: Song) => {
    if (!likedSongs.find(s => s.id === song.id)) {
      setLikedSongs([...likedSongs, song]);
    }
  };

  const removeLikedSong = (songId: string) => {
    setLikedSongs(likedSongs.filter(s => s.id !== songId));
  };

  const getModelColor = (modelType: string): string => {
    const colors = {
      cluster: '#1DB954',
      hdbscan_knn: '#8B5CF6',
      lyrics: '#FF6B6B',
      artist_based: '#F59E0B',
      genre_based: '#10B981',
      global: '#4ECDC4',
      hybrid: '#45B7D1'
    };
    return colors[modelType as keyof typeof colors] || '#6B7280';
  };

  const getModelIcon = (modelType: string): string => {
    const icons = {
      cluster: '🎵',
      hdbscan_knn: '🔬',
      lyrics: '📝',
      artist_based: '🎤',
      genre_based: '🎵',
      global: '🌍',
      hybrid: '🔀'
    };
    return icons[modelType as keyof typeof icons] || '🎯';
  };

  return (
    <div className="model-comparison">
      <div className="mb-8">
        <h2 className="text-2xl font-bold mb-4">Model Comparison</h2>
        <p className="text-gray-600 mb-6">
          Compare different recommendation models to see how they perform with your music taste.
        </p>

        {/* Liked Songs Section */}
        <div className="mb-6">
          <h3 className="text-lg font-semibold mb-3">Your Liked Songs</h3>
          {likedSongs.length === 0 ? (
            <div className="p-4 border-2 border-dashed border-gray-300 rounded-lg text-center">
              <p className="text-gray-500">No songs selected. Search and add songs to get recommendations.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {likedSongs.map((song) => (
                <div key={song.id} className="relative">
                  <SongCard 
                    song={song} 
                    onPlay={onSongSelect}
                    isPlaying={false}
                    showSimilarityScore={false}
                  />
                  <button
                    onClick={() => removeLikedSong(song.id)}
                    className="absolute top-2 right-2 w-6 h-6 bg-red-500 text-white rounded-full text-xs hover:bg-red-600"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Model Selection */}
        <ModelSelector
          selectedModels={selectedModels}
          onModelChange={setSelectedModels}
          availableModels={availableModels}
          disabled={isLoading}
        />

        {/* Compare Button */}
        <div className="mt-6">
          <button
            onClick={handleCompareModels}
            disabled={isLoading || selectedModels.length === 0 || likedSongs.length === 0}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <div className="flex items-center space-x-2">
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                <span>Comparing Models...</span>
              </div>
            ) : (
              'Compare Models'
            )}
          </button>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-700">❌ {error}</p>
          </div>
        )}
      </div>

      {/* Comparison Results */}
      {comparisonResults && (
        <div className="comparison-results">
          <div className="mb-6">
            <h3 className="text-xl font-semibold mb-2">Comparison Results</h3>
            <p className="text-gray-600">
              Processed in {comparisonResults.total_processing_time_ms.toFixed(1)}ms
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {comparisonResults.results.map((result: ModelComparisonResult) => (
              <div key={result.model_type} className="model-result">
                <div 
                  className="model-header p-4 rounded-t-lg"
                  style={{ backgroundColor: `${getModelColor(result.model_type)}20` }}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="text-2xl">{getModelIcon(result.model_type)}</div>
                      <div>
                        <h4 className="font-semibold text-lg capitalize">
                          {result.model_type} Model
                        </h4>
                        <p className="text-sm text-gray-600">
                          {result.total_found} recommendations in {result.processing_time_ms.toFixed(1)}ms
                        </p>
                      </div>
                    </div>
                    {result.error && (
                      <div className="text-red-500 text-sm">
                        ⚠️ Error
                      </div>
                    )}
                  </div>
                </div>

                <div className="model-content border border-t-0 rounded-b-lg p-4">
                  {result.error ? (
                    <div className="text-red-600 text-center py-8">
                      <p>❌ {result.error}</p>
                    </div>
                  ) : result.recommendations.length === 0 ? (
                    <div className="text-gray-500 text-center py-8">
                      <p>No recommendations found</p>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {result.recommendations.slice(0, 5).map((song) => (
                        <div 
                          key={`${result.model_type}-${song.id}`}
                          className="recommendation-item"
                        >
                          <SongCard 
                            song={song} 
                            onPlay={onSongSelect}
                            isPlaying={false}
                            showSimilarityScore={true}
                            compact={true}
                          />
                        </div>
                      ))}
                      {result.recommendations.length > 5 && (
                        <div className="text-center pt-2">
                          <button className="text-blue-600 hover:text-blue-800 text-sm">
                            View all {result.recommendations.length} recommendations
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Comparison Insights */}
          <div className="mt-8 p-6 bg-gray-50 rounded-lg">
            <h4 className="font-semibold mb-4">💡 Comparison Insights</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <strong>Fastest Model:</strong>{' '}
                {comparisonResults.results
                  .filter(r => !r.error)
                  .sort((a, b) => a.processing_time_ms - b.processing_time_ms)[0]?.model_type || 'N/A'}
              </div>
              <div>
                <strong>Most Recommendations:</strong>{' '}
                {comparisonResults.results
                  .filter(r => !r.error)
                  .sort((a, b) => b.total_found - a.total_found)[0]?.model_type || 'N/A'}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ModelComparison; 