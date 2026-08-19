"""
Session state management for Streamlit.
"""
import streamlit as st
from typing import Any, Optional, List, Dict
from datetime import datetime


class SessionStore:
    """Session state manager."""
    
    # Default session state values
    DEFAULTS = {
        "authenticated": False,
        "user": None,
        "token": None,
        "refresh_token": None,
        "messages": [],
        "current_conversation_id": None,
        "conversations": [],
        "models": [
            "deepseek-r1:7b",
            "llama3.2:7b",
            "qwen2.5:7b",
            "mistral:7b",
        ],
        "selected_model": "deepseek-r1:7b",
        "system_prompt": "",
        "temperature": 0.7,
        "top_p": 0.9,
        "max_tokens": 2048,
        "stream_enabled": True,
        "theme": "dark",
        "sidebar_collapsed": False,
        "generated_images": [],
        "chart_data": None,
        "chart_config": None,
        "preferences": {},
        "stats": {},
    }
    
    @classmethod
    def initialize(cls) -> None:
        """Initialize session state with defaults."""
        for key, default_value in cls.DEFAULTS.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
    
    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """Get a value from session state."""
        return st.session_state.get(key, default)
    
    @classmethod
    def set(cls, key: str, value: Any) -> None:
        """Set a value in session state."""
        st.session_state[key] = value
    
    @classmethod
    def update(cls, data: Dict[str, Any]) -> None:
        """Update multiple values in session state."""
        for key, value in data.items():
            st.session_state[key] = value
    
    @classmethod
    def delete(cls, key: str) -> None:
        """Delete a key from session state."""
        if key in st.session_state:
            del st.session_state[key]
    
    @classmethod
    def clear(cls, preserve_auth: bool = False) -> None:
        """Clear session state."""
        preserve_keys = ["authenticated", "user", "token", "refresh_token"] if preserve_auth else []
        
        for key in list(st.session_state.keys()):
            if key not in preserve_keys:
                del st.session_state[key]
    
    @classmethod
    def reset_to_defaults(cls) -> None:
        """Reset session state to defaults."""
        st.session_state.clear()
        cls.initialize()
    
    @classmethod
    def add_message(cls, role: str, content: str) -> None:
        """Add a message to chat history."""
        messages = cls.get("messages", [])
        messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
        })
        cls.set("messages", messages)
    
    @classmethod
    def clear_messages(cls) -> None:
        """Clear chat history."""
        cls.set("messages", [])
        cls.set("current_conversation_id", None)
    
    @classmethod
    def get_messages(cls) -> List[Dict[str, str]]:
        """Get all messages."""
        return cls.get("messages", [])
    
    @classmethod
    def get_last_n_messages(cls, n: int) -> List[Dict[str, str]]:
        """Get last N messages."""
        messages = cls.get("messages", [])
        return messages[-n:] if n > 0 else []
    
    @classmethod
    def is_authenticated(cls) -> bool:
        """Check if user is authenticated."""
        return cls.get("authenticated", False)
    
    @classmethod
    def get_user_id(cls) -> Optional[str]:
        """Get current user ID."""
        user = cls.get("user", {})
        return user.get("id")
    
    @classmethod
    def get_user_role(cls) -> str:
        """Get current user role."""
        user = cls.get("user", {})
        return user.get("role", "user")