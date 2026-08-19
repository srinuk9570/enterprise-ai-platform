"""
Streamlit Home Page - Main entry point for the web UI.
FIXED VERSION
"""

import streamlit as st
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.presentation.web.services.auth_service import AuthService
from src.presentation.web.state.session_store import SessionStore
from src.shared.config import settings


def main():
    """Main Streamlit application."""

    st.set_page_config(
        page_title=settings.APP_NAME,
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    SessionStore.initialize()

    # Load custom CSS
    css_path = Path(__file__).parent / "assets" / "css" / "custom_theme.css"

    if css_path.exists():
        with open(css_path, encoding="utf-8") as f:
            st.markdown(
                f"<style>{f.read()}</style>",
                unsafe_allow_html=True
            )

    # Authentication check
    if not st.session_state.get("authenticated"):
        render_auth_page()
        return

    # Main app
    render_sidebar()
    render_dashboard()


# =========================================================
# AUTH PAGE
# =========================================================

def render_auth_page():
    """Render login/register page."""

    st.title("🤖 Enterprise AI Platform")
    st.markdown("---")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("""
        ### Welcome to Your Local AI Platform

        - 💬 **Chat** with powerful LLMs
        - 📊 **Create** beautiful charts and analytics
        - 🎨 **Generate** AI images
        - 🔒 **100% Local** - Zero API costs
        """)

    with col2:

        tab1, tab2 = st.tabs(["Login", "Register"])

        with tab1:
            render_login_form()

        with tab2:
            render_register_form()


# =========================================================
# LOGIN
# =========================================================

def render_login_form():
    """Render login form."""

    with st.form("login_form"):

        st.subheader("🔐 Login")

        email = st.text_input(
            "Email or Username",
            placeholder="Enter email or username"
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter password"
        )

        submitted = st.form_submit_button(
            "Login",
            use_container_width=True,
            type="primary"
        )

        if submitted:

            if not email or not password:
                st.error("Please enter email and password")
                return

            auth_service = AuthService()

            try:
                success, result = auth_service.login(email, password)

                print("Login result:", result)

                if success:

                    user_data = {}

                    # SAFETY FIX
                    if isinstance(result, dict):

                        if result.get("user"):
                            user_data = result.get("user")

                        elif result.get("data"):

                            data = result.get("data")

                            if isinstance(data, dict):
                                user_data = data.get("user", {})

                    st.session_state["authenticated"] = True
                    st.session_state["user"] = user_data
                    st.session_state["token"] = result.get("access_token")
                    st.session_state["refresh_token"] = result.get("refresh_token")

                    st.success("Login successful!")

                    st.rerun()

                else:
                    st.error(result)

            except Exception as e:
                st.error(f"Login failed: {str(e)}")


# =========================================================
# REGISTER
# =========================================================

def render_register_form():
    """Render registration form."""

    with st.form("register_form"):

        st.subheader("📝 Create Account")

        username = st.text_input(
            "Username *",
            placeholder="Choose username"
        )

        email = st.text_input(
            "Email *",
            placeholder="your@email.com"
        )

        full_name = st.text_input(
            "Full Name",
            placeholder="John Doe"
        )

        col1, col2 = st.columns(2)

        with col1:
            password = st.text_input(
                "Password *",
                type="password"
            )

        with col2:
            confirm_password = st.text_input(
                "Confirm Password *",
                type="password"
            )

        submitted = st.form_submit_button(
            "Register",
            use_container_width=True,
            type="primary"
        )

        if submitted:

            errors = []

            if len(username) < 3:
                errors.append("Username must be at least 3 characters")

            if "@" not in email:
                errors.append("Enter valid email")

            if len(password) < 8:
                errors.append("Password must be at least 8 characters")

            if password != confirm_password:
                errors.append("Passwords do not match")

            if errors:

                for error in errors:
                    st.error(error)

            else:

                auth_service = AuthService()

                try:
                    success, result = auth_service.register(
                        username=username,
                        email=email,
                        password=password,
                        full_name=full_name,
                    )

                    if success:
                        st.success("Account created successfully!")
                        st.balloons()

                    else:
                        st.error(result)

                except Exception as e:
                    st.error(f"Registration failed: {str(e)}")


# =========================================================
# SIDEBAR
# =========================================================

def render_sidebar():
    """Render sidebar."""

    with st.sidebar:

        st.markdown("""
        <div style="text-align:center;padding:20px 0;">
            <h1>🤖</h1>
            <h3>Enterprise AI</h3>
            <p style="color:gray;">
                100% Local • Zero API Costs
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        st.markdown("### 📍 Navigation")

        # Navigation buttons

        if st.button("🏠 Home", use_container_width=True):
            st.rerun()

        if st.button("💬 Chat", use_container_width=True):
            st.switch_page("pages/1_Chat.py")

        if st.button("📊 Analytics", use_container_width=True):
            st.switch_page("pages/2_Analytics_Dashboard.py")

        if st.button("🎨 Image Studio", use_container_width=True):
            st.switch_page("pages/3_Image_Studio.py")

        if st.button("📈 Chart Builder", use_container_width=True):
            st.switch_page("pages/4_Chart_Builder.py")

        if st.button("⚙️ Settings", use_container_width=True):
            st.switch_page("pages/5_Settings.py")

        if st.button("📚 Documentation", use_container_width=True):
            st.switch_page("pages/6_Documentation.py")

        st.markdown("---")

        # USER SECTION
        if st.session_state.get("authenticated"):

            user = st.session_state.get("user")

            # IMPORTANT FIX
            if user is None:
                user = {}

            display_name = (
                user.get("display_name")
                or user.get("full_name")
                or user.get("username")
                or "User"
            )

            role = user.get("role", "user")

            st.markdown("### 👤 User")

            st.markdown(
                f"""
                **{display_name}**
                <br>
                <small>{role.upper()}</small>
                """,
                unsafe_allow_html=True
            )

            if st.button("🚪 Logout", use_container_width=True):

                try:
                    auth_service = AuthService()
                    auth_service.logout()

                except Exception:
                    pass

                st.session_state.clear()

                st.success("Logged out successfully")

                st.rerun()

        else:
            st.markdown("### 🔐 Guest")

        st.markdown("---")

        st.caption("v1.0.0 • Local AI Platform")


# =========================================================
# DASHBOARD
# =========================================================

def render_dashboard():
    """Render dashboard."""

    user = st.session_state.get("user") or {}

    display_name = (
        user.get("display_name")
        or user.get("full_name")
        or user.get("username")
        or "User"
    )

    st.title(f"🤖 {settings.APP_NAME}")

    st.markdown(f"""
    ### Welcome back, {display_name}! 👋

    Your all-in-one AI platform running locally.
    """)

    st.markdown("---")

    # Metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("💬 Conversations", "0")

    with col2:
        st.metric("📝 Messages", "0")

    with col3:
        st.metric("🎨 Images", "0")

    with col4:
        st.metric("🤖 Models", "3")

    st.markdown("---")

    st.subheader("⚡ Quick Actions")

    q1, q2, q3, q4 = st.columns(4)

    with q1:
        if st.button("💬 New Chat", use_container_width=True):
            st.switch_page("pages/1_Chat.py")

    with q2:
        if st.button("📊 Create Chart", use_container_width=True):
            st.switch_page("pages/4_Chart_Builder.py")

    with q3:
        if st.button("🎨 Generate Image", use_container_width=True):
            st.switch_page("pages/3_Image_Studio.py")

    with q4:
        if st.button("📈 Analytics", use_container_width=True):
            st.switch_page("pages/2_Analytics_Dashboard.py")


# =========================================================
# RUN APP
# =========================================================

if __name__ == "__main__":
    main()