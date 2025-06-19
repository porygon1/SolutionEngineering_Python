"""
Recommendations Component - AI-powered music recommendations display
"""

import streamlit as st
import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional, Tuple
from utils.data_utils import get_artist_name
from utils.formatting import format_duration
from utils.recommendations import (
    get_recommendations_within_cluster,
    get_global_recommendations,
    analyze_recommendations,
    get_artist_diversity
)
from .track_grid import render_track_grid
import plotly.graph_objects as go

logger = logging.getLogger(__name__)

def render_recommendations_section(tracks_df, artist_mapping, models, selected_track_idx, 
                                 spotify_client, num_recommendations=12, recommendation_type="cluster"):
    """Render recommendations section with prominent similarity scores"""
    
    if selected_track_idx is None:
        st.info("🎯 Select a track to get personalized recommendations!")
        return
    
    try:
        # Get the selected track
        selected_track = tracks_df.iloc[selected_track_idx]
        
        # Create prominent header with selected track info
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1db954 0%, #1ed760 100%); 
                    padding: 20px; border-radius: 12px; margin-bottom: 20px; color: white;">
            <h2 style="margin: 0; font-size: 24px;">🎯 Your Personalized Recommendations</h2>
            <p style="margin: 8px 0 0 0; font-size: 16px; opacity: 0.9;">
                Based on: <strong>{selected_track.get('name', 'Unknown')}</strong> by 
                <strong>{get_artist_name(selected_track, artist_mapping)}</strong>
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Get recommendations with similarity scores
        if recommendation_type == "cluster" and models.get('labels') is not None:
            distances, indices = get_recommendations_within_cluster(
                models['knn'], models['embeddings'], 
                models['labels'], selected_track_idx, 
                n_neighbors=num_recommendations + 1
            )
        else:
            distances, indices = get_global_recommendations(
                models['knn'], models['embeddings'], 
                selected_track_idx, 
                n_neighbors=num_recommendations + 1
            )
        
        if distances is None or indices is None:
            st.error("❌ Could not generate recommendations. Please try again.")
            return
        
        # Skip the first result (the selected track itself)
        rec_distances = distances[1:]
        rec_indices = indices[1:]
        
        # Convert distances to similarity scores (higher is better)
        max_distance = max(rec_distances) if len(rec_distances) > 0 else 1
        similarity_scores = [(max_distance - dist) / max_distance for dist in rec_distances]
        
        # Get recommended tracks with similarity scores
        recommended_tracks = []
        for i, (idx, score) in enumerate(zip(rec_indices, similarity_scores)):
            track = tracks_df.iloc[idx].copy()
            track['similarity_score'] = score
            track['recommendation_rank'] = i + 1
            recommended_tracks.append(track)
        
        # Sort by similarity score (highest first)
        recommended_tracks.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        # Display recommendation insights
        st.markdown("### 📊 Recommendation Insights")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_similarity = np.mean(similarity_scores) * 100
            st.markdown(f"""
            <div style="text-align: center; padding: 16px; background: linear-gradient(135deg, #1db954, #1ed760); 
                        border-radius: 8px; color: white;">
                <div style="font-size: 24px; font-weight: bold;">{avg_similarity:.1f}%</div>
                <div style="font-size: 12px; opacity: 0.9;">Avg Match</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            best_match = max(similarity_scores) * 100
            st.markdown(f"""
            <div style="text-align: center; padding: 16px; background: linear-gradient(135deg, #ff6b6b, #ee5a52); 
                        border-radius: 8px; color: white;">
                <div style="font-size: 24px; font-weight: bold;">{best_match:.1f}%</div>
                <div style="font-size: 12px; opacity: 0.9;">Best Match</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            # Calculate musical diversity
            selected_features = ['energy', 'danceability', 'valence', 'acousticness']
            selected_values = [selected_track.get(f, 0.5) for f in selected_features]
            
            diversity_scores = []
            for track in recommended_tracks:
                track_values = [track.get(f, 0.5) for f in selected_features]
                diversity = np.mean([abs(s - t) for s, t in zip(selected_values, track_values)])
                diversity_scores.append(diversity)
            
            avg_diversity = np.mean(diversity_scores) * 100
            st.markdown(f"""
            <div style="text-align: center; padding: 16px; background: linear-gradient(135deg, #4ecdc4, #44a08d); 
                        border-radius: 8px; color: white;">
                <div style="font-size: 24px; font-weight: bold;">{avg_diversity:.1f}%</div>
                <div style="font-size: 12px; opacity: 0.9;">Diversity</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            # Count unique artists
            unique_artists = len(set([get_artist_name(track, artist_mapping) for track in recommended_tracks]))
            st.markdown(f"""
            <div style="text-align: center; padding: 16px; background: linear-gradient(135deg, #a8edea, #fed6e3); 
                        border-radius: 8px; color: #333;">
                <div style="font-size: 24px; font-weight: bold;">{unique_artists}</div>
                <div style="font-size: 12px; opacity: 0.8;">Artists</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Musical characteristics comparison
        st.markdown("### 🎵 Musical Characteristics")
        
        # Create comparison chart
        selected_features = ['energy', 'danceability', 'valence', 'acousticness', 'instrumentalness']
        selected_values = [selected_track.get(f, 0) for f in selected_features]
        
        # Average values of recommended tracks
        avg_recommended_values = []
        for feature in selected_features:
            values = [track.get(feature, 0) for track in recommended_tracks]
            avg_recommended_values.append(np.mean(values))
        
        # Create radar chart data
        fig = go.Figure()
        
        # Add selected track
        fig.add_trace(go.Scatterpolar(
            r=selected_values + [selected_values[0]],  # Close the polygon
            theta=selected_features + [selected_features[0]],
            fill='toself',
            name='Selected Track',
            line_color='#1db954',
            fillcolor='rgba(29, 185, 84, 0.3)'
        ))
        
        # Add average of recommendations
        fig.add_trace(go.Scatterpolar(
            r=avg_recommended_values + [avg_recommended_values[0]],
            theta=selected_features + [selected_features[0]],
            fill='toself',
            name='Recommended Tracks (Avg)',
            line_color='#ff6b6b',
            fillcolor='rgba(255, 107, 107, 0.3)'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )),
            showlegend=True,
            title="Musical Feature Comparison",
            height=400,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white')
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Display recommendations with prominent similarity scores
        st.markdown("### 🎯 Your Recommendations (Ranked by Similarity)")
        
        # Create DataFrame for easier handling
        recommendations_df = pd.DataFrame(recommended_tracks)
        
        # Render recommendations grid with similarity scores
        render_track_grid(
            recommendations_df,
            artist_mapping,
            spotify_client,
            grid_id="recommendations"
        )
        
        # Additional insights
        with st.expander("🔍 Detailed Analysis", expanded=False):
            st.markdown("#### Top 3 Most Similar Tracks:")
            
            for i, track in enumerate(recommended_tracks[:3]):
                similarity = track['similarity_score'] * 100
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"""
                    **{i+1}. {track.get('name', 'Unknown')}** by {get_artist_name(track, artist_mapping)}
                    """)
                with col2:
                    st.markdown(f"""
                    <div style="text-align: center; padding: 8px; background: #1db954; 
                                border-radius: 6px; color: white; font-weight: bold;">
                        {similarity:.1f}% Match
                    </div>
                    """, unsafe_allow_html=True)
                
                # Show why it's similar
                feature_similarities = []
                for feature in ['energy', 'danceability', 'valence']:
                    selected_val = selected_track.get(feature, 0.5)
                    track_val = track.get(feature, 0.5)
                    similarity_pct = (1 - abs(selected_val - track_val)) * 100
                    feature_similarities.append(f"{feature.title()}: {similarity_pct:.0f}%")
                
                st.markdown(f"*Similar in: {', '.join(feature_similarities)}*")
                st.markdown("---")
        
    except Exception as e:
        st.error(f"❌ Error generating recommendations: {e}")
        logger.error(f"Recommendation error: {e}")

def generate_recommendations(tracks_df, models, selected_track_idx, num_recommendations, rec_type):
    """Generate recommendations using the specified method"""
    try:
        if rec_type == "cluster" and models.get('labels') is not None:
            distances, indices = get_recommendations_within_cluster(
                models['knn'], models['embeddings'], 
                models['labels'], selected_track_idx, 
                n_neighbors=num_recommendations + 1
            )
        else:
            distances, indices = get_global_recommendations(
                models['knn'], models['embeddings'], 
                selected_track_idx, 
                n_neighbors=num_recommendations + 1
            )
        
        if indices is not None:
            # Return recommendations (excluding the input track)
            rec_indices = indices[1:]  # Skip first one (input track)
            return tracks_df.iloc[rec_indices]
    except Exception as e:
        st.error(f"Error generating recommendations: {e}")
    
    return pd.DataFrame()

def render_current_track_display(track, artist_mapping, spotify_client):
    """Render the currently selected track display"""
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Display album cover
        album_cover_url = get_album_cover(track, spotify_client)
        if album_cover_url:
            st.image(album_cover_url, width=200)
        else:
            st.markdown("""
            <div style="width: 200px; height: 200px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        display: flex; align-items: center; justify-content: center; color: white; font-size: 3rem;">
                🎵
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        # Display track info
        artist_name = get_artist_name(track.get('artists_id', ''), artist_mapping)
        st.markdown(f"""
        <div class="track-display">
            <h2>{track.get('name', 'Unknown Track')}</h2>
            <p class="artist-name">{artist_name}</p>
            <div class="track-details">
                <span>⏱️ {format_duration(track.get('duration_ms', 0))}</span>
                <span>🎵 {track.get('key_name', 'Unknown Key')}</span>
                <span>⭐ {track.get('popularity', 0)}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Display quick stats
        render_track_quick_stats(track)

def render_track_quick_stats(track):
    """Render quick stats for the track"""
    features = ['danceability', 'energy', 'valence', 'acousticness']
    
    st.markdown("### Quick Stats")
    for feature in features:
        value = track.get(feature, 0)
        st.markdown(f"""
        <div class="feature-row">
            <span class="feature-label">{feature.title()}</span>
            <div class="feature-bar-container">
                <div class="feature-bar-fill" style="width: {value * 100}%"></div>
            </div>
            <span class="feature-value">{int(value * 100)}%</span>
        </div>
        """, unsafe_allow_html=True)

def render_recommendations_header(rec_type, num_recommendations):
    """Render the recommendations header"""
    st.markdown(f"""
    <div class="recommendations-header">
        <h2>🎵 Your Personalized Recommendations</h2>
        <p class="subtitle">
            {num_recommendations} tracks based on {rec_type.replace('_', ' ').title()} analysis
        </p>
    </div>
    """, unsafe_allow_html=True)

def render_recommendation_insights(current_track, recommendations_df, artist_mapping):
    """Render insights about the recommendations"""
    st.markdown("### 🎯 Recommendation Insights")
    
    # Get current artist
    current_artist = get_artist_name(current_track.get('artists_id', ''), artist_mapping)
    
    # Get recommended artists
    recommended_artists = []
    for _, rec_track in recommendations_df.iterrows():
        artist_name = get_artist_name(rec_track.get('artists_id', ''), artist_mapping)
        recommended_artists.append(artist_name)
    
    # Analyze recommendations
    analysis = analyze_recommendations(current_track, recommendations_df.to_dict('records'))
    diversity = get_artist_diversity(current_artist, recommended_artists)
    
    # Display insights
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🎵 Musical Characteristics:**")
        for insight in analysis.get('insights', []):
            st.markdown(f"""
            <div class="insights-section">
                <span class="insight-label">{insight['feature'].title()}:</span>
                <span class="insight-value {insight['status']}">{insight['message']}</span>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("**🎤 Artist Diversity:**")
        st.markdown(f"""
        <div class="insights-section">
            <span class="insight-label">Unique artists:</span>
            <span class="insight-value similar">{diversity['unique_artists']}</span>
        </div>
        <div class="insights-section">
            <span class="insight-label">Same artist tracks:</span>
            <span class="insight-value higher">{diversity['same_artist_count']}</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Show top artists
        if diversity['top_artists']:
            st.markdown("**Top recommended artists:**")
            for artist, count in diversity['top_artists']:
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

def render_compact_recommendations_section(tracks_df, artist_mapping, models, selected_track_idx, 
                                      spotify_client, num_recommendations=8, recommendation_type="cluster"):
    """Render a compact recommendations section optimized for sidebar/column display"""
    
    if selected_track_idx is None:
        st.info("🎯 Select a track to get recommendations!")
        return
    
    try:
        # Get the selected track
        selected_track = tracks_df.iloc[selected_track_idx]
        
        # Create compact header
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1db954 0%, #1ed760 100%); 
                    padding: 12px; border-radius: 8px; margin-bottom: 16px; color: white;">
            <h4 style="margin: 0; font-size: 16px;">🎯 Based on:</h4>
            <p style="margin: 4px 0 0 0; font-size: 14px; opacity: 0.9;">
                <strong>{selected_track.get('name', 'Unknown')[:30]}{'...' if len(selected_track.get('name', '')) > 30 else ''}</strong><br>
                <span style="font-size: 12px;">{get_artist_name(selected_track, artist_mapping)}</span>
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Get recommendations
        if recommendation_type == "cluster" and models.get('labels') is not None:
            distances, indices = get_recommendations_within_cluster(
                models['knn'], models['embeddings'], 
                models['labels'], selected_track_idx, 
                n_neighbors=num_recommendations + 1
            )
        else:
            distances, indices = get_global_recommendations(
                models['knn'], models['embeddings'], 
                selected_track_idx, 
                n_neighbors=num_recommendations + 1
            )
        
        if distances is None or indices is None:
            st.error("❌ Could not generate recommendations")
            return
        
        # Skip the first result (the selected track itself)
        rec_distances = distances[1:]
        rec_indices = indices[1:]
        
        # Convert distances to similarity scores
        max_distance = max(rec_distances) if len(rec_distances) > 0 else 1
        similarity_scores = [(max_distance - dist) / max_distance for dist in rec_distances]
        
        # Get recommended tracks with similarity scores
        recommended_tracks = []
        for i, (idx, score) in enumerate(zip(rec_indices, similarity_scores)):
            track = tracks_df.iloc[idx].copy()
            track['similarity_score'] = score
            track['recommendation_rank'] = i + 1
            recommended_tracks.append(track)
        
        # Sort by similarity score
        recommended_tracks.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        # Display top 3 insights compactly
        col1, col2, col3 = st.columns(3)
        
        with col1:
            avg_similarity = np.mean(similarity_scores) * 100
            st.markdown(f"""
            <div style="text-align: center; padding: 8px; background: #1db954; 
                        border-radius: 6px; color: white;">
                <div style="font-size: 18px; font-weight: bold;">{avg_similarity:.0f}%</div>
                <div style="font-size: 10px;">Avg Match</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            best_match = max(similarity_scores) * 100
            st.markdown(f"""
            <div style="text-align: center; padding: 8px; background: #ff6b6b; 
                        border-radius: 6px; color: white;">
                <div style="font-size: 18px; font-weight: bold;">{best_match:.0f}%</div>
                <div style="font-size: 10px;">Best</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            unique_artists = len(set([get_artist_name(track, artist_mapping) for track in recommended_tracks]))
            st.markdown(f"""
            <div style="text-align: center; padding: 8px; background: #4ecdc4; 
                        border-radius: 6px; color: white;">
                <div style="font-size: 18px; font-weight: bold;">{unique_artists}</div>
                <div style="font-size: 10px;">Artists</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("#### 🎵 Your Recommendations")
        
        # Display recommendations compactly
        for i, track in enumerate(recommended_tracks):
            similarity = track['similarity_score'] * 100
            track_name = track.get('name', 'Unknown')
            artist_name = get_artist_name(track, artist_mapping)
            
            # Truncate long names for compact display
            if len(track_name) > 25:
                track_name = track_name[:22] + "..."
            if len(artist_name) > 20:
                artist_name = artist_name[:17] + "..."
            
            # Create compact track row - simplified for column context
            with st.container():
                st.markdown(f"""
                <div style="padding: 8px; background: #2a2a2a; border-radius: 6px; margin-bottom: 8px;">
                    <div style="font-weight: bold; font-size: 14px; color: #1db954;">
                        {i+1}. {track_name}
                    </div>
                    <div style="font-size: 12px; color: #ccc; margin-top: 2px;">
                        {artist_name}
                    </div>
                    <div style="font-size: 11px; color: #888; margin-top: 4px;">
                        🎯 {similarity:.0f}% match
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Compact action button
                if st.button("▶️ Play", key=f"compact_play_{i}", help="Play", use_container_width=True):
                    # Set as current track
                    st.session_state.current_track = rec_indices[i]
                    st.session_state.selected_track_idx = rec_indices[i]
                    st.rerun()
        
        # Button to view full recommendations
        if st.button("📊 View Detailed Analysis", use_container_width=True, type="secondary"):
            # Clear selected track to show full layout
            st.session_state.show_full_recommendations = True
            st.rerun()
            
    except Exception as e:
        st.error(f"❌ Error generating recommendations: {e}")
        logger.error(f"Compact recommendation error: {e}") 