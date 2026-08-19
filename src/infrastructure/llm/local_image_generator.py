import logging, hashlib, os, time, requests, json
from pathlib import Path
from datetime import datetime
from typing import Optional
from io import BytesIO

logger = logging.getLogger(__name__)

COMFYUI_URL = "http://127.0.0.1:8188"

class LocalImageGenerator:
    def __init__(self):
        print("Image generator ready - using ComfyUI at http://127.0.0.1:8188")

    def generate(self, prompt, negative_prompt=None, width=512, height=512, num_inference_steps=20, guidance_scale=7.5):
        print(f"Generating via ComfyUI: {prompt[:60]}...")

        workflow = {
            "3": {
                "inputs": {
                    "seed": int(time.time()) % 999999999,
                    "steps": num_inference_steps or 20,
                    "cfg": guidance_scale or 7.5,
                    "sampler_name": "euler",
                    "scheduler": "normal",
                    "denoise": 1,
                    "model": ["4", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["5", 0]
                },
                "class_type": "KSampler"
            },
            "4": {
                "inputs": {"ckpt_name": "sd15.safetensors"},
                "class_type": "CheckpointLoaderSimple"
            },
            "5": {
                "inputs": {
                    "width": min(width or 512, 768),
                    "height": min(height or 512, 768),
                    "batch_size": 1
                },
                "class_type": "EmptyLatentImage"
            },
            "6": {
                "inputs": {"text": prompt, "clip": ["4", 1]},
                "class_type": "CLIPTextEncode"
            },
            "7": {
                "inputs": {
                    "text": negative_prompt or "blurry, bad quality, ugly, distorted, watermark",
                    "clip": ["4", 1]
                },
                "class_type": "CLIPTextEncode"
            },
            "8": {
                "inputs": {"samples": ["3", 0], "vae": ["4", 2]},
                "class_type": "VAEDecode"
            },
            "9": {
                "inputs": {"filename_prefix": "ai_platform", "images": ["8", 0]},
                "class_type": "SaveImage"
            },
        }

        try:
            # Check ComfyUI is running
            try:
                requests.get(f"{COMFYUI_URL}/system_stats", timeout=3)
            except Exception:
                raise Exception("ComfyUI is not running! Open a new terminal and run: cd D:\\ComfyUI && python main.py --cpu")

            # Submit job to ComfyUI
            resp = requests.post(
                f"{COMFYUI_URL}/prompt",
                json={"prompt": workflow},
                timeout=10
            )

            if resp.status_code != 200:
                raise Exception(f"ComfyUI rejected job: {resp.text[:200]}")

            prompt_id = resp.json()["prompt_id"]
            print(f"Job submitted to ComfyUI: {prompt_id}")
            print("Generating image (this takes 2-5 minutes on CPU)...")

            # Get timeout from environment variable (loaded from .env by settings)
            timeout_seconds = int(os.getenv("COMFYUI_TIMEOUT", "1200"))
            poll_interval = 2

            # Poll for completion with configurable timeout
            for i in range(timeout_seconds // poll_interval):
                time.sleep(poll_interval)
                try:
                    hist = requests.get(
                        f"{COMFYUI_URL}/history/{prompt_id}",
                        timeout=5
                    ).json()

                    if prompt_id in hist:
                        outputs = hist[prompt_id].get("outputs", {})
                        for node_id, node_output in outputs.items():
                            if "images" in node_output:
                                img_info = node_output["images"][0]
                                img_resp = requests.get(
                                    f"{COMFYUI_URL}/view",
                                    params={
                                        "filename": img_info["filename"],
                                        "subfolder": img_info.get("subfolder", ""),
                                        "type": img_info["type"]
                                    },
                                    timeout=30
                                )
                                if img_resp.status_code == 200:
                                    from PIL import Image
                                    image = Image.open(BytesIO(img_resp.content))
                                    from src.shared.config import settings
                                    images_dir = Path(settings.GENERATED_IMAGES_PATH)
                                    images_dir.mkdir(parents=True, exist_ok=True)
                                    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                                    ph = hashlib.md5(prompt.encode()).hexdigest()[:8]
                                    fp = images_dir / f"{ts}_sd_{ph}.png"
                                    image.save(str(fp), "PNG")
                                    print(f"Real image saved: {fp}")
                                    return fp
                except Exception as e:
                    print(f"Polling error: {e}")

                if i % 15 == 0 and i > 0:
                    elapsed = i * poll_interval
                    print(f"Still generating... ({elapsed}s elapsed)")

            raise Exception(
                f"ComfyUI timed out after {timeout_seconds} seconds"
            )

        except Exception as e:
            raise Exception(f"Image generation failed: {e}")


local_image_generator = LocalImageGenerator()