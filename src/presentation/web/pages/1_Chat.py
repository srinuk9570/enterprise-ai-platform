"""
Streamlit Chat Page - AI Conversations.
"""
import streamlit as st
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from src.presentation.web.state.session_store import SessionStore
from src.presentation.web.services.api_client import APIClient


def main():
    """Chat page."""
    
    st.set_page_config(
        page_title="Chat - Enterprise AI Platform",
        page_icon="💬",
        layout="wide",
    )
    
    SessionStore.initialize()
    
    if not st.session_state.get("authenticated"):
        st.warning("⚠️ Please login to access this page.")
        st.stop()
    
    st.title("💬 AI Chat Assistant")
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 📍 Navigation")
        if st.button("🏠 Home", use_container_width=True):
            st.switch_page("../Home.py")
        if st.button("🎨 Image Studio", use_container_width=True):
            st.switch_page("pages/3_Image_Studio.py")
        st.markdown("---")
        
        st.subheader("⚙️ Chat Settings")
        
        models = ["phi3-mini-fast", "tinyllama"]
        selected_model = st.selectbox("Select Model", models, index=0)
        
        with st.expander("📝 System Prompt"):
            system_prompt = st.text_area(
                "System Prompt",
                value="""You are Enterprise AI Assistant, a helpful, professional, general-purpose AI assistant.

Answer the user's current question directly and accurately.
Do not invent personal experiences, qualifications, clients, or real-world activities.
Do not assume facts about the user.
Do not introduce unrelated topics.
If asked about yourself, explain that you are a locally running AI assistant powered by Ollama.
For coding and technical questions, provide practical and accurate answers.
If you do not know something, say so clearly.""",
                height=180
            )
            if system_prompt != st.session_state.get("system_prompt"):
                st.session_state["system_prompt"] = system_prompt
        
        with st.expander("🔧 Advanced Parameters"):
            temperature = st.slider("Temperature", 0.0, 2.0, 0.7)
            top_p = st.slider("Top P", 0.0, 1.0, 0.9)
        
        stream_enabled = st.toggle("📡 Stream Response", value=True)
        
        st.markdown("---")
        
        if st.button("➕ New Conversation", use_container_width=True):
            st.session_state["current_conversation_id"] = None
            st.session_state["messages"] = []
            st.rerun()
        
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state["messages"] = []
            st.rerun()
        
        st.markdown("---")
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.clear()
            st.switch_page("Home.py")
    
    # Main chat area
    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    
    # Display chat history
    for message in st.session_state["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Type your message here..."):
        # Add user message
        st.session_state["messages"].append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get AI response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            api_client = APIClient()
            conversation_id = st.session_state.get("current_conversation_id")
            
            try:
                with st.spinner("Thinking..."):
                    response = api_client.chat(
                        message=prompt,
                        conversation_id=conversation_id,
                        model=selected_model,
                        system_prompt=system_prompt,
                        temperature=temperature,
                        top_p=top_p,
                    )
                    
                    if response.get("success"):
                        data = response.get("data", {})
                        full_response = data.get("message", "No response")
                        if data.get("conversation_id"):
                            st.session_state["current_conversation_id"] = data["conversation_id"]
                        message_placeholder.markdown(full_response)
                    else:
                        message_placeholder.error(f"Error: {response.get('error', 'Unknown error')}")
                
                if full_response and not full_response.startswith("Error:"):
                    st.session_state["messages"].append({"role": "assistant", "content": full_response})
                    
            except Exception as e:
                message_placeholder.error(f"Error: {str(e)}")


if __name__ == "__main__":
    main()