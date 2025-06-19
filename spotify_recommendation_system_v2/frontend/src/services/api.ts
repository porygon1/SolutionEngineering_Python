import axios from 'axios';

// API Configuration
const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
const API_VERSION = import.meta.env.VITE_API_VERSION || 'v2';
const API_PREFIX = `/api/${API_VERSION}`;

// Create axios instance
const api = axios.create({
  baseURL: `${API_BASE_URL}/api/${API_VERSION}`,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// Types
export interface Song {
  id: string;
  name: string;
  artist: string;
  album: string;
  duration_ms: number;
  popularity: number;
  acousticness: number;
  danceability: number;
  energy: number;
  instrumentalness: number;
  liveness: number;
  loudness: number;
  speechiness: number;
  tempo: number;
  valence: number;
  key: number;
  mode: number;
  time_signature: number;
  cluster_id: number;
  preview_url?: string;
  spotify_url: string;
  album_image_url?: string;
  similarity_score?: number;
  release_date?: string;
  explicit?: boolean;
}

export interface ClusterInfo {
  id: number;
  name: string;
  size: number;
  cohesion_score: number;
  separation_score: number;
  dominant_genres: string[];
  dominant_features: string[];
  era?: string;
}

export interface ClusterResponse {
  id: number;
  name: string;
  description?: string;
  size: number;
  cohesion_score: number;
  separation_score: number;
  dominant_genres: string[];
  dominant_features: string[];
  era?: string;
  statistics: {
    total_tracks: number;
    avg_popularity: number;
    avg_energy: number;
    avg_valence: number;
    avg_danceability: number;
    avg_tempo: number;
    unique_artists: number;
  };
  sample_tracks: Song[];
  audio_stats?: any;
}

export interface RecommendationRequest {
  liked_song_ids: string[];
  n_recommendations?: number;
  recommendation_type?: string;
  filters?: any;
}

export interface RecommendationResponse {
  recommendations: Song[];
  recommendation_type: string;
  clusters_used: Array<{
    cluster_id: number;
    size: number;
    source_song: string;
  }>;
  total_found: number;
  processing_time_ms: number;
  timestamp: string;
}

export interface ModelComparisonRequest {
  liked_song_ids: string[];
  models_to_compare: string[];
  n_recommendations?: number;
}

export interface ModelComparisonResult {
  model_type: string;
  recommendations: Song[];
  processing_time_ms: number;
  total_found: number;
  error?: string;
}

export interface ModelComparisonResponse {
  query_songs: Song[];
  results: ModelComparisonResult[];
  total_processing_time_ms: number;
  timestamp: string;
}

// API Functions
export const apiService = {
  // Songs endpoints
  songs: {
    search: async (params: {
      query?: string;
      limit?: number;
      offset?: number;
      cluster_id?: number;
    }): Promise<Song[]> => {
      const response = await api.get('/songs/', { params: { q: params.query, limit: params.limit } });
      return response.data;
    },

    getById: async (id: string): Promise<Song> => {
      const response = await api.get(`/songs/${id}`);
      return response.data;
    },

    getRandom: async (params: {
      limit?: number;
      cluster_id?: number;
    }): Promise<Song[]> => {
      const response = await api.get('/songs/random/', { params });
      return response.data;
    },

    getByCluster: async (clusterId: number, params: {
      limit?: number;
      offset?: number;
    }): Promise<Song[]> => {
      const response = await api.get(`/songs/cluster/${clusterId}`, { params });
      return response.data;
    },

    getPopular: async (params: {
      limit?: number;
      min_popularity?: number;
    }): Promise<Song[]> => {
      const response = await api.get('/songs/popular/', { params });
      return response.data;
    },

    getOverview: async (): Promise<any> => {
      const response = await api.get('/songs/stats/overview');
      return response.data;
    },
  },

  // Clusters endpoints
  clusters: {
    getAll: async (params: {
      skip?: number;
      limit?: number;
      min_size?: number;
      sort_by?: string;
      order?: string;
    }): Promise<ClusterInfo[]> => {
      const response = await api.get('/clusters/', { params });
      return response.data;
    },

    getById: async (id: number, params: {
      include_tracks?: boolean;
      track_limit?: number;
    }): Promise<ClusterResponse> => {
      const response = await api.get(`/clusters/${id}`, { params });
      return response.data;
    },

    getTracks: async (id: number, params: {
      skip?: number;
      limit?: number;
      sort_by?: string;
      order?: string;
    }): Promise<any> => {
      const response = await api.get(`/clusters/${id}/tracks`, { params });
      return response.data;
    },
  },

  // Recommendations endpoints
  recommendations: {
    get: async (request: RecommendationRequest): Promise<RecommendationResponse> => {
      const response = await api.post('/recommendations/', request);
      return response.data;
    },

    getSimilar: async (songId: string, params: {
      n_recommendations?: number;
      recommendation_type?: string;
    }): Promise<RecommendationResponse> => {
      const response = await api.get(`/recommendations/similar/${songId}`, { params });
      return response.data;
    },

    getPreferences: async (request: any): Promise<any> => {
      const response = await api.post('/recommendations/preferences', request);
      return response.data;
    },

    submitFeedback: async (feedback: any): Promise<any> => {
      const response = await api.post('/recommendations/feedback', feedback);
      return response.data;
    },

    compare: async (request: ModelComparisonRequest): Promise<ModelComparisonResponse> => {
      const response = await api.post('/recommendations/compare', request);
      return response.data;
    },

    // Model management endpoints
    getAvailableModels: async (): Promise<any> => {
      const response = await api.get('/recommendations/models/available');
      return response.data;
    },

    getCurrentModel: async (): Promise<any> => {
      const response = await api.get('/recommendations/models/current');
      return response.data;
    },

    switchModel: async (modelName: string): Promise<any> => {
      const response = await api.post(`/recommendations/models/switch/${modelName}`);
      return response.data;
    },

    getArtistBased: async (request: RecommendationRequest): Promise<RecommendationResponse> => {
      const response = await api.post('/recommendations/artist-based', request);
      return response.data;
    },

    getGenreBased: async (request: RecommendationRequest): Promise<RecommendationResponse> => {
      const response = await api.post('/recommendations/genre-based', request);
      return response.data;
    },

    getHdbscanKnn: async (request: RecommendationRequest): Promise<RecommendationResponse> => {
      const response = await api.post('/recommendations/hdbscan-knn', request);
      return response.data;
    },
  },

  // Health check
  health: async (): Promise<any> => {
    const response = await api.get('/health');
    return response.data;
  },
};

export default apiService; 