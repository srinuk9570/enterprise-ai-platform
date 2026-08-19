"""
Streamlit Image Studio Page - AI Image Generation.
"""

import os
import sys
from pathlib import Path

import streamlit as st
from PIL import Image

# Add project root to Python path
sys.path.insert(
    0,
    str(Path(__file__).parent.parent.parent.parent.parent)
)

from src.presentation.web.state.session_store import SessionStore
from src.presentation.web.services.api_client import APIClient
from src.shared.config import settings


def load_image_safely(image_path: Path):
    """Load an image safely and return a PIL Image."""
    try:
        image = Image.open(image_path)
        image.load()
        return image
    except Exception as e:
        raise RuntimeError(f"Could not load image: {e}")


def get_recent_images(limit: int = 6):
    """Get recently generated PNG images."""
    images_dir = Path(settings.GENERATED_IMAGES_PATH)

    if not images_dir.exists():
        return []

    return sorted(
        images_dir.glob("*.png"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )[:limit]


def main():
    """Image Studio page."""

    st.set_page_config(
        page_title="Image Studio - Enterprise AI Platform",
        page_icon="🎨",
        layout="wide",
    )

    SessionStore.initialize()

    # =========================
    # Authentication
    # =========================

    if not st.session_state.get("authenticated"):
        st.warning("⚠️ Please login to access this page.")
        st.stop()

    # =========================
    # Header
    # =========================

    st.title("🎨 AI Image Studio")

    st.markdown(
        "Generate stunning AI images locally using "
        "ComfyUI and Stable Diffusion."
    )

    st.markdown("---")

    # =========================
    # Sidebar
    # =========================

    with st.sidebar:

        st.markdown("### 📍 Navigation")

        if st.button("🏠 Home"):
            st.switch_page("Home.py")

        if st.button("💬 Chat"):
            st.switch_page("pages/1_Chat.py")

        st.markdown("---")

        st.subheader("⚙️ Image Settings")

        width = st.number_input(
            "Width",
            min_value=512,
            max_value=1024,
            value=512,
            step=64,
        )

        height = st.number_input(
            "Height",
            min_value=512,
            max_value=1024,
            value=512,
            step=64,
        )

        st.caption(
            "💡 CPU generation is much faster at 512×512."
        )

        st.markdown("---")

        if st.button("🚪 Logout"):
            st.session_state.clear()
            st.switch_page("Home.py")

    # =========================
    # Prompt
    # =========================

    prompt = st.text_area(
        "Describe the image you want to generate",
        height=120,
        placeholder=(
            "Example: A futuristic AI data center at night, "
            "cinematic lighting, realistic, highly detailed"
        ),
    )

    # =========================
    # Generate Image
    # =========================

    if st.button(
        "🎨 Generate Image",
        type="primary",
        disabled=not prompt.strip(),
    ):

        with st.spinner(
            "🎨 Generating image... "
            "This may take several minutes on CPU."
        ):

            try:

                api_client = APIClient()

                response = api_client.generate_image(
                    prompt=prompt.strip(),
                    width=width,
                    height=height,
                )

                # =========================
                # SUCCESS
                # =========================

                if response.get("success"):

                    st.success("✅ Image generated successfully!")

                    data = response.get("data") or {}

                    file_path = data.get("file_path")

                    # ---------------------------------
                    # Try backend returned file path
                    # ---------------------------------

                    if file_path:

                        returned_path = Path(file_path)

                        # Convert relative path to absolute
                        if not returned_path.is_absolute():
                            returned_path = (
                                Path.cwd() / returned_path
                            )

                        if returned_path.exists():

                            try:

                                image = load_image_safely(
                                    returned_path
                                )

                                st.image(
                                    image,
                                    caption=prompt[:100],
                                )

                                st.caption(
                                    f"📁 Saved to: "
                                    f"{returned_path}"
                                )

                            except Exception as e:

                                st.error(
                                    f"Could not load generated "
                                    f"image: {e}"
                                )

                        else:

                            st.warning(
                                "⚠️ Backend returned an image path "
                                "that does not exist."
                            )

                    # ---------------------------------
                    # Fallback
                    # ---------------------------------

                    # Always check configured image directory
                    recent_images = get_recent_images(limit=1)

                    if recent_images:

                        latest = recent_images[0]

                        # Only display fallback if we didn't
                        # already display the returned image.
                        returned_exists = False

                        if file_path:

                            returned_path = Path(file_path)

                            if not returned_path.is_absolute():
                                returned_path = (
                                    Path.cwd() / returned_path
                                )

                            returned_exists = (
                                returned_path.exists()
                            )

                        if not returned_exists:

                            st.info(
                                f"Using latest generated image: "
                                f"{latest.name}"
                            )

                            try:

                                image = load_image_safely(
                                    latest
                                )

                                st.image(
                                    image,
                                    caption=prompt[:100],
                                )

                                st.caption(
                                    f"📁 {latest}"
                                )

                            except Exception as e:

                                st.error(
                                    f"Could not load latest image: "
                                    f"{e}"
                                )

                    elif not file_path:

                        st.warning(
                            "⚠️ Image was generated, but no "
                            "image file could be located."
                        )

                # =========================
                # FAILED
                # =========================

                else:

                    error_message = response.get(
                        "error",
                        "Unknown error occurred",
                    )

                    st.error(
                        f"❌ Image generation failed: "
                        f"{error_message}"
                    )

            except Exception as e:

                st.error(
                    f"❌ System Error: {e}"
                )

    # =========================
    # Recent Generations
    # =========================

    st.markdown("---")

    st.subheader("🖼️ Recent Generations")

    images_dir = Path(settings.GENERATED_IMAGES_PATH)

    if not images_dir.exists():

        st.info(
            f"No image directory found yet:\n"
            f"`{images_dir}`"
        )

    else:

        image_files = get_recent_images(limit=6)

        if not image_files:

            st.info("No generated images yet.")

        else:

            cols = st.columns(3)

            for i, img_path in enumerate(image_files):

                with cols[i % 3]:

                    try:

                        image = load_image_safely(img_path)

                        st.image(image)

                        st.caption(img_path.name)

                    except Exception as e:

                        st.error(
                            f"Could not load "
                            f"{img_path.name}: {e}"
                        )


if __name__ == "__main__":
    main()