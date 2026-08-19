"""
Notification banner component for user feedback.
"""
import streamlit as st
from typing import Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import time


@dataclass
class Notification:
    """Notification data structure."""
    
    id: str
    type: str  # success, error, warning, info
    message: str
    duration: Optional[int] = None  # seconds, None for permanent
    dismissible: bool = True
    timestamp: datetime = None
    action: Optional[Callable] = None
    action_label: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class NotificationBanner:
    """
    Notification banner manager with auto-dismiss support.
    """
    
    def __init__(self, key: str = "notifications"):
        self.key = key
        self._initialize_session()
    
    def _initialize_session(self):
        """Initialize session state for notifications."""
        if f"{self.key}_notifications" not in st.session_state:
            st.session_state[f"{self.key}_notifications"] = []
        
        if f"{self.key}_dismissed" not in st.session_state:
            st.session_state[f"{self.key}_dismissed"] = set()
    
    @property
    def notifications(self) -> list:
        """Get all notifications."""
        return st.session_state.get(f"{self.key}_notifications", [])
    
    def add(
        self,
        message: str,
        type: str = "info",
        duration: Optional[int] = None,
        dismissible: bool = True,
        action: Optional[Callable] = None,
        action_label: Optional[str] = None,
    ) -> str:
        """
        Add a notification.
        Returns notification ID.
        """
        import uuid
        
        notification = Notification(
            id=str(uuid.uuid4()),
            type=type,
            message=message,
            duration=duration,
            dismissible=dismissible,
            action=action,
            action_label=action_label,
        )
        
        notifications = self.notifications
        notifications.append(notification)
        st.session_state[f"{self.key}_notifications"] = notifications
        
        return notification.id
    
    def success(
        self,
        message: str,
        duration: Optional[int] = 5,
        dismissible: bool = True,
    ) -> str:
        """Add a success notification."""
        return self.add(message, "success", duration, dismissible)
    
    def error(
        self,
        message: str,
        duration: Optional[int] = None,
        dismissible: bool = True,
    ) -> str:
        """Add an error notification."""
        return self.add(message, "error", duration, dismissible)
    
    def warning(
        self,
        message: str,
        duration: Optional[int] = 7,
        dismissible: bool = True,
    ) -> str:
        """Add a warning notification."""
        return self.add(message, "warning", duration, dismissible)
    
    def info(
        self,
        message: str,
        duration: Optional[int] = 5,
        dismissible: bool = True,
    ) -> str:
        """Add an info notification."""
        return self.add(message, "info", duration, dismissible)
    
    def dismiss(self, notification_id: str):
        """Dismiss a specific notification."""
        dismissed = st.session_state.get(f"{self.key}_dismissed", set())
        dismissed.add(notification_id)
        st.session_state[f"{self.key}_dismissed"] = dismissed
    
    def clear_all(self):
        """Clear all notifications."""
        st.session_state[f"{self.key}_notifications"] = []
        st.session_state[f"{self.key}_dismissed"] = set()
    
    def render(self):
        """
        Render all active notifications.
        """
        dismissed = st.session_state.get(f"{self.key}_dismissed", set())
        active_notifications = []
        expired_notifications = []
        
        for notification in self.notifications:
            if notification.id in dismissed:
                continue
            
            # Check expiration
            if notification.duration:
                elapsed = (datetime.utcnow() - notification.timestamp).total_seconds()
                if elapsed > notification.duration:
                    expired_notifications.append(notification.id)
                    continue
            
            active_notifications.append(notification)
        
        # Remove expired
        if expired_notifications:
            self._remove_notifications(expired_notifications)
        
        # Render active notifications
        for notification in active_notifications:
            self._render_notification(notification)
    
    def _remove_notifications(self, notification_ids: list):
        """Remove notifications by IDs."""
        notifications = self.notifications
        filtered = [n for n in notifications if n.id not in notification_ids]
        st.session_state[f"{self.key}_notifications"] = filtered
    
    def _render_notification(self, notification: Notification):
        """Render a single notification."""
        
        # Create container
        if notification.type == "success":
            container = st.success(notification.message, icon="✅")
        elif notification.type == "error":
            container = st.error(notification.message, icon="❌")
        elif notification.type == "warning":
            container = st.warning(notification.message, icon="⚠️")
        else:
            container = st.info(notification.message, icon="ℹ️")
        
        # Add action button if present
        if notification.action and notification.action_label:
            col1, col2 = container.columns([4, 1])
            with col2:
                if st.button(notification.action_label, key=f"action_{notification.id}"):
                    notification.action()
                    self.dismiss(notification.id)
                    st.rerun()
        
        # Add dismiss button
        if notification.dismissible:
            if st.button("✕", key=f"dismiss_{notification.id}"):
                self.dismiss(notification.id)
                st.rerun()


# Global notification banner instance
_notification_banner: Optional[NotificationBanner] = None


def get_notification_banner() -> NotificationBanner:
    """Get or create global notification banner."""
    global _notification_banner
    if _notification_banner is None:
        _notification_banner = NotificationBanner()
    return _notification_banner


def show_notification(
    message: str,
    type: str = "info",
    duration: Optional[int] = 5,
) -> str:
    """
    Show a notification banner.
    
    Args:
        message: Notification message
        type: Type of notification (success, error, warning, info)
        duration: Duration in seconds (None for permanent)
    
    Returns:
        Notification ID
    """
    banner = get_notification_banner()
    return banner.add(message, type, duration)


def show_success(message: str, duration: int = 5) -> str:
    """Show a success notification."""
    return get_notification_banner().success(message, duration)


def show_error(message: str, duration: Optional[int] = None) -> str:
    """Show an error notification."""
    return get_notification_banner().error(message, duration)


def show_warning(message: str, duration: int = 7) -> str:
    """Show a warning notification."""
    return get_notification_banner().warning(message, duration)


def show_info(message: str, duration: int = 5) -> str:
    """Show an info notification."""
    return get_notification_banner().info(message, duration)


def render_notifications():
    """Render all pending notifications."""
    get_notification_banner().render()


def clear_notifications():
    """Clear all notifications."""
    get_notification_banner().clear_all()