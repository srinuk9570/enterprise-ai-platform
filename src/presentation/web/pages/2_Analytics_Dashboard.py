"""
Streamlit Analytics Dashboard Page.
"""
import streamlit as st
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from src.presentation.web.state.session_store import SessionStore


def main():
    """Analytics Dashboard page."""
    
    st.set_page_config(
        page_title="Analytics - Enterprise AI Platform",
        page_icon="📊",
        layout="wide",
    )
    
    SessionStore.initialize()
    
    if not st.session_state.get("authenticated"):
        st.warning("⚠️ Please login to access this page.")
        st.stop()
    
    st.title("📊 Analytics Dashboard")
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 📍 Navigation")
        if st.button("🏠 Home", use_container_width=True):
            st.switch_page("Home.py")
        if st.button("💬 Chat", use_container_width=True):
            st.switch_page("pages/1_Chat.py")
        if st.button("🎨 Image Studio", use_container_width=True):
            st.switch_page("pages/3_Image_Studio.py")
        st.markdown("---")
        
        st.subheader("📅 Time Period")
        period = st.selectbox("Select Period", ["7 Days", "30 Days", "90 Days", "All Time"], index=1)
        
        st.markdown("---")
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.clear()
            st.switch_page("Home.py")
    
    st.markdown("---")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(label="💬 Total Conversations", value="12")
    with col2:
        st.metric(label="📝 Total Messages", value="156")
    with col3:
        st.metric(label="🎨 Images Generated", value="8")
    with col4:
        st.metric(label="🤖 Tokens Used", value="45.2K")
    
    st.markdown("---")
    
    # Charts
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("📈 Message Activity")
        
        # Sample data
        import pandas as pd
        from datetime import datetime, timedelta
        
        dates = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7, 0, -1)]
        import random
        df_activity = pd.DataFrame({
            "Date": dates,
            "Messages": [random.randint(10, 50) for _ in range(7)],
        })
        
        st.line_chart(df_activity.set_index("Date"))
    
    with col_right:
        st.subheader("🤖 Model Usage")
        
        df_models = pd.DataFrame({
            "Model": ["DeepSeek R1 1.5B", "Llama 3.2 3B"],
            "Usage": [65, 35],
        })
        
        st.bar_chart(df_models.set_index("Model"))
    
    st.markdown("---")
    
    # Recent activity
    st.subheader("📋 Recent Activity")
    
    activities = [
        {"time": "10 minutes ago", "action": "Chat message sent", "model": "DeepSeek R1 1.5B"},
        {"time": "25 minutes ago", "action": "Image generated", "prompt": "A beautiful sunset..."},
        {"time": "1 hour ago", "action": "New conversation started", "model": "Llama 3.2 3B"},
        {"time": "2 hours ago", "action": "Chart created", "type": "Line Chart"},
        {"time": "3 hours ago", "action": "Document uploaded for RAG", "file": "research.pdf"},
    ]
    
    for activity in activities:
        with st.container():
            col1, col2, col3 = st.columns([2, 4, 2])
            with col1:
                st.caption(activity["time"])
            with col2:
                st.markdown(f"**{activity['action']}**")
            with col3:
                if "model" in activity:
                    st.caption(f"Model: {activity['model']}")
                elif "prompt" in activity:
                    st.caption(f"Prompt: {activity['prompt'][:30]}...")
            st.markdown("---")


if __name__ == "__main__":
    main()