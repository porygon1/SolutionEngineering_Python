import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { QueryClient, QueryClientProvider, useQuery, useInfiniteQuery, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { Music, Home, Search, TrendingUp, Play, Pause, Clock, Heart, Grid, List, ArrowLeft, Volume2, SkipBack, SkipForward } from 'lucide-react';
import { clsx } from 'clsx';
import { apiService, Song, ClusterInfo } from './services/api';
import { generateAlbumCover, getPreviewUrl, formatAudioFeatures, getMusicalKey, formatTempo, formatDuration } from './services/spotify';
import ImportedSongCard from './components/SongCard';

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

// Liked Songs context
interface LikedSongsContextType {
  likedSongIds: string[];
  likedSongs: Song[];
  addLikedSong: (songId: string) => void;
  removeLikedSong: (songId: string) => void;
  clearLikedSongs: () => void;
  isLikedSongsLoading: boolean;
}

const LikedSongsContext = React.createContext<LikedSongsContextType | null>(null);

function LikedSongsProvider({ children }: { children: React.ReactNode }) {
  const queryClient = useQueryClient();
  const [likedSongIds, setLikedSongIds] = React.useState<string[]>(() => {
    const saved = localStorage.getItem('likedSongs');
    const ids = saved ? JSON.parse(saved) : [];
    console.log('LikedSongsProvider: Initial liked song IDs:', ids);
    return ids;
  });

  // Fetch liked songs details for display
  const { data: likedSongs = [], isLoading: isLikedSongsLoading, refetch: refetchLikedSongs } = useQuery({
    queryKey: ['liked-songs-details', likedSongIds],
    queryFn: async () => {
      console.log('LikedSongsProvider: Fetching songs for IDs:', likedSongIds);
      if (likedSongIds.length === 0) return [];
      const promises = likedSongIds.map((id: string) => 
        apiService.songs.getById(id).catch(() => null)
      );
      const results = await Promise.all(promises);
      const filteredResults = results.filter(Boolean) as Song[];
      console.log('LikedSongsProvider: Fetched songs:', filteredResults);
      return filteredResults;
    },
    enabled: true, // Always enable the query, let the function handle empty arrays
    staleTime: 0, // Always refetch when the query key changes
    refetchOnMount: true
  });

  // Force refetch when liked song IDs change
  React.useEffect(() => {
    refetchLikedSongs();
  }, [likedSongIds, refetchLikedSongs]);

  const addLikedSong = (songId: string) => {
    console.log('LikedSongsProvider: Adding song ID:', songId);
    console.log('LikedSongsProvider: Current liked song IDs:', likedSongIds);
    if (!likedSongIds.includes(songId)) {
      const newLikedSongIds = [...likedSongIds, songId];
      console.log('LikedSongsProvider: New liked song IDs:', newLikedSongIds);
      setLikedSongIds(newLikedSongIds);
      localStorage.setItem('likedSongs', JSON.stringify(newLikedSongIds));
      // Invalidate the query to force a refetch
      queryClient.invalidateQueries({ queryKey: ['liked-songs-details'] });
    } else {
      console.log('LikedSongsProvider: Song already liked');
    }
  };

  const removeLikedSong = (songId: string) => {
    const newLikedSongIds = likedSongIds.filter((id: string) => id !== songId);
    setLikedSongIds(newLikedSongIds);
    localStorage.setItem('likedSongs', JSON.stringify(newLikedSongIds));
    // Invalidate the query to force a refetch
    queryClient.invalidateQueries({ queryKey: ['liked-songs-details'] });
  };

  const clearLikedSongs = () => {
    setLikedSongIds([]);
    localStorage.setItem('likedSongs', JSON.stringify([]));
    // Invalidate the query to force a refetch
    queryClient.invalidateQueries({ queryKey: ['liked-songs-details'] });
  };

  return (
    <LikedSongsContext.Provider value={{
      likedSongIds,
      likedSongs,
      addLikedSong,
      removeLikedSong,
      clearLikedSongs,
      isLikedSongsLoading
    }}>
      {children}
    </LikedSongsContext.Provider>
  );
}

function useLikedSongs() {
  const context = React.useContext(LikedSongsContext);
  if (!context) {
    throw new Error('useLikedSongs must be used within LikedSongsProvider');
  }
  return context;
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AudioProvider>
        <LikedSongsProvider>
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
        </LikedSongsProvider>
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

// Add a new component for the Base Songs Sidebar
function BaseSongsSidebar({ 
  baseSongs, 
  isOpen, 
  onToggle, 
  onRemoveSong, 
  onClearAll 
}: {
  baseSongs: Song[];
  isOpen: boolean;
  onToggle: () => void;
  onRemoveSong: (songId: string) => void;
  onClearAll: () => void;
}) {
  const { playTrack, currentTrack, isPlaying } = useAudio();

  return (
    <>
      {/* Toggle Button */}
      <motion.button
        onClick={onToggle}
        className={`fixed top-1/2 transform -translate-y-1/2 z-50 transition-all duration-300 ${
          isOpen ? 'right-80' : 'right-4'
        } bg-green-600 hover:bg-green-700 text-white p-3 rounded-full shadow-lg`}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
      >
        <Music className="w-5 h-5" />
        {baseSongs.length > 0 && (
          <span className="absolute -top-2 -left-2 bg-red-500 text-white text-xs rounded-full w-6 h-6 flex items-center justify-center">
            {baseSongs.length}
          </span>
        )}
      </motion.button>

      {/* Sidebar */}
      <motion.div
        initial={{ x: 320 }}
        animate={{ x: isOpen ? 0 : 320 }}
        transition={{ duration: 0.3, ease: "easeInOut" }}
        className="fixed right-0 top-0 h-full w-80 bg-gray-900/95 backdrop-blur-sm border-l border-gray-800 z-40 overflow-y-auto"
      >
        <div className="p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-lg font-semibold text-green-400">Base Songs</h3>
              <p className="text-sm text-gray-400">Songs used for recommendations</p>
            </div>
            <button
              onClick={onToggle}
              className="p-2 rounded-full hover:bg-gray-800 transition-colors text-gray-400 hover:text-white"
            >
              ×
            </button>
          </div>

          {baseSongs.length === 0 ? (
            <div className="text-center py-8">
              <Music className="w-12 h-12 text-gray-600 mx-auto mb-4" />
              <p className="text-gray-400 text-sm">
                No base songs selected yet. Like some songs to see them here!
              </p>
            </div>
          ) : (
            <>
              {/* Clear All Button */}
              <div className="mb-4">
                <button
                  onClick={onClearAll}
                  className="w-full px-3 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg text-sm transition-colors"
                >
                  Clear All ({baseSongs.length})
                </button>
              </div>

              {/* Songs List */}
              <div className="space-y-3">
                {baseSongs.map((song, index) => {
                  const isCurrentTrack = currentTrack?.id === song.id;
                  return (
                    <div
                      key={song.id}
                      className="bg-gray-800/50 rounded-lg p-3 border border-gray-700 hover:border-green-500/50 transition-all"
                    >
                      <div className="flex items-center space-x-3">
                        {/* Album Cover */}
                        <div className="relative flex-shrink-0">
                          <div className="w-12 h-12 rounded-md bg-gray-700 flex items-center justify-center overflow-hidden">
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
                          
                          {/* Play Button Overlay */}
                          <motion.button
                            whileHover={{ scale: 1.1 }}
                            onClick={() => playTrack(song)}
                            className="absolute inset-0 flex items-center justify-center bg-black/60 rounded-md opacity-0 hover:opacity-100 transition-opacity"
                          >
                            {isCurrentTrack && isPlaying ? (
                              <Pause className="w-4 h-4 text-white" />
                            ) : (
                              <Play className="w-4 h-4 text-white ml-0.5" />
                            )}
                          </motion.button>
                        </div>

                        {/* Song Info */}
                        <div className="flex-1 min-w-0">
                          <h4 className="text-white font-medium truncate text-sm">{song.name}</h4>
                          <p className="text-gray-400 text-xs truncate">{song.artist}</p>
                          <div className="flex items-center space-x-2 mt-1">
                            <div className="flex-1 bg-gray-700 rounded-full h-1">
                              <div
                                className="bg-green-500 h-full rounded-full"
                                style={{ width: `${song.popularity}%` }}
                              />
                            </div>
                            <span className="text-xs text-gray-500">{song.popularity}%</span>
                          </div>
                        </div>

                        {/* Remove Button */}
                        <button
                          onClick={() => onRemoveSong(song.id)}
                          className="p-1 text-gray-400 hover:text-red-400 transition-colors"
                        >
                          <span className="sr-only">Remove song</span>
                          ×
                        </button>
                      </div>

                      {/* Currently Playing Indicator */}
                      {isCurrentTrack && (
                        <div className="mt-2 flex items-center space-x-2">
                          <div className="flex space-x-1">
                            <div className="w-1 h-3 bg-green-500 rounded-full animate-pulse"></div>
                            <div className="w-1 h-2 bg-green-500 rounded-full animate-pulse" style={{ animationDelay: '0.1s' }}></div>
                            <div className="w-1 h-4 bg-green-500 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
                          </div>
                          <span className="text-xs text-green-400">
                            {isPlaying ? 'Now Playing' : 'Paused'}
                          </span>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </>
          )}
        </div>
      </motion.div>

      {/* Backdrop */}
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onToggle}
          className="fixed inset-0 bg-black/20 backdrop-blur-sm z-30"
        />
      )}
    </>
  );
}

function RecommendationsPage() {
  const { likedSongIds, likedSongs, addLikedSong, removeLikedSong, clearLikedSongs } = useLikedSongs();
  const { playTrack, pauseTrack, currentTrack, isPlaying } = useAudio();
  const [selectedApproach, setSelectedApproach] = React.useState<string>('audio_similarity');
  const [selectedLyricsModel, setSelectedLyricsModel] = React.useState<string>('svd_knn');
  const [selectedHdbscanModel, setSelectedHdbscanModel] = React.useState<string>('hdbscan_llav_pca');
  const [recommendationCount, setRecommendationCount] = React.useState<number>(20);
  const [isModelSwitching, setIsModelSwitching] = React.useState<boolean>(false);
  const [isSidebarOpen, setIsSidebarOpen] = React.useState<boolean>(false);
  const [selectedSong, setSelectedSong] = React.useState<Song | null>(null);
  const [showSongInfo, setShowSongInfo] = React.useState(false);

  const handleSongSelect = (song: Song) => {
    setSelectedSong(song);
    setShowSongInfo(true);
  };
  
  // Fetch available models (only needed for lyrics approach)
  const { data: availableModels, isLoading: modelsLoading, error: modelsError } = useQuery({
    queryKey: ['available-models'],
    queryFn: () => apiService.recommendations.getAvailableModels(),
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 3,
    enabled: selectedApproach === 'lyrics_similarity'
  });

  // Fetch available HDBSCAN models (only needed for audio similarity approach)
  const { data: availableHdbscanModels, isLoading: hdbscanModelsLoading, error: hdbscanModelsError } = useQuery({
    queryKey: ['available-hdbscan-models'],
    queryFn: async () => {
      try {
        const response = await apiService.recommendations.getAvailableModels();
        // Filter for HDBSCAN models
        return response.available_models?.filter((model: string) => model.startsWith('hdbscan_')) || [];
      } catch (error) {
        console.error('Failed to fetch HDBSCAN models:', error);
        return ['hdbscan_llav_pca', 'hdbscan_pca_features', 'hdbscan_combined_features', 'hdbscan_naive_features', 'hdbscan_llav_features'];
      }
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 3,
    enabled: selectedApproach === 'audio_similarity'
  });



  // Switch to selected lyrics model when needed
  React.useEffect(() => {
    if (selectedApproach === 'lyrics_similarity') {
      setIsModelSwitching(true);
      apiService.recommendations.switchModel(selectedLyricsModel)
        .then(() => {
          // Small delay to ensure model is fully loaded
          setTimeout(() => setIsModelSwitching(false), 500);
        })
        .catch((error) => {
          console.error('Failed to switch model:', error);
          setIsModelSwitching(false);
        });
    } else {
      setIsModelSwitching(false);
    }
  }, [selectedApproach, selectedLyricsModel]);

  // Switch to selected HDBSCAN model when needed
  React.useEffect(() => {
    if (selectedApproach === 'audio_similarity') {
      setIsModelSwitching(true);
      apiService.recommendations.switchModel(selectedHdbscanModel)
        .then(() => {
          // Small delay to ensure model is fully loaded
          setTimeout(() => setIsModelSwitching(false), 500);
        })
        .catch((error) => {
          console.error('Failed to switch HDBSCAN model:', error);
          setIsModelSwitching(false);
        });
    }
  }, [selectedApproach, selectedHdbscanModel]);

  // Map approaches to actual recommendation types and API calls
  const getRecommendationConfig = () => {
    switch (selectedApproach) {
      case 'audio_similarity':
        return { 
          type: 'hdbscan_knn', 
          queryFn: () => apiService.recommendations.getHdbscanKnn({
            liked_song_ids: likedSongIds,
            n_recommendations: recommendationCount,
            recommendation_type: 'hdbscan_knn'
          })
        };
      case 'lyrics_similarity':
        return { 
          type: 'lyrics', 
          queryFn: () => apiService.recommendations.get({
            liked_song_ids: likedSongIds,
            n_recommendations: recommendationCount,
            recommendation_type: 'lyrics'
          })
        };
      case 'similar_artists':
        return { 
          type: 'artist_based', 
          queryFn: () => apiService.recommendations.getArtistBased({
            liked_song_ids: likedSongIds,
            n_recommendations: recommendationCount,
            recommendation_type: 'artist_based'
          })
        };
      case 'similar_genres':
        return { 
          type: 'genre_based', 
          queryFn: () => apiService.recommendations.getGenreBased({
            liked_song_ids: likedSongIds,
            n_recommendations: recommendationCount,
            recommendation_type: 'genre_based'
          })
        };
      case 'cluster_based':
        return { 
          type: 'cluster', 
          queryFn: () => apiService.recommendations.get({
            liked_song_ids: likedSongIds,
            n_recommendations: recommendationCount,
            recommendation_type: 'cluster'
          })
        };
      default:
        return { 
          type: 'hdbscan_knn', 
          queryFn: () => apiService.recommendations.getHdbscanKnn({
            liked_song_ids: likedSongIds,
            n_recommendations: recommendationCount,
            recommendation_type: 'hdbscan_knn'
          })
        };
    }
  };

  const config = getRecommendationConfig();
  
  const { data: recommendations, isLoading, error, refetch } = useQuery({
    queryKey: ['recommendations', likedSongIds, selectedApproach, selectedLyricsModel, selectedHdbscanModel],
    queryFn: config.queryFn,
    enabled: likedSongIds.length > 0 && !isModelSwitching,
    staleTime: 0, // Always refetch when enabled
    refetchOnMount: true
  });

  const { data: popularSongs } = useQuery({
    queryKey: ['popular-songs'],
    queryFn: () => apiService.songs.getPopular({ limit: 20, min_popularity: 70 })
  });

  // Define recommendation approaches with clear descriptions
  const approaches = {
    audio_similarity: {
      name: '🎵 Audio Features',
      description: 'Find songs with similar musical characteristics (tempo, energy, mood)',
      details: 'Uses advanced machine learning to analyze audio features like danceability, energy, and acousticness. Best for discovering new songs that "feel" similar to your favorites.',
      badge: 'ML-Powered',
      badgeColor: 'bg-purple-500'
    },
    lyrics_similarity: {
      name: '📝 Lyrics & Themes', 
      description: 'Find songs with similar lyrical content and themes',
      details: 'Analyzes lyrics using natural language processing to find songs with similar themes, emotions, and storytelling styles.',
      badge: 'NLP-Powered',
      badgeColor: 'bg-blue-500'
    },
    similar_artists: {
      name: '🎤 Similar Artists',
      description: 'More songs by artists you already like',
      details: 'Simple but effective - finds more music from the same artists in your liked songs. Great for exploring an artist\'s catalog.',
      badge: 'Simple',
      badgeColor: 'bg-green-500'
    },
    similar_genres: {
      name: '🎶 Musical Styles',
      description: 'Songs from similar genres and musical styles',
      details: 'Groups songs by audio characteristics to find music from similar genres and subgenres. Good for staying within familiar styles.',
      badge: 'Genre-Based',
      badgeColor: 'bg-orange-500'
    },
    cluster_based: {
      name: '🎯 Music Clusters',
      description: 'Database-based clustering recommendations',
      details: 'Uses pre-computed music clusters from the database. Fast but less personalized than ML approaches.',
      badge: 'Fast',
      badgeColor: 'bg-gray-500'
    }
  };

  const currentApproach = approaches[selectedApproach as keyof typeof approaches];

  return (
    <>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className={`space-y-6 transition-all duration-300 ${isSidebarOpen ? 'mr-80' : ''}`}
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
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold mb-4 text-green-400">Choose Your Recommendation Approach</h3>
                <p className="text-gray-300 text-sm mb-4">
                  Each approach finds similar music in a different way. Pick the one that matches how you want to discover new songs.
                </p>
              </div>
              
              {/* Approach Selection */}
              <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
                {Object.entries(approaches).map(([key, approach]) => (
                  <div
                    key={key}
                    onClick={() => setSelectedApproach(key)}
                    className={`p-4 rounded-lg border-2 cursor-pointer transition-all duration-200 ${
                      selectedApproach === key
                        ? 'border-green-500 bg-green-500/10 shadow-lg'
                        : 'border-gray-700 hover:border-gray-600 bg-gray-800/30'
                    }`}
                  >
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <h4 className="font-semibold text-white">{approach.name}</h4>
                        <span className={`text-xs px-2 py-1 rounded-full text-white ${approach.badgeColor}`}>
                          {approach.badge}
                        </span>
                      </div>
                      <p className="text-sm text-gray-300">{approach.description}</p>
                      <p className="text-xs text-gray-400">{approach.details}</p>
                    </div>
                  </div>
                ))}
              </div>

              {/* Lyrics Model Selection (only shown for lyrics approach) */}
              {selectedApproach === 'lyrics_similarity' && (
                <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-4">
                  <h4 className="text-sm font-medium text-blue-300 mb-3">Choose Lyrics Analysis Method</h4>
                  <p className="text-xs text-gray-400 mb-4">
                    Each method analyzes lyrics differently. Compare them to see which works best for your music taste.
                  </p>
                  <div className="space-y-3">
                    {modelsLoading ? (
                      <div className="text-gray-400 text-sm">Loading lyrics analysis models...</div>
                    ) : modelsError ? (
                      <div className="text-red-400 text-sm">Error loading lyrics models</div>
                    ) : (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        <div
                          onClick={() => setSelectedLyricsModel('svd_knn')}
                          className={`p-3 rounded-lg border cursor-pointer transition-all ${
                            selectedLyricsModel === 'svd_knn'
                              ? 'border-blue-500 bg-blue-500/10'
                              : 'border-gray-600 hover:border-gray-500'
                          }`}
                        >
                          <div className="flex items-center space-x-2 mb-2">
                            <span className="text-lg">🔬</span>
                            <div>
                              <h5 className="font-medium text-blue-300">SVD + KNN</h5>
                              <span className="text-xs text-green-400 bg-green-400/20 px-2 py-0.5 rounded-full">Recommended</span>
                            </div>
                          </div>
                          <p className="text-xs text-gray-400">
                            Advanced dimensionality reduction + similarity matching. Best overall performance for finding lyrically similar songs.
                          </p>
                        </div>

                        <div
                          onClick={() => setSelectedLyricsModel('knn_cosine')}
                          className={`p-3 rounded-lg border cursor-pointer transition-all ${
                            selectedLyricsModel === 'knn_cosine'
                              ? 'border-blue-500 bg-blue-500/10'
                              : 'border-gray-600 hover:border-gray-500'
                          }`}
                        >
                          <div className="flex items-center space-x-2 mb-2">
                            <span className="text-lg">📐</span>
                            <div>
                              <h5 className="font-medium text-blue-300">KNN Cosine</h5>
                              <span className="text-xs text-blue-400 bg-blue-400/20 px-2 py-0.5 rounded-full">Semantic</span>
                            </div>
                          </div>
                          <p className="text-xs text-gray-400">
                            Cosine similarity for thematic matching. Good at finding songs with similar meaning and topics.
                          </p>
                        </div>

                        <div
                          onClick={() => setSelectedLyricsModel('knn_euclidean')}
                          className={`p-3 rounded-lg border cursor-pointer transition-all ${
                            selectedLyricsModel === 'knn_euclidean'
                              ? 'border-blue-500 bg-blue-500/10'
                              : 'border-gray-600 hover:border-gray-500'
                          }`}
                        >
                          <div className="flex items-center space-x-2 mb-2">
                            <span className="text-lg">📏</span>
                            <div>
                              <h5 className="font-medium text-blue-300">KNN Euclidean</h5>
                              <span className="text-xs text-orange-400 bg-orange-400/20 px-2 py-0.5 rounded-full">Precise</span>
                            </div>
                          </div>
                          <p className="text-xs text-gray-400">
                            Euclidean distance for exact word matching. More literal similarity, good for specific word patterns.
                          </p>
                        </div>

                        <div
                          onClick={() => setSelectedLyricsModel('knn_cosine_k20')}
                          className={`p-3 rounded-lg border cursor-pointer transition-all ${
                            selectedLyricsModel === 'knn_cosine_k20'
                              ? 'border-blue-500 bg-blue-500/10'
                              : 'border-gray-600 hover:border-gray-500'
                          }`}
                        >
                          <div className="flex items-center space-x-2 mb-2">
                            <span className="text-lg">🎯</span>
                            <div>
                              <h5 className="font-medium text-blue-300">KNN Cosine (K=20)</h5>
                              <span className="text-xs text-purple-400 bg-purple-400/20 px-2 py-0.5 rounded-full">Diverse</span>
                            </div>
                          </div>
                          <p className="text-xs text-gray-400">
                            Cosine similarity with more neighbors. Provides more diverse results, good for exploration.
                          </p>
                        </div>
                      </div>
                    )}
                    
                    {/* Current Model Status */}
                    <div className="bg-gray-800/50 rounded-lg p-3 mt-4">
                      <div className="flex items-center space-x-2">
                        <div className={`w-2 h-2 rounded-full ${isModelSwitching ? 'bg-yellow-500 animate-pulse' : 'bg-green-500'}`}></div>
                        <span className="text-sm text-gray-300">
                          {isModelSwitching ? (
                            <span className="text-yellow-300">Switching model...</span>
                          ) : (
                            <>
                              Current: <span className="text-blue-300 font-medium">
                                {selectedLyricsModel === 'svd_knn' ? 'SVD + KNN (Recommended)' :
                                 selectedLyricsModel === 'knn_cosine' ? 'KNN Cosine Distance' :
                                 selectedLyricsModel === 'knn_euclidean' ? 'KNN Euclidean Distance' :
                                 selectedLyricsModel === 'knn_cosine_k20' ? 'KNN Cosine (K=20)' :
                                 selectedLyricsModel}
                              </span>
                            </>
                          )}
                        </span>
                      </div>
                      <p className="text-xs text-gray-400 mt-1">
                        {isModelSwitching ? 
                          'Please wait while the model is being loaded...' :
                          'Try different methods to see how they affect your recommendations!'
                        }
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* HDBSCAN Model Selection (only shown for audio similarity approach) */}
              {selectedApproach === 'audio_similarity' && (
                <div className="bg-purple-900/20 border border-purple-500/30 rounded-lg p-4">
                  <h4 className="text-sm font-medium text-purple-300 mb-3">Choose Audio Analysis Method</h4>
                  <p className="text-xs text-gray-400 mb-4">
                    Each method processes audio features differently. Compare them to find the best approach for your music preferences.
                  </p>
                  <div className="space-y-3">
                    {hdbscanModelsLoading ? (
                      <div className="text-gray-400 text-sm">Loading audio analysis models...</div>
                    ) : hdbscanModelsError ? (
                      <div className="text-red-400 text-sm">Error loading HDBSCAN models</div>
                    ) : availableHdbscanModels && availableHdbscanModels.length > 0 ? (
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                        <div
                          onClick={() => setSelectedHdbscanModel('hdbscan_llav_pca')}
                          className={`p-3 rounded-lg border cursor-pointer transition-all ${
                            selectedHdbscanModel === 'hdbscan_llav_pca'
                              ? 'border-purple-500 bg-purple-500/10'
                              : 'border-gray-600 hover:border-gray-500'
                          }`}
                        >
                          <div className="flex items-center space-x-2 mb-2">
                            <span className="text-lg">⭐</span>
                            <div>
                              <h5 className="font-medium text-purple-300">Low-Level + PCA</h5>
                              <span className="text-xs text-green-400 bg-green-400/20 px-2 py-0.5 rounded-full">Best</span>
                            </div>
                          </div>
                          <p className="text-xs text-gray-400">
                            Advanced low-level audio features with PCA dimensionality reduction. Best overall performance for audio similarity.
                          </p>
                        </div>

                        <div
                          onClick={() => setSelectedHdbscanModel('hdbscan_pca_features')}
                          className={`p-3 rounded-lg border cursor-pointer transition-all ${
                            selectedHdbscanModel === 'hdbscan_pca_features'
                              ? 'border-purple-500 bg-purple-500/10'
                              : 'border-gray-600 hover:border-gray-500'
                          }`}
                        >
                          <div className="flex items-center space-x-2 mb-2">
                            <span className="text-lg">📊</span>
                            <div>
                              <h5 className="font-medium text-purple-300">PCA Features</h5>
                              <span className="text-xs text-blue-400 bg-blue-400/20 px-2 py-0.5 rounded-full">Efficient</span>
                            </div>
                          </div>
                          <p className="text-xs text-gray-400">
                            Basic audio features with PCA reduction. Good balance of performance and speed.
                          </p>
                        </div>

                        <div
                          onClick={() => setSelectedHdbscanModel('hdbscan_combined_features')}
                          className={`p-3 rounded-lg border cursor-pointer transition-all ${
                            selectedHdbscanModel === 'hdbscan_combined_features'
                              ? 'border-purple-500 bg-purple-500/10'
                              : 'border-gray-600 hover:border-gray-500'
                          }`}
                        >
                          <div className="flex items-center space-x-2 mb-2">
                            <span className="text-lg">🔀</span>
                            <div>
                              <h5 className="font-medium text-purple-300">Combined Features</h5>
                              <span className="text-xs text-orange-400 bg-orange-400/20 px-2 py-0.5 rounded-full">Comprehensive</span>
                            </div>
                          </div>
                          <p className="text-xs text-gray-400">
                            Combination of basic and low-level features. Most comprehensive analysis for complex patterns.
                          </p>
                        </div>

                        <div
                          onClick={() => setSelectedHdbscanModel('hdbscan_naive_features')}
                          className={`p-3 rounded-lg border cursor-pointer transition-all ${
                            selectedHdbscanModel === 'hdbscan_naive_features'
                              ? 'border-purple-500 bg-purple-500/10'
                              : 'border-gray-600 hover:border-gray-500'
                          }`}
                        >
                          <div className="flex items-center space-x-2 mb-2">
                            <span className="text-lg">🎯</span>
                            <div>
                              <h5 className="font-medium text-purple-300">Basic Features</h5>
                              <span className="text-xs text-gray-400 bg-gray-400/20 px-2 py-0.5 rounded-full">Simple</span>
                            </div>
                          </div>
                          <p className="text-xs text-gray-400">
                            Basic audio features only. Simple and fast, good for general similarity matching.
                          </p>
                        </div>

                        <div
                          onClick={() => setSelectedHdbscanModel('hdbscan_llav_features')}
                          className={`p-3 rounded-lg border cursor-pointer transition-all ${
                            selectedHdbscanModel === 'hdbscan_llav_features'
                              ? 'border-purple-500 bg-purple-500/10'
                              : 'border-gray-600 hover:border-gray-500'
                          }`}
                        >
                          <div className="flex items-center space-x-2 mb-2">
                            <span className="text-lg">🔍</span>
                            <div>
                              <h5 className="font-medium text-purple-300">Low-Level Audio</h5>
                              <span className="text-xs text-purple-400 bg-purple-400/20 px-2 py-0.5 rounded-full">Detailed</span>
                            </div>
                          </div>
                          <p className="text-xs text-gray-400">
                            Raw low-level audio features. Most detailed analysis for nuanced audio characteristics.
                          </p>
                        </div>
                      </div>
                    ) : (
                      <div className="text-gray-400 text-sm">No HDBSCAN models available</div>
                    )}
                    
                    {/* Current HDBSCAN Model Status */}
                    <div className="bg-gray-800/50 rounded-lg p-3 mt-4">
                      <div className="flex items-center space-x-2">
                        <div className={`w-2 h-2 rounded-full ${isModelSwitching ? 'bg-yellow-500 animate-pulse' : 'bg-green-500'}`}></div>
                        <span className="text-sm text-gray-300">
                          {isModelSwitching ? (
                            <span className="text-yellow-300">Switching model...</span>
                          ) : (
                            <>
                              Current: <span className="text-purple-300 font-medium">
                                {selectedHdbscanModel === 'hdbscan_llav_pca' ? 'Low-Level + PCA (Best)' :
                                 selectedHdbscanModel === 'hdbscan_pca_features' ? 'PCA Features (Efficient)' :
                                 selectedHdbscanModel === 'hdbscan_combined_features' ? 'Combined Features (Comprehensive)' :
                                 selectedHdbscanModel === 'hdbscan_naive_features' ? 'Basic Features (Simple)' :
                                 selectedHdbscanModel === 'hdbscan_llav_features' ? 'Low-Level Audio (Detailed)' :
                                 selectedHdbscanModel}
                              </span>
                            </>
                          )}
                        </span>
                      </div>
                      <p className="text-xs text-gray-400 mt-1">
                        {isModelSwitching ? 
                          'Please wait while the model is being loaded...' :
                          'Try different methods to see how they affect your audio-based recommendations!'
                        }
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Current Selection Summary */}
              <div className="bg-gray-800/50 rounded-lg p-4">
                <div className="flex items-center space-x-3">
                  <div className="text-2xl">{currentApproach.name.split(' ')[0]}</div>
                  <div>
                    <h4 className="font-medium text-white">Using: {currentApproach.name}</h4>
                    <p className="text-sm text-gray-400">{currentApproach.description}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
        
        <LikedSongsBar
          likedSongs={likedSongs}
          onRemoveSong={removeLikedSong}
          onClearAll={() => {
            clearLikedSongs();
            setIsSidebarOpen(false);
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
                    <ImportedSongCard
                      key={song.id}
                      song={song}
                      onPlay={(song) => playTrack(song)}
                      onPause={pauseTrack}
                      isPlaying={currentTrack?.id === song.id && isPlaying}
                      onLike={(song) => addLikedSong(song.id)}
                      onCardClick={handleSongSelect}
                      isLiked={likedSongIds.includes(song.id)}
                      layout="card"
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
                <h3 className="text-lg font-semibold">{currentApproach.name} Recommendations</h3>
                <span className="text-sm text-gray-400">
                  {recommendations?.recommendations?.length || 0} songs • Based on {likedSongIds.length} liked songs
                </span>
              </div>
              <p className="text-gray-300">{currentApproach.details}</p>
              {recommendations?.processing_time_ms && (
                <div className="text-xs text-gray-500 mt-2">
                  Generated in {recommendations.processing_time_ms.toFixed(1)}ms
                </div>
              )}
              
              {(isLoading || isModelSwitching) && (
                <div className="text-center py-8">
                  <div className="flex items-center justify-center space-x-3">
                    <div className="w-8 h-8 border-2 border-green-500 border-t-transparent rounded-full animate-spin"></div>
                    <span className="text-lg text-gray-300">
                      {isModelSwitching ? 'Switching model...' : 'Loading recommendations...'}
                    </span>
                  </div>
                </div>
              )}
              {error && <div className="text-red-400 text-center py-8">Error loading recommendations</div>}
              
              {!isLoading && !isModelSwitching && recommendations?.recommendations && recommendations.recommendations.length > 0 && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                  {recommendations.recommendations.map((song) => (
                    <ImportedSongCard
                      key={song.id}
                      song={song}
                      onPlay={(song) => playTrack(song)}
                      onPause={pauseTrack}
                      isPlaying={currentTrack?.id === song.id && isPlaying}
                      onLike={(song) => addLikedSong(song.id)}
                      onCardClick={handleSongSelect}
                      isLiked={likedSongIds.includes(song.id)}
                      showSimilarityScore={true}
                      layout="card"
                    />
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </motion.div>

      {/* Base Songs Sidebar */}
      <BaseSongsSidebar
        baseSongs={likedSongs}
        isOpen={isSidebarOpen}
        onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
        onRemoveSong={removeLikedSong}
        onClearAll={() => {
          clearLikedSongs();
          setIsSidebarOpen(false);
        }}
      />

      {/* Song Information Panel */}
      {showSongInfo && selectedSong && (
        <SongInfoPanel
          song={selectedSong}
          onClose={() => setShowSongInfo(false)}
        />
      )}
    </>
  );
}

function ExplorePage() {
  const { likedSongIds, likedSongs, addLikedSong, removeLikedSong, clearLikedSongs } = useLikedSongs();
  const { playTrack, pauseTrack, currentTrack, isPlaying } = useAudio();
  const [selectedCluster, setSelectedCluster] = React.useState<number | null>(null);
  const [viewMode, setViewMode] = React.useState<'clusters' | 'songs'>('clusters');
  const [layoutMode, setLayoutMode] = React.useState<'grid' | 'list'>('grid');
  const [searchQuery, setSearchQuery] = React.useState('');
  const [selectedSong, setSelectedSong] = React.useState<Song | null>(null);
  const [showSongInfo, setShowSongInfo] = React.useState(false);

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



  const handleClusterSelect = (cluster: ClusterInfo) => {
    setSelectedCluster(cluster.id);
    setViewMode('songs');
  };

  const handleSongLike = (songId: string) => {
    if (likedSongIds.includes(songId)) {
      removeLikedSong(songId);
    } else {
      addLikedSong(songId);
    }
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
        likedSongs={likedSongs}
        onRemoveSong={removeLikedSong}
        onClearAll={clearLikedSongs}
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
                    <ImportedSongCard
                      key={song.id}
                      song={song}
                      onPlay={(song) => playTrack(song)}
                      onPause={pauseTrack}
                      isPlaying={currentTrack?.id === song.id && isPlaying}
                      onLike={(song) => handleSongLike(song.id)}
                      onCardClick={handleSongSelect}
                      isLiked={likedSongIds.includes(song.id)}
                      layout="card"
                      showSimilarityScore={song.similarity_score !== undefined && song.similarity_score > 0}
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
                      isLiked={likedSongIds.includes(song.id)}
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

// Use the imported SongCard component instead of defining a duplicate here

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
  const { likedSongIds, likedSongs, addLikedSong, removeLikedSong, clearLikedSongs } = useLikedSongs();
  const [selectedApproaches, setSelectedApproaches] = React.useState<string[]>(['audio_similarity', 'lyrics_similarity']);
  const [selectedLyricsModels, setSelectedLyricsModels] = React.useState<string[]>(['svd_knn']);
  const [selectedHDBSCANModels, setSelectedHDBSCANModels] = React.useState<string[]>(['hdbscan_llav_pca']);
  const [comparisonResults, setComparisonResults] = React.useState<any>(null);
  const [isLoading, setIsLoading] = React.useState(false);
  const [isModelSwitching, setIsModelSwitching] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [searchQuery, setSearchQuery] = React.useState('');
  const [isSidebarOpen, setIsSidebarOpen] = React.useState<boolean>(false);
  const { playTrack } = useAudio();

  // Search songs for adding to liked songs
  const { data: searchResults, isLoading: isSearching } = useQuery({
    queryKey: ['search', searchQuery],
    queryFn: () => searchQuery ? apiService.songs.search({ query: searchQuery, limit: 10 }) : Promise.resolve([]),
    enabled: searchQuery.length > 2
  });

  // Define the available approaches for comparison
  const approaches = {
    audio_similarity: {
      name: '🎵 Audio Features',
      description: 'ML-powered audio analysis',
      details: 'Uses advanced machine learning to analyze musical characteristics',
      modelType: 'hdbscan_knn'
    },
    lyrics_similarity: {
      name: '📝 Lyrics Analysis', 
      description: 'NLP-powered lyrics analysis',
      details: 'Analyzes lyrics using natural language processing',
      modelType: 'lyrics'
    },
    similar_artists: {
      name: '🎤 Similar Artists',
      description: 'Artist-based matching',
      details: 'Finds more music from the same artists',
      modelType: 'artist_based'
    },
    similar_genres: {
      name: '🎶 Musical Styles',
      description: 'Genre-based grouping',
      details: 'Groups songs by musical styles and genres',
      modelType: 'genre_based'
    },
    cluster_based: {
      name: '🎯 Database Clusters',
      description: 'Pre-computed clustering',
      details: 'Uses database-stored music clusters',
      modelType: 'cluster'
    }
  };

  const handleCompareModels = async () => {
    if (selectedApproaches.length === 0 || likedSongIds.length === 0) {
      setError('Please select at least one approach and one song');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      setIsModelSwitching(true);
      
      // Create models to compare based on selected approaches and specific models
      const modelsToCompare: string[] = [];

      // Add selected approaches (non-model specific)
      selectedApproaches.forEach(approach => {
        if (approach === 'similar_artists') {
          modelsToCompare.push('artist_based');
        } else if (approach === 'similar_genres') {
          modelsToCompare.push('genre_based');
        } else if (approach === 'cluster_based') {
          modelsToCompare.push('cluster');
        }
      });

      // Add selected HDBSCAN models if audio similarity is selected
      if (selectedApproaches.includes('audio_similarity')) {
        selectedHDBSCANModels.forEach(model => {
          modelsToCompare.push(model);
        });
      }

      // Add selected lyrics models if lyrics similarity is selected
      if (selectedApproaches.includes('lyrics_similarity')) {
        selectedLyricsModels.forEach(model => {
          modelsToCompare.push(model);
        });
      }

      // Switch to the first model of each type for API compatibility
      if (selectedApproaches.includes('lyrics_similarity') && selectedLyricsModels.length > 0) {
        await apiService.recommendations.switchModel(selectedLyricsModels[0]);
        await new Promise(resolve => setTimeout(resolve, 500));
      }
      
      if (selectedApproaches.includes('audio_similarity') && selectedHDBSCANModels.length > 0) {
        await apiService.recommendations.switchModel(selectedHDBSCANModels[0]);
        await new Promise(resolve => setTimeout(resolve, 500));
      }
      
      setIsModelSwitching(false);

      const response = await apiService.recommendations.compare({
        liked_song_ids: likedSongIds,
        models_to_compare: modelsToCompare,
        n_recommendations: 10
      });
      setComparisonResults(response);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to compare models');
      setIsModelSwitching(false);
    } finally {
      setIsLoading(false);
    }
  };

  const addLikedSongFromSearch = (song: Song) => {
    addLikedSong(song.id);
  };

  const removeLikedSongFromList = (songId: string) => {
    removeLikedSong(songId);
  };

  const getApproachColor = (approachKey: string): string => {
    const colors = { 
      audio_similarity: '#8B5CF6', 
      lyrics_similarity: '#3B82F6', 
      similar_artists: '#10B981', 
      similar_genres: '#F59E0B',
      cluster_based: '#6B7280'
    };
    return colors[approachKey as keyof typeof colors] || '#6B7280';
  };

  return (
    <>
      <div className={`space-y-8 transition-all duration-300 ${isSidebarOpen ? 'mr-80' : ''}`}>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center"
        >
          <h1 className="text-4xl font-bold mb-4 bg-gradient-to-r from-green-400 to-teal-400 bg-clip-text text-transparent">
            Recommendation Approach Comparison
          </h1>
          <p className="text-xl text-gray-300 max-w-3xl mx-auto">
            Compare different recommendation approaches to see how they perform with your music taste.
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
                    onClick={() => addLikedSongFromSearch(song)}
                    disabled={likedSongIds.includes(song.id)}
                    className="px-3 py-1 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg text-sm"
                  >
                    {likedSongIds.includes(song.id) ? 'Added' : 'Add'}
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
                      onClick={() => removeLikedSongFromList(song.id)}
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

        {/* Approach Selection */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-gray-900/50 backdrop-blur-sm rounded-xl p-6 border border-gray-800"
        >
          <h2 className="text-xl font-semibold mb-4">Select Approaches to Compare</h2>
          <p className="text-gray-300 mb-6">Choose multiple approaches to see how they perform differently with your selected songs.</p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(approaches).map(([key, approach]) => (
              <div
                key={key}
                onClick={() => {
                  if (selectedApproaches.includes(key)) {
                    setSelectedApproaches(selectedApproaches.filter(a => a !== key));
                  } else {
                    setSelectedApproaches([...selectedApproaches, key]);
                  }
                }}
                className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${
                  selectedApproaches.includes(key)
                    ? 'border-green-500 bg-green-500/10 shadow-lg'
                    : 'border-gray-700 hover:border-gray-600'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <div className="text-2xl">{approach.name.split(' ')[0]}</div>
                  <div>
                    <h3 className="font-semibold">{approach.name}</h3>
                    <p className="text-sm text-gray-400">{approach.description}</p>
                    <p className="text-xs text-gray-500 mt-1">{approach.details}</p>
                  </div>
                </div>
                {selectedApproaches.includes(key) && (
                  <div className="mt-2">
                    <div className="w-3 h-3 bg-green-500 rounded-full ml-auto"></div>
                  </div>
                )}
              </div>
            ))}
          </div>
          
          {/* Compare Button */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="text-center"
          >
            <button
              onClick={handleCompareModels}
              disabled={isLoading || isModelSwitching || selectedApproaches.length === 0 || likedSongs.length === 0}
              className="px-8 py-3 bg-gradient-to-r from-green-600 to-teal-600 hover:from-green-700 hover:to-teal-700 disabled:from-gray-600 disabled:to-gray-600 disabled:cursor-not-allowed text-white rounded-lg font-semibold text-lg transition-all"
            >
              {isModelSwitching ? 'Switching Model...' : isLoading ? 'Comparing Approaches...' : 'Compare Approaches'}
            </button>
            {selectedApproaches.length > 0 && likedSongs.length > 0 && (
              <p className="mt-2 text-sm text-gray-400">
                Comparing {selectedApproaches.length} approach{selectedApproaches.length > 1 ? 'es' : ''} with {likedSongs.length} song{likedSongs.length > 1 ? 's' : ''}
              </p>
            )}
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
                {comparisonResults.results.map((result: any) => {
                  // Map backend model type back to approach
                  const approachKey = Object.keys(approaches).find(key => 
                    approaches[key as keyof typeof approaches].modelType === result.model_type
                  ) || result.model_type;
                  
                  const approach = approaches[approachKey as keyof typeof approaches] || {
                    name: result.model_type,
                    description: 'Unknown approach',
                    details: ''
                  };

                  return (
                    <div key={result.model_type} className="bg-gray-900/50 backdrop-blur-sm rounded-xl border border-gray-800 overflow-hidden">
                      <div 
                        className="p-4 text-white"
                        style={{ backgroundColor: `${getApproachColor(approachKey)}20` }}
                      >
                        <div className="flex items-center space-x-3">
                          <div className="text-2xl">{approach.name.split(' ')[0] || '🎯'}</div>
                          <div>
                            <h3 className="font-semibold text-lg">{approach.name}</h3>
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
                                  <span className="text-xs bg-green-500/20 border border-green-500/30 text-green-400 px-2 py-1 rounded-full font-medium">
                                    {(song.similarity_score * 100).toFixed(1)}% match
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
                  );
                })}
              </div>
            </motion.div>
          )}
        </motion.div>

        {/* HDBSCAN Model Selection (shown when audio similarity approach is selected) */}
        {selectedApproaches.includes('audio_similarity') && (
          <div className="mt-6 bg-purple-900/20 border border-purple-500/30 rounded-lg p-4">
            <h4 className="text-sm font-medium text-purple-300 mb-3">Audio Analysis Methods</h4>
            <p className="text-xs text-gray-400 mb-4">
              Choose multiple HDBSCAN audio analysis methods to compare. Each method uses different feature extraction approaches.
            </p>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div
                onClick={() => {
                  const modelName = 'hdbscan_llav_pca';
                  if (selectedHDBSCANModels.includes(modelName)) {
                    setSelectedHDBSCANModels(selectedHDBSCANModels.filter(m => m !== modelName));
                  } else {
                    setSelectedHDBSCANModels([...selectedHDBSCANModels, modelName]);
                  }
                }}
                className={`p-3 rounded-lg border cursor-pointer transition-all ${
                  selectedHDBSCANModels.includes('hdbscan_llav_pca')
                    ? 'border-purple-500 bg-purple-500/10'
                    : 'border-gray-600 hover:border-gray-500'
                }`}
              >
                <div className="flex items-center space-x-2 mb-1">
                  <span className="text-sm">⭐</span>
                  <h5 className="text-sm font-medium text-purple-300">Low-Level + PCA</h5>
                  <span className="text-xs text-green-400 bg-green-400/20 px-1.5 py-0.5 rounded-full">Best</span>
                </div>
                <p className="text-xs text-gray-400">Low-level audio features with PCA reduction</p>
              </div>

              <div
                onClick={() => {
                  const modelName = 'hdbscan_pca_features';
                  if (selectedHDBSCANModels.includes(modelName)) {
                    setSelectedHDBSCANModels(selectedHDBSCANModels.filter(m => m !== modelName));
                  } else {
                    setSelectedHDBSCANModels([...selectedHDBSCANModels, modelName]);
                  }
                }}
                className={`p-3 rounded-lg border cursor-pointer transition-all ${
                  selectedHDBSCANModels.includes('hdbscan_pca_features')
                    ? 'border-purple-500 bg-purple-500/10'
                    : 'border-gray-600 hover:border-gray-500'
                }`}
              >
                <div className="flex items-center space-x-2 mb-1">
                  <span className="text-sm">📊</span>
                  <h5 className="text-sm font-medium text-purple-300">PCA Features</h5>
                  <span className="text-xs text-blue-400 bg-blue-400/20 px-1.5 py-0.5 rounded-full">Efficient</span>
                </div>
                <p className="text-xs text-gray-400">PCA-reduced basic audio features</p>
              </div>

              <div
                onClick={() => {
                  const modelName = 'hdbscan_combined_features';
                  if (selectedHDBSCANModels.includes(modelName)) {
                    setSelectedHDBSCANModels(selectedHDBSCANModels.filter(m => m !== modelName));
                  } else {
                    setSelectedHDBSCANModels([...selectedHDBSCANModels, modelName]);
                  }
                }}
                className={`p-3 rounded-lg border cursor-pointer transition-all ${
                  selectedHDBSCANModels.includes('hdbscan_combined_features')
                    ? 'border-purple-500 bg-purple-500/10'
                    : 'border-gray-600 hover:border-gray-500'
                }`}
              >
                <div className="flex items-center space-x-2 mb-1">
                  <span className="text-sm">🔀</span>
                  <h5 className="text-sm font-medium text-purple-300">Combined Features</h5>
                  <span className="text-xs text-orange-400 bg-orange-400/20 px-1.5 py-0.5 rounded-full">Comprehensive</span>
                </div>
                <p className="text-xs text-gray-400">Combined basic and low-level features</p>
              </div>

              <div
                onClick={() => {
                  const modelName = 'hdbscan_naive_features';
                  if (selectedHDBSCANModels.includes(modelName)) {
                    setSelectedHDBSCANModels(selectedHDBSCANModels.filter(m => m !== modelName));
                  } else {
                    setSelectedHDBSCANModels([...selectedHDBSCANModels, modelName]);
                  }
                }}
                className={`p-3 rounded-lg border cursor-pointer transition-all ${
                  selectedHDBSCANModels.includes('hdbscan_naive_features')
                    ? 'border-purple-500 bg-purple-500/10'
                    : 'border-gray-600 hover:border-gray-500'
                }`}
              >
                <div className="flex items-center space-x-2 mb-1">
                  <span className="text-sm">🎯</span>
                  <h5 className="text-sm font-medium text-purple-300">Basic Features</h5>
                  <span className="text-xs text-gray-400 bg-gray-400/20 px-1.5 py-0.5 rounded-full">Simple</span>
                </div>
                <p className="text-xs text-gray-400">Basic audio features (tempo, key, etc.)</p>
              </div>

              <div
                onClick={() => {
                  const modelName = 'hdbscan_llav_features';
                  if (selectedHDBSCANModels.includes(modelName)) {
                    setSelectedHDBSCANModels(selectedHDBSCANModels.filter(m => m !== modelName));
                  } else {
                    setSelectedHDBSCANModels([...selectedHDBSCANModels, modelName]);
                  }
                }}
                className={`p-3 rounded-lg border cursor-pointer transition-all ${
                  selectedHDBSCANModels.includes('hdbscan_llav_features')
                    ? 'border-purple-500 bg-purple-500/10'
                    : 'border-gray-600 hover:border-gray-500'
                }`}
              >
                <div className="flex items-center space-x-2 mb-1">
                  <span className="text-sm">🔍</span>
                  <h5 className="text-sm font-medium text-purple-300">Low-Level Audio</h5>
                  <span className="text-xs text-purple-400 bg-purple-400/20 px-1.5 py-0.5 rounded-full">Detailed</span>
                </div>
                <p className="text-xs text-gray-400">Detailed low-level audio analysis</p>
              </div>
            </div>
            
            <div className="mt-3 text-center">
              <span className="text-xs text-gray-400">
                Selected ({selectedHDBSCANModels.length}): <span className="text-purple-300 font-medium">
                  {selectedHDBSCANModels.length === 0 ? 'None' : 
                   selectedHDBSCANModels.map(model => {
                     if (model === 'hdbscan_llav_pca') return 'Low-Level + PCA';
                     if (model === 'hdbscan_pca_features') return 'PCA Features';
                     if (model === 'hdbscan_combined_features') return 'Combined Features';
                     if (model === 'hdbscan_naive_features') return 'Basic Features';
                     if (model === 'hdbscan_llav_features') return 'Low-Level Audio';
                     return model;
                   }).join(', ')}
                </span>
              </span>
            </div>
          </div>
        )}

        {/* Lyrics Model Selection (shown when lyrics approach is selected) */}
        {selectedApproaches.includes('lyrics_similarity') && (
          <div className="mt-6 bg-blue-900/20 border border-blue-500/30 rounded-lg p-4">
            <h4 className="text-sm font-medium text-blue-300 mb-3">Lyrics Analysis Methods</h4>
            <p className="text-xs text-gray-400 mb-4">
              Choose multiple lyrics analysis methods to compare. Each method has different strengths.
            </p>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div
                onClick={() => {
                  const modelName = 'svd_knn';
                  if (selectedLyricsModels.includes(modelName)) {
                    setSelectedLyricsModels(selectedLyricsModels.filter(m => m !== modelName));
                  } else {
                    setSelectedLyricsModels([...selectedLyricsModels, modelName]);
                  }
                }}
                className={`p-3 rounded-lg border cursor-pointer transition-all ${
                  selectedLyricsModels.includes('svd_knn')
                    ? 'border-blue-500 bg-blue-500/10'
                    : 'border-gray-600 hover:border-gray-500'
                }`}
              >
                <div className="flex items-center space-x-2 mb-1">
                  <span className="text-sm">🔬</span>
                  <h5 className="text-sm font-medium text-blue-300">SVD + KNN</h5>
                  <span className="text-xs text-green-400 bg-green-400/20 px-1.5 py-0.5 rounded-full">Best</span>
                </div>
                <p className="text-xs text-gray-400">Advanced dimensionality reduction</p>
              </div>

              <div
                onClick={() => {
                  const modelName = 'knn_cosine';
                  if (selectedLyricsModels.includes(modelName)) {
                    setSelectedLyricsModels(selectedLyricsModels.filter(m => m !== modelName));
                  } else {
                    setSelectedLyricsModels([...selectedLyricsModels, modelName]);
                  }
                }}
                className={`p-3 rounded-lg border cursor-pointer transition-all ${
                  selectedLyricsModels.includes('knn_cosine')
                    ? 'border-blue-500 bg-blue-500/10'
                    : 'border-gray-600 hover:border-gray-500'
                }`}
              >
                <div className="flex items-center space-x-2 mb-1">
                  <span className="text-sm">📐</span>
                  <h5 className="text-sm font-medium text-blue-300">KNN Cosine</h5>
                  <span className="text-xs text-blue-400 bg-blue-400/20 px-1.5 py-0.5 rounded-full">Semantic</span>
                </div>
                <p className="text-xs text-gray-400">Thematic similarity matching</p>
              </div>

              <div
                onClick={() => {
                  const modelName = 'knn_euclidean';
                  if (selectedLyricsModels.includes(modelName)) {
                    setSelectedLyricsModels(selectedLyricsModels.filter(m => m !== modelName));
                  } else {
                    setSelectedLyricsModels([...selectedLyricsModels, modelName]);
                  }
                }}
                className={`p-3 rounded-lg border cursor-pointer transition-all ${
                  selectedLyricsModels.includes('knn_euclidean')
                    ? 'border-blue-500 bg-blue-500/10'
                    : 'border-gray-600 hover:border-gray-500'
                }`}
              >
                <div className="flex items-center space-x-2 mb-1">
                  <span className="text-sm">📏</span>
                  <h5 className="text-sm font-medium text-blue-300">KNN Euclidean</h5>
                  <span className="text-xs text-orange-400 bg-orange-400/20 px-1.5 py-0.5 rounded-full">Precise</span>
                </div>
                <p className="text-xs text-gray-400">Exact word pattern matching</p>
              </div>

              <div
                onClick={() => {
                  const modelName = 'knn_cosine_k20';
                  if (selectedLyricsModels.includes(modelName)) {
                    setSelectedLyricsModels(selectedLyricsModels.filter(m => m !== modelName));
                  } else {
                    setSelectedLyricsModels([...selectedLyricsModels, modelName]);
                  }
                }}
                className={`p-3 rounded-lg border cursor-pointer transition-all ${
                  selectedLyricsModels.includes('knn_cosine_k20')
                    ? 'border-blue-500 bg-blue-500/10'
                    : 'border-gray-600 hover:border-gray-500'
                }`}
              >
                <div className="flex items-center space-x-2 mb-1">
                  <span className="text-sm">🎯</span>
                  <h5 className="text-sm font-medium text-blue-300">KNN Cosine (K=20)</h5>
                  <span className="text-xs text-purple-400 bg-purple-400/20 px-1.5 py-0.5 rounded-full">Diverse</span>
                </div>
                <p className="text-xs text-gray-400">More diverse recommendations</p>
              </div>
            </div>
            
            <div className="mt-3 text-center">
              <span className="text-xs text-gray-400">
                Selected ({selectedLyricsModels.length}): <span className="text-blue-300 font-medium">
                  {selectedLyricsModels.length === 0 ? 'None' :
                   selectedLyricsModels.map(model => {
                     if (model === 'svd_knn') return 'SVD + KNN';
                     if (model === 'knn_cosine') return 'KNN Cosine';
                     if (model === 'knn_euclidean') return 'KNN Euclidean';
                     if (model === 'knn_cosine_k20') return 'KNN Cosine (K=20)';
                     return model;
                   }).join(', ')}
                </span>
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Base Songs Sidebar */}
      <BaseSongsSidebar
        baseSongs={likedSongs}
        isOpen={isSidebarOpen}
        onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
        onRemoveSong={removeLikedSong}
        onClearAll={() => {
          clearLikedSongs();
          setIsSidebarOpen(false);
        }}
      />
    </>
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
                  {(song.similarity_score * 100).toFixed(1)}% match
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
export { useLikedSongs }; 
