"""
Streaming handler for Server-Sent Events (SSE) and WebSocket streaming.
"""
import logging
import json
import asyncio
from typing import AsyncGenerator, Optional, Dict, Any, Callable
from dataclasses import dataclass
import time

logger = logging.getLogger(__name__)


@dataclass
class StreamChunk:
    """Represents a chunk of streamed content."""
    
    content: str
    is_final: bool = False
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    def to_sse(self) -> str:
        """Convert to Server-Sent Events format."""
        data = {
            "content": self.content,
            "is_final": self.is_final,
        }
        if self.metadata:
            data["metadata"] = self.metadata
        if self.error:
            data["error"] = self.error
        
        return f"data: {json.dumps(data)}\n\n"
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps({
            "content": self.content,
            "is_final": self.is_final,
            "metadata": self.metadata,
            "error": self.error,
        })


class StreamingHandler:
    """
    Handler for streaming LLM responses.
    Supports SSE, WebSocket, and async generators.
    """
    
    def __init__(self, ollama_client):
        self.ollama_client = ollama_client
        self._active_streams: Dict[str, asyncio.Task] = {}
    
    async def stream_to_sse(
        self,
        model: str,
        messages: list,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Stream response as Server-Sent Events.
        
        Usage:
            async for sse_chunk in handler.stream_to_sse(model, messages):
                yield sse_chunk
        """
        try:
            async for chunk in self.ollama_client.stream_chat(model, messages, parameters):
                if "content" in chunk:
                    stream_chunk = StreamChunk(content=chunk["content"])
                    yield stream_chunk.to_sse()
                
                if chunk.get("done"):
                    stream_chunk = StreamChunk(
                        content="",
                        is_final=True,
                        metadata=chunk.get("metadata"),
                    )
                    yield stream_chunk.to_sse()
                    
        except Exception as e:
            logger.error(f"Stream error: {e}")
            error_chunk = StreamChunk(content="", error=str(e))
            yield error_chunk.to_sse()
    
    async def stream_to_websocket(
        self,
        websocket,
        model: str,
        messages: list,
        parameters: Optional[Dict[str, Any]] = None,
        stream_id: Optional[str] = None,
    ) -> None:
        """
        Stream response to a WebSocket connection.
        """
        stream_id = stream_id or str(id(websocket))
        
        try:
            self._active_streams[stream_id] = asyncio.current_task()
            
            async for chunk in self.ollama_client.stream_chat(model, messages, parameters):
                if "content" in chunk:
                    await websocket.send_json({
                        "type": "chunk",
                        "content": chunk["content"],
                        "stream_id": stream_id,
                    })
                
                if chunk.get("done"):
                    await websocket.send_json({
                        "type": "done",
                        "stream_id": stream_id,
                        "metadata": chunk.get("metadata"),
                    })
                    
        except asyncio.CancelledError:
            logger.info(f"Stream {stream_id} cancelled")
            await websocket.send_json({
                "type": "cancelled",
                "stream_id": stream_id,
            })
        except Exception as e:
            logger.error(f"WebSocket stream error: {e}")
            await websocket.send_json({
                "type": "error",
                "error": str(e),
                "stream_id": stream_id,
            })
        finally:
            self._active_streams.pop(stream_id, None)
    
    async def stream_to_callback(
        self,
        model: str,
        messages: list,
        callback: Callable[[str], None],
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Stream response to a callback function.
        Returns final metadata.
        """
        accumulated = ""
        final_metadata = {}
        
        async for chunk in self.ollama_client.stream_chat(model, messages, parameters):
            if "content" in chunk:
                accumulated += chunk["content"]
                callback(chunk["content"])
            
            if chunk.get("done"):
                final_metadata = chunk.get("metadata", {})
        
        return {
            "content": accumulated,
            "metadata": final_metadata,
        }
    
    async def stream_with_throttling(
        self,
        model: str,
        messages: list,
        min_interval_ms: int = 50,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Stream with throttling to control output rate.
        """
        last_yield = 0.0
        buffer = ""
        
        async for chunk in self.ollama_client.stream_chat(model, messages, parameters):
            if "content" in chunk:
                buffer += chunk["content"]
                
                now = time.time() * 1000
                if now - last_yield >= min_interval_ms:
                    yield buffer
                    buffer = ""
                    last_yield = now
            
            if chunk.get("done"):
                if buffer:
                    yield buffer
                break
    
    async def stream_with_word_boundaries(
        self,
        model: str,
        messages: list,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[StreamChunk, None]:
        """
        Stream that yields complete words when possible.
        """
        buffer = ""
        
        async for chunk in self.ollama_client.stream_chat(model, messages, parameters):
            if "content" in chunk:
                buffer += chunk["content"]
                
                # Find word boundaries
                words = buffer.split()
                if len(words) > 1:
                    # Yield all complete words except the last (which may be partial)
                    complete = " ".join(words[:-1])
                    yield StreamChunk(content=complete + " ")
                    buffer = words[-1]
            
            if chunk.get("done"):
                if buffer:
                    yield StreamChunk(content=buffer)
                yield StreamChunk(content="", is_final=True, metadata=chunk.get("metadata"))
    
    def cancel_stream(self, stream_id: str) -> bool:
        """
        Cancel an active stream.
        """
        if stream_id in self._active_streams:
            task = self._active_streams[stream_id]
            task.cancel()
            return True
        return False
    
    def get_active_streams(self) -> Dict[str, str]:
        """
        Get information about active streams.
        """
        return {
            stream_id: "active" if not task.done() else "done"
            for stream_id, task in self._active_streams.items()
        }
    
    async def stream_heartbeat(
        self,
        interval_seconds: int = 30,
    ) -> AsyncGenerator[str, None]:
        """
        Send heartbeat messages during long streams.
        """
        while True:
            await asyncio.sleep(interval_seconds)
            yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"


class SSEFormatter:
    """
    Utility for formatting Server-Sent Events.
    """
    
    @staticmethod
    def format_event(event_type: str, data: Any, id: Optional[str] = None) -> str:
        """Format an SSE event."""
        lines = []
        
        if id:
            lines.append(f"id: {id}")
        
        lines.append(f"event: {event_type}")
        
        if isinstance(data, (dict, list)):
            data = json.dumps(data)
        
        for line in str(data).split("\n"):
            lines.append(f"data: {line}")
        
        lines.append("")
        return "\n".join(lines)
    
    @staticmethod
    def format_chunk(content: str, metadata: Optional[Dict] = None) -> str:
        """Format a content chunk as SSE."""
        data = {"content": content}
        if metadata:
            data["metadata"] = metadata
        return SSEFormatter.format_event("chunk", data)
    
    @staticmethod
    def format_done(metadata: Optional[Dict] = None) -> str:
        """Format a completion event."""
        data = {"done": True}
        if metadata:
            data["metadata"] = metadata
        return SSEFormatter.format_event("done", data)
    
    @staticmethod
    def format_error(error: str) -> str:
        """Format an error event."""
        return SSEFormatter.format_event("error", {"error": error})
    
    @staticmethod
    def format_heartbeat() -> str:
        """Format a heartbeat event."""
        return SSEFormatter.format_event("heartbeat", {"timestamp": time.time()})