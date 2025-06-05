"""
Enhanced Recommendation Cards with Rich Media
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, List, Optional
import numpy as np


def create_mini_audio_viz(track_info: Dict) -> str:
    """
    Create a mini audio features visualization for recommendation cards.
    
    Args:
        track_info: Track information
        
    Returns:
        HTML for mini visualization
    """
    features = ['danceability', 'energy', 'valence', 'acousticness']
    values = [track_info.get(f, 0) for f in features]
    
    bars_html = ""
    for i, (feature, value) in enumerate(zip(features, values)):
        height = max(10, value * 40)  # Scale for mini display
        color_intensity = value * 100
        
        bars_html += f"""
        <div style="display: flex; flex-direction: column; align-items: center; margin: 0 2px;">
            <div style="width: 8px; height: {height}px; background: linear-gradient(to top, #1db954, #1ed760); 
                        border-radius: 2px; margin-bottom: 2px; opacity: 0.8;"></div>
            <span style="font-size: 0.6rem; opacity: 0.7;">{feature[:4]}</span>
        </div>
        """
    
    return f"""
    <div style="display: flex; justify-content: center; align-items: end; margin: 0.5rem 0; height: 60px;">
        {bars_html}
    </div>
    """


def create_similarity_indicator(similarity_score: float) -> str:
    """
    Create a visual similarity indicator.
    
    Args:
        similarity_score: Similarity score (0-1)
        
    Returns:
        HTML for similarity indicator
    """
    percentage = similarity_score * 100
    
    if percentage >= 90:
        color = "#1db954"
        icon = "🎯"
        label = "Perfect Match"
    elif percentage >= 80:
        color = "#1ed760"
        icon = "⭐"
        label = "Great Match"
    elif percentage >= 70:
        color = "#ffeb3b"
        icon = "✨"
        label = "Good Match"
    elif percentage >= 60:
        color = "#ff9800"
        icon = "🔍"
        label = "Fair Match"
    else:
        color = "#9e9e9e"
        icon = "💎"
        label = "Discovery"
    
    return f"""
    <div style="display: flex; align-items: center; gap: 0.5rem; margin: 0.5rem 0;">
        <div style="background: {color}; color: white; padding: 0.2rem 0.6rem; border-radius: 12px; 
                    font-size: 0.7rem; font-weight: 600; display: flex; align-items: center; gap: 0.3rem;">
            {icon} {percentage:.0f}% {label}
        </div>
    </div>
    """


def create_track_preview_card(track_info: Dict, artist_name: str, similarity_score: float, 
                            card_index: int, spotify_client=None) -> str:
    """
    Create a preview card for a recommended track.
    
    Args:
        track_info: Track information
        artist_name: Artist name
        similarity_score: Similarity score
        card_index: Index for unique identification
        spotify_client: Optional Spotify client
        
    Returns:
        HTML for track preview card
    """
    # Get track artwork or create fallback
    artwork_html = ""
    if spotify_client:
        # Try to get artwork from Spotify
        try:
            track_id = track_info.get('id')
            if track_id:
                track = spotify_client.track(track_id)
                if track.get('album', {}).get('images'):
                    artwork_url = track['album']['images'][-1]['url']  # Smallest image
                    artwork_html = f"""
                    <img src="{artwork_url}" 
                         style="width: 60px; height: 60px; border-radius: 8px; object-fit: cover;"
                         alt="Album cover">
                    """
        except:
            pass
    
    if not artwork_html:
        # Create gradient fallback
        gradients = [
            "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
            "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
            "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
            "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)"
        ]
        gradient = gradients[card_index % len(gradients)]
        
        artwork_html = f"""
        <div style="width: 60px; height: 60px; background: {gradient}; border-radius: 8px;
                    display: flex; align-items: center; justify-content: center; color: white; font-size: 1.5rem;">
            🎵
        </div>
        """
    
    # Format track information
    track_name = track_info.get('name', 'Unknown Track')
    track_name_display = track_name[:35] + '...' if len(track_name) > 35 else track_name
    
    artist_display = artist_name[:25] + '...' if len(artist_name) > 25 else artist_name
    
    # Get audio features for mini viz
    mini_viz_html = create_mini_audio_viz(track_info)
    
    # Get similarity indicator
    similarity_html = create_similarity_indicator(similarity_score)
    
    # Format duration
    duration_ms = track_info.get('duration_ms', 0)
    if duration_ms > 0:
        duration_s = int(duration_ms / 1000)
        minutes = duration_s // 60
        seconds = duration_s % 60
        duration_str = f"{minutes}:{seconds:02d}"
    else:
        duration_str = "Unknown"
    
    # Get popularity and other stats
    popularity = track_info.get('popularity', 0)
    tempo = track_info.get('tempo', 0)
    key = track_info.get('key', 0)
    
    key_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    key_name = key_names[int(key) % 12] if key >= 0 else "Unknown"
    
    return f"""
    <div class="rec-card" style="position: relative; overflow: hidden;">
        <!-- Header with artwork and basic info -->
        <div style="display: flex; gap: 1rem; margin-bottom: 1rem;">
            {artwork_html}
            <div style="flex: 1; min-width: 0;">
                <h4 style="margin: 0 0 0.3rem 0; font-size: 1rem; line-height: 1.2; color: #ffffff;">
                    {track_name_display}
                </h4>
                <p style="margin: 0 0 0.3rem 0; color: #1db954; font-size: 0.9rem;">
                    {artist_display}
                </p>
                <div style="display: flex; gap: 0.5rem; font-size: 0.7rem; opacity: 0.8;">
                    <span>⏱️ {duration_str}</span>
                    <span>🎵 {key_name}</span>
                    <span>⭐ {popularity}</span>
                </div>
            </div>
        </div>
        
        <!-- Similarity indicator -->
        {similarity_html}
        
        <!-- Mini audio features visualization -->
        <div style="margin: 1rem 0;">
            <div style="font-size: 0.8rem; margin-bottom: 0.5rem; color: #1db954; font-weight: 500;">
                Audio DNA
            </div>
            {mini_viz_html}
        </div>
        
        <!-- Quick stats -->
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; margin: 1rem 0; font-size: 0.7rem;">
            <div>
                <span style="opacity: 0.7;">Dance:</span> 
                <span style="color: #1db954;">{track_info.get('danceability', 0):.2f}</span>
            </div>
            <div>
                <span style="opacity: 0.7;">Energy:</span> 
                <span style="color: #1db954;">{track_info.get('energy', 0):.2f}</span>
            </div>
            <div>
                <span style="opacity: 0.7;">Mood:</span> 
                <span style="color: #1db954;">{track_info.get('valence', 0):.2f}</span>
            </div>
            <div>
                <span style="opacity: 0.7;">Tempo:</span> 
                <span style="color: #1db954;">{tempo:.0f}</span>
            </div>
        </div>
        
        <!-- Hover overlay for preview -->
        <div style="position: absolute; top: 0; right: 0; padding: 0.5rem;">
            <div style="background: rgba(29, 185, 84, 0.8); color: white; border-radius: 50%; 
                        width: 30px; height: 30px; display: flex; align-items: center; 
                        justify-content: center; font-size: 0.8rem; opacity: 0.7;">
                ▶️
            </div>
        </div>
    </div>
    """


def render_enhanced_recommendations_grid(tracks_df: pd.DataFrame, artist_mapping: Dict, 
                                       indices: List[int], distances: List[float], 
                                       rec_type: str, n_recommendations: int = 5,
                                       spotify_client=None):
    """
    Render enhanced recommendations in a beautiful grid layout.
    
    Args:
        tracks_df: Tracks dataframe
        artist_mapping: Artist mapping
        indices: Recommendation indices
        distances: Recommendation distances
        rec_type: Type of recommendations
        n_recommendations: Number of recommendations to show
        spotify_client: Optional Spotify client
    """
    st.markdown(f"""
    <div style="margin: 2rem 0;">
        <h3 style="color: #1db954; margin-bottom: 1.5rem; display: flex; align-items: center; gap: 0.5rem;">
            🎵 Your Personalized Recommendations
            <span style="font-size: 0.8rem; opacity: 0.7; font-weight: normal;">
                ({rec_type.replace('_', ' ').title()})
            </span>
        </h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Create columns for grid layout
    cols = st.columns(min(3, n_recommendations))
    
    for i in range(1, min(n_recommendations + 1, len(indices))):  # Skip first (self)
        idx = indices[i]
        distance = distances[i]
        similarity = (1 - distance) if distance <= 1 else 0
        
        if idx < len(tracks_df):
            track = tracks_df.iloc[idx]
            
            # Get artist name
            from utils import get_artist_name
            artist_name = get_artist_name(track.get('artists_id', ''), artist_mapping)
            
            with cols[(i-1) % 3]:
                # Create track preview card
                card_html = create_track_preview_card(
                    track, artist_name, similarity, i, spotify_client
                )
                st.markdown(card_html, unsafe_allow_html=True)
                
                # Add play button
                if st.button(f"▶️ Play", key=f"{rec_type}_{i}_{idx}", use_container_width=True):
                    st.session_state.selected_track_idx = idx
                    st.rerun()
                
                # Add audio preview if available
                if pd.notna(track.get('preview_url')) and track['preview_url']:
                    with st.expander("🎧 Preview", expanded=False):
                        st.audio(track['preview_url'])
                        
                        # Show additional details
                        st.markdown(f"""
                        **Key Features:**
                        - 🕺 Danceability: {track.get('danceability', 0):.2f}
                        - ⚡ Energy: {track.get('energy', 0):.2f}
                        - 😊 Valence: {track.get('valence', 0):.2f}
                        - 🎼 Tempo: {track.get('tempo', 0):.0f} BPM
                        """)
                
                st.markdown("---")


