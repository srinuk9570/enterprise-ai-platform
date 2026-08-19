"""
Sidebar navigation component.
"""
import streamlit as st


def render_sidebar():
    """Render the sidebar navigation."""
    
    with st.sidebar:
        # Logo and title
        st.markdown("""
        <div style="text-align: center; padding: 20px 0;">
            <h1 style="margin: 0;">🤖</h1>
            <h3 style="margin: 5px 0;">Enterprise AI</h3>
            <p style="color: #888; font-size: 0.9em;">100% Local • Zero API Costs</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Navigation
        st.markdown("### 📍 Navigation")
        
        # Use buttons for navigation (more reliable)
        if st.button("🏠 Home", key="nav_home", use_container_width=True):
            st.switch_page("Home.py")
        
        if st.button("💬 Chat", key="nav_chat", use_container_width=True):
            st.switch_page("pages/1_Chat.py")
        
        if st.button("📊 Analytics", key="nav_analytics", use_container_width=True):
            st.switch_page("pages/2_Analytics_Dashboard.py")
        
        if st.button("🎨 Image Studio", key="nav_image", use_container_width=True):
            st.switch_page("pages/3_Image_Studio.py")
        
        if st.button("📈 Chart Builder", key="nav_chart", use_container_width=True):
            st.switch_page("pages/4_Chart_Builder.py")
        
        if st.button("⚙️ Settings", key="nav_settings", use_container_width=True):
            st.switch_page("pages/5_Settings.py")
        
        if st.button("📚 Documentation", key="nav_docs", use_container_width=True):
            st.switch_page("pages/6_Documentation.py")
        
        st.markdown("---")
        
        # User info
        if st.session_state.get("authenticated"):
            user = st.session_state.get("user", {})
            
            st.markdown("### 👤 User")
            st.markdown(f"""
            **{user.get('display_name', user.get('username', 'User'))}**
            <br>
            <small>{user.get('role', 'user').upper()}</small>
            """, unsafe_allow_html=True)
            
            if st.button("🚪 Logout", key="nav_logout", use_container_width=True):
                from src.presentation.web.services.auth_service import AuthService
                auth_service = AuthService()
                auth_service.logout()
                st.session_state.clear()
                st.rerun()
        else:
            st.markdown("### 🔐 Guest")
        
        st.markdown("---")
        
        # System status
        st.markdown("### 📊 System Status")
        
        models_count = len(st.session_state.get("models", []))
        st.metric("Available Models", models_count)
        
        # Connection status
        try:
            from src.presentation.web.services.api_client import APIClient
            api = APIClient()
            health = api.health_check()
            if health.get("success"):
                st.success("🟢 API Connected")
            else:
                st.error("🔴 API Offline")
        except Exception:
            st.warning("🟡 Checking...")
        
        st.markdown("---")
        st.caption("v1.0.0 • Local AI Platform")