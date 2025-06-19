# 🎵 Spotify Web API Integration Setup

## Important Update - November 27, 2024

**⚠️ Spotify API Changes:** As of November 27, 2024, Spotify has deprecated several key API endpoints for new applications:

### Deprecated Endpoints (No Longer Available)
- ❌ **Related Artists** (`/artists/{id}/related-artists`)
- ❌ **Recommendations** (`/recommendations`) 
- ❌ **Audio Features** (`/audio-features`)
- ❌ **Audio Analysis** (`/audio-analysis`)
- ❌ **Featured Playlists** (`/browse/featured-playlists`)
- ❌ **Category Playlists** (`/browse/categories/{id}/playlists`)
- ❌ **30-second Preview URLs** (in multi-get responses)

### Still Available Endpoints ✅
- ✅ **Get Artist** (`/artists/{id}`)
- ✅ **Get Album** (`/albums/{id}`)
- ✅ **Get Track** (`/tracks/{id}`)
- ✅ **Get Artist's Albums** (`/artists/{id}/albums`)
- ✅ **Search** (`/search`)
- ✅ **Basic track/artist/album metadata**

## Current Integration Features

Our Spotify API integration now provides:

### 🎤 Artist Information
- Artist details (name, followers, popularity, genres)
- Artist profile images
- Links to Spotify profiles

### 💿 Album Information  
- Album details (name, release date, label, popularity)
- Album cover artwork
- Track count and metadata

### 📀 Artist Discography
- Recent albums and singles
- Release dates and album types
- Links to albums on Spotify

## 📋 Prerequisites

- A Spotify account (free or premium)
- Access to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/applications)

## 🚀 Quick Setup

### Step 1: Create a Spotify App

1. **Login** to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/applications)
2. **Click** "Create an App"
3. **Fill out** the app form:
   - **App Name**: `Music Recommendation System` (or your preferred name)
   - **App Description**: `Streamlit app for music recommendations with enhanced Spotify features`
   - **Website**: `http://localhost:8501` (or your domain)
   - **Redirect URI**: `http://localhost:8501/callback`
4. **Accept** the Developer Terms of Service
5. **Click** "Create"

### Step 2: Get Your Credentials

1. **Copy** your `Client ID` from the app overview page
2. **Click** "Show Client Secret" and copy your `Client Secret`
3. ⚠️ **Keep your Client Secret private and secure!**

### Step 3: Configure the Application

Choose one of these methods to configure your credentials:

#### Option A: Environment Variables (Recommended)

Create a `.env` file in your project root:

```bash
# .env file
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
SPOTIFY_API_BASE_URL=https://api.spotify.com/v1
SPOTIFY_TOKEN_URL=https://accounts.spotify.com/api/token
SPOTIFY_REQUESTS_PER_SECOND=10
SPOTIFY_MAX_RETRIES=3
ENABLE_SPOTIFY_API=true
```

#### Option B: Streamlit Secrets

Add to your `.streamlit/secrets.toml` file:

```toml
[spotify]
spotify_client_id = "your_client_id_here"
spotify_client_secret = "your_client_secret_here"
```

### Step 4: Install Dependencies

The app uses standard Python libraries that should already be installed:
- `requests` for API calls
- `base64` for authentication encoding
- `datetime` for token management

### Step 5: Restart the Application

```bash
streamlit run streamlit_app/app.py
```

## ✨ Enhanced Features Available

Once configured, you'll have access to:

### 🎤 Artist Information
- Artist details (name, followers, popularity, genres)
- Artist profile images
- Links to Spotify profiles

### 💿 Album Information
- Album details (name, release date, label, popularity)
- Album cover artwork
- Track count and metadata

### 📀 Artist Discography
- Recent albums and singles
- Release dates and album types
- Links to albums on Spotify

## 🔧 Configuration Options

### Rate Limiting
```bash
SPOTIFY_REQUESTS_PER_SECOND=10  # Adjust for your usage
SPOTIFY_MAX_RETRIES=3           # API retry attempts
```

### Caching
```bash
SPOTIFY_TOKEN_CACHE_DURATION=3600  # Token cache (1 hour)
SPOTIFY_API_CACHE_DURATION=300     # API response cache (5 min)
```

