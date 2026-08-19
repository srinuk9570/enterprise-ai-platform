"""
Streamlit Settings Page.
"""

import streamlit as st
from pathlib import Path
import sys

# Add project root
sys.path.insert(
    0,
    str(Path(__file__).parent.parent.parent.parent.parent)
)

from src.presentation.web.state.session_store import SessionStore


def main():
    """Settings page."""

    st.set_page_config(
        page_title="Settings - Enterprise AI Platform",
        page_icon="⚙️",
        layout="wide",
    )

    SessionStore.initialize()

    # Authentication check
    if not st.session_state.get("authenticated"):

        st.warning("⚠️ Please login first.")

        st.stop()

    # Page title
    st.title("⚙️ Settings")

    # =========================
    # SIDEBAR
    # =========================
    with st.sidebar:

        st.markdown("## 📍 Navigation")

        if st.button("🏠 Home", use_container_width=True):
            st.switch_page("Home.py")

        if st.button("💬 Chat", use_container_width=True):
            st.switch_page("pages/1_Chat.py")

        if st.button("🎨 Image Studio", use_container_width=True):
            st.switch_page("pages/3_Image_Studio.py")

        st.markdown("---")

        if st.button("🚪 Logout", use_container_width=True):

            st.session_state.clear()

            st.switch_page("Home.py")

    st.markdown("---")

    # =========================
    # PROFILE
    # =========================
    st.subheader("👤 Profile Settings")

    user = st.session_state.get("user", {})

    with st.form("profile_form"):

        username = st.text_input(
            "Username",
            value=user.get("username", "")
        )

        email = st.text_input(
            "Email",
            value=user.get("email", "")
        )

        full_name = st.text_input(
            "Full Name",
            value=user.get("full_name", "")
        )

        bio = st.text_area(
            "Bio",
            value=user.get("bio", ""),
            height=80
        )

        if st.form_submit_button(
            "💾 Save Profile",
            type="primary"
        ):

            st.success("✅ Profile updated successfully!")

    st.markdown("---")

    # =========================
    # PASSWORD
    # =========================
    st.subheader("🔐 Change Password")

    with st.form("password_form"):

        current_password = st.text_input(
            "Current Password",
            type="password"
        )

        new_password = st.text_input(
            "New Password",
            type="password"
        )

        confirm_password = st.text_input(
            "Confirm New Password",
            type="password"
        )

        if st.form_submit_button(
            "🔄 Change Password",
            type="primary"
        ):

            if new_password != confirm_password:

                st.error("❌ Passwords do not match")

            elif len(new_password) < 6:

                st.error(
                    "❌ Password must be at least 6 characters"
                )

            else:

                st.success(
                    "✅ Password changed successfully!"
                )

    st.markdown("---")

    # =========================
    # AI PREFERENCES
    # =========================
    st.subheader("🤖 AI Preferences")

    with st.form("preferences_form"):

        theme = st.selectbox(
            "Theme",
            ["Dark", "Light"],
            index=0
        )

        default_model = st.selectbox(
            "Default Model",
            [
                "phi3-mini-fast",
                "tinyllama",
                "llama3.2:3b",
                "deepseek-r1:1.5b",
            ],
            index=0
        )

        stream_response = st.checkbox(
            "Enable Stream Response",
            value=True
        )

        notifications = st.checkbox(
            "Enable Notifications",
            value=True
        )

        if st.form_submit_button(
            "💾 Save Preferences",
            type="primary"
        ):

            st.session_state["theme"] = theme

            st.session_state["default_model"] = default_model

            st.session_state["stream_response"] = stream_response

            st.success("✅ Preferences saved!")

    st.markdown("---")

    # =========================
    # API KEYS
    # =========================
    st.subheader("🔑 API Keys")

    st.info(
        "API keys allow secure programmatic access."
    )

    if st.button("Generate New API Key"):

        fake_key = "eap_" + "x" * 32

        st.success("✅ API Key generated!")

        st.code(fake_key, language="text")

        st.warning(
            "⚠️ Save this key now. "
            "It won't be shown again."
        )

    st.markdown("---")

    # =========================
    # SYSTEM INFO
    # =========================
    st.subheader("💻 System Information")

    st.info(
        """
        Recommended for your laptop:

        • Model: phi3-mini-fast
        • Stream Response: Enabled
        • Image Size: 512x512
        • CPU Mode Enabled
        """
    )

    st.markdown("---")

    # =========================
    # DANGER ZONE
    # =========================
    st.subheader("⚠️ Danger Zone")

    with st.expander("Delete Account"):

        st.warning(
            "This action cannot be undone."
        )

        confirm = st.text_input(
            "Type DELETE to confirm"
        )

        delete_enabled = confirm == "DELETE"

        if st.button(
            "🗑️ Delete My Account",
            disabled=not delete_enabled
        ):

            st.error(
                "Account deletion disabled in demo mode."
            )


if __name__ == "__main__":
    main()