import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os

# Set page configuration
st.set_page_config(
    page_title="Spotify Music Analysis",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Page title
st.title("🎧 Spotify Music Analysis & Modeling")
st.markdown("Explore patterns and insights from Spotify track data")

# Sidebar
st.sidebar.header("Data Filters")

# Define paths to data files
DATA_PATH = "/app/data"
TRACKS_CSV = os.path.join(DATA_PATH, "spotify_tracks.csv")
ARTISTS_CSV = os.path.join(DATA_PATH, "spotify_artists.csv")
ALBUMS_CSV = os.path.join(DATA_PATH, "spotify_albums.csv")
LYRICS_CSV = os.path.join(DATA_PATH, "lyrics_features.csv")
AUDIO_CSV = os.path.join(DATA_PATH, "low_level_audio_features.csv")

@st.cache_data
def load_data(file_path):
    """Load and cache data"""
    try:
        return pd.read_csv(file_path)
    except Exception as e:
        st.error(f"Error loading data from {file_path}: {e}")
        return pd.DataFrame()

# Load the data with a loading indicator
with st.spinner("Loading track data..."):
    if os.path.exists(TRACKS_CSV):
        tracks_df = load_data(TRACKS_CSV)
        # Limit to a sample for performance if needed
        if len(tracks_df) > 10000:
            tracks_sample = tracks_df.sample(10000, random_state=42)
        else:
            tracks_sample = tracks_df
    else:
        st.warning(f"Tracks data file not found at {TRACKS_CSV}")
        tracks_sample = pd.DataFrame()

# Load artists data
with st.spinner("Loading artist data..."):
    if os.path.exists(ARTISTS_CSV):
        artists_df = load_data(ARTISTS_CSV)
    else:
        st.warning(f"Artists data file not found at {ARTISTS_CSV}")
        artists_df = pd.DataFrame()

# Main content
if not tracks_sample.empty:
    # Dashboard tabs
    tab1, tab2, tab3 = st.tabs(["Track Analysis", "Artist Analysis", "Modeling Strategy"])
    
    with tab1:
        st.header("Track Analysis")
        
        # Summary statistics
        st.subheader("Summary Statistics")
        col1, col2 = st.columns(2)
        
        with col1:
            if 'popularity' in tracks_sample.columns:
                st.metric("Average Track Popularity", f"{tracks_sample['popularity'].mean():.1f}")
            
            if 'duration_ms' in tracks_sample.columns:
                avg_duration_min = tracks_sample['duration_ms'].mean() / 60000
                st.metric("Average Track Duration", f"{avg_duration_min:.2f} minutes")
        
        with col2:
            if 'explicit' in tracks_sample.columns:
                explicit_pct = tracks_sample['explicit'].mean() * 100
                st.metric("Explicit Tracks", f"{explicit_pct:.1f}%")
            
            if len(tracks_sample) > 0:
                st.metric("Total Tracks Analyzed", f"{len(tracks_sample):,}")
        
        # Popularity distribution
        if 'popularity' in tracks_sample.columns:
            st.subheader("Popularity Distribution")
            fig = px.histogram(
                tracks_sample, 
                x='popularity',
                nbins=20,
                color_discrete_sequence=['#1DB954'],
                title="Distribution of Track Popularity"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Audio features analysis (if available)
        if os.path.exists(AUDIO_CSV) and not tracks_sample.empty:
            st.subheader("Audio Features")
            st.info("This would display audio feature analysis from the audio features dataset")
    
    with tab2:
        st.header("Artist Analysis")
        
        if not artists_df.empty:
            # Artist popularity distribution
            if 'popularity' in artists_df.columns:
                st.subheader("Artist Popularity")
                fig = px.histogram(
                    artists_df, 
                    x='popularity',
                    nbins=20,
                    color_discrete_sequence=['#1DB954'],
                    title="Distribution of Artist Popularity"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Top genres if available
            if 'genres' in artists_df.columns:
                st.subheader("Top Genres")
                # This assumes genres are stored as a string list or similar
                # You may need to adjust based on actual data format
                st.info("Genre analysis would appear here based on the actual data format")
        else:
            st.info("Artist data not available. Please check the data files.")
    
    with tab3:
        st.header("Modeling Strategy")
        
        st.markdown("""
        ## Potential Modeling Approaches
        
        ### 1. Popularity Prediction
        - **Objective**: Predict track popularity based on audio features and metadata
        - **Approach**: Regression models (Linear Regression, Random Forest, Gradient Boosting)
        - **Features**: Audio features, artist popularity, release date, etc.
        
        ### 2. Genre Classification
        - **Objective**: Classify tracks into genres based on audio characteristics
        - **Approach**: Multi-class classification (Random Forest, SVM, Neural Networks)
        - **Features**: Audio features, BPM, key, energy, etc.
        
        ### 3. Song Clustering
        - **Objective**: Discover natural groupings of songs with similar characteristics
        - **Approach**: Unsupervised learning (K-means, DBSCAN, Hierarchical Clustering)
        - **Features**: Audio features normalized and reduced with PCA or t-SNE
        """)
else:
    st.error("Unable to load data. Please check that the data files exist and are properly formatted.")

# Footer
st.sidebar.markdown("---")
st.sidebar.info("Spotify Music Analysis App - v1.0") 