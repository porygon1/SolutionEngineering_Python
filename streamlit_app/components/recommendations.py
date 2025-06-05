"""
Recommendations Component - AI-powered music recommendations display
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Optional
from utils import get_artist_name, format_duration
from .track_grid import render_track_grid

def render_recommendations_section(tracks_df, artist_mapping, models, selected_track_idx, spotify_client, num_recommendations=12, rec_type="cluster"):
    """Render the full recommendations section"""
    
    if selected_track_idx is None:
        st.info("🎯 Select a track from the Featured Tracks to get personalized recommendations!")
        return
    
    # Get the current track
    current_track = tracks_df.iloc[selected_track_idx]
    
    # Display currently selected track
    render_current_track_display(current_track, artist_mapping, spotify_client)
    
    st.markdown("---")
    
    # Generate recommendations
    with st.spinner("🤖 Generating AI-powered recommendations..."):
        recommendations_df = generate_recommendations(
            tracks_df, models, selected_track_idx, num_recommendations, rec_type
        )
    
    if not recommendations_df.empty:
        # Display recommendations header
        render_recommendations_header(rec_type, num_recommendations)
        
        # Display recommendations grid
        render_track_grid(
            recommendations_df, 
            artist_mapping, 
            spotify_client,
            grid_id="recommendations",
            cols=4
        )
        
        # Display recommendation insights
        render_recommendation_insights(current_track, recommendations_df, artist_mapping)
    else:
        st.error("❌ Unable to generate recommendations. Please ensure AI models are loaded properly.")

def render_current_track_display(track, artist_mapping, spotify_client):
    """Display the currently selected track"""
    
    st.markdown("### 🎵 Currently Selected Track")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        # Try to get album cover from Spotify API
        album_image_url = get_album_cover(track, spotify_client)
        
        if album_image_url:
            st.image(album_image_url, width=150)
        else:
            # Create a placeholder with track features
            energy = track.get('energy', 0.5)
            valence = track.get('valence', 0.5)
            color_intensity = int(255 * energy)
            
            placeholder_html = f"""
            <div style="
                width: 150px;
                height: 150px;
                background: linear-gradient(135deg, 
                    rgba({color_intensity}, 185, 84, 0.8), 
                    rgba({color_intensity//2}, 100, 150, 0.6));
                border-radius: 12px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 2.5rem;
                box-shadow: 0 4px 16px rgba(0,0,0,0.3);
                margin: 0 auto;
            ">
                🎵
            </div>
            """
            st.markdown(placeholder_html, unsafe_allow_html=True)
    
    with col2:
        # Track information
        track_name = track.get('name', 'Unknown Track')
        artist_name = get_artist_name(track.get('artists_id', ''), artist_mapping)
        
        st.markdown(f"""
        <div style="padding: 1rem 0;">
            <h3 style="margin: 0; color: white; font-weight: 600;">
                {track_name}
            </h3>
            <h4 style="margin: 0.5rem 0; color: #1db954; font-weight: 500;">
                {artist_name}
            </h4>
            <p style="margin: 0; color: #b3b3b3;">
                {format_duration(track.get('duration_ms', 0))} • 
                {track.get('popularity', 0)}% popularity •
                {track.get('year', 'Unknown')}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Quick stats
        render_track_quick_stats(track)
    
    with col3:
        # Action buttons
        st.markdown("**Actions:**")
        
        if st.button("🎵 Play Track", use_container_width=True, type="primary"):
            st.session_state.current_track = track.name if hasattr(track, 'name') else st.session_state.selected_track_idx
            st.success("Now playing!")
        
        if st.button("🔄 New Recommendations", use_container_width=True):
            # Force regenerate recommendations
            st.rerun()
        
        # Spotify link if available
        spotify_url = get_spotify_url(track, spotify_client)
        if spotify_url:
            st.markdown(f"""
            <a href="{spotify_url}" target="_blank" style="text-decoration: none;">
                <button style="
                    background: #1db954;
                    border: none;
                    color: white;
                    padding: 0.5rem 1rem;
                    border-radius: 8px;
                    width: 100%;
                    cursor: pointer;
                    font-weight: 500;
                    margin-top: 0.5rem;
                ">🎧 Open in Spotify</button>
            </a>
            """, unsafe_allow_html=True)

def render_track_quick_stats(track):
    """Render quick statistics for a track"""
    
    # Key audio features
    features = {
        'Energy': track.get('energy', 0),
        'Danceability': track.get('danceability', 0),
        'Valence': track.get('valence', 0),
        'Acousticness': track.get('acousticness', 0)
    }
    
    st.markdown("**Audio Features:**")
    
    for feature_name, value in features.items():
        percentage = int(value * 100)
        color = get_feature_color_simple(value)
        
        st.markdown(f"""
        <div style="display: flex; align-items: center; margin: 0.3rem 0;">
            <span style="color: #b3b3b3; font-size: 0.9rem; width: 80px;">
                {feature_name}:
            </span>
            <div style="
                flex: 1;
                height: 6px;
                background: #333;
                border-radius: 3px;
                margin: 0 0.5rem;
                overflow: hidden;
            ">
                <div style="
                    width: {percentage}%;
                    height: 100%;
                    background: {color};
                    transition: width 0.3s ease;
                "></div>
            </div>
            <span style="color: white; font-size: 0.9rem; width: 35px;">
                {percentage}%
            </span>
        </div>
        """, unsafe_allow_html=True)

def render_recommendations_header(rec_type, num_recommendations):
    """Render the recommendations section header"""
    
    if rec_type == "cluster":
        st.markdown(f"""
        ### 🎯 Similar Music Style 
        <p style="color: #b3b3b3; margin-top: 0;">
            {num_recommendations} tracks with similar musical DNA from the same cluster
        </p>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        ### 🌍 Global Recommendations
        <p style="color: #b3b3b3; margin-top: 0;">
            {num_recommendations} most similar tracks from our entire database
        </p>
        """, unsafe_allow_html=True)

def generate_recommendations(tracks_df, models, selected_track_idx, num_recommendations, rec_type):
    """Generate recommendations using AI models"""
    
    if not models or tracks_df.empty:
        return pd.DataFrame()
    
    try:
        from utils.recommendations import get_recommendations_within_cluster, get_global_recommendations
        
        if rec_type == "cluster" and models.get('labels') is not None:
            distances, indices = get_recommendations_within_cluster(
                models['knn'], models['embeddings'], 
                models['labels'], selected_track_idx, 
                n_neighbors=num_recommendations + 1
            )
        else:
            distances, indices = get_global_recommendations(
                models['knn'], models['embeddings'], 
                selected_track_idx, n_neighbors=num_recommendations + 1
            )
        
        # Return recommendations (excluding the input track)
        rec_indices = indices[1:]  # Skip first one (input track)
        recommendations_df = tracks_df.iloc[rec_indices].copy()
        
        # Add similarity scores
        recommendations_df['similarity_score'] = 1 - distances[1:]  # Convert distance to similarity
        
        return recommendations_df
        
    except Exception as e:
        st.error(f"Error generating recommendations: {e}")
        return pd.DataFrame()

def render_recommendation_insights(current_track, recommendations_df, artist_mapping):
    """Render insights about the recommendations"""
    
    if recommendations_df.empty:
        return
    
    st.markdown("---")
    st.markdown("### 📊 Recommendation Insights")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🎵 Musical Characteristics:**")
        
        # Compare average features
        current_features = {
            'Energy': current_track.get('energy', 0),
            'Danceability': current_track.get('danceability', 0),
            'Valence': current_track.get('valence', 0),
            'Acousticness': current_track.get('acousticness', 0)
        }
        
        avg_features = {
            'Energy': recommendations_df['energy'].mean(),
            'Danceability': recommendations_df['danceability'].mean(),
            'Valence': recommendations_df['valence'].mean(),
            'Acousticness': recommendations_df['acousticness'].mean()
        }
        
        for feature_name in current_features.keys():
            current_val = current_features[feature_name]
            avg_val = avg_features[feature_name]
            diff = avg_val - current_val
            
            if abs(diff) < 0.1:
                status = "🎯 Very similar"
                color = "#1db954"
            elif diff > 0:
                status = f"📈 {abs(diff):.2f} higher"
                color = "#ffa500"
            else:
                status = f"📉 {abs(diff):.2f} lower"
                color = "#ff6b6b"
            
            st.markdown(f"""
            <div style="margin: 0.5rem 0;">
                <span style="color: #b3b3b3;">{feature_name}:</span>
                <span style="color: {color}; margin-left: 0.5rem;">{status}</span>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("**🎤 Artist Diversity:**")
        
        # Analyze artist diversity
        current_artist = get_artist_name(current_track.get('artists_id', ''), artist_mapping)
        
        recommended_artists = []
        for _, rec_track in recommendations_df.iterrows():
            artist_name = get_artist_name(rec_track.get('artists_id', ''), artist_mapping)
            recommended_artists.append(artist_name)
        
        unique_artists = list(set(recommended_artists))
        same_artist_count = recommended_artists.count(current_artist)
        
        st.markdown(f"""
        <div style="margin: 0.5rem 0;">
            <span style="color: #b3b3b3;">Unique artists:</span>
            <span style="color: #1db954; margin-left: 0.5rem;">{len(unique_artists)}</span>
        </div>
        <div style="margin: 0.5rem 0;">
            <span style="color: #b3b3b3;">Same artist tracks:</span>
            <span style="color: #ffa500; margin-left: 0.5rem;">{same_artist_count}</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Show top artists
        if len(unique_artists) > 0:
            st.markdown("**Top recommended artists:**")
            for artist in unique_artists[:3]:
                count = recommended_artists.count(artist)
                st.markdown(f"• {artist} ({count} track{'s' if count > 1 else ''})")

def get_album_cover(track, spotify_client):
    """Get album cover URL from Spotify API"""
    
    if not spotify_client:
        return None
    
    try:
        from components.track_grid import get_enhanced_track_info
        track_details = get_enhanced_track_info(track, spotify_client)
        
        if track_details:
            album_images = track_details.get('album', {}).get('images', [])
            if album_images:
                return album_images[0]['url']  # Return largest image
    except Exception as e:
        pass
    
    return None

def get_spotify_url(track, spotify_client):
    """Get Spotify URL for a track"""
    
    if not spotify_client:
        return None
    
    try:
        from components.track_grid import get_enhanced_track_info
        track_details = get_enhanced_track_info(track, spotify_client)
        
        if track_details:
            external_urls = track_details.get('external_urls', {})
            return external_urls.get('spotify')
    except Exception as e:
        pass
    
    return None

def get_feature_color_simple(value):
    """Get color for audio feature visualization"""
    
    if value < 0.3:
        return "#ff6b6b"  # Red for low values
    elif value < 0.7:
        return "#ffa500"  # Orange for medium values
    else:
        return "#1db954"  # Green for high values

def render_recommendation_comparison_chart(current_track, recommendations_df):
    """Render a comparison chart between current track and recommendations"""
    
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        
        # Features to compare
        features = ['energy', 'danceability', 'valence', 'acousticness', 'instrumentalness']
        
        # Get current track values
        current_values = [current_track.get(feature, 0) for feature in features]
        
        # Get average recommendation values
        avg_values = [recommendations_df[feature].mean() for feature in features]
        
        # Create radar chart
        fig = go.Figure()
        
        # Add current track
        fig.add_trace(go.Scatterpolar(
            r=current_values,
            theta=[f.title() for f in features],
            fill='toself',
            name='Current Track',
            line_color='#1db954'
        ))
        
        # Add recommendations average
        fig.add_trace(go.Scatterpolar(
            r=avg_values,
            theta=[f.title() for f in features],
            fill='toself',
            name='Recommendations Avg',
            line_color='#ffa500'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )),
            showlegend=True,
            title="Audio Features Comparison",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white')
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except ImportError:
        st.info("Install Plotly for advanced visualizations")
    except Exception as e:
        st.error(f"Error creating comparison chart: {e}") 