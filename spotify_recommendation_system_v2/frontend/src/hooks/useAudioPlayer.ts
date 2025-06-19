import { useState, useRef, useCallback, useEffect } from 'react';

interface Track {
  id: string;
  name: string;
  artist: string;
  preview_url?: string;
}

interface AudioPlayerState {
  currentTrack: Track | null;
  isPlaying: boolean;
  currentTime: number;
  duration: number;
  volume: number;
  isLoading: boolean;
}

export const useAudioPlayer = () => {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [state, setState] = useState<AudioPlayerState>({
    currentTrack: null,
    isPlaying: false,
    currentTime: 0,
    duration: 0,
    volume: 0.7,
    isLoading: false,
  });

  // Initialize audio element
  useEffect(() => {
    const audio = new Audio();
    audio.volume = state.volume;
    audioRef.current = audio;

    // Audio event listeners
    const handleLoadStart = () => setState(prev => ({ ...prev, isLoading: true }));
    const handleCanPlay = () => setState(prev => ({ ...prev, isLoading: false }));
    const handleTimeUpdate = () => {
      if (audio.currentTime && audio.duration) {
        setState(prev => ({
          ...prev,
          currentTime: audio.currentTime,
          duration: audio.duration,
        }));
      }
    };
    const handleEnded = () => setState(prev => ({ ...prev, isPlaying: false }));
    const handleError = () => {
      setState(prev => ({ ...prev, isPlaying: false, isLoading: false }));
      console.error('Audio playback error');
    };

    audio.addEventListener('loadstart', handleLoadStart);
    audio.addEventListener('canplay', handleCanPlay);
    audio.addEventListener('timeupdate', handleTimeUpdate);
    audio.addEventListener('ended', handleEnded);
    audio.addEventListener('error', handleError);

    return () => {
      audio.removeEventListener('loadstart', handleLoadStart);
      audio.removeEventListener('canplay', handleCanPlay);
      audio.removeEventListener('timeupdate', handleTimeUpdate);
      audio.removeEventListener('ended', handleEnded);
      audio.removeEventListener('error', handleError);
      audio.pause();
    };
  }, [state.volume]);

  const play = useCallback((track: Track) => {
    if (!audioRef.current || !track.preview_url) {
      console.warn('No preview URL available for this track');
      return;
    }

    const audio = audioRef.current;

    // If same track, just toggle play/pause
    if (state.currentTrack?.id === track.id) {
      if (state.isPlaying) {
        audio.pause();
        setState(prev => ({ ...prev, isPlaying: false }));
      } else {
        audio.play().catch(console.error);
        setState(prev => ({ ...prev, isPlaying: true }));
      }
      return;
    }

    // Load new track
    audio.src = track.preview_url;
    setState(prev => ({
      ...prev,
      currentTrack: track,
      isPlaying: true,
      currentTime: 0,
      duration: 0,
    }));

    audio.play().catch((error) => {
      console.error('Playback failed:', error);
      setState(prev => ({ ...prev, isPlaying: false }));
    });
  }, [state.currentTrack, state.isPlaying]);

  const pause = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      setState(prev => ({ ...prev, isPlaying: false }));
    }
  }, []);

  const stop = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      setState(prev => ({
        ...prev,
        isPlaying: false,
        currentTime: 0,
      }));
    }
  }, []);

  const seek = useCallback((time: number) => {
    if (audioRef.current) {
      audioRef.current.currentTime = time;
      setState(prev => ({ ...prev, currentTime: time }));
    }
  }, []);

  const setVolume = useCallback((volume: number) => {
    const clampedVolume = Math.max(0, Math.min(1, volume));
    if (audioRef.current) {
      audioRef.current.volume = clampedVolume;
      setState(prev => ({ ...prev, volume: clampedVolume }));
    }
  }, []);

  return {
    ...state,
    play,
    pause,
    stop,
    seek,
    setVolume,
    togglePlayPause: () => state.isPlaying ? pause() : play(state.currentTrack!),
  };
}; 