// Spotify service for handling album art and preview URLs
// This service primarily uses data from our backend/dataset rather than making direct API calls

import { Song } from './api';

export interface SpotifyTrackData {
  id: string;
  name: string;
  artist: string;
  album: string;
  preview_url?: string;
  spotify_url: string;
  duration_ms: number;
  popularity: number;
  images?: Array<{
    url: string;
    height: number;
    width: number;
  }>;
}

// Fallback image for tracks without album art
const DEFAULT_ALBUM_ART = '/api/placeholder/300/300';

// Color palette for album covers
const ALBUM_COLORS = [
  ['#FF6B6B', '#4ECDC4'], // Red to Teal
  ['#A8E6CF', '#88D8C0'], // Light Green to Green
  ['#FFD93D', '#6BCF7F'], // Yellow to Green
  ['#4D4D4D', '#999999'], // Dark to Light Gray
  ['#FF8A80', '#FF5722'], // Light Red to Deep Orange
  ['#81C784', '#4CAF50'], // Light Green to Green
  ['#64B5F6', '#2196F3'], // Light Blue to Blue
  ['#BA68C8', '#9C27B0'], // Light Purple to Purple
  ['#FFB74D', '#FF9800'], // Light Orange to Orange
  ['#F06292', '#E91E63'], // Light Pink to Pink
];

// Generate a deterministic album cover based on song ID
export function generateAlbumCover(song: Song): string {
  // First, check if we have a real album image URL from the API
  if (song.album_image_url && song.album_image_url.trim() !== '') {
    return song.album_image_url;
  }
  
  // Fallback to generated album cover if no real image is available
  // Use song ID to determine color palette
  const colorIndex = song.id.charCodeAt(song.id.length - 1) % ALBUM_COLORS.length;
  const [color1, color2] = ALBUM_COLORS[colorIndex];
  
  // Create a simple gradient SVG
  const svg = `
    <svg width="300" height="300" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style="stop-color:${color1};stop-opacity:1" />
          <stop offset="100%" style="stop-color:${color2};stop-opacity:1" />
        </linearGradient>
      </defs>
      <rect width="100%" height="100%" fill="url(#grad)" />
      <circle cx="150" cy="120" r="40" fill="rgba(255,255,255,0.2)" />
      <text x="150" y="200" text-anchor="middle" fill="rgba(255,255,255,0.8)" 
            font-family="Arial, sans-serif" font-size="14" font-weight="bold">
        ${song.name.slice(0, 15)}${song.name.length > 15 ? '...' : ''}
      </text>
      <text x="150" y="220" text-anchor="middle" fill="rgba(255,255,255,0.6)" 
            font-family="Arial, sans-serif" font-size="12">
        ${song.artist.slice(0, 20)}${song.artist.length > 20 ? '...' : ''}
      </text>
    </svg>
  `;
  
  // Convert SVG to data URL
  const encodedSvg = encodeURIComponent(svg);
  return `data:image/svg+xml,${encodedSvg}`;
}

// Get a working preview URL (use sample if none available)
export function getPreviewUrl(song: Song): string | null {
  if (song.preview_url && song.preview_url !== 'null' && !song.preview_url.includes('example.com')) {
    return song.preview_url;
  }
  
  // Return null if no real preview URL is available
  // This will prevent the audio player from trying to play non-existent audio
  return null;
}

