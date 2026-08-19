"""
Model registry for managing available LLM models and their capabilities.
"""
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ModelCapability(str, Enum):
    """Model capabilities."""
    CHAT = "chat"
    COMPLETION = "completion"
    CODE = "code"
    IMAGE_GENERATION = "image_generation"
    EMBEDDING = "embedding"
    VISION = "vision"
    FUNCTION_CALLING = "function_calling"
    REASONING = "reasoning"


class ModelSize(str, Enum):
    """Model size categories."""
    TINY = "tiny"      # < 1B params
    SMALL = "small"    # 1-3B params
    MEDIUM = "medium"  # 3-7B params
    LARGE = "large"    # 7-13B params
    XLARGE = "xlarge"  # > 13B params


@dataclass
class ModelInfo:
    """Information about a model."""
    
    name: str
    display_name: str
    provider: str = "ollama"
    size: ModelSize = ModelSize.MEDIUM
    capabilities: List[ModelCapability] = field(default_factory=list)
    context_length: int = 4096
    description: str = ""
    tags: List[str] = field(default_factory=list)
    recommended_for: List[str] = field(default_factory=list)
    is_experimental: bool = False
    requires_gpu: bool = False
    min_ram_gb: int = 8
    
    # Performance characteristics
    tokens_per_second: float = 0.0
    quality_score: float = 0.0  # 0-1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "provider": self.provider,
            "size": self.size.value,
            "capabilities": [c.value for c in self.capabilities],
            "context_length": self.context_length,
            "description": self.description,
            "tags": self.tags,
            "recommended_for": self.recommended_for,
            "is_experimental": self.is_experimental,
            "requires_gpu": self.requires_gpu,
            "min_ram_gb": self.min_ram_gb,
            "tokens_per_second": self.tokens_per_second,
            "quality_score": self.quality_score,
        }


