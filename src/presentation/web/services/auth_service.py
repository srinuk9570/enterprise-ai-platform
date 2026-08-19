"""
Authentication service for Streamlit frontend.
"""
import streamlit as st
from typing import Tuple, Optional, Dict, Any
from datetime import datetime

from src.presentation.web.services.api_client import APIClient


class AuthService:
    """Authentication service."""
    
    def __init__(self):
        self.api_client = APIClient()
    
    def login(self, email: str, password: str) -> Tuple[bool, Any]:
        """
        Login user.
        Returns (success, result).
        """
        # Validate inputs
        if not email or not password:
            return False, "Email and password are required"
        
        if "@" not in email:
            return False, "Please enter a valid email address"
        
        response = self.api_client.login(email, password)
        
        if response.get("success"):
            data = response.get("data", {})
            
            # Store tokens
            st.session_state["token"] = data.get("access_token")
            st.session_state["refresh_token"] = data.get("refresh_token")
            st.session_state["authenticated"] = True
            st.session_state["login_time"] = datetime.utcnow().isoformat()
            
            # Get user info
            user_response = self.api_client.get_current_user()
            if user_response.get("success"):
                st.session_state["user"] = user_response.get("data", {})
            else:
                # Set basic user info from login response
                st.session_state["user"] = {
                    "email": email,
                    "username": email.split("@")[0],
                }
            
            return True, data
        
        return False, response.get("error", "Login failed")
    
    def register(
        self,
        username: str,
        email: str,
        password: str,
        full_name: Optional[str] = None,
    ) -> Tuple[bool, Any]:
        """
        Register new user.
        Returns (success, result).
        """
        # Validate inputs
        if not username or len(username) < 3:
            return False, "Username must be at least 3 characters"
        
        if not email or "@" not in email:
            return False, "Please enter a valid email address"
        
        if not password or len(password) < 8:
            return False, "Password must be at least 8 characters"
        
        response = self.api_client.register(
            username=username,
            email=email,
            password=password,
            full_name=full_name,
        )
        
        if response.get("success"):
            return True, response.get("data", {})
        
        return False, response.get("error", "Registration failed")
    
    def logout(self) -> None:
        """Logout user."""
        if st.session_state.get("token"):
            try:
                self.api_client.logout()
            except:
                pass
        
        # Clear session
        keys_to_clear = [
            "token", "refresh_token", "authenticated", "user",
            "messages", "current_conversation_id", "login_time",
        ]
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
    
    def change_password(self, current_password: str, new_password: str) -> Tuple[bool, str]:
        """
        Change user password.
        Returns (success, message).
        """
        if not current_password or not new_password:
            return False, "Both passwords are required"
        
        if len(new_password) < 8:
            return False, "New password must be at least 8 characters"
        
        response = self.api_client.change_password(current_password, new_password)
        
        if response.get("success"):
            return True, "Password changed successfully"
        
        return False, response.get("error", "Failed to change password")
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        return st.session_state.get("authenticated", False)
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get current user info."""
        return st.session_state.get("user")