// Format audio features for display
export function formatAudioFeatures(song: Song) {
  return {
    energy: {
      value: song.energy,
      label: song.energy > 0.7 ? 'High Energy' : song.energy > 0.4 ? 'Medium Energy' : 'Low Energy',
      color: song.energy > 0.7 ? '#FF5722' : song.energy > 0.4 ? '#FF9800' : '#4CAF50',
      icon: '⚡'
    },
    valence: {
      value: song.valence,
      label: song.valence > 0.7 ? 'Very Positive' : song.valence > 0.4 ? 'Positive' : 'Melancholic',
      color: song.valence > 0.7 ? '#4CAF50' : song.valence > 0.4 ? '#8BC34A' : '#FF5722',
      icon: song.valence > 0.5 ? '😊' : '😔'
    },
    danceability: {
      value: song.danceability,
      label: song.danceability > 0.7 ? 'Very Danceable' : song.danceability > 0.4 ? 'Danceable' : 'Not Danceable',
      color: song.danceability > 0.7 ? '#E91E63' : song.danceability > 0.4 ? '#FF4081' : '#9E9E9E',
      icon: '💃'
    },
    acousticness: {
      value: song.acousticness,
      label: song.acousticness > 0.7 ? 'Very Acoustic' : song.acousticness > 0.4 ? 'Acoustic' : 'Electronic',
      color: song.acousticness > 0.7 ? '#8BC34A' : song.acousticness > 0.4 ? '#CDDC39' : '#2196F3',
      icon: song.acousticness > 0.5 ? '🎸' : '🎹'
    },
    instrumentalness: {
      value: song.instrumentalness,
      label: song.instrumentalness > 0.7 ? 'Instrumental' : song.instrumentalness > 0.4 ? 'Some Vocals' : 'Vocal',
      color: song.instrumentalness > 0.7 ? '#9C27B0' : song.instrumentalness > 0.4 ? '#673AB7' : '#3F51B5',
      icon: song.instrumentalness > 0.5 ? '🎵' : '🎤'
    },
    liveness: {
      value: song.liveness,
      label: song.liveness > 0.7 ? 'Live Recording' : song.liveness > 0.4 ? 'Some Live Elements' : 'Studio',
      color: song.liveness > 0.7 ? '#FF5722' : song.liveness > 0.4 ? '#FF9800' : '#607D8B',
      icon: song.liveness > 0.5 ? '🎤' : '🎧'
    },
    speechiness: {
      value: song.speechiness,
      label: song.speechiness > 0.7 ? 'Very Spoken' : song.speechiness > 0.4 ? 'Some Speech' : 'Musical',
      color: song.speechiness > 0.7 ? '#795548' : song.speechiness > 0.4 ? '#8D6E63' : '#4CAF50',
      icon: song.speechiness > 0.5 ? '🗣️' : '🎶'
    },
    loudness: {
      value: Math.max(0, (song.loudness + 60) / 60), // Normalize loudness from -60dB to 0dB
      label: song.loudness > -10 ? 'Very Loud' : song.loudness > -20 ? 'Loud' : song.loudness > -30 ? 'Moderate' : 'Quiet',
      color: song.loudness > -10 ? '#F44336' : song.loudness > -20 ? '#FF9800' : song.loudness > -30 ? '#4CAF50' : '#2196F3',
      icon: song.loudness > -15 ? '🔊' : '🔉'
    }
  };
}

// Get key and mode as readable string
export function getMusicalKey(song: Song): string {
  const keys = ['C', 'C♯/D♭', 'D', 'D♯/E♭', 'E', 'F', 'F♯/G♭', 'G', 'G♯/A♭', 'A', 'A♯/B♭', 'B'];
  const keyName = keys[song.key] || 'Unknown';
  const modeName = song.mode === 1 ? 'Major' : 'Minor';
  return `${keyName} ${modeName}`;
}

// Format tempo for display
export function formatTempo(tempo: number): string {
  if (tempo < 70) return `${Math.round(tempo)} BPM (Very Slow)`;
  if (tempo < 100) return `${Math.round(tempo)} BPM (Slow)`;
  if (tempo < 130) return `${Math.round(tempo)} BPM (Moderate)`;
  if (tempo < 160) return `${Math.round(tempo)} BPM (Fast)`;
  return `${Math.round(tempo)} BPM (Very Fast)`;
}

