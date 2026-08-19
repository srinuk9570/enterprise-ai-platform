"""
Ollama API client for local LLM inference.
Uses the official ollama Python SDK for reliable async/sync handling.
"""
import logging
import asyncio
import subprocess
import time
from functools import partial
from typing import Optional, Dict, Any, List, AsyncGenerator, Tuple
from pathlib import Path

import ollama

from src.shared.config import settings
from src.domain.value_objects.model_parameters import ModelParameters

logger = logging.getLogger(__name__)


class OllamaClient:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or settings.OLLAMA_HOST
        self.default_model = settings.DEFAULT_MODEL
        self.image_model = settings.IMAGE_MODEL
        self._available_models: Optional[List[str]] = None
        self._last_model_check: float = 0
        self._client = ollama.Client(host=self.base_url)
        logger.info(f"OllamaClient initialized with base URL: {self.base_url}")

    async def _run(self, fn, *args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, partial(fn, *args, **kwargs))

    async def health_check(self) -> bool:
        try:
            await self._run(self._client.list)
            return True
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False

    async def list_models(self, force_refresh: bool = False) -> List[str]:
        if not force_refresh and self._available_models and (time.time() - self._last_model_check) < 60:
            return self._available_models
        try:
            result = await self._run(self._client.list)
            models = [m.model for m in result.models]
            self._available_models = models
            self._last_model_check = time.time()
            return models
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []

    async def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        try:
            result = await self._run(self._client.show, model_name)
            return result.model_dump() if hasattr(result, "model_dump") else dict(result)
        except Exception as e:
            logger.error(f"Error getting model info for {model_name}: {e}")
            return None

    async def pull_model(self, model_name: str) -> bool:
        try:
            await self._run(self._client.pull, model_name)
            self._available_models = None
            return True
        except Exception as e:
            logger.error(f"Error pulling model {model_name}: {e}")
            return False

    async def delete_model(self, model_name: str) -> bool:
        try:
            await self._run(self._client.delete, model_name)
            self._available_models = None
            return True
        except Exception as e:
            logger.error(f"Error deleting model {model_name}: {e}")
            return False

    async def chat(self, model: str, messages: List[Dict[str, str]], parameters: Optional[ModelParameters] = None) -> Tuple[str, Dict[str, Any]]:
        params = parameters or ModelParameters.balanced()
        options = params.to_dict() if hasattr(params, "to_dict") else {}
        start_time = time.time()
        try:
            response = await self._run(self._client.chat, model=model, messages=messages, options=options, stream=False)
            response_text = response.message.content or ""
            metadata = {
                "model": response.model,
                "tokens": (response.eval_count or 0) + (response.prompt_eval_count or 0),
                "prompt_tokens": response.prompt_eval_count or 0,
                "completion_tokens": response.eval_count or 0,
                "total_duration": response.total_duration or 0,
                "load_duration": response.load_duration or 0,
                "finish_reason": "stop",
                "generation_time_ms": (time.time() - start_time) * 1000,
            }
            return response_text, metadata
        except Exception as e:
            logger.error(f"Chat request error for model {model}: {e}")
            raise

    async def stream_chat(self, model: str, messages: List[Dict[str, str]], parameters: Optional[ModelParameters] = None) -> AsyncGenerator[Dict[str, Any], None]:
        params = parameters or ModelParameters.balanced()
        options = params.to_dict() if hasattr(params, "to_dict") else {}
        loop = asyncio.get_event_loop()
        queue: asyncio.Queue = asyncio.Queue()
        DONE_SENTINEL = object()

        def _stream_worker():
            try:
                for chunk in self._client.chat(model=model, messages=messages, options=options, stream=True):
                    content = chunk.message.content or ""
                    payload: Dict[str, Any] = {"content": content}
                    if chunk.done:
                        payload["done"] = True
                        payload["metadata"] = {"model": chunk.model, "tokens": (chunk.eval_count or 0) + (chunk.prompt_eval_count or 0), "finish_reason": "stop"}
                    loop.call_soon_threadsafe(queue.put_nowait, payload)
            except Exception as e:
                loop.call_soon_threadsafe(queue.put_nowait, {"error": str(e)})
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, DONE_SENTINEL)

        loop.run_in_executor(None, _stream_worker)
        while True:
            item = await queue.get()
            if item is DONE_SENTINEL:
                break
            if "error" in item:
                raise Exception(item["error"])
            yield item

    async def generate_embeddings(self, model: str, texts: List[str]) -> List[List[float]]:
        embeddings = []
        for text in texts:
            try:
                result = await self._run(self._client.embeddings, model=model, prompt=text)
                embeddings.append(result.embedding or [])
            except Exception as e:
                logger.error(f"Embedding failed: {e}")
                embeddings.append([])
        return embeddings

    async def check_model_availability(self, model_name: str) -> bool:
        models = await self.list_models()
        return model_name in models

    def check_model_availability_sync(self, model_name: str) -> bool:
        try:
            result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                for line in result.stdout.strip().split("\n")[1:]:
                    parts = line.split()
                    if parts and parts[0] == model_name:
                        return True
            return False
        except Exception as e:
            logger.error(f"Error checking model availability: {e}")
            return False

    async def get_model_size(self, model_name: str) -> Optional[int]:
        info = await self.get_model_info(model_name)
        return info.get("size", 0) if info else None

    async def unload_model(self, model_name: str) -> bool:
        try:
            await self._run(self._client.generate, model=model_name, prompt="", keep_alive=0)
            return True
        except Exception as e:
            logger.error(f"Error unloading model: {e}")
            return False

    async def keep_model_alive(self, model_name: str, keep_alive: str = "5m") -> bool:
        try:
            await self._run(self._client.generate, model=model_name, prompt="", keep_alive=keep_alive)
            return True
        except Exception as e:
            logger.error(f"Error keeping model alive: {e}")
            return False

    async def close(self) -> None:
        pass


class OllamaClientSync:
    def __init__(self):
        self.default_model = settings.DEFAULT_MODEL

    def list_models(self) -> List[str]:
        try:
            result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return [line.split()[0] for line in result.stdout.strip().split("\n")[1:] if line.split()]
            return []
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []

    def chat(self, model: str, prompt: str, system_prompt: Optional[str] = None) -> str:
        try:
            cmd = ["ollama", "run", model]
            if system_prompt:
                cmd.extend(["--system", system_prompt])
            result = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=300)
            return result.stdout.strip() if result.returncode == 0 else ""
        except subprocess.TimeoutExpired:
            logger.error("Chat timeout")
            return ""
        except Exception as e:
            logger.error(f"Chat error: {e}")
            return ""

    def check_model_exists(self, model_name: str) -> bool:
        return model_name in self.list_models()
