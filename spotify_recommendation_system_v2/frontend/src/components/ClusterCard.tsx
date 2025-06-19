import React from 'react';
import { motion } from 'framer-motion';
import { 
  MusicalNoteIcon, 
  UserGroupIcon, 
  ChartBarIcon,
  SparklesIcon
} from '@heroicons/react/24/outline';
import { clsx } from 'clsx';
import { ClusterInfo } from '../services/api';

interface ClusterCardProps {
  cluster: ClusterInfo;
  onClick?: (cluster: ClusterInfo) => void;
  isSelected?: boolean;
}

const ClusterCard: React.FC<ClusterCardProps> = ({
  cluster,
  onClick,
  isSelected = false
}) => {
  const getClusterColor = (clusterId: number): string => {
    const colors = [
      'from-purple-500 to-pink-500',
      'from-blue-500 to-cyan-500',
      'from-green-500 to-teal-500',
      'from-yellow-500 to-orange-500',
      'from-red-500 to-pink-500',
      'from-indigo-500 to-purple-500',
      'from-emerald-500 to-green-500',
      'from-orange-500 to-red-500',
    ];
    return colors[clusterId % colors.length];
  };

  const getClusterIcon = (genres: string[]): JSX.Element => {
    if (genres.some(genre => genre.toLowerCase().includes('rock'))) {
      return <span className="text-2xl">🎸</span>;
    }
    if (genres.some(genre => genre.toLowerCase().includes('pop'))) {
      return <span className="text-2xl">🎤</span>;
    }
    if (genres.some(genre => genre.toLowerCase().includes('jazz'))) {
      return <span className="text-2xl">🎷</span>;
    }
    if (genres.some(genre => genre.toLowerCase().includes('electronic'))) {
      return <span className="text-2xl">🎧</span>;
    }
    if (genres.some(genre => genre.toLowerCase().includes('classical'))) {
      return <span className="text-2xl">🎻</span>;
    }
    return <MusicalNoteIcon className="w-8 h-8" />;
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -4, scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      onClick={() => onClick?.(cluster)}
      className={clsx(
        'relative overflow-hidden rounded-xl cursor-pointer transition-all duration-300',
        'bg-gray-900/50 backdrop-blur-sm border hover:border-green-500/50',
        isSelected ? 'border-green-500 ring-2 ring-green-500/20' : 'border-gray-800'
      )}
    >
      {/* Background Gradient */}
      <div className={clsx(
        'absolute inset-0 bg-gradient-to-br opacity-10',
        getClusterColor(cluster.id)
      )} />
      
      {/* Content */}
      <div className="relative p-6 space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            {getClusterIcon(cluster.dominant_genres)}
            <div>
              <h3 className="text-lg font-semibold text-white">
                {cluster.name || `Cluster ${cluster.id}`}
              </h3>
              <p className="text-sm text-gray-400">
                {cluster.size} tracks
              </p>
            </div>
          </div>
          
          <div className="flex items-center space-x-1 text-yellow-400">
            <SparklesIcon className="w-4 h-4" />
            <span className="text-sm font-medium">
              {Math.round(cluster.cohesion_score * 100)}%
            </span>
          </div>
        </div>

        {/* Dominant Genres */}
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-300">Dominant Genres</h4>
          <div className="flex flex-wrap gap-2">
            {cluster.dominant_genres.slice(0, 3).map((genre, index) => (
              <span
                key={index}
                className={clsx(
                  'px-2 py-1 rounded-full text-xs font-medium',
                  'bg-gradient-to-r text-white',
                  getClusterColor(cluster.id)
                )}
              >
                {genre}
              </span>
            ))}
            {cluster.dominant_genres.length > 3 && (
              <span className="px-2 py-1 rounded-full text-xs font-medium bg-gray-700 text-gray-300">
                +{cluster.dominant_genres.length - 3}
              </span>
            )}
          </div>
        </div>

        {/* Dominant Features */}
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-300">Key Features</h4>
          <div className="flex flex-wrap gap-2">
            {cluster.dominant_features.slice(0, 3).map((feature, index) => (
              <span
                key={index}
                className="px-2 py-1 rounded-full text-xs font-medium bg-gray-700 text-gray-300"
              >
                {feature}
              </span>
            ))}
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-700">
          <div className="flex items-center space-x-2">
            <UserGroupIcon className="w-4 h-4 text-gray-400" />
            <div>
              <p className="text-xs text-gray-400">Size</p>
              <p className="text-sm font-medium text-white">{cluster.size}</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <ChartBarIcon className="w-4 h-4 text-gray-400" />
            <div>
              <p className="text-xs text-gray-400">Cohesion</p>
              <p className="text-sm font-medium text-white">
                {Math.round(cluster.cohesion_score * 100)}%
              </p>
            </div>
          </div>
        </div>

        {/* Era Info */}
        {cluster.era && (
          <div className="pt-2">
            <p className="text-xs text-gray-400">Era</p>
            <p className="text-sm font-medium text-white">{cluster.era}</p>
          </div>
        )}
      </div>

      {/* Hover Effect */}
      <motion.div
        initial={{ opacity: 0 }}
        whileHover={{ opacity: 1 }}
        className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent pointer-events-none"
      />
    </motion.div>
  );
};

export default ClusterCard; 