"""
Streamlit pages module.
"""

# Pages are automatically discovered by Streamlit from the pages/ directory.
# This file can be empty or used for shared page utilities.

from typing import Dict, Any, Optional
import streamlit as st


def check_authentication() -> bool:
    """
    Check if user is authenticated.
    Returns True if authenticated, redirects to home if not.
    """
    if not st.session_state.get("authenticated"):
        st.warning("⚠️ Please login to access this page.")
        st.switch_page("Home.py")
        return False
    return True


def set_page_config(title: str, icon: str = "📄"):
    """
    Set page configuration with defaults.
    """
    st.set_page_config(
        page_title=f"{title} - Enterprise AI Platform",
        page_icon=icon,
        layout="wide",
    )


def get_page_icon(page_name: str) -> str:
    """Get icon for page."""
    icons = {
        "chat": "💬",
        "analytics": "📊",
        "image": "🎨",
        "chart": "📈",
        "settings": "⚙️",
        "documentation": "📚",
    }
    return icons.get(page_name, "📄")


__all__ = [
    "check_authentication",
    "set_page_config",
    "get_page_icon",
]