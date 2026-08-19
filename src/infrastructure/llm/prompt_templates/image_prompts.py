"""
Image generation prompt templates and enhancers.
"""
from typing import Dict, List, Optional


class ImagePrompts:
    """
    Collection of image generation prompts and style modifiers.
    """
    
    # Style modifiers
    STYLES: Dict[str, str] = {
        "photorealistic": "photorealistic, hyperrealistic, 8k, highly detailed, professional photography",
        "anime": "anime style, manga art, studio ghibli inspired, vibrant colors",
        "oil_painting": "oil painting, classical art style, textured brushstrokes, fine art",
        "watercolor": "watercolor painting, soft colors, artistic, flowing, delicate",
        "cyberpunk": "cyberpunk aesthetic, neon lights, futuristic city, high tech, low life, blade runner style",
        "fantasy": "fantasy art, magical, mystical, ethereal, epic fantasy illustration",
        "minimalist": "minimalist, simple, clean lines, negative space, modern design",
        "vintage": "vintage, retro, film grain, sepia tones, nostalgic, old photograph",
        "3d_render": "3D render, octane render, unreal engine, cinema 4D, hyperrealistic 3D",
        "sketch": "pencil sketch, hand-drawn, charcoal drawing, artistic sketch",
        "pop_art": "pop art style, bold colors, comic book style, andy warhol inspired",
        "steampunk": "steampunk, victorian era, brass and copper, gears, industrial revolution aesthetic",
        "abstract": "abstract art, non-representational, geometric, expressionist, modern art",
        "pixel_art": "pixel art, 8-bit, retro gaming style, pixelated, video game art",
        "vector_art": "vector art, flat design, clean lines, scalable, illustration style",
    }
    
    # Lighting modifiers
    LIGHTING: Dict[str, str] = {
        "studio": "studio lighting, professional photography lighting, soft shadows",
        "golden_hour": "golden hour, warm sunset light, long shadows, magical glow",
        "cinematic": "cinematic lighting, dramatic shadows, film noir, high contrast",
        "natural": "natural lighting, daylight, sunlit, ambient light",
        "neon": "neon lighting, colorful glow, night atmosphere, cyberpunk aesthetic",
        "backlit": "backlit, rim lighting, silhouette, dramatic light from behind",
        "soft": "soft lighting, diffused light, gentle shadows, dreamy atmosphere",
        "harsh": "harsh lighting, strong shadows, midday sun, high contrast",
    }
    
    # Camera/Lens modifiers
    CAMERA: Dict[str, str] = {
        "portrait": "85mm lens, portrait photography, shallow depth of field, bokeh",
        "wide": "wide angle lens, expansive view, 24mm, sweeping landscape",
        "macro": "macro lens, extreme close-up, fine details, 100mm macro",
        "telephoto": "telephoto lens, compressed perspective, 200mm, distant subject",
        "fisheye": "fisheye lens, ultra-wide, distorted perspective, 180 degree view",
        "tilt_shift": "tilt-shift effect, miniature appearance, selective focus",
    }
    
    # Quality boosters
    QUALITY: Dict[str, str] = {
        "high": "8k, ultra high resolution, highly detailed, sharp focus, professional",
        "masterpiece": "masterpiece, award-winning, trending on artstation, breathtaking",
        "cinematic": "cinematic, movie still, 35mm film, anamorphic, dolby vision",
        "product": "product photography, commercial, clean background, studio quality",
    }
    
    # Negative prompts
    NEGATIVE_PROMPTS: Dict[str, str] = {
        "general": "blurry, low quality, distorted, deformed, ugly, bad anatomy, watermark, text, logo",
        "portrait": "blurry face, distorted face, asymmetric face, bad eyes, bad teeth, ugly",
        "landscape": "blurry, noisy, oversaturated, unnatural colors, bad composition",
        "architecture": "distorted perspective, unrealistic, floating objects, bad geometry",
    }
    
    @classmethod
    def enhance_prompt(
        cls,
        base_prompt: str,
        style: Optional[str] = None,
        lighting: Optional[str] = None,
        camera: Optional[str] = None,
        quality: Optional[str] = None,
        additional: Optional[str] = None,
    ) -> str:
        """
        Enhance a base prompt with style, lighting, camera, and quality modifiers.
        """
        parts = [base_prompt]
        
        if style and style in cls.STYLES:
            parts.append(cls.STYLES[style])
        
        if lighting and lighting in cls.LIGHTING:
            parts.append(cls.LIGHTING[lighting])
        
        if camera and camera in cls.CAMERA:
            parts.append(cls.CAMERA[camera])
        
        if quality and quality in cls.QUALITY:
            parts.append(cls.QUALITY[quality])
        
        if additional:
            parts.append(additional)
        
        return ", ".join(parts)
    
    @classmethod
    def get_negative_prompt(cls, prompt_type: str = "general") -> str:
        """Get a negative prompt for the given type."""
        return cls.NEGATIVE_PROMPTS.get(prompt_type, cls.NEGATIVE_PROMPTS["general"])
    
    @classmethod
    def build_image_prompt(
        cls,
        subject: str,
        style: str = "photorealistic",
        composition: Optional[str] = None,
        colors: Optional[str] = None,
        mood: Optional[str] = None,
    ) -> str:
        """
        Build a structured image prompt.
        """
        parts = [subject]
        
        if composition:
            parts.append(composition)
        
        if colors:
            parts.append(f"{colors} colors")
        
        if mood:
            parts.append(f"{mood} mood")
        
        parts.append(cls.STYLES.get(style, style))
        
        return ", ".join(parts)
    
    @classmethod
    def list_styles(cls) -> List[str]:
        """List available style modifiers."""
        return list(cls.STYLES.keys())
    
    @classmethod
    def list_lighting(cls) -> List[str]:
        """List available lighting modifiers."""
        return list(cls.LIGHTING.keys())
    
    @classmethod
    def list_camera(cls) -> List[str]:
        """List available camera/lens modifiers."""
        return list(cls.CAMERA.keys())
    
    @classmethod
    def list_quality(cls) -> List[str]:
        """List available quality boosters."""
        return list(cls.QUALITY.keys())