### Feature Toggles
```bash
ENABLE_AUDIO_ANALYSIS=true
ENABLE_ARTIST_INFO=true
ENABLE_ALBUM_INFO=true
ENABLE_RELATED_TRACKS=true
```

## 🛠️ Troubleshooting

### Common Issues

#### ❌ "Spotify API credentials not configured"
- **Solution**: Check your `.env` file or Streamlit secrets
- **Verify**: Client ID and Secret are correctly set
- **Restart**: The Streamlit application

#### ❌ "Failed to get Spotify access token"
- **Check**: Client ID and Secret are valid
- **Verify**: No extra spaces in credentials
- **Try**: Regenerating credentials in Spotify Dashboard

#### ❌ "Rate limited by Spotify API"
- **Wait**: For the rate limit to reset
- **Adjust**: `SPOTIFY_REQUESTS_PER_SECOND` to a lower value
- **Note**: Free tier has stricter limits

#### ❌ Missing images or data
- **Reason**: Some tracks may not have complete metadata
- **Expected**: Normal behavior for older or less popular tracks
- **Fallback**: App continues to work with basic data

## 📊 API Usage and Limits

### Spotify Web API Limits
- **Rate Limit**: Varies by endpoint (typically 100 requests/minute)
- **Token Expiration**: 1 hour (automatically refreshed)
- **Request Size**: Individual track/artist requests

### App Optimization
- **Caching**: Responses cached for 5 minutes
- **Smart Requests**: Only fetches when enhanced features enabled
- **Rate Limiting**: Built-in delays between requests
- **Retry Logic**: Automatic retry with exponential backoff

## 🔒 Security Best Practices

### Credential Management
- ✅ **Use environment variables** or Streamlit secrets
- ✅ **Add .env to .gitignore**
- ✅ **Regenerate credentials** if compromised
- ❌ **Never commit secrets** to version control
- ❌ **Don't share credentials** in chat or email

### Production Deployment
- Use Streamlit Cloud secrets management
- Set up proper environment variable injection
- Monitor API usage and costs
- Implement proper error handling

## 📈 Monitoring and Analytics

### Available Metrics
- **API Response Times**: Built-in timing
- **Cache Hit Rates**: Streamlit cache statistics  
- **Error Rates**: Automatic error logging
- **Feature Usage**: Track which enhanced features are used

### Spotify Dashboard Analytics
- **Daily/Monthly Active Users**: View in Spotify Dashboard
- **API Request Volume**: Monitor usage patterns
- **Error Rates**: Track failed requests
- **Geographic Usage**: See where users access from

## 🎯 Example Enhanced Experience

### Before Spotify API Integration
```
🎵 Track: "Bohemian Rhapsody"
👤 Artist: Queen
⏱️ Duration: 5:55
🔥 Popularity: 87/100
```

### After Spotify API Integration
```
🎵 Track: "Bohemian Rhapsody"
👤 Artist: Queen (2.1M followers)
💿 Album: "A Night at the Opera" (1975)
⏱️ Duration: 5:55
🔥 Popularity: 87/100
🎼 Genres: Rock, Classic Rock, Glam Rock
🎤 Related Artists: David Bowie, Led Zeppelin, The Beatles
🎵 Artist Top Track: "Bohemian Rhapsody", "We Will Rock You"
🖼️ [Album Cover] [Artist Photo]
🔗 [Open in Spotify] [View Artist] [View Album]
```

## 🤝 Support

### Getting Help
- **Check**: This documentation first
- **Search**: Existing GitHub issues
- **Create**: New issue with detailed description
- **Include**: Error messages and configuration details

### Useful Links
- [Spotify Web API Documentation](https://developer.spotify.com/documentation/web-api)
- [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/applications)
- [Spotify Developer Community](https://community.spotify.com/t5/Spotify-for-Developers/bd-p/Spotify_Developer)
- [Rate Limiting Guidelines](https://developer.spotify.com/documentation/web-api/concepts/rate-limits)

---

🎵 **Enjoy your enhanced music recommendation experience!** 🎵 