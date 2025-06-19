# Frontend Setup Guide

## Overview
This is the React frontend for the Spotify Music Recommendation System v2. It provides a modern, Spotify-like interface for exploring music clusters, viewing song recommendations, and playing audio previews.

## Features
- 🎵 **Music Exploration**: Browse songs organized by AI-powered clustering
- 🎨 **Spotify-like Design**: Modern, dark theme with smooth animations
- 🎧 **Audio Previews**: Play 30-second previews directly in the browser
- 📱 **Responsive Design**: Works on desktop, tablet, and mobile
- ⚡ **Real-time Data**: Connect to your backend API for live data
- 🔍 **Advanced Filtering**: Search and filter by clusters, genres, and audio features

## Prerequisites
- Node.js 18+ 
- npm or yarn
- Backend API running (see backend setup instructions)

## Installation

### 1. Install Dependencies
```bash
cd spotify_recommendation_system_v2/frontend
npm install
```

### 2. Environment Configuration
Create a `.env` file in the frontend directory:

```bash
# Backend API Configuration
VITE_BACKEND_URL=http://localhost:8000
VITE_API_VERSION=v2

# Spotify API Configuration (optional - for enhanced features)
VITE_SPOTIFY_CLIENT_ID=your_spotify_client_id_here
VITE_SPOTIFY_CLIENT_SECRET=your_spotify_client_secret_here

# Development Settings
VITE_NODE_ENV=development
```

### 3. Install Required Dependencies
The application requires these key dependencies:

```bash
# Core React dependencies (should already be in package.json)
npm install react@^18.3.1 react-dom@^18.3.1

# Routing
npm install react-router-dom@^6.28.0

# API and State Management
npm install axios@^1.7.9 @tanstack/react-query@^5.62.7

# UI and Animations
npm install framer-motion@^11.15.0 lucide-react@^0.468.0
npm install @heroicons/react@^2.2.0 @headlessui/react@^2.2.0
npm install clsx@^2.1.1

# TypeScript types
npm install --save-dev @types/react@^18.3.17 @types/react-dom@^18.3.5

# Tailwind CSS (should already be configured)
npm install --save-dev tailwindcss@^4.0.0 @tailwindcss/vite@^4.0.0
```

## Development

### Start Development Server
```bash
npm run dev
```

The application will be available at `http://localhost:5173`

### Available Scripts
- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm run lint:fix` - Fix ESLint errors
- `npm run format` - Format code with Prettier
- `npm run type-check` - Run TypeScript type checking

## Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── SongCard.tsx     # Individual song display component
│   ├── ClusterCard.tsx  # Music cluster display component
│   ├── Navbar.tsx       # Navigation component
│   └── Sidebar.tsx      # Sidebar navigation
├── services/            # API and external services
│   ├── api.ts           # Backend API client
│   └── spotify.ts       # Spotify-specific utilities
├── hooks/               # Custom React hooks
│   └── useAudioPlayer.ts # Audio playback management
├── pages/               # Page components
│   └── Home.tsx         # Home page component
├── utils/               # Utility functions
├── types/               # TypeScript type definitions
└── App.tsx              # Main application component
```

## Key Components

### ExplorePage
The main exploration interface with:
- **Cluster View**: Browse music clusters with genre tags and statistics
- **Song View**: View songs in grid or list layout
- **Audio Playback**: Play 30-second previews
- **Interactive Controls**: Like songs, switch views, filter content

### SongCard Component
Displays individual songs with:
- Album artwork (from dataset or Spotify API)
- Play/pause controls with hover effects
- Audio feature visualization (energy, valence, danceability)
- Popularity indicators
- Like/unlike functionality

### ClusterCard Component
Shows music cluster information:
- Cluster statistics and cohesion scores
- Dominant genres and audio features
- Visual indicators and gradients
- Click-to-explore functionality

## API Integration

### Backend Connection
The frontend connects to your Python backend via:
- **Songs API**: Get songs, search, random songs, cluster songs
- **Clusters API**: Get all clusters, cluster details, cluster tracks
- **Recommendations API**: Get personalized recommendations

### Data Flow
1. **Clusters**: Load from `/api/v2/clusters/`
2. **Songs**: Load from `/api/v2/songs/` with various filters
3. **Audio Features**: Display from song data (energy, valence, etc.)
4. **Album Art**: Use URLs from dataset or fallback to placeholder

## Spotify Integration

### Album Artwork
- Primary source: URLs from your dataset
- Fallback: Spotify Web API (if credentials provided)
- Default: Placeholder images for missing artwork

### Audio Previews
- 30-second preview URLs from your dataset
- Built-in audio player with controls
- Automatic fallback for songs without previews

### External Links
- "Open in Spotify" buttons link to Spotify Web Player
- Deep links work on mobile Spotify app

## Customization

### Styling
The app uses Tailwind CSS with a custom dark theme:
- Green accent color (`text-green-400`, `bg-green-500`)
- Dark backgrounds with transparency effects
- Smooth animations and hover effects

### Theme Colors
- Primary: Green (`#22c55e`)
- Background: Dark gray (`#1f2937`, `#111827`)
- Text: White/Gray scale
- Accents: Various colors for audio features

### Adding New Features
1. Create new components in `/components/`
2. Add API endpoints in `/services/api.ts`
3. Update routing in `App.tsx`
4. Add new hooks in `/hooks/` for complex state

## Troubleshooting

### Common Issues

1. **CORS Errors**
   - Ensure backend allows frontend origin
   - Check backend CORS configuration

2. **Missing Dependencies**
   - Run `npm install` to install all dependencies
   - Check package.json for version mismatches

3. **API Connection Issues**
   - Verify backend is running on correct port
   - Check `.env` file for correct `VITE_BACKEND_URL`

4. **Audio Playback Issues**
   - Ensure preview URLs are valid in dataset
   - Check browser console for CORS or network errors

5. **TypeScript Errors**
   - Run `npm run type-check` to identify issues
   - Ensure all dependencies have proper type definitions

### Environment Variables
Make sure these are set in your `.env` file:
- `VITE_BACKEND_URL`: Your backend API URL
- `VITE_API_VERSION`: API version (usually 'v2')

### Performance Tips
- Use React Query for efficient data caching
- Implement pagination for large song lists
- Use React.memo() for expensive components
- Optimize images with proper sizing

## Production Deployment

### Build for Production
```bash
npm run build
```

### Environment Variables for Production
Update `.env` or set environment variables:
```bash
VITE_BACKEND_URL=https://your-api-domain.com
VITE_SPOTIFY_CLIENT_ID=your_production_client_id
```

### Deployment Options
- **Vercel**: `vercel --prod`
- **Netlify**: `netlify deploy --prod`
- **Docker**: Use provided Dockerfile
- **Static Hosting**: Deploy `dist/` folder

## Contributing
1. Follow the existing code style
2. Add TypeScript types for new features
3. Write component tests when adding new functionality
4. Update this README when adding new features

## Support
For issues or questions:
1. Check the console for error messages
2. Verify all dependencies are installed
3. Ensure backend API is running and accessible
4. Check environment variables are set correctly 