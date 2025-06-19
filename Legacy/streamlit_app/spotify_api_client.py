"""
Spotify Web API Client for Enhanced Track Information
Integrates with existing dataset URLs to fetch additional data

Note: Updated for Spotify API changes as of November 27, 2024
Some endpoints (Related Artists, Audio Analysis, Audio Features) have been deprecated for new applications.
This client now only uses supported endpoints.
"""

import os
import requests
import streamlit as st
import base64
import time
from typing import Dict, Optional, Any
import json
from datetime import datetime, timedelta
import pandas as pd

# Import the advanced logging system
try:
    from logging_config import get_logger, log_spotify_api_call, log_user_action, log_performance
    logger = get_logger("spotify_api")
    ADVANCED_LOGGING = True
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    ADVANCED_LOGGING = False
    # Fallback functions if advanced logging not available
    def log_spotify_api_call(endpoint, success, response_time=None, details=None):
        pass
    def log_user_action(action, details=None):
        pass
    def log_performance(operation, duration, details=None):
        pass

class SpotifyAPIClient:
    """
    Spotify Web API Client for fetching enhanced track information
    Uses Client Credentials flow for app-only authentication
    """
    
    def __init__(self, client_id: str, client_secret: str):
        """Initialize the Spotify API client"""
        logger.info("Initializing Spotify API client")
        
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.token_expires_at = None
        self.base_url = "https://api.spotify.com/v1"
        
        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'SpotifyRecommendationSystem/1.0'
        })
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 10 requests per second max
        
        logger.debug(f"Spotify API client initialized with client_id: {client_id[:8]}...")
    
    def _get_client_credentials_token(self) -> bool:
        """Get access token using Client Credentials flow"""
        logger.info("Requesting new Spotify access token")
        start_time = time.time()
        
        try:
            # Prepare credentials
            auth_string = f"{self.client_id}:{self.client_secret}"
            auth_b64 = base64.b64encode(auth_string.encode()).decode()
            
            headers = {
                "Authorization": f"Basic {auth_b64}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            data = {"grant_type": "client_credentials"}
            
            response = self.session.post(
                "https://accounts.spotify.com/api/token",
                headers=headers,
                data=data,
                timeout=10
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data["access_token"]
                expires_in = token_data.get("expires_in", 3600)
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                # Update session headers
                self.session.headers.update({
                    "Authorization": f"Bearer {self.access_token}"
                })
                
                logger.info(f"Successfully obtained Spotify access token (expires in {expires_in}s)")
                log_spotify_api_call("token_request", True, response_time, {
                    'expires_in': expires_in,
                    'token_type': token_data.get('token_type', 'Bearer')
                })
                
                return True
            else:
                logger.error(f"Failed to get Spotify access token: {response.status_code} - {response.text}")
                log_spotify_api_call("token_request", False, response_time, {
                    'status_code': response.status_code,
                    'error': response.text[:200]
                })
                return False
                
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"Exception during token request: {e}")
            log_spotify_api_call("token_request", False, response_time, {
                'exception': str(e)
            })
            return False
    
    def _ensure_valid_token(self) -> bool:
        """Ensure we have a valid access token"""
        if (self.access_token is None or 
            self.token_expires_at is None or 
            datetime.now() >= self.token_expires_at - timedelta(minutes=5)):
            
            logger.debug("Token expired or missing, requesting new token")
            return self._get_client_credentials_token()
        
        return True
    
    def _rate_limit(self):
        """Simple rate limiting to avoid hitting API limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.3f}s")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint: str, max_retries: int = 3) -> Optional[Dict]:
        """Make a request to the Spotify API with error handling and retries"""
        if not self._ensure_valid_token():
            logger.error("Cannot make request: no valid token")
            return None
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        logger.debug(f"Making Spotify API request to: {endpoint}")
        
        for attempt in range(max_retries):
            self._rate_limit()
            start_time = time.time()
            
            try:
                response = self.session.get(url, timeout=10)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    logger.debug(f"Successful API call to {endpoint} in {response_time:.3f}s")
                    log_spotify_api_call(endpoint, True, response_time, {
                        'attempt': attempt + 1,
                        'response_size': len(str(data))
                    })
                    return data
                
                elif response.status_code == 404:
                    logger.warning(f"API endpoint {endpoint} returned 404 - likely deprecated")
                    log_spotify_api_call(endpoint, False, response_time, {
                        'status_code': 404,
                        'deprecated': True,
                        'attempt': attempt + 1
                    })
                    return None
                
                elif response.status_code == 429:
                    # Rate limited
                    retry_after = int(response.headers.get('Retry-After', 1))
                    logger.warning(f"Rate limited, waiting {retry_after}s before retry")
                    log_spotify_api_call(endpoint, False, response_time, {
                        'status_code': 429,
                        'retry_after': retry_after,
                        'attempt': attempt + 1
                    })
                    time.sleep(retry_after)
                    continue
                
                elif response.status_code == 401:
                    logger.warning("Token expired, requesting new token")
                    self.access_token = None
                    if not self._get_client_credentials_token():
                        logger.error("Failed to refresh token")
                        return None
                    continue
                
                else:
                    logger.warning(f"API call to {endpoint} failed: {response.status_code} - {response.text[:200]}")
                    log_spotify_api_call(endpoint, False, response_time, {
                        'status_code': response.status_code,
                        'error': response.text[:200],
                        'attempt': attempt + 1
                    })
                    
                    if attempt == max_retries - 1:
                        return None
                    
                    time.sleep(2 ** attempt)  # Exponential backoff
                
            except requests.exceptions.Timeout:
                response_time = time.time() - start_time
                logger.warning(f"Request to {endpoint} timed out (attempt {attempt + 1})")
                log_spotify_api_call(endpoint, False, response_time, {
                    'timeout': True,
                    'attempt': attempt + 1
                })
                
                if attempt == max_retries - 1:
                    return None
                time.sleep(2 ** attempt)
                
            except Exception as e:
                response_time = time.time() - start_time
                logger.error(f"Exception during API call to {endpoint}: {e}")
                log_spotify_api_call(endpoint, False, response_time, {
                    'exception': str(e),
                    'attempt': attempt + 1
                })
                
                if attempt == max_retries - 1:
                    return None
                time.sleep(2 ** attempt)
        
        logger.error(f"Failed to get response from {endpoint} after {max_retries} attempts")
        return None
    
    def get_artist_details(self, artist_id: str) -> Optional[Dict]:
        """Get detailed artist information (SUPPORTED endpoint)"""
        logger.debug(f"Getting artist details for ID: {artist_id}")
        
        if not artist_id:
            logger.warning("No artist ID provided")
            return None
        
        start_time = time.time()
        data = self._make_request(f"artists/{artist_id}")
        
        if data:
            processing_time = time.time() - start_time
            log_performance("get_artist_details", processing_time, {
                'artist_id': artist_id,
                'artist_name': data.get('name', 'Unknown'),
                'followers': data.get('followers', {}).get('total', 0)
            })
            
            logger.info(f"Retrieved artist details for '{data.get('name', 'Unknown')}' in {processing_time:.3f}s")
        
        return data
    
    def get_artist_albums(self, artist_id: str, limit: int = 10) -> Optional[Dict]:
        """Get artist's albums (SUPPORTED endpoint)"""
        logger.debug(f"Getting albums for artist ID: {artist_id}")
        
        if not artist_id:
            logger.warning("No artist ID provided")
            return None
        
        start_time = time.time()
        data = self._make_request(f"artists/{artist_id}/albums?limit={limit}&include_groups=album,single")
        
        if data:
            processing_time = time.time() - start_time
            num_albums = len(data.get('items', []))
            log_performance("get_artist_albums", processing_time, {
                'artist_id': artist_id,
                'num_albums': num_albums,
                'limit': limit
            })
            
            logger.info(f"Retrieved {num_albums} albums for artist {artist_id} in {processing_time:.3f}s")
        
        return data
    
    def get_album_details(self, album_id: str) -> Optional[Dict]:
        """Get detailed album information (SUPPORTED endpoint)"""
        logger.debug(f"Getting album details for ID: {album_id}")
        
        if not album_id:
            logger.warning("No album ID provided")
            return None
        
        start_time = time.time()
        data = self._make_request(f"albums/{album_id}")
        
        if data:
            processing_time = time.time() - start_time
            log_performance("get_album_details", processing_time, {
                'album_id': album_id,
                'album_name': data.get('name', 'Unknown'),
                'total_tracks': data.get('total_tracks', 0)
            })
            
            logger.info(f"Retrieved album details for '{data.get('name', 'Unknown')}' in {processing_time:.3f}s")
        
        return data
    
    def get_track_details(self, track_id: str) -> Optional[Dict]:
        """Get detailed track information (SUPPORTED endpoint)"""
        logger.debug(f"Getting track details for ID: {track_id}")
        
        if not track_id:
            logger.warning("No track ID provided")
            return None
        
        start_time = time.time()
        data = self._make_request(f"tracks/{track_id}")
        
        if data:
            processing_time = time.time() - start_time
            log_performance("get_track_details", processing_time, {
                'track_id': track_id,
                'track_name': data.get('name', 'Unknown'),
                'popularity': data.get('popularity', 0)
            })
            
            logger.info(f"Retrieved track details for '{data.get('name', 'Unknown')}' in {processing_time:.3f}s")
        
        return data
    
    def test_connection(self) -> bool:
        """Test the API connection"""
        logger.info("Testing Spotify API connection")
        start_time = time.time()
        
        success = self._ensure_valid_token()
        test_time = time.time() - start_time
        
        log_performance("test_connection", test_time, {
            'success': success,
            'has_token': self.access_token is not None
        })
        
        if success:
            logger.info(f"Spotify API connection test successful in {test_time:.3f}s")
        else:
            logger.error(f"Spotify API connection test failed in {test_time:.3f}s")
        
        return success

def create_spotify_client() -> Optional[SpotifyAPIClient]:
    """Create and configure Spotify API client from environment variables or Streamlit secrets"""
    logger.info("Creating Spotify API client")
    
    # Try environment variables first
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    
    # Fallback to Streamlit secrets
    if not client_id or not client_secret:
        try:
            logger.debug("Environment variables not found, trying Streamlit secrets")
            client_id = st.secrets["spotify"]["spotify_client_id"]
            client_secret = st.secrets["spotify"]["spotify_client_secret"]
            logger.debug("Successfully loaded credentials from Streamlit secrets")
        except Exception as e:
            logger.debug(f"Could not load from Streamlit secrets: {e}")
            client_id = None
            client_secret = None
    
    if not client_id or not client_secret:
        logger.warning("Spotify API credentials not found in environment variables or Streamlit secrets")
        return None
    
    try:
        client = SpotifyAPIClient(client_id, client_secret)
        
        # Test the connection
        if client.test_connection():
            logger.info("Spotify API client created and tested successfully")
            log_user_action("spotify_client_created", {
                'client_id_prefix': client_id[:8],
                'connection_test': True
            })
            return client
        else:
            logger.error("Spotify API client connection test failed")
            return None
            
    except Exception as e:
        logger.error(f"Failed to create Spotify API client: {e}")
        return None

def display_spotify_api_status(client: SpotifyAPIClient) -> bool:
    """Display Spotify API connection status in Streamlit"""
    logger.debug("Displaying Spotify API status")
    
    if client is None:
        st.error("❌ **Spotify API**: Not configured")
        st.info("💡 Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET environment variables or configure in .streamlit/secrets.toml")
        logger.info("Displayed Spotify API status: not configured")
        return False
    
    # Test connection
    if client.test_connection():
        st.success("✅ **Spotify API**: Connected and ready")
        st.info("🎵 Enhanced features available: Artist info, album details, discography")
        
        # Show API limitations
        st.warning("⚠️ **Limited Features**: Some endpoints deprecated as of Nov 2024")
        
        # Instead of nested expander, use markdown sections
        st.markdown("---")
        st.markdown("**📋 Available vs Deprecated Features**")
        st.markdown("""
        **✅ Available:**
        - Artist information & images
        - Album details & artwork  
        - Artist discography
        - Track metadata
        - External Spotify links
        
        **❌ Deprecated (Nov 27, 2024):**
        - Related artists discovery
        - Audio feature analysis  
        - Spotify recommendations
        - 30-second previews (new apps)
        """)
        
        logger.info("Displayed Spotify API status: connected")
        log_user_action("spotify_status_viewed", {
            'status': 'connected',
            'features_available': True
        })
        return True
    else:
        st.error("❌ **Spotify API**: Connection failed")
        st.info("🔧 Check your credentials and network connection")
        logger.info("Displayed Spotify API status: connection failed")
        log_user_action("spotify_status_viewed", {
            'status': 'failed',
            'features_available': False
        })
        return False

def display_enhanced_track_info(client: SpotifyAPIClient, track_data: Dict):
    """Display enhanced track information using Spotify API"""
    logger.info("Displaying enhanced track information")
    log_user_action("view_enhanced_track_info", {
        'track_name': track_data.get('name', 'Unknown')
    })
    
    if client is None:
        st.warning("Spotify API client not available")
        return
    
    # Extract Spotify ID from track data
    spotify_id = None
    
    # Method 1: Direct ID field (most reliable for our CSV data)
    if 'id' in track_data and track_data['id'] and not pd.isna(track_data['id']):
        spotify_id = str(track_data['id']).strip()
        logger.debug(f"Found Spotify ID from 'id' field: {spotify_id}")
    
    # Method 2: Extract from URI if ID not available
    elif 'uri' in track_data and track_data['uri'] and not pd.isna(track_data['uri']):
        uri = str(track_data['uri']).strip()
        if uri.startswith('spotify:track:'):
            spotify_id = uri.split(':')[-1]
            logger.debug(f"Extracted Spotify ID from URI: {spotify_id}")
    
    # Method 3: Extract from track_href as fallback
    elif 'track_href' in track_data and track_data['track_href'] and not pd.isna(track_data['track_href']):
        track_href = str(track_data['track_href']).strip()
        if '/tracks/' in track_href:
            spotify_id = track_href.split('/tracks/')[-1]
            logger.debug(f"Extracted Spotify ID from track_href: {spotify_id}")
    
    # Method 4: Legacy external_urls method (for backward compatibility)
    else:
        external_urls = track_data.get('external_urls', {})
        
        if isinstance(external_urls, str):
            try:
                external_urls = eval(external_urls) if external_urls.startswith('{') else {}
            except:
                external_urls = {}
        
        if isinstance(external_urls, dict) and 'spotify' in external_urls:
            spotify_url = external_urls['spotify']
            if '/track/' in spotify_url:
                spotify_id = spotify_url.split('/track/')[-1].split('?')[0]
                logger.debug(f"Extracted Spotify ID from external_urls: {spotify_id}")
    
    if not spotify_id:
        st.info("💡 No Spotify ID available for enhanced features")
        logger.debug("No Spotify ID found for enhanced features")
        logger.debug(f"Available track_data keys: {list(track_data.keys())}")
        return
    
    logger.info(f"Using Spotify ID: {spotify_id}")
    
    try:
        start_time = time.time()
        
        # Get track details
        track_details = client.get_track_details(spotify_id)
        
        if track_details:
            st.markdown("#### 🎵 Enhanced Track Information")
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                # Album artwork
                album_images = track_details.get('album', {}).get('images', [])
                if album_images:
                    image_url = album_images[0]['url']  # Largest image
                    st.image(image_url, width=200, caption="Album Artwork")
                    logger.debug("Displayed album artwork")
            
            with col2:
                # Track information
                album_info = track_details.get('album', {})
                artists_info = track_details.get('artists', [])
                
                st.markdown("**📀 Album Information:**")
                st.write(f"**Album**: {album_info.get('name', 'Unknown')}")
                st.write(f"**Release Date**: {album_info.get('release_date', 'Unknown')}")
                st.write(f"**Total Tracks**: {album_info.get('total_tracks', 'Unknown')}")
                
                if artists_info:
                    st.markdown("**👤 Artist Information:**")
                    for artist in artists_info[:3]:  # Show up to 3 artists
                        artist_name = artist.get('name', 'Unknown')
                        st.write(f"**Artist**: {artist_name}")
                        
                        # Get detailed artist info
                        artist_details = client.get_artist_details(artist['id'])
                        if artist_details:
                            followers = artist_details.get('followers', {}).get('total', 0)
                            genres = artist_details.get('genres', [])
                            popularity = artist_details.get('popularity', 0)
                            
                            st.write(f"**Followers**: {followers:,}")
                            st.write(f"**Popularity**: {popularity}/100")
                            if genres:
                                st.write(f"**Genres**: {', '.join(genres[:3])}")
                
                # External links
                external_urls = track_details.get('external_urls', {})
                if external_urls.get('spotify'):
                    st.markdown("**🔗 External Links:**")
                    st.markdown(f"[🎵 Listen on Spotify]({external_urls['spotify']})")
            
            # Artist discography (separate section)
            if artists_info:
                st.markdown("---")
                st.markdown("**📀 Artist Discography**")
                
                artist_id = artists_info[0]['id']  # Primary artist
                albums_data = client.get_artist_albums(artist_id, limit=10)
                
                if albums_data and albums_data.get('items'):
                    st.markdown("**Recent Albums & Singles:**")
                    
                    for album in albums_data['items'][:5]:  # Show top 5
                        album_name = album.get('name', 'Unknown')
                        release_date = album.get('release_date', 'Unknown')
                        album_type = album.get('album_type', 'album').title()
                        
                        st.markdown(f"- **{album_name}** ({album_type}, {release_date})")
                else:
                    st.info("No recent albums found")
            
            processing_time = time.time() - start_time
            logger.info(f"Enhanced track info displayed successfully in {processing_time:.3f}s")
            log_performance("display_enhanced_track_info", processing_time, {
                'spotify_id': spotify_id,
                'track_name': track_details.get('name', 'Unknown')
            })
            
        else:
            st.warning("⚠️ Could not fetch enhanced track information")
            logger.warning(f"Failed to fetch track details for Spotify ID: {spotify_id}")
    
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Error displaying enhanced track info: {e}")
        st.error(f"Error fetching enhanced information: {e}")
        log_performance("display_enhanced_track_info", processing_time, {
            'error': str(e),
            'spotify_id': spotify_id
        }) 