// Format duration
export function formatDuration(durationMs: number): string {
  const minutes = Math.floor(durationMs / 60000);
  const seconds = Math.floor((durationMs % 60000) / 1000);
  return `${minutes}:${seconds.toString().padStart(2, '0')}`;
}

// Get genre color based on common genre patterns
export function getGenreColor(genre: string): string {
  const lowerGenre = genre.toLowerCase();
  
  if (lowerGenre.includes('rock') || lowerGenre.includes('metal')) return '#FF5722';
  if (lowerGenre.includes('pop')) return '#E91E63';
  if (lowerGenre.includes('jazz') || lowerGenre.includes('blues')) return '#3F51B5';
  if (lowerGenre.includes('classical')) return '#9C27B0';
  if (lowerGenre.includes('electronic') || lowerGenre.includes('edm')) return '#00BCD4';
  if (lowerGenre.includes('hip hop') || lowerGenre.includes('rap')) return '#795548';
  if (lowerGenre.includes('country')) return '#FF9800';
  if (lowerGenre.includes('folk') || lowerGenre.includes('acoustic')) return '#4CAF50';
  if (lowerGenre.includes('ambient') || lowerGenre.includes('chill')) return '#607D8B';
  
  return '#9E9E9E'; // Default gray
}

export const spotifyService = {
  // Get album art URL (primarily from our dataset)
  getAlbumArt: (track: SpotifyTrackData, size: 'small' | 'medium' | 'large' = 'medium'): string => {
    if (track.images && track.images.length > 0) {
      // Return appropriate size based on request
      if (size === 'small' && track.images.length > 2) {
        return track.images[2].url; // Smallest image
      } else if (size === 'large') {
        return track.images[0].url; // Largest image
      } else {
        return track.images[1]?.url || track.images[0].url; // Medium or fallback to largest
      }
    }
    return DEFAULT_ALBUM_ART;
  },

  // Format duration from milliseconds to mm:ss
  formatDuration: (duration_ms: number): string => {
    const minutes = Math.floor(duration_ms / 60000);
    const seconds = Math.floor((duration_ms % 60000) / 1000);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  },

  // Get preview URL for audio playback
  getPreviewUrl: (track: SpotifyTrackData): string | null => {
    return track.preview_url || null;
  },

  // Open Spotify Web Player
  openInSpotify: (track: SpotifyTrackData): void => {
    if (track.spotify_url) {
      window.open(track.spotify_url, '_blank');
    }
  },

  // Get audio feature color coding
  getFeatureColor: (value: number, feature: string): string => {
    const intensity = Math.round(value * 100);
    
    switch (feature) {
      case 'energy':
        return intensity > 70 ? 'text-red-400' : intensity > 40 ? 'text-orange-400' : 'text-blue-400';
      case 'valence':
        return intensity > 70 ? 'text-green-400' : intensity > 40 ? 'text-yellow-400' : 'text-purple-400';
      case 'danceability':
        return intensity > 70 ? 'text-pink-400' : intensity > 40 ? 'text-indigo-400' : 'text-gray-400';
      default:
        return 'text-gray-400';
    }
  },

  // Get audio feature icon
  getFeatureIcon: (feature: string): string => {
    switch (feature) {
      case 'energy':
        return '⚡';
      case 'valence':
        return '😊';
      case 'danceability':
        return '💃';
      case 'acousticness':
        return '🎸';
      case 'instrumentalness':
        return '🎵';
      case 'liveness':
        return '🎤';
      case 'speechiness':
        return '🗣️';
      default:
        return '🎶';
    }
  },

  // Get popularity bar color
  getPopularityColor: (popularity: number): string => {
    if (popularity >= 80) return 'bg-green-500';
    if (popularity >= 60) return 'bg-yellow-500';
    if (popularity >= 40) return 'bg-orange-500';
    return 'bg-red-500';
  },

  // Convert audio features to percentage
  featureToPercentage: (value: number): number => {
    return Math.round(value * 100);
  }
};

export default spotifyService; 