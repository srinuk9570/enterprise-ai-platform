"""
Quick test for local image generation.
Run this file to test if image generation works.
"""
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Test the generator
from src.infrastructure.llm.local_image_generator import local_image_generator

print("=" * 50)
print("🖼️  Testing Local Image Generation")
print("=" * 50)
print("First run will download the Flux model (~12GB). This is one-time only!")
print("")

# Generate a simple test image
filepath = local_image_generator.generate(
    prompt="A simple red circle on white background",
    width=512,
    height=512,
)

print("")
print("=" * 50)
print(f"✅ SUCCESS! Image saved to:")
print(f"   {filepath}")
print("=" * 50)