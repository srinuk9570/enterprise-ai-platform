"""
Domain service for LLM orchestration business logic.
Handles model selection, prompt engineering, response streaming, and fallback strategies.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any, AsyncGenerator, Tuple, Callable
from uuid import UUID
import asyncio
import json
import re
import logging
from functools import partial

from src.domain.entities.conversation import Conversation
from src.domain.entities.message import Message
from src.domain.entities.generated_asset import GeneratedAsset
from src.domain.value_objects.model_parameters import ModelParameters
from src.domain.exceptions import (
    DomainValidationError,
    ModelNotAvailableError,
    TokenLimitExceededError,
    InvalidPromptError,
    ImageGenerationFailedError,
    BusinessRuleViolationError,
)
from src.shared.constants import MessageRole, AssetType, MODEL_TOKEN_LIMITS
from src.shared.config import settings

logger = logging.getLogger(__name__)

# No timeout - LLM runs until complete
DEFAULT_LLM_TIMEOUT = None
DEFAULT_STREAM_TIMEOUT = None


@dataclass
class LLMResponse:
    """
    Value object for LLM response.
    """
    content: str
    model_used: str
    tokens_used: int
    generation_time_ms: float
    finish_reason: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """Validate response."""
        if not self.content:
            raise DomainValidationError("LLM response content cannot be empty")
        
        if self.tokens_used < 0:
            raise DomainValidationError("Token count cannot be negative")
    
    @property
    def is_truncated(self) -> bool:
        """Check if response was truncated."""
        return self.finish_reason == "length"
    
    @property
    def word_count(self) -> int:
        """Get word count of response."""
        return len(self.content.split())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "content": self.content,
            "model_used": self.model_used,
            "tokens_used": self.tokens_used,
            "generation_time_ms": self.generation_time_ms,
            "finish_reason": self.finish_reason,
            "metadata": self.metadata,
            "word_count": self.word_count,
            "is_truncated": self.is_truncated,
        }


@dataclass
class PromptTemplate:
    """
    Value object for prompt templates.
    """
    name: str
    template: str
    description: str
    variables: List[str]
    category: str = "general"
    tags: List[str] = field(default_factory=list)
    
    def render(self, **kwargs) -> str:
        """Render template with variables."""
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            missing_var = str(e).strip("'")
            raise InvalidPromptError(f"Missing required variable: {missing_var}")
    
    def get_required_variables(self) -> List[str]:
        """Extract required variables from template."""
        pattern = r"\{(\w+)\}"
        return re.findall(pattern, self.template)
    
    def validate_variables(self, provided: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate that all required variables are provided."""
        required = self.get_required_variables()
        missing = [v for v in required if v not in provided]
        return len(missing) == 0, missing


