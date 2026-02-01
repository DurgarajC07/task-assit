"""Ollama provider adapter for local models.

Supports:
- All Ollama models (Llama, Mistral, etc.)
- Local inference
- Embeddings
- Streaming
"""
from typing import List, Optional, Dict, Any, AsyncIterator
import asyncio
import logging
import aiohttp

from app.services.providers.adapter import (
    ProviderAdapter,
    ProviderConfig,
    ChatMessage,
    ChatResponse,
    EmbeddingResponse,
    MessageRole,
    ProviderError,
    RateLimitError,
    AuthenticationError,
    ProviderTimeoutError,
)

logger = logging.getLogger(__name__)


class OllamaAdapter(ProviderAdapter):
    """Ollama local inference adapter."""
    
    def __init__(self, config: ProviderConfig):
        """Initialize Ollama adapter.
        
        Args:
            config: Provider configuration (base_url defaults to localhost:11434)
        """
        super().__init__(config)
        
        # Set default Ollama URL
        self.base_url = config.base_url or "http://localhost:11434"
        self.timeout = aiohttp.ClientTimeout(total=config.timeout)
        
        logger.info(f"Ollama adapter initialized (URL: {self.base_url})")
    
    async def chat(
        self,
        messages: List[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        functions: Optional[List[Dict[str, Any]]] = None,
        function_call: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
        **kwargs
    ) -> ChatResponse:
        """Send chat completion request to Ollama.
        
        Args:
            messages: List of chat messages
            model: Model identifier (llama3, mistral, etc.)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            top_p: Nucleus sampling
            functions: Not supported
            function_call: Not supported
            tools: Not supported
            tool_choice: Not supported
            **kwargs: Additional parameters
            
        Returns:
            ChatResponse with model output
        """
        try:
            # Convert messages to Ollama format
            ollama_messages = self._convert_messages(messages)
            
            # Build request
            payload = {
                "model": model,
                "messages": ollama_messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                }
            }
            
            if max_tokens:
                payload["options"]["num_predict"] = max_tokens
            if top_p:
                payload["options"]["top_p"] = top_p
            
            # Add additional options
            if kwargs:
                payload["options"].update(kwargs)
            
            # Make request
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{self.base_url}/api/chat",
                    json=payload
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise ProviderError(
                            message=f"Ollama request failed: {error_text}",
                            provider="ollama",
                            status_code=response.status,
                            error_type="api_error"
                        )
                    
                    result = await response.json()
            
            # Extract response
            message = result.get("message", {})
            content = message.get("content", "")
            
            return ChatResponse(
                content=content,
                role=MessageRole.ASSISTANT,
                finish_reason=result.get("done_reason", "stop"),
                usage={
                    "tokens_input": result.get("prompt_eval_count", 0),
                    "tokens_output": result.get("eval_count", 0),
                    "tokens_total": result.get("prompt_eval_count", 0) + result.get("eval_count", 0),
                } if "eval_count" in result else None,
                model=result.get("model", model),
            )
            
        except asyncio.TimeoutError as e:
            logger.error(f"Ollama request timeout: {e}")
            raise ProviderTimeoutError(
                message="Request timed out",
                provider="ollama",
                error_type="timeout"
            )
        except aiohttp.ClientError as e:
            logger.error(f"Ollama connection error: {e}")
            raise ProviderError(
                message=f"Connection error: {str(e)}",
                provider="ollama",
                error_type="connection_error"
            )
        except Exception as e:
            logger.error(f"Unexpected error in Ollama chat: {e}")
            raise ProviderError(
                message=f"Unexpected error: {str(e)}",
                provider="ollama",
                error_type="unknown"
            )
    
    async def stream_chat(
        self,
        messages: List[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        functions: Optional[List[Dict[str, Any]]] = None,
        function_call: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream chat completion from Ollama.
        
        Args:
            messages: List of chat messages
            model: Model identifier
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            top_p: Nucleus sampling
            functions: Not supported
            function_call: Not supported
            tools: Not supported
            tool_choice: Not supported
            **kwargs: Additional parameters
            
        Yields:
            Content chunks as they arrive
        """
        try:
            # Convert messages
            ollama_messages = self._convert_messages(messages)
            
            # Build request
            payload = {
                "model": model,
                "messages": ollama_messages,
                "stream": True,
                "options": {
                    "temperature": temperature,
                }
            }
            
            if max_tokens:
                payload["options"]["num_predict"] = max_tokens
            if top_p:
                payload["options"]["top_p"] = top_p
            
            if kwargs:
                payload["options"].update(kwargs)
            
            # Stream response
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{self.base_url}/api/chat",
                    json=payload
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise ProviderError(
                            message=f"Ollama stream failed: {error_text}",
                            provider="ollama",
                            status_code=response.status,
                            error_type="stream_error"
                        )
                    
                    async for line in response.content:
                        if line:
                            import json
                            try:
                                chunk = json.loads(line)
                                if "message" in chunk:
                                    content = chunk["message"].get("content", "")
                                    if content:
                                        yield content
                            except json.JSONDecodeError:
                                continue
                        
        except Exception as e:
            logger.error(f"Error in Ollama stream: {e}")
            raise ProviderError(
                message=f"Stream error: {str(e)}",
                provider="ollama",
                error_type="stream_error"
            )
    
    async def embed(
        self,
        text: str,
        model: Optional[str] = None,
        **kwargs
    ) -> EmbeddingResponse:
        """Generate embedding using Ollama.
        
        Args:
            text: Text to embed
            model: Embedding model (e.g., nomic-embed-text)
            **kwargs: Additional parameters
            
        Returns:
            EmbeddingResponse with vector
        """
        try:
            model = model or "nomic-embed-text"
            
            payload = {
                "model": model,
                "prompt": text,
            }
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{self.base_url}/api/embeddings",
                    json=payload
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise ProviderError(
                            message=f"Ollama embedding failed: {error_text}",
                            provider="ollama",
                            status_code=response.status,
                            error_type="embedding_error"
                        )
                    
                    result = await response.json()
            
            return EmbeddingResponse(
                embedding=result["embedding"],
                model=model,
                usage=None,  # Ollama doesn't provide token usage
            )
            
        except Exception as e:
            logger.error(f"Ollama embedding error: {e}")
            raise ProviderError(
                message=f"Embedding error: {str(e)}",
                provider="ollama",
                error_type="embedding_error"
            )
    
    async def embed_batch(
        self,
        texts: List[str],
        model: Optional[str] = None,
        **kwargs
    ) -> List[EmbeddingResponse]:
        """Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            model: Embedding model
            **kwargs: Additional parameters
            
        Returns:
            List of EmbeddingResponse
        """
        # Ollama doesn't support batch embeddings, so process sequentially
        results = []
        for text in texts:
            result = await self.embed(text, model, **kwargs)
            results.append(result)
        return results
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List available Ollama models.
        
        Returns:
            List of model information
        """
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise ProviderError(
                            message=f"Ollama list models failed: {error_text}",
                            provider="ollama",
                            status_code=response.status,
                            error_type="list_error"
                        )
                    
                    result = await response.json()
            
            return [
                {
                    "id": model["name"],
                    "name": model["name"],
                    "size": model.get("size", 0),
                    "modified_at": model.get("modified_at"),
                }
                for model in result.get("models", [])
            ]
            
        except Exception as e:
            logger.error(f"Ollama list models error: {e}")
            raise ProviderError(
                message=f"List models error: {str(e)}",
                provider="ollama",
                error_type="list_error"
            )
