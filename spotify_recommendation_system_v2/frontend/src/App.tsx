import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { QueryClient, QueryClientProvider, useQuery, useInfiniteQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { Music, Home, Search, TrendingUp, Play, Pause, Clock, Heart, Grid, List, ArrowLeft, Volume2, SkipBack, SkipForward } from 'lucide-react';
import { clsx } from 'clsx';
import { apiService, Song, ClusterInfo } from './services/api';
import { generateAlbumCover, getPreviewUrl, formatAudioFeatures, getMusicalKey, formatTempo, formatDuration } from './services/spotify';

// Create a client for React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

// Audio player context
interface AudioContextType {
  currentTrack: Song | null;
  isPlaying: boolean;
  volume: number;
  currentTime: number;
  duration: number;
  playTrack: (track: Song) => void;
  pauseTrack: () => void;
  setVolume: (volume: number) => void;
  seekTo: (time: number) => void;
}

const AudioContext = React.createContext<AudioContextType | null>(null);

function AudioProvider({ children }: { children: React.ReactNode }) {
  const [currentTrack, setCurrentTrack] = React.useState<Song | null>(null);
  const [isPlaying, setIsPlaying] = React.useState(false);
  const [volume, setVolumeState] = React.useState(0.7);
  const [currentTime, setCurrentTime] = React.useState(0);
  const [duration, setDuration] = React.useState(0);
  const audioRef = React.useRef<HTMLAudioElement | null>(null);

  React.useEffect(() => {
    const audio = new Audio();
    audioRef.current = audio;

    const handleTimeUpdate = () => setCurrentTime(audio.currentTime);
    const handleDurationChange = () => setDuration(audio.duration);
    const handleEnded = () => setIsPlaying(false);

    audio.addEventListener('timeupdate', handleTimeUpdate);
    audio.addEventListener('durationchange', handleDurationChange);
    audio.addEventListener('ended', handleEnded);

    return () => {
      audio.removeEventListener('timeupdate', handleTimeUpdate);
      audio.removeEventListener('durationchange', handleDurationChange);
      audio.removeEventListener('ended', handleEnded);
      audio.pause();
    };
  }, []);

  const playTrack = (track: Song) => {
    if (audioRef.current) {
      if (currentTrack?.id === track.id) {
        if (isPlaying) {
          audioRef.current.pause();
          setIsPlaying(false);
        } else {
          audioRef.current.play();
          setIsPlaying(true);
        }
      } else {
        setCurrentTrack(track);
        const previewUrl = getPreviewUrl(track);
        audioRef.current.src = previewUrl || '';
        audioRef.current.volume = volume;
        if (previewUrl) {
          audioRef.current.play();
          setIsPlaying(true);
        }
      }
    }
  };

  const pauseTrack = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      setIsPlaying(false);
    }
  };

  const setVolume = (newVolume: number) => {
    setVolumeState(newVolume);
    if (audioRef.current) {
      audioRef.current.volume = newVolume;
    }
  };

  const seekTo = (time: number) => {
    if (audioRef.current) {
      audioRef.current.currentTime = time;
    }
  };

  return (
    <AudioContext.Provider value={{
      currentTrack,
      isPlaying,
      volume,
      currentTime,
      duration,
      playTrack,
      pauseTrack,
      setVolume,
      seekTo
    }}>
      {children}
    </AudioContext.Provider>
  );
}

function useAudio() {
  const context = React.useContext(AudioContext);
  if (!context) {
    throw new Error('useAudio must be used within AudioProvider');
  }
  return context;
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AudioProvider>
      <Router>
        <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-900 text-white">
          {/* Background gradient */}
          <div className="fixed inset-0 bg-gradient-to-br from-green-500/5 via-transparent to-green-500/5 pointer-events-none" />
          
          {/* Main layout */}
          <div className="relative flex h-screen overflow-hidden">
            {/* Sidebar */}
            <motion.aside
              initial={{ x: -300 }}
              animate={{ x: 0 }}
              transition={{ duration: 0.5, ease: "easeOut" }}
              className="hidden md:flex w-64 bg-black/50 backdrop-blur-sm border-r border-gray-800"
            >
              <Navigation />
            </motion.aside>

            {/* Main content area */}
            <div className="flex-1 flex flex-col overflow-hidden">
              {/* Top navbar */}
              <motion.header
                initial={{ y: -100 }}
                animate={{ y: 0 }}
                transition={{ duration: 0.5, ease: "easeOut", delay: 0.2 }}
                className="bg-black/30 backdrop-blur-sm border-b border-gray-800 p-4"
              >
                <TopNavbar />
              </motion.header>

              {/* Main content */}
              <motion.main
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, ease: "easeOut", delay: 0.3 }}
                  className="flex-1 overflow-y-auto p-6 pb-24"
              >
                <div className="max-w-7xl mx-auto">
                  <Routes>
                    <Route path="/" element={<HomePage />} />
                    <Route path="/recommendations" element={<RecommendationsPage />} />
                    <Route path="/explore" element={<ExplorePage />} />
                    <Route path="/compare" element={<ModelComparisonPage />} />
                  </Routes>
                </div>
              </motion.main>

                {/* Audio Player */}
                <AudioPlayer />
            </div>
          </div>
        </div>
      </Router>
      </AudioProvider>
    </QueryClientProvider>
  );
}

// Navigation Component
function Navigation() {
  const navItems = [
    { icon: Home, label: 'Home', path: '/' },
    { icon: Search, label: 'Explore', path: '/explore' },
    { icon: TrendingUp, label: 'Recommendations', path: '/recommendations' },
    { icon: Grid, label: 'Model Comparison', path: '/compare' },
  ];

  return (
    <nav className="flex flex-col p-6 space-y-4">
      <div className="flex items-center space-x-2 mb-8">
        <Music className="w-8 h-8 text-green-500" />
        <span className="text-xl font-bold">Spotify AI</span>
      </div>
      
      {navItems.map((item) => (
        <Link
          key={item.path}
          to={item.path}
          className={clsx(
            'flex items-center space-x-3 px-4 py-3 rounded-lg transition-all duration-200',
            'hover:bg-gray-800/50 hover:text-green-400 group'
          )}
        >
          <item.icon className="w-5 h-5 group-hover:scale-110 transition-transform" />
          <span className="font-medium">{item.label}</span>
        </Link>
      ))}
    </nav>
  );
}

// Top Navbar Component
function TopNavbar() {
  return (
    <div className="flex items-center justify-between">
      <h1 className="text-2xl font-bold bg-gradient-to-r from-green-400 to-green-600 bg-clip-text text-transparent">
        Music Recommendation System v2
      </h1>
      <div className="flex items-center space-x-4">
        <span className="text-sm text-gray-400">AI-Powered Discovery</span>
      </div>
    </div>
  );
}

