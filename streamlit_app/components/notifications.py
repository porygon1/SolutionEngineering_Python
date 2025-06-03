"""
Notification components for user feedback and messages.
"""

import streamlit as st
from typing import Optional


def create_streamlit_notification(
    message: str, 
    banner_key: str, 
    icon: str = "✅", 
    notification_type: str = "success"
) -> None:
    """
    Create a dismissible notification using Streamlit's built-in toast functionality.
    
    st.toast() features:
    - Auto-dismisses after ~4 seconds
    - Appears as overlay (doesn't affect layout)
    - Built-in dismiss button (×)
    - Native Streamlit styling
    - No session state management needed
    
    Args:
        message (str): Notification message
        banner_key (str): Unique key for the notification (not used with toast)
        icon (str): Icon to display
        notification_type (str): Type of notification (success, info, warning, error)
    """
    try:
        from logging_config import get_logger
        logger = get_logger()
        logger.debug(f"Displaying {notification_type} notification: {message}")
    except:
        pass
    
    # Use st.toast() for temporary, auto-dismissible notifications
    # This replaces the custom notification system with Streamlit's native solution
    
    if notification_type == "success":
        st.toast(f"{icon} {message}", icon="✅")
    elif notification_type == "info":
        st.toast(f"{icon} {message}", icon="ℹ️")
    elif notification_type == "warning":
        st.toast(f"{icon} {message}", icon="⚠️")
    elif notification_type == "error":
        st.toast(f"{icon} {message}", icon="❌")
    else:
        st.toast(f"{icon} {message}", icon="✅")


def show_success_message(message: str, icon: str = "✅") -> None:
    """Show a success notification."""
    create_streamlit_notification(message, "success", icon, "success")


def show_info_message(message: str, icon: str = "ℹ️") -> None:
    """Show an info notification."""
    create_streamlit_notification(message, "info", icon, "info")


def show_warning_message(message: str, icon: str = "⚠️") -> None:
    """Show a warning notification."""
    create_streamlit_notification(message, "warning", icon, "warning")


def show_error_message(message: str, icon: str = "❌") -> None:
    """Show an error notification."""
    create_streamlit_notification(message, "error", icon, "error") 