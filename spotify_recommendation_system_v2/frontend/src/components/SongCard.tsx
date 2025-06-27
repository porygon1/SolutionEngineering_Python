import React, { useState, useRef } from 'react';
import { motion } from 'framer-motion';
import { 
  PlayIcon, 
  PauseIcon, 
  HeartIcon, 
  EllipsisHorizontalIcon,
  MusicalNoteIcon,
  ClockIcon
} from '@heroicons/react/24/solid';
import { HeartIcon as HeartOutlineIcon } from '@heroicons/react/24/outline';
import { clsx } from 'clsx';
import { Song } from '../services/api';
import { spotifyService, generateAlbumCover } from '../services/spotify';

interface SongCardProps {
  song: Song;
  isPlaying?: boolean;
  onPlay?: (song: Song) => void;
  onPause?: () => void;
  onLike?: (song: Song) => void;
  onCardClick?: (song: Song) => void;
  isLiked?: boolean;
  showFeatures?: boolean;
  layout?: 'card' | 'list';
  showSimilarityScore?: boolean;
  compact?: boolean;
}

const SongCard: React.FC<SongCardProps> = ({
  song,
  isPlaying = false,
  onPlay,
  onPause,
  onLike,
  onCardClick,
  isLiked = false,
  showFeatures = true,
  layout = 'card',
  showSimilarityScore = false,
  compact = false
}) => {
  const [imageError, setImageError] = useState(false);
  const [isHovered, setIsHovered] = useState(false);
  const audioRef = useRef<HTMLAudioElement>(null);

  const handlePlayPause = (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent card click when clicking play button
    if (isPlaying) {
      onPause?.();
    } else {
      onPlay?.(song);
    }
  };

  const handleLike = (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent card click when clicking like button
    onLike?.(song);
  };

  const handleCardClick = () => {
    onCardClick?.(song);
  };

  const handleImageError = () => {
    setImageError(true);
  };

  // Get album art URL using the generateAlbumCover function
  const albumArtUrl = imageError 
    ? generateAlbumCover(song) 
    : generateAlbumCover(song);

  if (layout === 'list') {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        whileHover={{ backgroundColor: 'rgba(255, 255, 255, 0.05)' }}
        className="flex items-center space-x-4 p-3 rounded-lg hover:bg-white/5 transition-all duration-200 group cursor-pointer"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        onClick={handleCardClick}
      >
        {/* Album Art */}
        <div className="relative flex-shrink-0">
          <img
            src={albumArtUrl}
            alt={`${song.name} by ${song.artist}`}
            className="w-12 h-12 rounded-md object-cover"
            onError={handleImageError}
          />
          {/* Play Button Overlay */}
          <motion.button
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ 
              opacity: isHovered || isPlaying ? 1 : 0, 
              scale: isHovered || isPlaying ? 1 : 0.8 
            }}
            onClick={handlePlayPause}
            className="absolute inset-0 flex items-center justify-center bg-black/60 rounded-md"
          >
            {isPlaying ? (
              <PauseIcon className="w-4 h-4 text-white" />
            ) : (
              <PlayIcon className="w-4 h-4 text-white ml-0.5" />
            )}
          </motion.button>
        </div>

        {/* Song Info */}
        <div className="flex-1 min-w-0">
          <h3 className="text-white font-medium truncate">{song.name}</h3>
          <p className="text-gray-400 text-sm truncate">{song.artist}</p>
          {showSimilarityScore && song.similarity_score !== undefined && (
            <div className="flex items-center space-x-1 mt-1">
              <div className="px-2 py-1 bg-green-500/20 rounded-full border border-green-500/30">
                <span className="text-xs text-green-400 font-medium">
                  {(song.similarity_score * 100).toFixed(1)}% match
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Duration */}
        <div className="flex items-center space-x-2 text-gray-400 text-sm">
          <ClockIcon className="w-4 h-4" />
          <span>{spotifyService.formatDuration(song.duration_ms)}</span>
        </div>

        {/* Actions */}
        <div className="flex items-center space-x-2">
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleLike}
            className={clsx(
              'p-2 rounded-full transition-colors',
              isLiked ? 'text-green-500' : 'text-gray-400 hover:text-white'
            )}
          >
            {isLiked ? (
              <HeartIcon className="w-5 h-5" />
            ) : (
              <HeartOutlineIcon className="w-5 h-5" />
            )}
          </motion.button>
          <button className="p-2 text-gray-400 hover:text-white transition-colors">
            <EllipsisHorizontalIcon className="w-5 h-5" />
          </button>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -4 }}
      className="bg-gray-900/50 backdrop-blur-sm rounded-xl p-4 border border-gray-800 hover:border-green-500/50 transition-all duration-200 group cursor-pointer"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={handleCardClick}
    >
      {/* Album Art Container */}
      <div className="relative mb-4">
        <div className="aspect-square rounded-lg overflow-hidden bg-gray-800">
          {imageError ? (
            <div className="w-full h-full flex items-center justify-center">
              <MusicalNoteIcon className="w-16 h-16 text-gray-600" />
            </div>
          ) : (
            <img
              src={albumArtUrl}
              alt={`${song.name} by ${song.artist}`}
              className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
              onError={handleImageError}
            />
          )}
        </div>

        {/* Play Button Overlay */}
        <motion.button
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ 
            opacity: isHovered || isPlaying ? 1 : 0, 
            scale: isHovered || isPlaying ? 1 : 0.8 
          }}
          onClick={handlePlayPause}
          className="absolute bottom-2 right-2 w-12 h-12 bg-green-500 hover:bg-green-400 rounded-full flex items-center justify-center shadow-lg transition-colors"
        >
          {isPlaying ? (
            <PauseIcon className="w-6 h-6 text-black" />
          ) : (
            <PlayIcon className="w-6 h-6 text-black ml-0.5" />
          )}
        </motion.button>

        {/* Like Button */}
        <motion.button
          initial={{ opacity: 0 }}
          animate={{ opacity: isHovered ? 1 : 0 }}
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.95 }}
          onClick={handleLike}
          className={clsx(
            'absolute top-2 right-2 p-2 rounded-full backdrop-blur-sm transition-colors',
            isLiked 
              ? 'bg-green-500/20 text-green-500' 
              : 'bg-black/40 text-gray-400 hover:text-white'
          )}
        >
          {isLiked ? (
            <HeartIcon className="w-5 h-5" />
          ) : (
            <HeartOutlineIcon className="w-5 h-5" />
          )}
        </motion.button>
      </div>

      {/* Song Info */}
      <div className="space-y-2">
        <h3 className="text-white font-semibold text-lg truncate group-hover:text-green-400 transition-colors">
          {song.name}
        </h3>
        <p className="text-gray-400 text-sm truncate">{song.artist}</p>
        
        {/* Popularity Bar */}
        <div className="flex items-center space-x-2">
          <div className="flex-1 bg-gray-700 rounded-full h-1">
            <div
              className={clsx(
                'h-full rounded-full transition-all duration-300',
                spotifyService.getPopularityColor(song.popularity)
              )}
              style={{ width: `${song.popularity}%` }}
            />
          </div>
          <span className="text-xs text-gray-500">{song.popularity}%</span>
        </div>

        {/* Audio Features */}
        {showFeatures && (
          <div className="grid grid-cols-3 gap-2 pt-2 border-t border-gray-700">
            <div className="text-center">
              <div className={clsx('text-lg', spotifyService.getFeatureColor(song.energy, 'energy'))}>
                ⚡
              </div>
              <div className="text-xs text-gray-400">
                {spotifyService.featureToPercentage(song.energy)}%
              </div>
            </div>
            <div className="text-center">
              <div className={clsx('text-lg', spotifyService.getFeatureColor(song.valence, 'valence'))}>
                😊
              </div>
              <div className="text-xs text-gray-400">
                {spotifyService.featureToPercentage(song.valence)}%
              </div>
            </div>
            <div className="text-center">
              <div className={clsx('text-lg', spotifyService.getFeatureColor(song.danceability, 'danceability'))}>
                💃
              </div>
              <div className="text-xs text-gray-400">
                {spotifyService.featureToPercentage(song.danceability)}%
              </div>
            </div>
          </div>
        )}

        {/* Similarity Score */}
        {showSimilarityScore && song.similarity_score !== undefined && (
          <div className="flex items-center justify-center bg-gradient-to-r from-green-500/20 to-blue-500/20 rounded-lg p-2 border border-green-500/30">
            <div className="text-center">
              <div className="text-lg font-bold text-green-400">
                {(song.similarity_score * 100).toFixed(1)}%
              </div>
              <div className="text-xs text-gray-400">Similarity</div>
            </div>
          </div>
        )}

        {/* Duration */}
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span>Cluster {song.cluster_id}</span>
          <span>{spotifyService.formatDuration(song.duration_ms)}</span>
        </div>
      </div>

      {/* Hidden audio element for preview */}
      {song.preview_url && (
        <audio
          ref={audioRef}
          src={song.preview_url}
          preload="none"
        />
      )}
    </motion.div>
  );
};

export default SongCard; 