"""
Chat interface component for Streamlit.
"""
import streamlit as st
from typing import Optional

from src.presentation.web.services.api_client import APIClient


class ChatInterface:
    """Chat interface component."""
    
    @classmethod
    def render(
        cls,
        model: str = "phi3-mini-fast",
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_tokens: int = 2048,
        stream: bool = True,
    ):
        """Render the chat interface."""
        
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
                    if stream:
                        for chunk in api_client.stream_chat(
                            message=prompt,
                            conversation_id=conversation_id,
                            model=model,
                            system_prompt=system_prompt,
                            temperature=temperature,
                            top_p=top_p,
                            max_tokens=max_tokens,
                        ):
                            if chunk.get("type") == "conversation_created":
                                st.session_state["current_conversation_id"] = chunk.get("conversation_id")
                            elif chunk.get("type") == "chunk":
                                full_response += chunk.get("content", "")
                                message_placeholder.markdown(full_response + "▌")
                            elif chunk.get("type") == "done":
                                message_placeholder.markdown(full_response)
                            elif chunk.get("type") == "error":
                                message_placeholder.error(f"Error: {chunk.get('message')}")
                    else:
                        with st.spinner("Thinking..."):
                            response = api_client.chat(
                                message=prompt,
                                conversation_id=conversation_id,
                                model=model,
                                system_prompt=system_prompt,
                                temperature=temperature,
                                top_p=top_p,
                                max_tokens=max_tokens,
                            )
                            
                            if response.get("success"):
                                data = response.get("data", {})
                                full_response = data.get("message", "")
                                if data.get("conversation_id"):
                                    st.session_state["current_conversation_id"] = data["conversation_id"]
                                message_placeholder.markdown(full_response)
                            else:
                                message_placeholder.error(f"Error: {response.get('error')}")
                    
                    if full_response and not full_response.startswith("Error:"):
                        st.session_state["messages"].append({"role": "assistant", "content": full_response})
                        
                except Exception as e:
                    message_placeholder.error(f"Error: {str(e)}")
    
    @classmethod
    def clear_history(cls):
        """Clear chat history."""
        st.session_state["messages"] = []
        st.session_state["current_conversation_id"] = None