class ModelRegistry:
    """
    Registry of available models with their capabilities and metadata.
    """
    
    # Pre-defined model configurations
    BUILTIN_MODELS: Dict[str, ModelInfo] = {
        # DeepSeek models
        "deepseek-r1:1.5b": ModelInfo(
            name="deepseek-r1:1.5b",
            display_name="DeepSeek R1 1.5B",
            provider="ollama",
            size=ModelSize.SMALL,
            capabilities=[ModelCapability.CHAT, ModelCapability.REASONING, ModelCapability.CODE],
            context_length=8192,
            description="Small reasoning model with strong coding abilities",
            tags=["reasoning", "code", "math"],
            recommended_for=["coding", "problem-solving", "quick-responses"],
            min_ram_gb=4,
            tokens_per_second=50,
            quality_score=0.75,
        ),
        "deepseek-r1:7b": ModelInfo(
            name="deepseek-r1:7b",
            display_name="DeepSeek R1 7B",
            provider="ollama",
            size=ModelSize.MEDIUM,
            capabilities=[ModelCapability.CHAT, ModelCapability.REASONING, ModelCapability.CODE],
            context_length=8192,
            description="Balanced reasoning model with excellent coding and math",
            tags=["reasoning", "code", "math", "balanced"],
            recommended_for=["coding", "problem-solving", "general-purpose"],
            min_ram_gb=8,
            tokens_per_second=30,
            quality_score=0.85,
        ),
        "deepseek-r1:14b": ModelInfo(
            name="deepseek-r1:14b",
            display_name="DeepSeek R1 14B",
            provider="ollama",
            size=ModelSize.LARGE,
            capabilities=[ModelCapability.CHAT, ModelCapability.REASONING, ModelCapability.CODE],
            context_length=16384,
            description="Powerful reasoning model for complex tasks",
            tags=["reasoning", "code", "complex", "high-quality"],
            recommended_for=["complex-coding", "research", "advanced-problem-solving"],
            requires_gpu=True,
            min_ram_gb=16,
            tokens_per_second=20,
            quality_score=0.92,
        ),
        
        # Llama models
        "llama3.2:3b": ModelInfo(
            name="llama3.2:3b",
            display_name="Llama 3.2 3B",
            provider="ollama",
            size=ModelSize.SMALL,
            capabilities=[ModelCapability.CHAT, ModelCapability.COMPLETION],
            context_length=4096,
            description="Fast and efficient general-purpose model",
            tags=["fast", "efficient", "general"],
            recommended_for=["quick-responses", "simple-tasks", "edge-devices"],
            min_ram_gb=4,
            tokens_per_second=60,
            quality_score=0.70,
        ),
        "llama3.2:7b": ModelInfo(
            name="llama3.2:7b",
            display_name="Llama 3.2 7B",
            provider="ollama",
            size=ModelSize.MEDIUM,
            capabilities=[ModelCapability.CHAT, ModelCapability.COMPLETION, ModelCapability.FUNCTION_CALLING],
            context_length=8192,
            description="Solid all-rounder with good general knowledge",
            tags=["balanced", "general", "reliable"],
            recommended_for=["general-purpose", "conversation", "knowledge-tasks"],
            min_ram_gb=8,
            tokens_per_second=35,
            quality_score=0.82,
        ),
        
        # Qwen models
        "qwen2.5:7b": ModelInfo(
            name="qwen2.5:7b",
            display_name="Qwen 2.5 7B",
            provider="ollama",
            size=ModelSize.MEDIUM,
            capabilities=[ModelCapability.CHAT, ModelCapability.CODE, ModelCapability.FUNCTION_CALLING],
            context_length=32768,
            description="Excellent for long context and multilingual tasks",
            tags=["long-context", "multilingual", "code"],
            recommended_for=["long-documents", "translation", "code-generation"],
            min_ram_gb=8,
            tokens_per_second=30,
            quality_score=0.84,
        ),
        
        # Mistral models
        "mistral:7b": ModelInfo(
            name="mistral:7b",
            display_name="Mistral 7B",
            provider="ollama",
            size=ModelSize.MEDIUM,
            capabilities=[ModelCapability.CHAT, ModelCapability.COMPLETION],
            context_length=8192,
            description="Efficient model with strong reasoning",
            tags=["efficient", "reasoning", "fast"],
            recommended_for=["reasoning", "analysis", "efficient-inference"],
            min_ram_gb=8,
            tokens_per_second=40,
            quality_score=0.80,
        ),
        
        # Code-specific models
        "codellama:7b": ModelInfo(
            name="codellama:7b",
            display_name="Code Llama 7B",
            provider="ollama",
            size=ModelSize.MEDIUM,
            capabilities=[ModelCapability.CODE, ModelCapability.COMPLETION],
            context_length=16384,
            description="Specialized for code generation and understanding",
            tags=["code", "programming", "fill-in-middle"],
            recommended_for=["code-generation", "code-review", "debugging"],
            min_ram_gb=8,
            tokens_per_second=35,
            quality_score=0.85,
        ),
        "codellama:13b": ModelInfo(
            name="codellama:13b",
            display_name="Code Llama 13B",
            provider="ollama",
            size=ModelSize.LARGE,
            capabilities=[ModelCapability.CODE, ModelCapability.COMPLETION],
            context_length=16384,
            description="Powerful code generation model",
            tags=["code", "programming", "high-quality"],
            recommended_for=["complex-code", "architecture", "refactoring"],
            requires_gpu=True,
            min_ram_gb=16,
            tokens_per_second=25,
            quality_score=0.90,
        ),
        
        # Image generation models
        "x/z-image-turbo": ModelInfo(
            name="x/z-image-turbo",
            display_name="Z-Image Turbo",
            provider="ollama",
            size=ModelSize.MEDIUM,
            capabilities=[ModelCapability.IMAGE_GENERATION],
            context_length=0,
            description="Fast photorealistic image generation",
            tags=["image", "photorealistic", "fast"],
            recommended_for=["photorealistic-images", "quick-generation"],
            requires_gpu=True,
            min_ram_gb=8,
            quality_score=0.85,
        ),
        "x/flux2-klein:4b": ModelInfo(
            name="x/flux2-klein:4b",
            display_name="Flux.2 Klein 4B",
            provider="ollama",
            size=ModelSize.SMALL,
            capabilities=[ModelCapability.IMAGE_GENERATION],
            context_length=0,
            description="Text-rendering focused image generation",
            tags=["image", "text", "typography"],
            recommended_for=["text-images", "logos", "ui-mockups"],
            min_ram_gb=6,
            quality_score=0.80,
        ),
        
        # Embedding models
        "nomic-embed-text": ModelInfo(
            name="nomic-embed-text",
            display_name="Nomic Embed Text",
            provider="ollama",
            size=ModelSize.TINY,
            capabilities=[ModelCapability.EMBEDDING],
            context_length=8192,
            description="Efficient text embedding model for RAG",
            tags=["embedding", "rag", "semantic-search"],
            recommended_for=["embeddings", "rag", "semantic-search"],
            min_ram_gb=2,
            tokens_per_second=100,
            quality_score=0.75,
        ),
    }
    
    def __init__(self, ollama_client: Optional[Any] = None):
        self.ollama_client = ollama_client
        self._custom_models: Dict[str, ModelInfo] = {}
        self._available_models: List[str] = []
    
    async def refresh_available_models(self) -> List[str]:
        """
        Refresh the list of available models from Ollama.
        """
        if self.ollama_client:
            self._available_models = await self.ollama_client.list_models()
        return self._available_models
    
    def get_model_info(self, model_name: str) -> Optional[ModelInfo]:
        """
        Get information about a specific model.
        """
        # Check built-in models
        if model_name in self.BUILTIN_MODELS:
            return self.BUILTIN_MODELS[model_name]
        
        # Check custom models
        if model_name in self._custom_models:
            return self._custom_models[model_name]
        
        # Try partial match
        for name, info in self.BUILTIN_MODELS.items():
            if model_name in name or name in model_name:
                return info
        
        return None
    
    def register_custom_model(self, model_info: ModelInfo) -> None:
        """
        Register a custom model configuration.
        """
        self._custom_models[model_info.name] = model_info
        logger.info(f"Registered custom model: {model_info.name}")
    
    def list_all_models(self) -> List[ModelInfo]:
        """
        List all known models (built-in and custom).
        """
        models = list(self.BUILTIN_MODELS.values())
        models.extend(self._custom_models.values())
        return models
    
    def list_models_by_capability(self, capability: ModelCapability) -> List[ModelInfo]:
        """
        List models that have a specific capability.
        """
        return [
            m for m in self.list_all_models()
            if capability in m.capabilities
        ]
    
    def list_models_by_tag(self, tag: str) -> List[ModelInfo]:
        """
        List models with a specific tag.
        """
        return [
            m for m in self.list_all_models()
            if tag in m.tags
        ]
    
    def list_models_by_size(self, max_size: ModelSize) -> List[ModelInfo]:
        """
        List models up to a certain size.
        """
        size_order = {
            ModelSize.TINY: 0,
            ModelSize.SMALL: 1,
            ModelSize.MEDIUM: 2,
            ModelSize.LARGE: 3,
            ModelSize.XLARGE: 4,
        }
        
        max_level = size_order.get(max_size, 4)
        
        return [
            m for m in self.list_all_models()
            if size_order.get(m.size, 4) <= max_level
        ]
    
    def recommend_model(
        self,
        task: str,
        available_ram_gb: int = 8,
        has_gpu: bool = False,
        prioritize_speed: bool = False,
    ) -> Optional[ModelInfo]:
        """
        Recommend a model based on task and hardware constraints.
        """
        # Filter by hardware constraints
        candidates = [
            m for m in self.list_all_models()
            if m.min_ram_gb <= available_ram_gb
            and (not m.requires_gpu or has_gpu)
        ]
        
        if not candidates:
            return None
        
        # Task-based filtering
        task_lower = task.lower()
        
        if any(word in task_lower for word in ["code", "programming", "function"]):
            candidates = [m for m in candidates if ModelCapability.CODE in m.capabilities]
        elif any(word in task_lower for word in ["image", "picture", "draw"]):
            candidates = [m for m in candidates if ModelCapability.IMAGE_GENERATION in m.capabilities]
        elif any(word in task_lower for word in ["embed", "search", "similarity"]):
            candidates = [m for m in candidates if ModelCapability.EMBEDDING in m.capabilities]
        elif any(word in task_lower for word in ["reason", "math", "logic", "solve"]):
            candidates = [m for m in candidates if ModelCapability.REASONING in m.capabilities]
        
        if not candidates:
            # Fall back to general chat models
            candidates = [
                m for m in self.list_all_models()
                if ModelCapability.CHAT in m.capabilities
                and m.min_ram_gb <= available_ram_gb
            ]
        
        if not candidates:
            return None
        
        # Sort by appropriate metric
        if prioritize_speed:
            candidates.sort(key=lambda m: m.tokens_per_second, reverse=True)
        else:
            candidates.sort(key=lambda m: m.quality_score, reverse=True)
        
        return candidates[0]
    
    def get_fallback_model(self, primary_model: str) -> Optional[str]:
        """
        Get a fallback model if primary is unavailable.
        """
        fallback_chain = {
            "deepseek-r1:14b": "deepseek-r1:7b",
            "deepseek-r1:7b": "llama3.2:7b",
            "llama3.2:7b": "llama3.2:3b",
            "llama3.2:3b": "qwen2.5:7b",
            "qwen2.5:7b": "mistral:7b",
            "mistral:7b": "llama3.2:3b",
        }
        
        return fallback_chain.get(primary_model, "llama3.2:3b")
    
    def get_model_parameters(self, model_name: str) -> Dict[str, Any]:
        """
        Get recommended parameters for a model.
        """
        model_info = self.get_model_info(model_name)
        
        if not model_info:
            return {
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 2048,
            }
        
        # Adjust parameters based on model characteristics
        if ModelCapability.CODE in model_info.capabilities:
            return {
                "temperature": 0.2,
                "top_p": 0.95,
                "max_tokens": 4096,
            }
        elif ModelCapability.REASONING in model_info.capabilities:
            return {
                "temperature": 0.3,
                "top_p": 0.95,
                "max_tokens": 8192,
            }
        else:
            return {
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 2048,
            }
    
    def export_model_list(self) -> List[Dict[str, Any]]:
        """
        Export all model information as a list of dictionaries.
        """
        return [m.to_dict() for m in self.list_all_models()]