def create_recommendation_comparison_chart(current_track: Dict, recommendations: List[Dict]) -> go.Figure:
    """
    Create a comparison chart showing how recommendations compare to the current track.
    
    Args:
        current_track: Current track information
        recommendations: List of recommended tracks
        
    Returns:
        Plotly figure
    """
    features = ['danceability', 'energy', 'valence', 'acousticness', 'instrumentalness']
    
    fig = go.Figure()
    
    # Add current track
    current_values = [current_track.get(f, 0) for f in features]
    fig.add_trace(go.Scatterpolar(
        r=current_values,
        theta=features,
        fill='toself',
        name='Current Track',
        line=dict(color='#1db954', width=3),
        fillcolor='rgba(29, 185, 84, 0.3)'
    ))
    
    # Add recommendations
    colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#f9ca24', '#f0932b']
    for i, rec in enumerate(recommendations[:3]):  # Show top 3 recommendations
        rec_values = [rec.get(f, 0) for f in features]
        fig.add_trace(go.Scatterpolar(
            r=rec_values,
            theta=features,
            fill='toself',
            name=f"Rec {i+1}: {rec.get('name', 'Unknown')[:20]}",
            line=dict(color=colors[i % len(colors)], width=2),
            fillcolor=f"rgba({','.join([str(int(colors[i % len(colors)][j:j+2], 16)) for j in range(1, 7, 2)])}, 0.1)"
        ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1],
                gridcolor='rgba(255, 255, 255, 0.2)',
                linecolor='rgba(255, 255, 255, 0.3)'
            ),
            angularaxis=dict(
                gridcolor='rgba(255, 255, 255, 0.2)',
                linecolor='rgba(255, 255, 255, 0.3)'
            )
        ),
        showlegend=True,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white', size=10),
        height=500,
        title=dict(
            text="🎵 Track Comparison: Audio Features",
            x=0.5,
            font=dict(color='white', size=16)
        )
    )
    
    return fig