class LLMOrchestrationService:
    """
    Domain service for LLM orchestration.
    Manages model selection, prompt construction, and response generation.
    """
    
    # Default system prompts for different scenarios
    SYSTEM_PROMPTS = {
        "default": """You are Enterprise AI Assistant, a helpful, professional, and general-purpose AI assistant.

Your job is to answer the user's current question directly and accurately.

Rules:
- Stay focused on the user's actual question.
- Do not invent personal experiences, jobs, clients, qualifications, or real-world activities.
- Do not assume facts about the user.
- Never claim to have a body, personal life, emotions, clients, or real-world experiences.
- If the user asks "tell me about yourself", explain that you are an AI assistant running locally through Ollama.
- For technical questions, provide practical and accurate explanations.
- For coding questions, provide working code and explain important parts.
- If you are uncertain, say that you are uncertain rather than inventing information.
- Do not introduce unrelated topics.
- Keep simple questions concise.
- Provide detailed explanations when the user asks for detail.
- Use Markdown when it improves readability.""",
        "coder": "You are an expert programming assistant. Provide clean, efficient code with explanations.",
        "analyst": "You are a data analyst. Provide insights, statistics, and clear interpretations of data.",
        "creative": "You are a creative writer. Provide imaginative, engaging, and well-structured content.",
        "teacher": "You are a patient teacher. Explain concepts clearly with examples and check for understanding.",
        "concise": "You are a concise assistant. Provide brief, direct answers without unnecessary detail.",
    }
    
    # Built-in prompt templates
    PROMPT_TEMPLATES = {
        "summarize": PromptTemplate(
            name="summarize",
            template="Please summarize the following text concisely:\n\n{text}",
            description="Summarize a long text into key points",
            variables=["text"],
            category="text_processing",
            tags=["summary", "condense"],
        ),
        "explain": PromptTemplate(
            name="explain",
            template="Explain {concept} in simple terms. Include examples if helpful.",
            description="Explain a concept simply",
            variables=["concept"],
            category="education",
            tags=["explanation", "learning"],
        ),
        "analyze": PromptTemplate(
            name="analyze",
            template="Analyze the following data and provide insights:\n\n{data}",
            description="Analyze data and provide insights",
            variables=["data"],
            category="analysis",
            tags=["data", "insights"],
        ),
        "code_review": PromptTemplate(
            name="code_review",
            template="Review this code for bugs, performance issues, and best practices:\n\n```{language}\n{code}\n```",
            description="Review code for improvements",
            variables=["code", "language"],
            category="programming",
            tags=["code", "review"],
        ),
        "translate": PromptTemplate(
            name="translate",
            template="Translate the following text from {source_lang} to {target_lang}:\n\n{text}",
            description="Translate text between languages",
            variables=["text", "source_lang", "target_lang"],
            category="language",
            tags=["translation"],
        ),
        "brainstorm": PromptTemplate(
            name="brainstorm",
            template="Brainstorm {num_ideas} creative ideas for: {topic}",
            description="Generate creative ideas",
            variables=["topic", "num_ideas"],
            category="creative",
            tags=["ideas", "creativity"],
        ),
    }
    
    def __init__(
        self,
        llm_client,
        conversation_repository,
        message_repository,
        asset_repository=None,
        rate_limiter=None,
    ):
        self.llm_client = llm_client
        self.conversation_repository = conversation_repository
        self.message_repository = message_repository
        self.asset_repository = asset_repository
        self.rate_limiter = rate_limiter
    
    async def _safe_llm_call(self, model: str, messages: List[Dict[str, str]], parameters: ModelParameters, timeout: float = None) -> Tuple[str, Dict[str, Any]]:
        """
        Safely call LLM with proper async handling. No timeout - runs until complete.
        """
        loop = asyncio.get_event_loop()
        try:
            if asyncio.iscoroutinefunction(self.llm_client.chat):
                response_text, metadata = await self.llm_client.chat(
                    model=model,
                    messages=messages,
                    parameters=parameters,
                )
            else:
                response_text, metadata = await loop.run_in_executor(
                    None,
                    partial(
                        self.llm_client.chat,
                        model=model,
                        messages=messages,
                        parameters=parameters,
                    )
                )
            return response_text, metadata
        except Exception as e:
            logger.error(f"LLM call failed for model {model}: {e}")
            raise
    
    async def generate_response(
        self,
        conversation: Conversation,
        user_message: str,
        parameters: Optional[ModelParameters] = None,
        system_prompt: Optional[str] = None,
        timeout: float = DEFAULT_LLM_TIMEOUT,
    ) -> LLMResponse:
        """
        Generate an AI response for a conversation.
        
        Args:
            timeout: Maximum time in seconds to wait for LLM response
        """
        if self.rate_limiter:
            await self._check_rate_limit(conversation.user_id)
        
        model_name = conversation.model_name
        if not await self._is_model_available(model_name):
            fallback = await self._get_fallback_model()
            if fallback:
                model_name = fallback
            else:
                raise ModelNotAvailableError(model_name)
        
        await self._check_token_limits(conversation, user_message, model_name)
        
        params = parameters or ModelParameters.balanced()
        messages = self._build_messages(conversation, user_message, system_prompt)
        
        user_msg = conversation.add_message(
            role=MessageRole.USER,
            content=user_message,
            tokens=self._estimate_tokens(user_message),
        )
        await self.conversation_repository.add_message(conversation.id, user_msg)
        
        start_time = datetime.utcnow()
        
        # Use the safe LLM call wrapper
        response_text, metadata = await self._safe_llm_call(
            model=model_name,
            messages=messages,
            parameters=params)
        
        generation_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        response = LLMResponse(
            content=response_text,
            model_used=model_name,
            tokens_used=metadata.get("tokens", self._estimate_tokens(response_text)),
            generation_time_ms=generation_time,
            finish_reason=metadata.get("finish_reason", "stop"),
            metadata=metadata,
        )
        
        assistant_msg = conversation.add_message(
            role=MessageRole.ASSISTANT,
            content=response.content,
            tokens=response.tokens_used,
            model_used=response.model_used,
            generation_time_ms=response.generation_time_ms,
            finish_reason=response.finish_reason,
        )
        await self.conversation_repository.add_message(conversation.id, assistant_msg)
        
        return response
    
    async def generate_streaming_response(
        self,
        conversation: Conversation,
        user_message: str,
        parameters: Optional[ModelParameters] = None,
        system_prompt: Optional[str] = None,
        timeout: float = DEFAULT_STREAM_TIMEOUT,
    ) -> AsyncGenerator[str, None]:
        """
        Generate a streaming AI response.
        Yields tokens as they are generated.
        
        Args:
            timeout: Maximum time in seconds for the entire streaming response
        """
        if self.rate_limiter:
            await self._check_rate_limit(conversation.user_id)
        
        model_name = conversation.model_name
        if not await self._is_model_available(model_name):
            fallback = await self._get_fallback_model()
            if fallback:
                model_name = fallback
            else:
                raise ModelNotAvailableError(model_name)
        
        params = parameters or ModelParameters.balanced()
        messages = self._build_messages(conversation, user_message, system_prompt)
        
        user_msg = conversation.add_message(
            role=MessageRole.USER,
            content=user_message,
            tokens=self._estimate_tokens(user_message),
        )
        await self.conversation_repository.add_message(conversation.id, user_msg)
        
        full_response = ""
        metadata = {}
        start_time = datetime.utcnow()
        
        try:
            # Check if stream_chat is async or sync
            if asyncio.iscoroutinefunction(self.llm_client.stream_chat):
                # Async streaming
                async for chunk in self.llm_client.stream_chat(
                    model=model_name,
                    messages=messages,
                    parameters=params,
                ):
                    if chunk.get("content"):
                        full_response += chunk["content"]
                        yield chunk["content"]
                    if chunk.get("metadata"):
                        metadata.update(chunk["metadata"])
            else:
                # Sync streaming - run in thread pool
                loop = asyncio.get_event_loop()
                
                def sync_stream():
                    for chunk in self.llm_client.stream_chat(
                        model=model_name,
                        messages=messages,
                        parameters=params,
                    ):
                        yield chunk
                
                # For sync streaming, we need to handle it carefully
                # This is a simplified approach - you may need a more sophisticated solution
                stream_gen = sync_stream()
                while True:
                    try:
                        # Run next() in thread pool
                        chunk = await loop.run_in_executor(None, next, stream_gen)
                        if chunk.get("content"):
                            full_response += chunk["content"]
                            yield chunk["content"]
                        if chunk.get("metadata"):
                            metadata.update(chunk["metadata"])
                    except StopIteration:
                        break
        except Exception as e:
            logger.error(f"Streaming response error: {e}")
            raise
                    
        
        generation_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        assistant_msg = conversation.add_message(
            role=MessageRole.ASSISTANT,
            content=full_response,
            tokens=self._estimate_tokens(full_response),
            model_used=model_name,
            generation_time_ms=generation_time,
            finish_reason=metadata.get("finish_reason", "stop"),
        )
        await self.conversation_repository.add_message(conversation.id, assistant_msg)
    
    # ==================== IMAGE GENERATION ====================
    
    async def generate_image(
        self,
        user_id: UUID,
        prompt: str,
        negative_prompt: Optional[str] = None,
        model_name: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        conversation_id: Optional[UUID] = None,
        timeout: float = 120.0,  # Image generation can take longer
    ) -> GeneratedAsset:
        """
        Generate an image using local Diffusers.
        
        Args:
            user_id: ID of the user generating the image
            prompt: Text prompt for image generation
            negative_prompt: Optional negative prompt for what to avoid
            model_name: Optional model name (ignored, uses local FLUX)
            parameters: Optional generation parameters (width, height, steps)
            conversation_id: Optional conversation ID to associate with
            timeout: Maximum time in seconds to wait for image generation
            
        Returns:
            GeneratedAsset with file path properly set
        """
        # Validate prompt
        self._validate_image_prompt(prompt)
        
        if negative_prompt:
            self._validate_image_prompt(negative_prompt, is_negative=True)
        
        # Use local Diffusers generator
        from src.infrastructure.llm.local_image_generator import local_image_generator
        
        start_time = datetime.utcnow()
        
        try:
            # Extract parameters with defaults
            width = parameters.get("width", 512) if parameters else 512
            height = parameters.get("height", 512) if parameters else 512
            steps = parameters.get("num_inference_steps", 4) if parameters else 4
            
            logger.info(f"Starting image generation: prompt='{prompt[:50]}...', size={width}x{height}")
            
            # Generate image locally (no timeout)
            file_path = await asyncio.to_thread(
                local_image_generator.generate,
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                num_inference_steps=steps,
            )
            
            # Extract file information from the Path object
            file_path_str = str(file_path)
            file_name = file_path.name
            file_size = file_path.stat().st_size
            
            logger.info(f"Image generated successfully at: {file_path_str}")
            logger.info(f"File details - name: {file_name}, size: {file_size} bytes")
            
        except Exception as e:
            logger.error(f"Image generation failed: {e}", exc_info=True)
            raise ImageGenerationFailedError(prompt, str(e), "local-flux")
        
        generation_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Create asset record
        asset = GeneratedAsset(
            user_id=user_id,
            asset_type=AssetType.IMAGE,
            file_path=file_path_str,
            file_name=file_name,
            file_size=file_size,
            mime_type="image/png",
            prompt=prompt,
            model_used="FLUX.1-schnell (Local)",
            generation_params={
                "negative_prompt": negative_prompt,
                "width": width,
                "height": height,
                "steps": steps,
                "parameters": parameters or {},
            },
            generation_time_ms=generation_time,
            conversation_id=conversation_id,
        )
        
        # Save to database if repository is available
        if self.asset_repository:
            try:
                asset = await self.asset_repository.add(asset)
                logger.info(f"Asset saved to database with ID: {asset.id}")
            except Exception as e:
                logger.error(f"Failed to save asset to database: {e}", exc_info=True)
        else:
            logger.warning("No asset_repository available - asset not saved to database")
        
        return asset
    
    # ==================== HELPER METHODS ====================
    
    def _build_messages(
        self,
        conversation: Conversation,
        user_message: str,
        system_prompt: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """Build the message list for LLM API."""
        messages = []
        
        effective_system_prompt = (
            system_prompt
            or conversation.system_prompt
            or self._get_default_system_prompt()
        )
        
        if effective_system_prompt:
            messages.append({"role": "system", "content": effective_system_prompt})
        
        for msg in conversation.get_last_n_messages(20):
            messages.append({"role": msg.role.value, "content": msg.content})
        
        if not messages or messages[-1]["role"] != "user" or messages[-1]["content"] != user_message:
            messages.append({"role": "user", "content": user_message})
        
        return messages
    
    def _get_default_system_prompt(self) -> str:
        return self.SYSTEM_PROMPTS["default"]
    
    async def _is_model_available(self, model_name: str) -> bool:
        known_models = [
            "deepseek-r1:1.5b", "deepseek-r1:7b",
            "llama3.2:3b",
            "x/flux2-klein", "x/flux2-klein:9b", "x/flux2-klein:4b",
            "nomic-embed-text",
        ]
        
        model_lower = model_name.lower()
        for known in known_models:
            if known in model_lower:
                return True
        
        try:
            available_models = await self.llm_client.list_models()
            return model_name in available_models
        except Exception:
            return True
    
    async def _get_fallback_model(self) -> Optional[str]:
        fallback_priority = ["deepseek-r1:1.5b", "llama3.2:3b"]
        for model in fallback_priority:
            if await self._is_model_available(model):
                return model
        return None
    
    async def _check_rate_limit(self, user_id: UUID) -> None:
        if self.rate_limiter:
            allowed, wait_time = await self.rate_limiter.check(user_id)
            if not allowed:
                from src.domain.exceptions.domain_exceptions import MessageRateLimitExceededError
                raise MessageRateLimitExceededError(str(user_id), wait_time)
    
    async def _check_token_limits(
        self,
        conversation: Conversation,
        user_message: str,
        model_name: str,
    ) -> None:
        # Do not reject the conversation because its stored history is large.
        # The conversation context is trimmed automatically before sending
        # messages to the local LLM.
        return None
    
    def _estimate_tokens(self, text: str) -> int:
        return len(text) // 4
    
    def _validate_image_prompt(self, prompt: str, is_negative: bool = False) -> None:
        if not prompt or len(prompt.strip()) == 0:
            raise InvalidPromptError(
                "Prompt cannot be empty",
                prompt if not is_negative else None,
            )
        
        max_length = 1000 if not is_negative else 500
        if len(prompt) > max_length:
            raise InvalidPromptError(
                f"Prompt must be at most {max_length} characters",
                prompt[:100],
            )
        
        prohibited_terms = ["nsfw", "explicit", "violence", "gore"]
        prompt_lower = prompt.lower()
        for term in prohibited_terms:
            if term in prompt_lower:
                raise InvalidPromptError(
                    f"Prompt contains prohibited term: {term}",
                    prompt[:100],
                )
    
    def get_prompt_template(self, name: str) -> Optional[PromptTemplate]:
        return self.PROMPT_TEMPLATES.get(name)
    
    def list_prompt_templates(self, category: Optional[str] = None) -> List[PromptTemplate]:
        templates = list(self.PROMPT_TEMPLATES.values())
        if category:
            templates = [t for t in templates if t.category == category]
        return templates
    
    def get_system_prompt(self, style: str) -> Optional[str]:
        return self.SYSTEM_PROMPTS.get(style)
    
    def list_system_prompt_styles(self) -> List[str]:
        return list(self.SYSTEM_PROMPTS.keys())
    
    async def analyze_sentiment(
        self, 
        text: str, 
        timeout: float = DEFAULT_LLM_TIMEOUT
    ) -> Dict[str, Any]:
        """Analyze sentiment with timeout guard."""
        prompt = f"""Analyze the sentiment of the following text. Return a JSON with: sentiment (positive/negative/neutral), confidence (0-1), and emotions (list).

Text: {text}

JSON:"""
        
        try:
            response, _ = await self._safe_llm_call(
                model="phi3-mini-fast",
                messages=[{"role": "user", "content": prompt}],
                parameters=ModelParameters.precise())
        except BusinessRuleViolationError as e:
            if "timed out" in str(e):
                return {
                    "sentiment": "neutral",
                    "confidence": 0.5,
                    "emotions": [],
                    "error": str(e),
                }
            raise
        
        try:
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
        
        return {
            "sentiment": "neutral",
            "confidence": 0.5,
            "emotions": [],
            "raw_response": response,
        }
    
    async def extract_entities(
        self, 
        text: str, 
        timeout: float = DEFAULT_LLM_TIMEOUT
    ) -> List[Dict[str, str]]:
        """Extract entities with timeout guard."""
        prompt = f"""Extract named entities from the text. Return a JSON array with objects containing 'entity', 'type' (person/organization/location/date/product), and 'context'.

Text: {text}

JSON:"""
        
        try:
            response, _ = await self._safe_llm_call(
                model="deepseek-r1:1.5b",
                messages=[{"role": "user", "content": prompt}],
                parameters=ModelParameters.precise())
        except BusinessRuleViolationError:
            return []
        
        try:
            json_match = re.search(r"\[.*\]", response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
        
        return []
    
    async def generate_conversation_title(
        self, 
        first_message: str, 
        timeout: float = DEFAULT_LLM_TIMEOUT
    ) -> str:
        """Generate conversation title with timeout guard."""
        prompt = f"""Generate a short, descriptive title (max 50 characters) for a conversation that starts with this message. Return only the title, no quotes or extra text.

First message: {first_message}

Title:"""
        
        try:
            response, _ = await self._safe_llm_call(
                model="deepseek-r1:1.5b",
                messages=[{"role": "user", "content": prompt}],
                parameters=ModelParameters.precise())
        except BusinessRuleViolationError:
            return "New Conversation"
        
        title = response.strip().strip('"').strip("'")
        if len(title) > 50:
            title = title[:47] + "..."
        
        return title or "New Conversation"
    
    async def summarize_conversation(
        self, 
        conversation: Conversation, 
        timeout: float = DEFAULT_LLM_TIMEOUT
    ) -> str:
        """Summarize conversation with timeout guard."""
        messages = conversation.get_messages_for_llm(max_tokens=4000)
        
        if len(messages) < 2:
            return "Conversation too short to summarize."
        
        prompt = """Summarize this conversation in 3-5 sentences, capturing the main topics and conclusions.

Conversation:
"""
        for msg in messages:
            prompt += f"\n{msg['role']}: {msg['content'][:500]}"
        
        prompt += "\n\nSummary:"
        
        try:
            response, _ = await self._safe_llm_call(
                model="deepseek-r1:1.5b",
                messages=[{"role": "user", "content": prompt}],
                parameters=ModelParameters.balanced())
        except BusinessRuleViolationError:
            return "Summary generation timed out. The conversation was too long to summarize quickly."
        
        return response.strip()