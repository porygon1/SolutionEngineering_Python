"""
Utility module for loading and applying CSS styles to the Streamlit app.
"""

import streamlit as st
import os
from pathlib import Path


def load_css(css_file_path: str) -> str:
    """
    Load CSS content from a file.
    
    Args:
        css_file_path (str): Path to the CSS file
        
    Returns:
        str: CSS content as string
    """
    try:
        css_path = Path(css_file_path)
        if css_path.exists():
            return css_path.read_text(encoding='utf-8')
        else:
            st.warning(f"CSS file not found: {css_file_path}")
            return ""
    except Exception as e:
        st.error(f"Error loading CSS file: {e}")
        return ""


def apply_custom_css(css_content: str) -> None:
    """
    Apply custom CSS to the Streamlit app.
    
    Args:
        css_content (str): CSS content to apply
    """
    if css_content:
        st.markdown(f"""
        <style>
        {css_content}
        </style>
        """, unsafe_allow_html=True)


def load_and_apply_css(css_file_path: str) -> None:
    """
    Load CSS from file and apply it to the Streamlit app.
    
    Args:
        css_file_path (str): Path to the CSS file
    """
    css_content = load_css(css_file_path)
    apply_custom_css(css_content)


def get_css_path(filename: str = "styles.css") -> str:
    """
    Get the path to a CSS file in the static/css directory.
    
    Args:
        filename (str): Name of the CSS file
        
    Returns:
        str: Full path to the CSS file
    """
    # Get the directory where this script is located
    current_dir = Path(__file__).parent.parent
    css_path = current_dir / "static" / "css" / filename
    return str(css_path)


def initialize_app_styles() -> None:
    """
    Initialize and apply all custom styles for the Spotify Music Recommendation app.
    """
    # Load main styles
    main_css_path = get_css_path("styles.css")
    load_and_apply_css(main_css_path) 