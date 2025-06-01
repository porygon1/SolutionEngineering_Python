import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import pickle
from sklearn.neighbors import NearestNeighbors
import warnings
import ast
warnings.filterwarnings('ignore')

# Set page configuration
st.set_page_config(
    page_title="🎵 Spotify Music Recommendation System",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .recommendation-card {
        background-color: #ffffff;
        border: 2px solid #e0e0e0;
        border-radius: 12px;
        padding: 20px;
        margin: 15px 0;
        border-left: 6px solid #1DB954;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        color: #2c3e50;
    }
    
    .recommendation-card h5 {
        color: #1DB954;
        font-weight: bold;
        margin-bottom: 10px;
        font-size: 16px;
    }
    
    .recommendation-card p {
        color: #34495e;
        margin: 5px 0;
        font-size: 14px;
        line-height: 1.4;
    }
    
    .recommendation-card strong {
        color: #2c3e50;
        font-weight: 600;
    }
    
    .feature-set-header {
        background: linear-gradient(135deg, #1DB954, #1ed760);
        color: white;
        padding: 15px;
        border-radius: 8px;
        text-align: center;
        margin: 15px 0;
        box-shadow: 0 4px 12px rgba(29, 185, 84, 0.3);
    }
    
    .feature-set-header h4 {
        margin: 0;
        font-weight: bold;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
    }
    
    .metric-card {
        background-color: #2c3e50;
        color: white;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    }
    
    .stSelectbox > div > div {
        background-color: white;
        color: #2c3e50;
    }
    
    .stTextInput > div > div > input {
        background-color: white;
        color: #2c3e50;
    }
</style>
""", unsafe_allow_html=True)

# Page title
st.title("🎵 Spotify Music Recommendation System")
st.markdown("**HDBSCAN Clustering with KNN-Based Song Discovery**")

# Define paths to data files
DATA_PATH = "/app/data"
RAW_DATA_PATH = os.path.join(DATA_PATH, "raw")
MODELS_PATH = os.path.join(DATA_PATH, "models")

# File paths
TRACKS_CSV = os.path.join(RAW_DATA_PATH, "spotify_tracks.csv")
ARTISTS_CSV = os.path.join(RAW_DATA_PATH, "spotify_artists.csv")
AUDIO_CSV = os.path.join(RAW_DATA_PATH, "low_level_audio_features.csv")

# Model paths (only for existing models)
MODEL_PATHS = {
    "hdbscan": os.path.join(MODELS_PATH, "hdbscan_model.pkl"),
    "knn": os.path.join(MODELS_PATH, "knn_model.pkl"),
    "embeddings": os.path.join(MODELS_PATH, "audio_embeddings.pkl"),
    "labels": os.path.join(MODELS_PATH, "cluster_labels.pkl"),
    "song_indices": os.path.join(MODELS_PATH, "song_indices.pkl")
}

@st.cache_data
def load_data(file_path):
    """Load and cache data"""
    try:
        return pd.read_csv(file_path)
    except Exception as e:
        st.error(f"Error loading data from {file_path}: {e}")
        return pd.DataFrame()

@st.cache_resource
def load_model(model_path):
    """Load and cache model"""
    try:
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        return model
    except Exception as e:
        st.error(f"Error loading model from {model_path}: {e}")
        return None

@st.cache_resource
def load_all_models():
    """Load all available recommendation models"""
    models = {}
    
    # Check if models directory exists
    if not os.path.exists(MODELS_PATH):
        return None
    
    for model_name, path in MODEL_PATHS.items():
        if os.path.exists(path):
            models[model_name] = load_model(path)
            st.success(f"✅ Loaded {model_name}")
        else:
            st.warning(f"⚠️ Model {model_name} not found at {path}")
            models[model_name] = None
    
    return models

def get_recommendations_within_cluster(knn_model, embeddings, labels, song_idx, n_neighbors=6):
    """Get song recommendations within the same cluster using KNN model"""
    if knn_model is None or embeddings is None or labels is None:
        return None, None
    
    try:
        # Get the cluster label for the selected song
        cluster_id = labels[song_idx]
        
        # Find all songs in the same cluster
        cluster_mask = np.array(labels) == cluster_id
        cluster_indices = np.where(cluster_mask)[0]
        
        # If cluster has fewer songs than requested neighbors, adjust
        n_neighbors = min(n_neighbors, len(cluster_indices))
        
        if n_neighbors <= 1:
            return None, None
        
        # Get embeddings for songs in the same cluster
        cluster_embeddings = embeddings[cluster_mask]
        
        # Create KNN model for this cluster
        cluster_knn = NearestNeighbors(n_neighbors=n_neighbors, metric='euclidean')
        cluster_knn.fit(cluster_embeddings)
        
        # Find position of selected song within cluster
        song_cluster_idx = np.where(cluster_indices == song_idx)[0][0]
        
        # Get recommendations within cluster
        distances, local_indices = cluster_knn.kneighbors(
            cluster_embeddings[song_cluster_idx].reshape(1, -1), 
            n_neighbors=n_neighbors
        )
        
        # Convert local indices back to global indices
        global_indices = cluster_indices[local_indices[0]]
        
        return distances[0], global_indices
    except Exception as e:
        st.error(f"Error getting cluster recommendations: {e}")
        return None, None

def get_global_recommendations(knn_model, embeddings, song_idx, n_neighbors=6):
    """Get song recommendations from entire dataset using pre-trained KNN model"""
    if knn_model is None or embeddings is None:
        return None, None
    
    try:
        # Get the embedding for the selected song
        song_embedding = embeddings[song_idx].reshape(1, -1)
        
        # Find nearest neighbors
        distances, indices = knn_model.kneighbors(song_embedding, n_neighbors=n_neighbors)
        
        return distances[0], indices[0]
    except Exception as e:
        st.error(f"Error getting global recommendations: {e}")
        return None, None

def check_audio_url(url):
    """Check if an audio URL is valid and accessible"""
    if pd.isna(url) or url == '' or url == 'None' or url is None:
        return False
    
    try:
        # Just check if it's a valid URL format
        return url.startswith('http') and 'spotify' in url
    except:
        return False

def display_audio_player(track_data, title="🎵 Audio Preview", artist_mapping=None):
    """Display an audio player for a track with preview URL"""
    preview_url = track_data.get('preview_url', '')
    
    if check_audio_url(preview_url):
        st.markdown(f"### {title}")
        
        # Display track info with audio player
        artist_name = get_artist_name(track_data.get('artists_id', ''), artist_mapping)
        
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #1DB954, #1ed760);
            color: white;
            padding: 15px;
            border-radius: 10px;
            margin: 10px 0;
            box-shadow: 0 4px 12px rgba(29, 185, 84, 0.3);
        ">
            <h4 style="margin: 0 0 5px 0;">🎵 {track_data.get('name', 'Unknown Track')}</h4>
            <p style="margin: 0; opacity: 0.9;">👤 {artist_name}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Streamlit's built-in audio player
        st.audio(preview_url, format='audio/mp3')
        
        return True
    else:
        st.warning(f"⚠️ No audio preview available for: **{track_data.get('name', 'Unknown Track')}**")
        return False

def display_song_info_with_audio(tracks_df, song_idx, artist_mapping):
    """Display information about the selected song with audio player"""
    selected_song = tracks_df.iloc[song_idx]
    
    st.markdown("### 🎵 Selected Song")
    
    # Create a nice card for the selected song
    artist_name = get_artist_name(selected_song['artists_id'], artist_mapping)
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #f8f9fa, #e9ecef);
        border: 2px solid #1DB954;
        border-radius: 15px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: 0 4px 12px rgba(29, 185, 84, 0.2);
    ">
        <h4 style="color: #1DB954; margin: 0 0 10px 0; font-size: 20px;">
            🎵 {selected_song['name']}
        </h4>
        <p style="color: #6c757d; margin: 5px 0; font-size: 16px;">
            <strong>Artist:</strong> {artist_name}
        </p>
        <p style="color: #495057; margin: 5px 0; font-size: 14px;">
            <strong>Popularity:</strong> 
            <span style="color: #e74c3c; font-weight: bold;">
                {selected_song.get('popularity', 'N/A')}
            </span>
        </p>
        <p style="color: #495057; margin: 5px 0; font-size: 14px;">
            <strong>Duration:</strong> 
            <span style="color: #17a2b8;">
                {format_duration(selected_song.get('duration_ms', 0))}
            </span>
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Display audio player for selected song
    display_audio_player(selected_song, "🎧 Listen to Selected Song", artist_mapping)

def format_duration(duration_ms):
    """Format duration from milliseconds to MM:SS format"""
    if pd.isna(duration_ms) or duration_ms == 0:
        return "Unknown"
    
    try:
        duration_seconds = int(duration_ms) // 1000
        minutes = duration_seconds // 60
        seconds = duration_seconds % 60
        return f"{minutes}:{seconds:02d}"
    except:
        return "Unknown"

def display_recommendations_with_audio(tracks_df, rec_indices, rec_distances, title, description, artist_mapping):
    """Display recommendations in a formatted way with audio players"""
    st.markdown(f"<div class='feature-set-header'><h4>{title}</h4></div>", unsafe_allow_html=True)
    st.markdown(f"*{description}*")
    
    if rec_indices is None or rec_distances is None:
        st.error("Unable to generate recommendations")
        return
    
    # Skip the first result if it's the same song
    start_idx = 1 if len(rec_indices) > 1 and rec_indices[0] == tracks_df.index[0] else 0
    
    # Display recommendations with audio
    for j, (idx, distance) in enumerate(zip(rec_indices[start_idx:], rec_distances[start_idx:])):
        if j >= 5:  # Limit to 5 recommendations
            break
            
        rec_song = tracks_df.iloc[idx]
        similarity_score = 1 - distance  # Convert distance to similarity
        artist_name = get_artist_name(rec_song['artists_id'], artist_mapping)
        
        # Create expandable section for each recommendation
        with st.expander(f"🎵 #{j+1} {rec_song['name']} - {artist_name} (Similarity: {similarity_score:.3f})"):
            
            # Display track details
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"""
                <div class='recommendation-card'>
                    <h5>🎵 {rec_song['name']}</h5>
                    <p><strong>Artist:</strong> <span style="color: #555;">{artist_name}</span></p>
                    <p><strong>Similarity:</strong> <span style="color: #1DB954; font-weight: bold;">{similarity_score:.3f}</span></p>
                    <p><strong>Popularity:</strong> <span style="color: #e74c3c; font-weight: bold;">{rec_song.get('popularity', 'N/A')}</span></p>
                    <p><strong>Duration:</strong> <span style="color: #17a2b8;">{format_duration(rec_song.get('duration_ms', 0))}</span></p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                # Audio features comparison
                features_to_show = ['danceability', 'energy', 'valence', 'acousticness']
                feature_values = []
                
                for feature in features_to_show:
                    value = rec_song.get(feature, 0)
                    if pd.notna(value):
                        feature_values.append(f"**{feature.title()}:** {value:.2f}")
                
                if feature_values:
                    st.markdown("**Audio Features:**")
                    for feature_val in feature_values:
                        st.markdown(f"- {feature_val}")
            
            # Display audio player for this recommendation
            display_audio_player(rec_song, f"🎧 Preview #{j+1}", artist_mapping)
    
    # Similarity visualization
    st.markdown("#### 📊 Similarity Scores Comparison")
    display_indices = rec_indices[start_idx:start_idx+5]  # Limit to 5 for visualization
    display_distances = rec_distances[start_idx:start_idx+5]
    
    # Create labels with song name and artist
    chart_labels = []
    for idx in display_indices:
        song = tracks_df.iloc[idx]
        artist_name = get_artist_name(song['artists_id'], artist_mapping)
        label = f"{song['name'][:15]}... - {artist_name[:15]}..."
        chart_labels.append(label)
    
    fig = px.bar(
        x=chart_labels,
        y=[1 - d for d in display_distances],
        title=f"Recommendation Similarity - {title}",
        labels={'x': 'Recommended Songs', 'y': 'Similarity Score'},
        color_discrete_sequence=['#1DB954']
    )
    fig.update_layout(height=400, xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

@st.cache_data
def create_artist_mapping(artists_df):
    """Create a mapping from artist ID to artist name"""
    if artists_df.empty:
        return {}
    
    # Create mapping from id to name
    artist_mapping = {}
    if 'id' in artists_df.columns and 'name' in artists_df.columns:
        artist_mapping = dict(zip(artists_df['id'], artists_df['name']))
    
    return artist_mapping

def get_artist_name(artist_id, artist_mapping):
    """Get artist name from artist ID using the mapping"""
    if pd.isna(artist_id) or artist_id == '' or artist_mapping is None:
        return "Unknown Artist"
    
    try:
        # Handle string representation of Python list format like "['3mxJuHRn2ZWD5OofvJtDZY']"
        if isinstance(artist_id, str) and artist_id.startswith('[') and artist_id.endswith(']'):
            # Parse the string as a Python list
            artist_ids = ast.literal_eval(artist_id)
        elif isinstance(artist_id, str) and ',' in artist_id:
            # Handle comma-separated IDs
            artist_ids = [aid.strip() for aid in artist_id.split(',')]
        else:
            # Single artist ID
            artist_ids = [artist_id]
        
        # Get names for all artist IDs
        artist_names = []
        for aid in artist_ids:
            if aid and aid in artist_mapping:
                name = artist_mapping[aid]
                # Ensure the name is a string and not None
                if name and isinstance(name, str):
                    artist_names.append(name)
                else:
                    artist_names.append(f"Unknown ({aid})")
            else:
                artist_names.append(f"Unknown ({aid})")
        
        # Ensure we have at least one name and all are strings
        if not artist_names:
            return "Unknown Artist"
        
        # Filter out any None values and ensure all are strings
        valid_names = [str(name) for name in artist_names if name is not None]
        
        return ", ".join(valid_names) if valid_names else "Unknown Artist"
        
    except (ValueError, SyntaxError, TypeError) as e:
        # If parsing fails, return a safe fallback
        return f"Unknown Artist"

def create_searchable_song_index(tracks_df, artist_mapping):
    """Create a searchable index for songs with artist names resolved"""
    search_index = tracks_df[['name', 'artists_id', 'popularity']].copy()
    
    # Add resolved artist names
    search_index['artist_name'] = search_index['artists_id'].apply(
        lambda x: get_artist_name(x, artist_mapping)
    )
    
    # Create searchable text combining song name and artist
    search_index['search_text'] = (
        search_index['name'].astype(str) + " " + 
        search_index['artist_name'].astype(str)
    ).str.lower()
    
    # Create display name for dropdown
    search_index['display_name'] = (
        search_index['name'].astype(str) + " - " + 
        search_index['artist_name'].astype(str)
    )
    
    return search_index

def fuzzy_search_songs(search_term, search_index, max_results=50):
    """Perform fuzzy search on songs with scoring"""
    if not search_term or len(search_term.strip()) < 2:
        return search_index.head(max_results)
    
    search_term = search_term.lower().strip()
    
    # Split search term into words for better matching
    search_words = search_term.split()
    
    # Calculate relevance scores
    scores = []
    for idx, row in search_index.iterrows():
        search_text = row['search_text']
        score = 0
        
        # Exact match gets highest score
        if search_term in search_text:
            score += 100
            
        # Bonus for matching at start of song name or artist
        song_name_lower = row['name'].lower()
        artist_name_lower = row['artist_name'].lower()
        
        if song_name_lower.startswith(search_term):
            score += 80
        elif artist_name_lower.startswith(search_term):
            score += 70
            
        # Word-by-word matching
        for word in search_words:
            if word in search_text:
                score += 20
                if word in song_name_lower:
                    score += 10  # Bonus for song name match
                if word in artist_name_lower:
                    score += 8   # Bonus for artist match
        
        # Popularity bonus (scaled)
        popularity = row.get('popularity', 0)
        if pd.notna(popularity):
            score += popularity * 0.1
            
        scores.append((idx, score))
    
    # Sort by score and return top results
    scores.sort(key=lambda x: x[1], reverse=True)
    top_indices = [idx for idx, score in scores[:max_results] if score > 0]
    
    return search_index.loc[top_indices]

def create_song_search_interface(tracks_df, search_index):
    """Create enhanced song search interface"""
    st.sidebar.markdown("### 🎵 Song Search & Selection")
    
    # Search input with help text
    search_term = st.sidebar.text_input(
        "🔍 Search for songs:",
        placeholder="Enter song name, artist, or both...",
        help="Search by song title, artist name, or both. Try 'Bohemian Rhapsody', 'Queen', or 'Queen Bohemian'"
    )
    
    # Search results
    if search_term and len(search_term.strip()) >= 2:
        with st.sidebar.container():
            st.markdown("**🔎 Search Results:**")
            
            # Perform search
            search_results = fuzzy_search_songs(search_term, search_index, max_results=50)
            
            if not search_results.empty:
                # Show number of results
                st.caption(f"Found {len(search_results)} matches")
                
                # Create options for selectbox
                search_options = []
                for idx, row in search_results.head(20).iterrows():  # Limit to top 20 for UI
                    popularity_indicator = "🔥" if row.get('popularity', 0) > 70 else "⭐" if row.get('popularity', 0) > 40 else ""
                    option_text = f"{row['display_name']} {popularity_indicator}"
                    search_options.append((option_text, idx))
                
                # Selection dropdown
                if search_options:
                    selected_option = st.sidebar.selectbox(
                        "Select a song:",
                        options=[opt[0] for opt in search_options],
                        key="song_search_select"
                    )
                    
                    # Get the selected index
                    selected_idx = next(opt[1] for opt in search_options if opt[0] == selected_option)
                    
                    # Show preview of selected song
                    selected_song = tracks_df.loc[selected_idx]
                    with st.sidebar.expander("📖 Song Preview", expanded=False):
                        st.write(f"**Song:** {selected_song['name']}")
                        st.write(f"**Artist:** {search_index.loc[selected_idx, 'artist_name']}")
                        if 'popularity' in selected_song and pd.notna(selected_song['popularity']):
                            st.write(f"**Popularity:** {selected_song['popularity']}/100")
                        if 'duration_ms' in selected_song and pd.notna(selected_song['duration_ms']):
                            duration = format_duration(selected_song['duration_ms'])
                            st.write(f"**Duration:** {duration}")
                    
                    return selected_idx
                else:
                    st.sidebar.warning("No valid search results found.")
                    return None
            else:
                st.sidebar.warning(f"No songs found matching '{search_term}'")
                st.sidebar.info("💡 Try searching with different keywords or check spelling")
                return None
    
    elif search_term and len(search_term.strip()) < 2:
        st.sidebar.info("Please enter at least 2 characters to search")
        return None
    
    else:
        # No search term - show popular songs and random option
        st.sidebar.markdown("**🎲 Quick Options:**")
        
        col1, col2 = st.sidebar.columns(2)
        
        with col1:
            if st.button("🎲 Random Song", use_container_width=True):
                return np.random.randint(0, len(tracks_df))
        
        with col2:
            if st.button("🔥 Popular Song", use_container_width=True):
                # Get a random popular song (popularity > 60)
                popular_songs = search_index[search_index['popularity'] > 60]
                if not popular_songs.empty:
                    return popular_songs.sample(1).index[0]
                else:
                    return np.random.randint(0, len(tracks_df))
        
        # Show some popular suggestions
        with st.sidebar.expander("💡 Song Suggestions", expanded=False):
            popular_songs = search_index.nlargest(10, 'popularity')
            st.markdown("**Popular tracks to try:**")
            for _, row in popular_songs.head(5).iterrows():
                if st.button(f"🎵 {row['name'][:20]}{'...' if len(row['name']) > 20 else ''}", 
                           key=f"suggest_{row.name}", use_container_width=True):
                    return row.name
        
        return None

def create_advanced_search_interface(search_index):
    """Create advanced search filters"""
    with st.sidebar.expander("🔧 Advanced Search Filters", expanded=False):
        st.markdown("**Filter by popularity:**")
        popularity_range = st.slider(
            "Popularity Range",
            min_value=0,
            max_value=100,
            value=(0, 100),
            help="Filter songs by their popularity score"
        )
        
        # Artist filter
        st.markdown("**Filter by artist (partial name):**")
        artist_filter = st.text_input(
            "Artist contains:",
            placeholder="e.g., Beatles, Taylor",
            help="Show only songs from artists containing this text"
        )
        
        # Apply filters
        filtered_index = search_index.copy()
        
        # Apply popularity filter
        filtered_index = filtered_index[
            (filtered_index['popularity'] >= popularity_range[0]) & 
            (filtered_index['popularity'] <= popularity_range[1])
        ]
        
        # Apply artist filter
        if artist_filter:
            filtered_index = filtered_index[
                filtered_index['artist_name'].str.contains(artist_filter, case=False, na=False)
            ]
        
        # Show filter results
        if len(filtered_index) != len(search_index):
            st.info(f"Filters applied: {len(filtered_index):,} of {len(search_index):,} songs match")
            
            if len(filtered_index) > 0:
                # Quick select from filtered results
                if st.button("🎲 Random from Filtered", use_container_width=True):
                    return filtered_index.sample(1).index[0]
        
        return filtered_index if len(filtered_index) != len(search_index) else None

def main():
    """Main application function"""
    
    # Sidebar controls
    st.sidebar.header("🎛️ Recommendation Controls")
    
    # Audio Settings
    with st.sidebar.expander("🔊 Audio Settings"):
        st.markdown("**Audio Preview Information:**")
        st.info("🎵 30-second previews from Spotify")
        st.markdown("- Click ▶️ to play audio previews")
        st.markdown("- Compare selected song with recommendations")
        st.markdown("- Some tracks may not have preview URLs")
        
        auto_play = st.checkbox("🎯 Focus on audio comparison", value=True, 
                               help="Expand recommendations with audio for easy comparison")
    
    # Load data
    with st.spinner("Loading track data..."):
        tracks_df = load_data(TRACKS_CSV)
        
    if tracks_df.empty:
        st.error("Cannot load track data. Please ensure the data files are available.")
        return

    # Load artists data
    with st.spinner("Loading artist data..."):
        artists_df = load_data(ARTISTS_CSV)
        artist_mapping = create_artist_mapping(artists_df)
        
    if not artist_mapping:
        st.warning("Could not load artist mapping. Artist names may not display correctly.")
    else:
        st.success(f"✅ Loaded {len(artist_mapping)} artist mappings")
    
    # Create searchable index
    with st.spinner("Creating search index..."):
        search_index = create_searchable_song_index(tracks_df, artist_mapping)
    
    # Load models
    with st.spinner("Loading recommendation models..."):
        models = load_all_models()
        
    if models is None:
        st.error("Cannot load models. Please ensure the models are exported to the data/models directory.")
        st.info("Run the HDBSCAN notebook to generate the required models.")
        return
    
    # Check if essential models are available
    essential_models = ['knn', 'embeddings']
    missing_models = [m for m in essential_models if models.get(m) is None]
    
    if missing_models:
        st.error(f"Missing essential models: {missing_models}")
        st.info("Please ensure all required models are exported from the HDBSCAN notebook.")
        return
    
    st.success(f"✅ Successfully loaded recommendation system!")
    
    # Sidebar controls
    n_recommendations = st.sidebar.slider(
        "Number of Recommendations", 
        min_value=3, 
        max_value=10, 
        value=5
    )
    
    # Enhanced song search interface
    selected_idx = create_song_search_interface(tracks_df, search_index)
    
    # Advanced search filters
    filtered_search_result = create_advanced_search_interface(search_index)
    if filtered_search_result is not None and selected_idx is None:
        selected_idx = filtered_search_result
    
    # Fallback to first song if no selection
    if selected_idx is None:
        selected_idx = 0
        st.sidebar.info("💡 Using first song as default. Try searching above!")
    
    # Display current selection info in sidebar
    if selected_idx is not None:
        selected_song_info = tracks_df.iloc[selected_idx]
        selected_artist = get_artist_name(selected_song_info['artists_id'], artist_mapping)
        
        with st.sidebar.container():
            st.markdown("---")
            st.markdown("**🎵 Currently Selected:**")
            st.markdown(f"**{selected_song_info['name']}**")
            st.markdown(f"*by {selected_artist}*")
            
            # Quick stats
            if 'popularity' in selected_song_info and pd.notna(selected_song_info['popularity']):
                popularity = selected_song_info['popularity']
                popularity_color = "🔥" if popularity > 70 else "⭐" if popularity > 40 else "📻"
                st.markdown(f"{popularity_color} Popularity: {popularity}/100")
    
    # Display selected song info
    display_song_info_with_audio(tracks_df, selected_idx, artist_mapping)
    
    # Quick Audio Comparison Section
    if auto_play:
        st.markdown("---")
        st.markdown("### 🎧 Quick Audio Comparison")
        st.markdown("*Listen to your selected song and top recommendations side-by-side*")
        
        # Get a few quick recommendations for comparison
        with st.spinner("Generating quick recommendations for audio comparison..."):
            quick_distances, quick_indices = get_global_recommendations(
                models['knn'], 
                models['embeddings'], 
                selected_idx, 
                4  # Just get 3 recommendations + original
            )
        
        if quick_distances is not None and quick_indices is not None:
            # Skip the first result if it's the same song
            start_idx_quick = 1 if len(quick_indices) > 1 else 0
            
            st.markdown("#### 🔀 Top 3 Similar Songs")
            comparison_cols = st.columns(3)
            
            for i, (idx, distance) in enumerate(zip(quick_indices[start_idx_quick:start_idx_quick+3], 
                                                   quick_distances[start_idx_quick:start_idx_quick+3])):
                rec_song = tracks_df.iloc[idx]
                similarity_score = 1 - distance
                artist_name = get_artist_name(rec_song['artists_id'], artist_mapping)
                
                with comparison_cols[i]:
                    st.markdown(f"""
                    <div style="
                        background: #f8f9fa;
                        border: 1px solid #1DB954;
                        border-radius: 8px;
                        padding: 10px;
                        margin: 5px 0;
                        text-align: center;
                    ">
                        <h6 style="color: #1DB954; margin: 0;">{rec_song['name'][:20]}{'...' if len(rec_song['name']) > 20 else ''}</h6>
                        <p style="margin: 5px 0; font-size: 12px; color: #666;">{artist_name[:20]}{'...' if len(artist_name) > 20 else ''}</p>
                        <p style="margin: 0; font-size: 11px;"><strong>Similarity: {similarity_score:.2f}</strong></p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Mini audio player
                    preview_url = rec_song.get('preview_url', '')
                    if check_audio_url(preview_url):
                        st.audio(preview_url, format='audio/mp3')
                    else:
                        st.markdown("<p style='text-align: center; color: #999; font-size: 10px;'>No preview</p>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Create tabs for different recommendation approaches
    tab1, tab2 = st.tabs(["🌍 Global Recommendations", "🎯 Cluster-Based Recommendations"])
    
    with tab1:
        st.markdown("## Global Audio-Based Recommendations")
        st.markdown("*Finding similar songs from the entire dataset using audio features*")
        
        # Get global recommendations
        distances, indices = get_global_recommendations(
            models['knn'], 
            models['embeddings'], 
            selected_idx, 
            n_recommendations + 1
        )
        
        if distances is not None and indices is not None:
            display_recommendations_with_audio(
                tracks_df, indices, distances,
                "🎼 Global Audio Feature Similarity",
                "Recommendations based on overall audio characteristics from the entire dataset",
                artist_mapping
            )
        else:
            st.error("Unable to generate global recommendations")
    
    with tab2:
        st.markdown("## Cluster-Based Recommendations")
        st.markdown("*Finding similar songs within the same musical cluster*")
        
        if models['hdbscan'] is not None and models['labels'] is not None:
            # Show cluster information
            cluster_id = models['labels'][selected_idx]
            cluster_size = sum(1 for label in models['labels'] if label == cluster_id)
            
            st.info(f"🎯 Selected song belongs to **Cluster {cluster_id}** (contains {cluster_size} songs)")
            
            # Get cluster-based recommendations
            distances, indices = get_recommendations_within_cluster(
                models['knn'],
                models['embeddings'],
                models['labels'],
                selected_idx,
                n_recommendations + 1
            )
            
            if distances is not None and indices is not None:
                display_recommendations_with_audio(
                    tracks_df, indices, distances,
                    f"🎯 Cluster {cluster_id} Recommendations",
                    f"Songs with similar characteristics from the same musical cluster ({cluster_size} total songs)",
                    artist_mapping
                )
            else:
                st.warning("Unable to generate cluster-based recommendations (cluster may be too small)")
        else:
            st.warning("Clustering models not available. Only global recommendations are shown.")
    
    # Model information
    with st.expander("ℹ️ About the Recommendation System"):
        st.markdown("""
        ### How It Works:
        
        1. **HDBSCAN Clustering**: Songs are grouped into clusters based on audio similarity
        2. **Global Recommendations**: Uses K-Nearest Neighbors on the entire dataset
        3. **Cluster Recommendations**: Finds similar songs within the same musical cluster
        4. **Audio Previews**: 30-second Spotify previews for direct song comparison
        5. **Smart Search**: Enhanced search with fuzzy matching and popularity scoring
        
        ### Available Models:
        """)
        
        for model_name, model in models.items():
            status = "✅ Loaded" if model is not None else "❌ Not Available"
            st.markdown(f"- **{model_name.title()}**: {status}")
        
        # Audio availability statistics
        st.markdown("### 🎵 Audio Preview Statistics:")
        total_tracks = len(tracks_df)
        tracks_with_audio = tracks_df['preview_url'].apply(check_audio_url).sum()
        audio_percentage = (tracks_with_audio / total_tracks) * 100
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Tracks", f"{total_tracks:,}")
        with col2:
            st.metric("With Audio Preview", f"{tracks_with_audio:,}")
        with col3:
            st.metric("Audio Coverage", f"{audio_percentage:.1f}%")
        
        if models['hdbscan'] is not None:
            n_clusters = len(set(models['labels']) - {-1})
            n_noise = sum(1 for label in models['labels'] if label == -1)
            st.markdown(f"""
            ### Clustering Statistics:
            - **Number of Clusters**: {n_clusters}
            - **Noise Points**: {n_noise}
            - **Total Songs**: {len(models['labels'])}
            """)
            
        st.markdown("""
        ### 🎧 Audio Comparison Tips:
        - **Play multiple tracks**: Open several recommendations to compare
        - **Listen for similarities**: Notice similar tempo, energy, or mood
        - **Use headphones**: For better audio quality and comparison
        - **Compare clusters**: Songs in the same cluster should sound similar
        - **Try the search**: Use fuzzy search to find specific songs or artists
        """)

if __name__ == "__main__":
    main() 