// Audio Player Component
function AudioPlayer() {
  const { currentTrack, isPlaying, volume, currentTime, duration, playTrack, pauseTrack, setVolume, seekTo } = useAudio();

  if (!currentTrack) return null;

  const formatTime = (time: number) => {
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  return (
    <motion.div
      initial={{ y: 100 }}
      animate={{ y: 0 }}
      className="fixed bottom-0 left-0 right-0 bg-gray-900/95 backdrop-blur-sm border-t border-gray-800 p-4"
    >
      <div className="flex items-center space-x-4">
        {/* Track Info */}
        <div className="flex items-center space-x-3 min-w-0 flex-1">
          <div className="w-12 h-12 bg-gray-800 rounded-md flex items-center justify-center overflow-hidden">
            <img
              src={generateAlbumCover(currentTrack)}
              alt={`${currentTrack.name} by ${currentTrack.artist}`}
              className="w-full h-full object-cover"
              onError={(e) => {
                e.currentTarget.style.display = 'none';
                e.currentTarget.nextElementSibling?.classList.remove('hidden');
              }}
            />
            <Music className="w-6 h-6 text-gray-400 hidden" />
          </div>
          <div className="min-w-0">
            <h4 className="text-white font-medium truncate">{currentTrack.name}</h4>
            <p className="text-gray-400 text-sm truncate">{currentTrack.artist}</p>
          </div>
        </div>

        {/* Controls */}
        <div className="flex items-center space-x-2">
          <button className="p-2 text-gray-400 hover:text-white transition-colors">
            <SkipBack className="w-5 h-5" />
          </button>
          <button
            onClick={() => isPlaying ? pauseTrack() : playTrack(currentTrack)}
            className="p-3 bg-green-500 hover:bg-green-400 rounded-full text-black transition-colors"
          >
            {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5 ml-0.5" />}
          </button>
          <button className="p-2 text-gray-400 hover:text-white transition-colors">
            <SkipForward className="w-5 h-5" />
          </button>
        </div>

        {/* Progress */}
        <div className="flex items-center space-x-2 flex-1">
          <span className="text-xs text-gray-400">{formatTime(currentTime)}</span>
          <div className="flex-1 bg-gray-700 rounded-full h-1">
            <div
              className="bg-green-500 h-full rounded-full cursor-pointer"
              style={{ width: `${duration ? (currentTime / duration) * 100 : 0}%` }}
              onClick={(e) => {
                const rect = e.currentTarget.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const percentage = x / rect.width;
                seekTo(duration * percentage);
              }}
            />
          </div>
          <span className="text-xs text-gray-400">{formatTime(duration)}</span>
        </div>

        {/* Volume */}
        <div className="flex items-center space-x-2">
          <Volume2 className="w-4 h-4 text-gray-400" />
          <input
            type="range"
            min="0"
            max="1"
            step="0.1"
            value={volume}
            onChange={(e) => setVolume(parseFloat(e.target.value))}
            className="w-20 accent-green-500"
          />
        </div>
      </div>
    </motion.div>
  );
}

// Page Components
function HomePage() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="space-y-8"
    >
      <div className="text-center space-y-4">
        <h2 className="text-4xl font-bold bg-gradient-to-r from-green-400 to-blue-500 bg-clip-text text-transparent">
          Welcome to Your Music Discovery Hub
        </h2>
        <p className="text-xl text-gray-300 max-w-2xl mx-auto">
          Discover new music tailored to your taste using advanced machine learning algorithms
          powered by HDBSCAN clustering and KNN recommendations.
        </p>
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        <FeatureCard
          icon={<TrendingUp className="w-8 h-8" />}
          title="Smart Recommendations"
          description="Get personalized music suggestions based on your listening patterns and preferences."
        />
        <FeatureCard
          icon={<Search className="w-8 h-8" />}
          title="Explore Clusters"
          description="Discover music organized into intelligent clusters using HDBSCAN algorithm."
        />
        <FeatureCard
          icon={<Music className="w-8 h-8" />}
          title="Advanced Analytics"
          description="Dive deep into music features and analytics with our comprehensive dashboard."
        />
      </div>

      <div className="text-center">
        <Link
          to="/explore"
          className="inline-flex items-center px-8 py-4 bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white font-semibold rounded-full transition-all duration-200 transform hover:scale-105 shadow-lg hover:shadow-green-500/25"
        >
          Start Exploring
          <Search className="ml-2 w-5 h-5" />
        </Link>
      </div>
    </motion.div>
  );
}

