"""
Model selector component.
"""
import streamlit as st
from typing import Optional, List, Dict, Any


class ModelSelector:
    """Model selection component."""

    # Fast CPU-friendly models
    MODEL_INFO = {
        "phi3-mini-fast": {
            "name": "Phi-3 Mini",
            "description": "Fast and lightweight for CPU laptops",
            "context": "4K tokens",
            "size": "2.2 GB",
            "tags": ["fast", "lightweight", "chat"],
        },

        "tinyllama": {
            "name": "TinyLlama",
            "description": "Ultra fast lightweight model",
            "context": "2K tokens",
            "size": "1.1 GB",
            "tags": ["ultra-fast", "lightweight"],
        },

        "llama3.2:3b": {
            "name": "Llama 3.2 3B",
            "description": "Balanced general-purpose model",
            "context": "4K tokens",
            "size": "2.0 GB",
            "tags": ["general", "balanced"],
        },

        "deepseek-r1:1.5b": {
            "name": "DeepSeek R1 1.5B",
            "description": "Reasoning and coding model",
            "context": "4K tokens",
            "size": "1.5 GB",
            "tags": ["reasoning", "coding"],
        },
    }

    @classmethod
    def render(cls, key: str = "model_selector") -> str:
        """Render the model selector and return selected model."""

        # Available models
        available_models = [
                                "phi3-mini-fast",
                                "tinyllama",
                                "llama3.2:3b",
                             ]

        # Default model
        default_model = "phi3-mini-fast"

        if "selected_model" not in st.session_state:
            st.session_state["selected_model"] = default_model

        default_index = 0

        if st.session_state["selected_model"] in available_models:
            default_index = available_models.index(
                st.session_state["selected_model"]
            )

        # Model dropdown
        selected = st.selectbox(
            "Select Model",
            available_models,
            index=default_index,
            key=key,
            help="Choose AI model",
        )

        # Model information
        if selected in cls.MODEL_INFO:
            info = cls.MODEL_INFO[selected]

            with st.expander("ℹ️ Model Info", expanded=False):
                st.markdown(f"### {info['name']}")
                st.caption(info['description'])

                st.markdown(f"**Context:** {info['context']}")
                st.markdown(f"**Size:** {info['size']}")

                tags = " • ".join(
                    [f"`{tag}`" for tag in info["tags"]]
                )

                st.markdown(f"**Tags:** {tags}")

        else:
            with st.expander("ℹ️ Model Info", expanded=False):
                st.markdown(f"### {selected}")
                st.caption("Custom model")

        # Refresh models button
        if st.button("🔄 Refresh Models", key="refresh_models"):

            cls._refresh_models()

            st.rerun()

        # Save selected model
        st.session_state["selected_model"] = selected

        return selected

    @classmethod
    def _refresh_models(cls):
        """Refresh available models from API."""

        try:
            from src.presentation.web.services.api_client import APIClient

            api_client = APIClient()

            response = api_client.list_models()

            if response.get("success"):

                models_data = response.get("data", {})

                models = models_data.get("models", [])

                model_names = [
                    m.get("name")
                    for m in models
                    if m.get("name")
                ]

                if model_names:

                    st.session_state["models"] = model_names

                    st.success(
                        f"Loaded {len(model_names)} models"
                    )

                else:
                    st.warning("No models found")

            else:
                st.error("Failed to load models")

        except Exception as e:
            st.error(f"Error refreshing models: {e}")