"""
Streamlit Documentation Page.
"""
import streamlit as st
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.presentation.web.state.session_store import SessionStore


def main():
    """Documentation page."""
    
    st.set_page_config(
        page_title="Documentation - Enterprise AI Platform",
        page_icon="📚",
        layout="wide",
    )
    
    SessionStore.initialize()
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 📍 Navigation")
        st.page_link("Home.py", label="🏠 Home", icon="🏠")
        st.page_link("pages/1_Chat.py", label="💬 Chat", icon="💬")
        st.markdown("---")
        
        if st.session_state.get("authenticated"):
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.clear()
                st.rerun()
    
    st.title("📚 Documentation")
    st.markdown("---")
    
    st.markdown("""
    ## Getting Started
    
    ### Chat with AI
    1. Navigate to the **Chat** page
    2. Select a model from the dropdown
    3. Type your message and press Enter
    
    ### Generate Images
    1. Go to **Image Studio**
    2. Enter a prompt describing the image
    3. Click **Generate Image**
    
    ### Available Models
    - **DeepSeek R1 1.5B**: Fast reasoning model
    - **Z-Image-Turbo**: AI image generation
    
    ### Tips
    - Be specific in your prompts
    - Use the system prompt to set AI behavior
    - Stream responses for real-time feedback
    """)


if __name__ == "__main__":
    main()