function RecommendationsPage() {
  const [likedSongIds, setLikedSongIds] = React.useState<string[]>(() => {
    const saved = localStorage.getItem('likedSongs');
    return saved ? JSON.parse(saved) : [];
  });
  const [selectedStrategy, setSelectedStrategy] = React.useState<string>('cluster');
  const [selectedModel, setSelectedModel] = React.useState<string>('svd_knn');
  const [recommendationCount, setRecommendationCount] = React.useState<number>(20);
  
  // Fetch available models
  const { data: availableModels, isLoading: modelsLoading, error: modelsError } = useQuery({
    queryKey: ['available-models'],
    queryFn: () => apiService.recommendations.getAvailableModels(),
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 3
  });

  // Debug log for models
  React.useEffect(() => {
    if (availableModels) {
      console.log('Available models loaded:', availableModels);
    }
    if (modelsError) {
      console.error('Error loading models:', modelsError);
    }
  }, [availableModels, modelsError]);

  // Fetch liked songs details for display
  const { data: likedSongs } = useQuery({
    queryKey: ['liked-songs-details', likedSongIds],
    queryFn: async () => {
      if (likedSongIds.length === 0) return [];
      const promises = likedSongIds.map(id => 
        apiService.songs.getById(id).catch(() => null)
      );
      const results = await Promise.all(promises);
      return results.filter(Boolean) as Song[];
    },
    enabled: likedSongIds.length > 0
  });

  // Switch model when selected model changes
  React.useEffect(() => {
    if (selectedStrategy === 'cluster' || selectedStrategy === 'hdbscan_knn' || selectedStrategy === 'lyrics') {
      apiService.recommendations.switchModel(selectedModel).catch(console.error);
    }
  }, [selectedModel, selectedStrategy]);

  const { data: recommendations, isLoading, error, refetch } = useQuery({
    queryKey: ['recommendations', likedSongIds, selectedStrategy, selectedModel, recommendationCount],
    queryFn: () => apiService.recommendations.get({
      liked_song_ids: likedSongIds,
      n_recommendations: recommendationCount,
      recommendation_type: selectedStrategy
    }),
    enabled: likedSongIds.length > 0
  });

  const { data: popularSongs } = useQuery({
    queryKey: ['popular-songs'],
    queryFn: () => apiService.songs.getPopular({ limit: 20, min_popularity: 70 })
  });

  // Additional recommendation strategies
  const { data: artistBasedRecs, isLoading: artistBasedLoading } = useQuery({
    queryKey: ['artist-based-recs', likedSongIds, recommendationCount],
    queryFn: () => apiService.recommendations.getArtistBased({
      liked_song_ids: likedSongIds,
      n_recommendations: recommendationCount,
      recommendation_type: 'artist_based'
    }),
    enabled: likedSongIds.length > 0 && selectedStrategy === 'similar_artists'
  });

  const { data: genreBasedRecs, isLoading: genreBasedLoading } = useQuery({
    queryKey: ['genre-based-recs', likedSongIds, recommendationCount],
    queryFn: () => apiService.recommendations.getGenreBased({
      liked_song_ids: likedSongIds,
      n_recommendations: recommendationCount,
      recommendation_type: 'genre_based'
    }),
    enabled: likedSongIds.length > 0 && selectedStrategy === 'genre_based'
  });

  const { data: hdbscanRecs, isLoading: hdbscanLoading } = useQuery({
    queryKey: ['hdbscan-recs', likedSongIds, recommendationCount, selectedModel],
    queryFn: () => apiService.recommendations.getHdbscanKnn({
      liked_song_ids: likedSongIds,
      n_recommendations: recommendationCount,
      recommendation_type: 'hdbscan_knn'
    }),
    enabled: likedSongIds.length > 0 && selectedStrategy === 'hdbscan_knn'
  });

  const getCurrentRecommendations = () => {
    switch (selectedStrategy) {
      case 'similar_artists':
        return { 
          recommendations: artistBasedRecs?.recommendations || [], 
          isLoading: artistBasedLoading, 
          error: null,
          processingTime: artistBasedRecs?.processing_time_ms 
        };
      case 'genre_based':
        return { 
          recommendations: genreBasedRecs?.recommendations || [], 
          isLoading: genreBasedLoading, 
          error: null,
          processingTime: genreBasedRecs?.processing_time_ms 
        };
      case 'hdbscan_knn':
        return { 
          recommendations: hdbscanRecs?.recommendations || [], 
          isLoading: hdbscanLoading, 
          error: null,
          processingTime: hdbscanRecs?.processing_time_ms 
        };
      default:
        return { 
          recommendations: recommendations?.recommendations || [], 
          isLoading, 
          error,
          processingTime: recommendations?.processing_time_ms 
        };
    }
  };

  const currentRecs = getCurrentRecommendations();

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="space-y-6"
    >
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold text-green-400">Your Recommendations</h2>
        
        {likedSongIds.length > 0 && (
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-400">Count:</span>
              <select
                value={recommendationCount}
                onChange={(e) => setRecommendationCount(Number(e.target.value))}
                className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1 text-white text-sm focus:outline-none focus:border-green-500"
              >
                <option value={10}>10</option>
                <option value={20}>20</option>
                <option value={30}>30</option>
                <option value={50}>50</option>
              </select>
            </div>
          </div>
        )}
      </div>

      {likedSongIds.length > 0 && (
        <div className="bg-gray-900/50 backdrop-blur-sm rounded-xl p-6 border border-gray-800">
          <h3 className="text-lg font-semibold mb-4 text-green-400">Recommendation Settings</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Strategy Selection */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-300">Recommendation Strategy</label>
              <select
                value={selectedStrategy}
                onChange={(e) => setSelectedStrategy(e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-green-500"
              >
                <option value="cluster">🎯 Cluster-Based (ML)</option>
                <option value="hdbscan_knn">🔬 HDBSCAN + KNN</option>
                <option value="lyrics">📝 Lyrics Similarity</option>
                <option value="similar_artists">🎤 Similar Artists</option>
                <option value="genre_based">🎵 Genre-Based</option>
              </select>
              <p className="text-xs text-gray-400">
                {selectedStrategy === 'cluster' && 'Uses trained ML models to find similar songs based on audio features'}
                {selectedStrategy === 'hdbscan_knn' && 'Uses HDBSCAN clustering + KNN for high-quality audio feature similarity'}
                {selectedStrategy === 'lyrics' && 'Finds songs with similar lyrical content and themes'}
                {selectedStrategy === 'similar_artists' && 'Recommends more songs by artists you already like'}
                {selectedStrategy === 'genre_based' && 'Discovers songs from similar genres and styles'}
              </p>
            </div>

            {/* Model Selection (only for ML strategies) */}
            {(selectedStrategy === 'cluster' || selectedStrategy === 'hdbscan_knn' || selectedStrategy === 'lyrics') && (
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-300">ML Model</label>
                {modelsLoading ? (
                  <div className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-gray-400">
                    Loading models...
                  </div>
                ) : modelsError ? (
                  <div className="w-full bg-red-900/20 border border-red-500/30 rounded-lg px-3 py-2 text-red-400">
                    Error loading models
                  </div>
                ) : (
                  <select
                    value={selectedModel}
                    onChange={(e) => setSelectedModel(e.target.value)}
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-green-500"
                  >
                    {(availableModels?.available_models || ['svd_knn', 'knn_cosine', 'knn_euclidean', 'knn_cosine_k20']).map((model: string) => (
                      <option key={model} value={model}>
                        {model === 'svd_knn' && '🔬 SVD + KNN (Best)'}
                        {model === 'knn_cosine' && '📐 KNN Cosine'}
                        {model === 'knn_euclidean' && '📏 KNN Euclidean'}
                        {model === 'knn_cosine_k20' && '🎯 KNN Cosine (K=20)'}
                        {model === 'hdbscan_knn' && '🔬 HDBSCAN + KNN'}
                        {model === 'cluster' && '🎯 Cluster-Based'}
                        {!['svd_knn', 'knn_cosine', 'knn_euclidean', 'knn_cosine_k20', 'hdbscan_knn', 'cluster'].includes(model) && `🤖 ${model}`}
                      </option>
                    ))}
                  </select>
                )}
                <p className="text-xs text-gray-400">
                  {selectedModel === 'svd_knn' && 'Dimensionality reduction + K-Nearest Neighbors (recommended)'}
                  {selectedModel.includes('knn_cosine') && 'K-Nearest Neighbors with cosine similarity'}
                  {selectedModel === 'knn_euclidean' && 'K-Nearest Neighbors with euclidean distance'}
                  {selectedModel === 'hdbscan_knn' && 'HDBSCAN clustering with K-Nearest Neighbors'}
                  {selectedModel === 'cluster' && 'Traditional cluster-based recommendations'}
                </p>
              </div>
            )}

            {/* Current Model Info */}
            {(selectedStrategy === 'cluster' || selectedStrategy === 'hdbscan_knn' || selectedStrategy === 'lyrics') && availableModels?.current_model && (
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-300">Current Model Status</label>
                <div className="bg-green-900/20 border border-green-500/30 rounded-lg p-3">
                  <div className="text-sm text-green-400 font-medium">
                    ✅ {availableModels.current_model.model_name}
                  </div>
                  <div className="text-xs text-gray-400 mt-1">
                    Type: {availableModels.current_model.model_type}
                    {availableModels.current_model.has_svd && ' • SVD Enhanced'}
                  </div>
                  {availableModels.current_model.vocabulary_size && (
                    <div className="text-xs text-gray-400">
                      Vocab: {availableModels.current_model.vocabulary_size.toLocaleString()} terms
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
      
      <LikedSongsBar
        likedSongs={likedSongs || []}
        onRemoveSong={(songId) => {
          const newLikedSongIds = likedSongIds.filter(id => id !== songId);
          setLikedSongIds(newLikedSongIds);
          localStorage.setItem('likedSongs', JSON.stringify(newLikedSongIds));
        }}
        onClearAll={() => {
          setLikedSongIds([]);
          localStorage.setItem('likedSongs', JSON.stringify([]));
        }}
      />
      
      {likedSongIds.length === 0 ? (
        <div className="space-y-6">
          <div className="bg-gray-900/50 backdrop-blur-sm rounded-xl p-8 border border-gray-800 text-center">
            <h3 className="text-xl font-semibold mb-4">Get Started</h3>
            <p className="text-gray-300 mb-6">
              Like some songs below to get personalized recommendations based on your taste.
        </p>
      </div>
          
          <div>
            <h3 className="text-xl font-semibold mb-4">Popular Songs</h3>
            {popularSongs && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                {popularSongs.map((song) => (
                  <SongCard
                    key={song.id}
                    song={song}
                    onLike={(songId) => {
                      const newLikedSongIds = [...likedSongIds, songId];
                      setLikedSongIds(newLikedSongIds);
                      localStorage.setItem('likedSongs', JSON.stringify(newLikedSongIds));
                    }}
                    isLiked={likedSongIds.includes(song.id)}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          <div className="bg-gray-900/50 backdrop-blur-sm rounded-xl p-6 border border-gray-800">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-lg font-semibold">
                {selectedStrategy === 'cluster' && '🎯 Cluster-Based Recommendations'}
                {selectedStrategy === 'hdbscan_knn' && '🔬 HDBSCAN + KNN Recommendations'}
                {selectedStrategy === 'lyrics' && '📝 Lyrics-Based Recommendations'}
                {selectedStrategy === 'similar_artists' && '🎤 Similar Artists Recommendations'}
                {selectedStrategy === 'genre_based' && '🎵 Genre-Based Recommendations'}
              </h3>
              <span className="text-sm text-gray-400">
                {currentRecs.recommendations.length} songs • Based on {likedSongIds.length} liked songs
              </span>
            </div>
            <p className="text-gray-300">
              {selectedStrategy === 'cluster' && `Using ${selectedModel} model to find songs with similar audio features and patterns.`}
              {selectedStrategy === 'hdbscan_knn' && 'Using trained HDBSCAN clustering and KNN models for precise audio feature similarity.'}
              {selectedStrategy === 'lyrics' && `Using ${selectedModel} model to find songs with similar lyrical themes and content.`}
              {selectedStrategy === 'similar_artists' && 'Discovering more music from artists you already enjoy.'}
              {selectedStrategy === 'genre_based' && 'Exploring songs from similar genres and musical styles.'}
            </p>
            {currentRecs.processingTime && (
              <div className="text-xs text-gray-500 mt-2">
                Generated in {currentRecs.processingTime.toFixed(1)}ms
              </div>
            )}
          </div>
          
          {currentRecs.isLoading && <div className="text-center py-8">Loading recommendations...</div>}
          {currentRecs.error && <div className="text-red-400 text-center py-8">Error loading recommendations</div>}
          
          {currentRecs.recommendations.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {currentRecs.recommendations.map((song) => (
                <SongCard
                  key={song.id}
                  song={song}
                  onLike={(songId) => {
                      const newLikedSongIds = [...likedSongIds, songId];
                      setLikedSongIds(newLikedSongIds);
                      localStorage.setItem('likedSongs', JSON.stringify(newLikedSongIds));
                    }}
                  isLiked={likedSongIds.includes(song.id)}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </motion.div>
  );
}

function ExplorePage() {
  const [selectedCluster, setSelectedCluster] = React.useState<number | null>(null);
  const [viewMode, setViewMode] = React.useState<'clusters' | 'songs'>('clusters');
  const [layoutMode, setLayoutMode] = React.useState<'grid' | 'list'>('grid');
  const [searchQuery, setSearchQuery] = React.useState('');
  const [selectedSong, setSelectedSong] = React.useState<Song | null>(null);
  const [showSongInfo, setShowSongInfo] = React.useState(false);
  const [likedSongs, setLikedSongs] = React.useState<Set<string>>(() => {
    const saved = localStorage.getItem('likedSongs');
    return new Set(saved ? JSON.parse(saved) : []);
  });

  // Fetch clusters
  const { data: clusters, isLoading: clustersLoading } = useQuery({
    queryKey: ['clusters'],
    queryFn: () => apiService.clusters.getAll({ limit: 50 })
  });

  // Search songs
  const { data: searchResults, isLoading: searchLoading } = useQuery({
    queryKey: ['search', searchQuery],
    queryFn: () => apiService.songs.search({ query: searchQuery, limit: 50 }),
    enabled: searchQuery.length >= 2
  });

  // Get cluster songs
  const { data: clusterSongs, isLoading: clusterSongsLoading } = useQuery({
    queryKey: ['cluster-songs', selectedCluster],
    queryFn: () => apiService.songs.getByCluster(selectedCluster!, { limit: 100 }),
    enabled: selectedCluster !== null
  });

  // Get random songs for initial display
  const { data: randomSongs } = useQuery({
    queryKey: ['random-songs'],
    queryFn: () => apiService.songs.getRandom({ limit: 50 })
  });

  // Fetch liked songs details for display
  const { data: likedSongsDetails } = useQuery({
    queryKey: ['liked-songs-details', Array.from(likedSongs)],
    queryFn: async () => {
      if (likedSongs.size === 0) return [];
      const promises = Array.from(likedSongs).map(id => 
        apiService.songs.getById(id).catch(() => null)
      );
      const results = await Promise.all(promises);
      return results.filter(Boolean) as Song[];
    },
    enabled: likedSongs.size > 0
  });

  const handleClusterSelect = (cluster: ClusterInfo) => {
    setSelectedCluster(cluster.id);
    setViewMode('songs');
  };

  const handleSongLike = (songId: string) => {
    const newLikedSongs = new Set(likedSongs);
    if (likedSongs.has(songId)) {
      newLikedSongs.delete(songId);
    } else {
      newLikedSongs.add(songId);
    }
    setLikedSongs(newLikedSongs);
    // Persist to localStorage
    localStorage.setItem('likedSongs', JSON.stringify(Array.from(newLikedSongs)));
  };

  const handleSongSelect = (song: Song) => {
    setSelectedSong(song);
    setShowSongInfo(true);
  };

  const currentSongs = searchQuery.length >= 2 ? searchResults : 
                     selectedCluster ? clusterSongs : 
                     randomSongs;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="flex space-x-6"
    >
      {/* Main Content */}
      <div className={clsx("flex-1 space-y-6", showSongInfo && "mr-80")}>
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
        <h2 className="text-3xl font-bold text-green-400">Explore Music</h2>
            <p className="text-gray-300 mt-2">
              Discover music organized by AI-powered clustering
            </p>
          </div>
          
          {/* Search Bar */}
          <div className="flex items-center space-x-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search songs or artists..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-green-500 w-64"
              />
            </div>
            
            {/* View Controls */}
            <div className="flex bg-gray-800 rounded-lg p-1">
              <button
                onClick={() => setViewMode('clusters')}
                className={clsx(
                  'px-4 py-2 rounded-md text-sm font-medium transition-colors',
                  viewMode === 'clusters'
                    ? 'bg-green-600 text-white'
                    : 'text-gray-400 hover:text-white'
                )}
              >
                Clusters
              </button>
              <button
                onClick={() => setViewMode('songs')}
                className={clsx(
                  'px-4 py-2 rounded-md text-sm font-medium transition-colors',
                  viewMode === 'songs'
                    ? 'bg-green-600 text-white'
                    : 'text-gray-400 hover:text-white'
                )}
              >
                Songs
              </button>
            </div>
            
            {viewMode === 'songs' && (
              <div className="flex bg-gray-800 rounded-lg p-1">
                <button
                  onClick={() => setLayoutMode('grid')}
                  className={clsx(
                    'px-3 py-2 rounded-md text-sm transition-colors',
                    layoutMode === 'grid'
                      ? 'bg-green-600 text-white'
                      : 'text-gray-400 hover:text-white'
                  )}
                >
                  <Grid className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setLayoutMode('list')}
                  className={clsx(
                    'px-3 py-2 rounded-md text-sm transition-colors',
                    layoutMode === 'list'
                      ? 'bg-green-600 text-white'
                      : 'text-gray-400 hover:text-white'
                  )}
                >
                  <List className="w-4 h-4" />
                </button>
              </div>
            )}
          </div>
        </div>

              <LikedSongsBar
        likedSongs={likedSongsDetails || []}
        onRemoveSong={(songId) => {
          const newLikedSongs = new Set(likedSongs);
          newLikedSongs.delete(songId);
          setLikedSongs(newLikedSongs);
          localStorage.setItem('likedSongs', JSON.stringify(Array.from(newLikedSongs)));
        }}
        onClearAll={() => {
          setLikedSongs(new Set());
          localStorage.setItem('likedSongs', JSON.stringify([]));
        }}
      />

        {/* Clusters View */}
        {viewMode === 'clusters' && (
          <div>
            {clustersLoading ? (
              <div className="text-center py-8">Loading clusters...</div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {clusters?.map((cluster) => (
                  <ClusterCard
                    key={cluster.id}
                    cluster={cluster}
                    onClick={() => handleClusterSelect(cluster)}
                  />
                ))}
              </div>
            )}
          </div>
        )}

        {/* Songs View */}
        {viewMode === 'songs' && (
          <div className="space-y-6">
            {selectedCluster && (
              <div className="flex items-center space-x-4">
                <button
                  onClick={() => {
                    setViewMode('clusters');
                    setSelectedCluster(null);
                  }}
                  className="flex items-center space-x-2 text-gray-400 hover:text-white transition-colors"
                >
                  <ArrowLeft className="w-4 h-4" />
                  <span>Back to Clusters</span>
                </button>
                <div className="h-4 w-px bg-gray-600"></div>
                <span className="text-gray-300">
                  Cluster {selectedCluster} Songs
                </span>
              </div>
            )}

            {searchQuery.length >= 2 && (
              <div className="text-gray-300">
                Search results for "{searchQuery}"
              </div>
            )}

            {(searchLoading || clusterSongsLoading) ? (
              <div className="text-center py-8">Loading songs...</div>
            ) : currentSongs && currentSongs.length > 0 ? (
              layoutMode === 'grid' ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                  {currentSongs.map((song) => (
                    <SongCard
                      key={song.id}
                      song={song}
                      onLike={handleSongLike}
                      onSelect={handleSongSelect}
                      isLiked={likedSongs.has(song.id)}
                    />
                  ))}
                </div>
              ) : (
                <div className="space-y-2">
                  {currentSongs.map((song, index) => (
                    <SongListItem
                      key={song.id}
                      song={song}
                      index={index}
                      onLike={handleSongLike}
                      onSelect={handleSongSelect}
                      isLiked={likedSongs.has(song.id)}
                    />
                  ))}
                </div>
              )
            ) : (
              <div className="text-center py-8 text-gray-400">
              {searchQuery.length >= 2 ? 'No songs found' : 'No songs available'}
              </div>
            )}
          </div>
      )}
      </div>

      {/* Right Sidebar - Song Information Panel */}
      {showSongInfo && selectedSong && (
        <SongInfoPanel
          song={selectedSong}
          onClose={() => setShowSongInfo(false)}
        />
      )}
    </motion.div>
  );
}

// Song Card Component
function SongCard({ song, onLike, onSelect, isLiked }: {
  song: Song;
  onLike: (songId: string) => void;
  onSelect?: (song: Song) => void;
  isLiked: boolean;
}) {
  const { playTrack, currentTrack, isPlaying } = useAudio();
  const isCurrentTrack = currentTrack?.id === song.id;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -4 }}
      onClick={() => onSelect?.(song)}
      className="bg-gray-900/50 backdrop-blur-sm rounded-xl p-4 border border-gray-800 hover:border-green-500/50 transition-all duration-200 group cursor-pointer"
    >
      <div className="relative mb-4">
        <div className="aspect-square rounded-lg overflow-hidden bg-gray-800">
          <img
            src={generateAlbumCover(song)}
            alt={`${song.name} by ${song.artist}`}
            className="w-full h-full object-cover"
            onError={(e) => {
              e.currentTarget.style.display = 'none';
              e.currentTarget.nextElementSibling?.classList.remove('hidden');
            }}
          />
          <div className="w-full h-full flex items-center justify-center hidden">
            <Music className="w-16 h-16 text-gray-600" />
          </div>
        </div>
        <motion.button
          whileHover={{ scale: 1.1 }}
          onClick={() => playTrack(song)}
          className="absolute bottom-2 right-2 w-12 h-12 bg-green-500 hover:bg-green-400 rounded-full flex items-center justify-center shadow-lg transition-colors"
        >
          {isCurrentTrack && isPlaying ? (
            <Pause className="w-6 h-6 text-black" />
          ) : (
            <Play className="w-6 h-6 text-black ml-0.5" />
          )}
        </motion.button>
      </div>
      <div className="space-y-2">
        <h3 className="text-white font-semibold text-lg truncate">{song.name}</h3>
        <p className="text-gray-400 text-sm truncate">{song.artist}</p>
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="flex-1 bg-gray-700 rounded-full h-1 w-16">
                <div
                  className="bg-green-500 h-full rounded-full"
                  style={{ width: `${song.popularity}%` }}
                />
              </div>
              <span className="text-xs text-gray-500">{song.popularity}%</span>
            </div>
            <button
              onClick={() => onLike(song.id)}
              className={clsx(
                'p-1 rounded-full transition-colors',
                isLiked ? 'text-green-500' : 'text-gray-400 hover:text-white'
              )}
            >
              <Heart className="w-4 h-4" />
            </button>
          </div>
          {song.similarity_score && (
            <div className="flex items-center justify-center">
              <div className="bg-gradient-to-r from-green-500 to-teal-500 text-white text-xs px-2 py-1 rounded-full font-medium">
                {Math.round(song.similarity_score * 100)}% match
              </div>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}

// Song List Item Component
function SongListItem({ song, index, onLike, onSelect, isLiked }: {
  song: Song;
  index: number;
  onLike: (songId: string) => void;
  onSelect?: (song: Song) => void;
  isLiked: boolean;
}) {
  const { playTrack, currentTrack, isPlaying } = useAudio();
  const isCurrentTrack = currentTrack?.id === song.id;

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.05 }}
      onClick={() => onSelect?.(song)}
      className="flex items-center space-x-4 p-3 rounded-lg hover:bg-white/5 transition-all duration-200 group cursor-pointer"
    >
      <div className="relative flex-shrink-0">
        <div className="w-12 h-12 rounded-md bg-gray-800 flex items-center justify-center overflow-hidden">
          <img
            src={generateAlbumCover(song)}
            alt={`${song.name} by ${song.artist}`}
            className="w-full h-full object-cover"
            onError={(e) => {
              e.currentTarget.style.display = 'none';
              e.currentTarget.nextElementSibling?.classList.remove('hidden');
            }}
          />
          <Music className="w-6 h-6 text-gray-600 hidden" />
        </div>
        <motion.button
          whileHover={{ scale: 1.1 }}
          onClick={() => playTrack(song)}
          className="absolute inset-0 flex items-center justify-center bg-black/60 rounded-md opacity-0 group-hover:opacity-100 transition-opacity"
        >
          {isCurrentTrack && isPlaying ? (
            <Pause className="w-4 h-4 text-white" />
          ) : (
            <Play className="w-4 h-4 text-white ml-0.5" />
          )}
        </motion.button>
      </div>
      <div className="flex-1 min-w-0">
        <h3 className="text-white font-medium truncate">{song.name}</h3>
        <p className="text-gray-400 text-sm truncate">{song.artist}</p>
      </div>
      <div className="flex items-center space-x-2 text-gray-400 text-sm">
        <Clock className="w-4 h-4" />
        <span>{Math.floor(song.duration_ms / 60000)}:{Math.floor((song.duration_ms % 60000) / 1000).toString().padStart(2, '0')}</span>
      </div>
      <button
        onClick={() => onLike(song.id)}
        className={clsx(
          'p-2 rounded-full transition-colors',
          isLiked ? 'text-green-500' : 'text-gray-400 hover:text-white'
        )}
      >
        <Heart className="w-5 h-5" />
      </button>
    </motion.div>
  );
}

// Cluster Card Component
function ClusterCard({ cluster, onClick }: {
  cluster: ClusterInfo;
  onClick: () => void;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -4, scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className="relative overflow-hidden rounded-xl cursor-pointer transition-all duration-300 bg-gray-900/50 backdrop-blur-sm border border-gray-800 hover:border-green-500/50 p-6"
    >
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-teal-500 rounded-xl flex items-center justify-center">
              <Music className="w-6 h-6 text-white" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white">{cluster.name || `Cluster ${cluster.id}`}</h3>
              <p className="text-sm text-gray-400">{cluster.size} tracks</p>
            </div>
          </div>
        </div>

        {cluster.dominant_genres && cluster.dominant_genres.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-gray-300">Genres</h4>
            <div className="flex flex-wrap gap-2">
              {cluster.dominant_genres.slice(0, 3).map((genre, index) => (
                <span
                  key={index}
                  className="px-2 py-1 rounded-full text-xs font-medium bg-gradient-to-r from-green-500 to-teal-500 text-white"
                >
                  {genre}
                </span>
              ))}
            </div>
          </div>
        )}

        <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-700">
          <div>
            <p className="text-xs text-gray-400">Cohesion</p>
            <p className="text-sm font-medium text-white">
              {cluster.cohesion_score ? Math.round(cluster.cohesion_score * 100) : 'N/A'}%
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-400">Size</p>
            <p className="text-sm font-medium text-white">{cluster.size}</p>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

// Liked Songs Bar Component
function LikedSongsBar({ likedSongs, onRemoveSong, onClearAll }: {
  likedSongs: Song[];
  onRemoveSong: (songId: string) => void;
  onClearAll: () => void;
}) {
  if (likedSongs.length === 0) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-green-900/20 backdrop-blur-sm border border-green-500/30 rounded-xl p-4 mb-6"
    >
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-lg font-semibold text-green-400">
          Liked Songs ({likedSongs.length})
        </h3>
        <button
          onClick={onClearAll}
          className="px-3 py-1 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg text-sm transition-colors"
        >
          Clear All
        </button>
      </div>
      <div className="flex flex-wrap gap-2">
        {likedSongs.slice(0, 10).map((song) => (
          <div
            key={song.id}
            className="flex items-center space-x-2 bg-green-500/20 rounded-full px-3 py-1"
          >
            <span className="text-sm text-green-300 truncate max-w-32" title={`${song.name} - ${song.artist}`}>
              {song.name}
            </span>
            <button
              onClick={() => onRemoveSong(song.id)}
              className="text-green-400 hover:text-red-400 transition-colors"
            >
              ×
            </button>
          </div>
        ))}
        {likedSongs.length > 10 && (
          <div className="flex items-center px-3 py-1 text-sm text-gray-400">
            +{likedSongs.length - 10} more
          </div>
        )}
      </div>
    </motion.div>
  );
}

// Feature Card Component
function FeatureCard({ icon, title, description }: {
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <motion.div
      whileHover={{ scale: 1.05 }}
      className="bg-gray-900/50 backdrop-blur-sm rounded-xl p-6 border border-gray-800 hover:border-green-500/50 transition-all duration-200"
    >
      <div className="text-green-400 mb-4">{icon}</div>
      <h3 className="text-xl font-semibold mb-2 text-white">{title}</h3>
      <p className="text-gray-300">{description}</p>
    </motion.div>
  );
}

// Model Comparison Page Component
function ModelComparisonPage() {
  const [likedSongs, setLikedSongs] = React.useState<Song[]>([]);
  const [selectedModels, setSelectedModels] = React.useState<string[]>(['cluster', 'lyrics']);
  const [comparisonResults, setComparisonResults] = React.useState<any>(null);
  const [isLoading, setIsLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [searchQuery, setSearchQuery] = React.useState('');
  const { playTrack } = useAudio();

  // Search songs for adding to liked songs
  const { data: searchResults, isLoading: isSearching } = useQuery({
    queryKey: ['search', searchQuery],
    queryFn: () => searchQuery ? apiService.songs.search({ query: searchQuery, limit: 10 }) : Promise.resolve([]),
    enabled: searchQuery.length > 2
  });

  const handleCompareModels = async () => {
    if (selectedModels.length === 0 || likedSongs.length === 0) {
      setError('Please select at least one model and one song');
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
    const colors = { cluster: '#1DB954', lyrics: '#FF6B6B', global: '#4ECDC4', hybrid: '#45B7D1' };
    return colors[modelType as keyof typeof colors] || '#6B7280';
  };

  const getModelIcon = (modelType: string): string => {
    const icons = { cluster: '🎵', lyrics: '📝', global: '🌍', hybrid: '🔀' };
    return icons[modelType as keyof typeof icons] || '🎯';
  };

  return (
    <div className="space-y-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center"
      >
        <h1 className="text-4xl font-bold mb-4 bg-gradient-to-r from-green-400 to-teal-400 bg-clip-text text-transparent">
          Model Comparison
        </h1>
        <p className="text-xl text-gray-300 max-w-3xl mx-auto">
          Compare different recommendation models to see how they perform with your music taste.
        </p>
      </motion.div>

      {/* Search and Add Songs */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="bg-gray-900/50 backdrop-blur-sm rounded-xl p-6 border border-gray-800"
      >
        <h2 className="text-xl font-semibold mb-4">Add Songs for Comparison</h2>
        <div className="relative mb-4">
          <input
            type="text"
            placeholder="Search for songs to add..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-green-500"
          />
          {isSearching && (
            <div className="absolute right-3 top-3">
              <div className="w-4 h-4 border-2 border-green-500 border-t-transparent rounded-full animate-spin" />
            </div>
          )}
        </div>

        {searchResults && searchResults.length > 0 && (
          <div className="space-y-2 mb-4">
            {searchResults.map((song) => (
              <div key={song.id} className="flex items-center justify-between p-3 bg-gray-800 rounded-lg">
                <div>
                  <h4 className="font-medium">{song.name}</h4>
                  <p className="text-sm text-gray-400">{song.artist}</p>
                </div>
                <button
                  onClick={() => addLikedSong(song)}
                  disabled={likedSongs.find(s => s.id === song.id) !== undefined}
                  className="px-3 py-1 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg text-sm"
                >
                  {likedSongs.find(s => s.id === song.id) ? 'Added' : 'Add'}
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Liked Songs Display */}
        {likedSongs.length > 0 && (
          <div>
            <h3 className="font-semibold mb-3">Selected Songs ({likedSongs.length})</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {likedSongs.map((song) => (
                <div key={song.id} className="flex items-center justify-between p-3 bg-gray-800 rounded-lg">
                  <div className="flex-1">
                    <h4 className="font-medium truncate">{song.name}</h4>
                    <p className="text-sm text-gray-400 truncate">{song.artist}</p>
                  </div>
                  <button
                    onClick={() => removeLikedSong(song.id)}
                    className="ml-2 text-red-400 hover:text-red-300"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </motion.div>

      {/* Model Selection */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="bg-gray-900/50 backdrop-blur-sm rounded-xl p-6 border border-gray-800"
      >
        <h2 className="text-xl font-semibold mb-4">Select Models to Compare</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {['cluster', 'lyrics', 'global', 'hybrid'].map((model) => (
            <div
              key={model}
              onClick={() => {
                if (selectedModels.includes(model)) {
                  setSelectedModels(selectedModels.filter(m => m !== model));
                } else {
                  setSelectedModels([...selectedModels, model]);
                }
              }}
              className={clsx(
                'p-4 border-2 rounded-lg cursor-pointer transition-all',
                selectedModels.includes(model)
                  ? 'border-green-500 bg-green-500/10'
                  : 'border-gray-700 hover:border-gray-600'
              )}
            >
              <div className="flex items-center space-x-3">
                <div className="text-2xl">{getModelIcon(model)}</div>
                <div>
                  <h3 className="font-semibold capitalize">{model}</h3>
                  <p className="text-sm text-gray-400">
                    {model === 'cluster' && 'Audio feature clustering'}
                    {model === 'lyrics' && 'Lyrical content similarity'}
                    {model === 'global' && 'Global recommendations'}
                    {model === 'hybrid' && 'Combined approach'}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </motion.div>

      {/* Compare Button */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="text-center"
      >
        <button
          onClick={handleCompareModels}
          disabled={isLoading || selectedModels.length === 0 || likedSongs.length === 0}
          className="px-8 py-3 bg-gradient-to-r from-green-600 to-teal-600 hover:from-green-700 hover:to-teal-700 disabled:from-gray-600 disabled:to-gray-600 disabled:cursor-not-allowed text-white rounded-lg font-semibold text-lg transition-all"
        >
          {isLoading ? 'Comparing Models...' : 'Compare Models'}
        </button>
        {error && (
          <p className="mt-2 text-red-400">{error}</p>
        )}
      </motion.div>

      {/* Comparison Results */}
      {comparisonResults && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-8"
        >
          <h2 className="text-2xl font-bold text-center">Comparison Results</h2>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {comparisonResults.results.map((result: any) => (
              <div key={result.model_type} className="bg-gray-900/50 backdrop-blur-sm rounded-xl border border-gray-800 overflow-hidden">
                <div 
                  className="p-4 text-white"
                  style={{ backgroundColor: `${getModelColor(result.model_type)}20` }}
                >
                  <div className="flex items-center space-x-3">
                    <div className="text-2xl">{getModelIcon(result.model_type)}</div>
                    <div>
                      <h3 className="font-semibold text-lg capitalize">{result.model_type} Model</h3>
                      <p className="text-sm opacity-80">
                        {result.total_found} recommendations in {result.processing_time_ms.toFixed(1)}ms
                      </p>
                    </div>
                  </div>
                </div>
                <div className="p-4">
                  {result.error ? (
                    <div className="text-red-400 text-center py-8">
                      Error: {result.error}
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {result.recommendations.slice(0, 5).map((song: Song, index: number) => (
                        <div key={song.id} className="flex items-center space-x-3 p-2 hover:bg-gray-800 rounded">
                          <span className="text-gray-400 text-sm w-6">{index + 1}</span>
                          <div className="flex-1">
                            <h4 className="font-medium truncate">{song.name}</h4>
                            <p className="text-sm text-gray-400 truncate">{song.artist}</p>
                          </div>
                          {song.similarity_score && (
                            <span className="text-xs bg-gray-700 px-2 py-1 rounded">
                              {(song.similarity_score * 100).toFixed(0)}%
                            </span>
                          )}
                          <button
                            onClick={() => playTrack(song)}
                            className="p-1 text-gray-400 hover:text-white"
                          >
                            <Play className="w-4 h-4" />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  );
}

// Song Information Panel Component
function SongInfoPanel({ song, onClose }: {
  song: Song;
  onClose: () => void;
}) {
  const { playTrack, currentTrack, isPlaying } = useAudio();
  const isCurrentTrack = currentTrack?.id === song.id;

  return (
    <motion.div
      initial={{ x: 320, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      exit={{ x: 320, opacity: 0 }}
      className="fixed right-0 top-0 h-full w-80 bg-gray-900/95 backdrop-blur-sm border-l border-gray-800 p-6 overflow-y-auto z-50"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-green-400">Song Details</h2>
        <button
          onClick={onClose}
          className="p-2 rounded-full hover:bg-gray-800 transition-colors"
        >
          ×
        </button>
      </div>

      {/* Album Cover */}
      <div className="relative mb-6">
        <div className="aspect-square rounded-xl overflow-hidden bg-gray-800">
          <img
            src={generateAlbumCover(song)}
            alt={`${song.name} by ${song.artist}`}
            className="w-full h-full object-cover"
            onError={(e) => {
              e.currentTarget.style.display = 'none';
              e.currentTarget.nextElementSibling?.classList.remove('hidden');
            }}
          />
          <div className="w-full h-full flex items-center justify-center hidden">
            <Music className="w-16 h-16 text-gray-600" />
          </div>
        </div>
        <motion.button
          whileHover={{ scale: 1.1 }}
          onClick={() => playTrack(song)}
          className="absolute bottom-4 right-4 w-14 h-14 bg-green-500 hover:bg-green-400 rounded-full flex items-center justify-center shadow-lg transition-colors"
        >
          {isCurrentTrack && isPlaying ? (
            <Pause className="w-7 h-7 text-black" />
          ) : (
            <Play className="w-7 h-7 text-black ml-0.5" />
          )}
        </motion.button>
      </div>

      {/* Song Information */}
      <div className="space-y-6">
        <div>
          <h3 className="text-2xl font-bold text-white mb-2">{song.name}</h3>
          <p className="text-lg text-gray-300">{song.artist}</p>
          {song.album && (
            <p className="text-sm text-gray-400 mt-1">Album: {song.album}</p>
          )}
        </div>

        {/* Audio Features */}
        <div className="space-y-4">
          <h4 className="text-lg font-semibold text-green-400">Audio Features</h4>
          <div className="grid grid-cols-2 gap-3">
            {Object.entries(formatAudioFeatures(song)).map(([key, feature]) => (
              <div key={key} className="bg-gray-800/50 rounded-lg p-3">
                <div className="flex items-center space-x-2 mb-2">
                  <span className="text-lg">{feature.icon}</span>
                  <div className="text-xs text-gray-400 uppercase tracking-wide">
                    {key}
                  </div>
                </div>
                <div className="text-sm font-medium text-white mb-2">
                  {feature.label}
                </div>
                <div className="bg-gray-700 rounded-full h-2">
                  <div
                    className="h-full rounded-full transition-all duration-300"
                    style={{ 
                      width: `${feature.value * 100}%`,
                      backgroundColor: feature.color
                    }}
                  />
                </div>
                <div className="text-xs text-gray-400 mt-1">
                  {Math.round(feature.value * 100)}%
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Track Stats */}
        <div className="space-y-4">
          <h4 className="text-lg font-semibold text-green-400">Track Stats</h4>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-gray-300">Popularity</span>
              <div className="flex items-center space-x-2">
                <div className="w-20 bg-gray-700 rounded-full h-2">
                  <div
                    className="bg-green-500 h-full rounded-full"
                    style={{ width: `${song.popularity}%` }}
                  />
                </div>
                <span className="text-sm text-gray-400">{song.popularity}%</span>
              </div>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-gray-300">Duration</span>
              <span className="text-gray-400">
                {Math.floor(song.duration_ms / 60000)}:
                {Math.floor((song.duration_ms % 60000) / 1000).toString().padStart(2, '0')}
              </span>
            </div>

            {song.similarity_score && (
              <div className="flex items-center justify-between">
                <span className="text-gray-300">Match Score</span>
                <div className="bg-gradient-to-r from-green-500 to-teal-500 text-white text-sm px-3 py-1 rounded-full font-medium">
                  {Math.round(song.similarity_score * 100)}%
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Musical Details */}
        <div className="space-y-4">
          <h4 className="text-lg font-semibold text-green-400">Musical Details</h4>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-gray-300 flex items-center space-x-2">
                <span>🎵</span>
                <span>Key</span>
              </span>
              <span className="text-gray-400 font-mono">{getMusicalKey(song)}</span>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-gray-300 flex items-center space-x-2">
                <span>🥁</span>
                <span>Tempo</span>
              </span>
              <span className="text-gray-400">{formatTempo(song.tempo)}</span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-gray-300 flex items-center space-x-2">
                <span>⏱️</span>
                <span>Time Signature</span>
              </span>
              <span className="text-gray-400 font-mono">{song.time_signature}/4</span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-gray-300 flex items-center space-x-2">
                <span>🎯</span>
                <span>Cluster</span>
              </span>
              <span className="text-gray-400">#{song.cluster_id}</span>
            </div>
          </div>
        </div>

        {/* Additional Info */}
        <div className="space-y-4">
          <h4 className="text-lg font-semibold text-green-400">Additional Info</h4>
          <div className="space-y-3">
            {song.release_date && (
              <div className="flex items-center justify-between">
                <span className="text-gray-300 flex items-center space-x-2">
                  <span>📅</span>
                  <span>Release Date</span>
                </span>
                <span className="text-gray-400">{song.release_date}</span>
              </div>
            )}
            {song.explicit !== undefined && (
              <div className="flex items-center justify-between">
                <span className="text-gray-300 flex items-center space-x-2">
                  <span>🚫</span>
                  <span>Explicit</span>
                </span>
                <span className="text-gray-400">{song.explicit ? 'Yes' : 'No'}</span>
              </div>
            )}
            <div className="flex items-center justify-between">
              <span className="text-gray-300 flex items-center space-x-2">
                <span>🔗</span>
                <span>Spotify</span>
              </span>
              <button
                onClick={() => window.open(song.spotify_url, '_blank')}
                className="text-green-400 hover:text-green-300 text-sm underline"
              >
                Open in Spotify
              </button>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

export default App; 