def create_recommendation_insights(current_track: Dict, recommendations: List[Dict]) -> str:
    """
    Create insights about why tracks were recommended.
    
    Args:
        current_track: Current track information
        recommendations: List of recommended tracks
        
    Returns:
        HTML string with insights
    """
    if not recommendations:
        return ""
    
    # Analyze patterns in recommendations
    avg_danceability = np.mean([r.get('danceability', 0) for r in recommendations])
    avg_energy = np.mean([r.get('energy', 0) for r in recommendations])
    avg_valence = np.mean([r.get('valence', 0) for r in recommendations])
    
    current_danceability = current_track.get('danceability', 0)
    current_energy = current_track.get('energy', 0)
    current_valence = current_track.get('valence', 0)
    
    insights = []
    
    # Generate insights based on patterns
    if avg_danceability > 0.7:
        insights.append("🕺 These recommendations are perfect for dancing!")
    elif avg_danceability < 0.3:
        insights.append("🎵 These tracks are more suitable for listening than dancing.")
    
    if avg_energy > 0.7:
        insights.append("⚡ High-energy tracks that will pump you up!")
    elif avg_energy < 0.3:
        insights.append("😌 Calm, low-energy tracks for relaxation.")
    
    if avg_valence > 0.7:
        insights.append("😄 These songs will lift your mood!")
    elif avg_valence < 0.3:
        insights.append("😢 Emotional, melancholic tracks that resonate with your current choice.")
    
    # Compare with current track
    if abs(avg_danceability - current_danceability) < 0.1:
        insights.append("🎯 Similar danceability to your current track.")
    
    if len(insights) == 0:
        insights.append("🎵 Diverse recommendations based on your musical taste.")
    
    insights_html = ""
    for insight in insights[:3]:  # Show max 3 insights
        insights_html += f"""
        <div style="background: rgba(29, 185, 84, 0.1); border-left: 3px solid #1db954; 
                    padding: 0.8rem; margin: 0.5rem 0; border-radius: 0 8px 8px 0;">
            {insight}
        </div>
        """
    
    return f"""
    <div style="margin: 2rem 0;">
        <h4 style="color: #1db954; margin-bottom: 1rem;">🧠 AI Insights</h4>
        {insights_html}
    </div>
    """ 