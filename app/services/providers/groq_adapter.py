"""Groq provider adapter.

Supports:
- Llama 3.1 (8B, 70B, 405B)
- Mixtral 8x7B
- Gemma 7B
- Ultra-fast inference
"""
from typing import List, Optional, Dict, Any, AsyncIterator
import asyncio
import logging
from groq import AsyncGroq, APIError, RateLimitError as GroqRateLimit, AuthenticationError as GroqAuthError

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


class GroqAdapter(ProviderAdapter):
    """Groq API adapter (OpenAI-compatible)."""
    
    def __init__(self, config: ProviderConfig):
        """Initialize Groq adapter.
        
        Args:
            config: Provider configuration with api_key
        """
        super().__init__(config)
        
        # Initialize Groq client (OpenAI-compatible)
        self.client = AsyncGroq(
            api_key=config.api_key,
            timeout=config.timeout,
            max_retries=config.max_retries,
        )
        
        logger.info("Groq adapter initialized")
    
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
        """Send chat completion request to Groq.
        
        Args:
            messages: List of chat messages
            model: Model identifier (llama3-70b, mixtral-8x7b, etc.)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            top_p: Nucleus sampling
            functions: Function definitions
            function_call: Function call mode
            tools: Tool definitions
            tool_choice: Tool choice mode
            **kwargs: Additional parameters
            
        Returns:
            ChatResponse with model output
        """
        try:
            # Convert messages to OpenAI format
            groq_messages = self._convert_messages(messages)
            
            # Build request parameters
            params = {
                "model": model,
                "messages": groq_messages,
                "temperature": temperature,
            }
            
            if max_tokens:
                params["max_tokens"] = max_tokens
            if top_p:
                params["top_p"] = top_p
            
            # Note: Groq supports tools but implementation varies
            if tools:
                params["tools"] = tools
                if tool_choice:
                    params["tool_choice"] = tool_choice
            
            # Add additional parameters
            params.update(kwargs)
            
            # Make request
            response = await self.client.chat.completions.create(**params)
            
            # Extract response
            choice = response.choices[0]
            message = choice.message
            
            return ChatResponse(
                content=message.content or "",
                role=MessageRole(message.role),
                finish_reason=choice.finish_reason,
                function_call=message.function_call.model_dump() if hasattr(message, 'function_call') and message.function_call else None,
                tool_calls=[tc.model_dump() for tc in message.tool_calls] if hasattr(message, 'tool_calls') and message.tool_calls else None,
                usage={
                    "tokens_input": response.usage.prompt_tokens,
                    "tokens_output": response.usage.completion_tokens,
                    "tokens_total": response.usage.total_tokens,
                } if response.usage else None,
                model=response.model,
            )
            
        except GroqRateLimit as e:
            logger.warning(f"Groq rate limit hit: {e}")
            raise RateLimitError(
                message=str(e),
                provider="groq",
                status_code=429,
                error_type="rate_limit"
            )
        except GroqAuthError as e:
            logger.error(f"Groq authentication failed: {e}")
            raise AuthenticationError(
                message=str(e),
                provider="groq",
                status_code=401,
                error_type="authentication"
            )
        except asyncio.TimeoutError as e:
            logger.error(f"Groq request timeout: {e}")
            raise ProviderTimeoutError(
                message="Request timed out",
                provider="groq",
                error_type="timeout"
            )
        except APIError as e:
            logger.error(f"Groq API error: {e}")
            raise ProviderError(
                message=str(e),
                provider="groq",
                error_type="api_error"
            )
        except Exception as e:
            logger.error(f"Unexpected error in Groq chat: {e}")
            raise ProviderError(
                message=f"Unexpected error: {str(e)}",
                provider="groq",
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
        """Stream chat completion from Groq.
        
        Args:
            messages: List of chat messages
            model: Model identifier
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            top_p: Nucleus sampling
            functions: Function definitions
            function_call: Function call mode
            tools: Tool definitions
            tool_choice: Tool choice mode
            **kwargs: Additional parameters
            
        Yields:
            Content chunks as they arrive
        """
        try:
            # Convert messages
            groq_messages = self._convert_messages(messages)
            
            # Build request parameters
            params = {
                "model": model,
                "messages": groq_messages,
                "temperature": temperature,
                "stream": True,
            }
            
            if max_tokens:
                params["max_tokens"] = max_tokens
            if top_p:
                params["top_p"] = top_p
            
            if tools:
                params["tools"] = tools
                if tool_choice:
                    params["tool_choice"] = tool_choice
            
            # Add additional parameters
            params.update(kwargs)
            
            # Stream response
            stream = await self.client.chat.completions.create(**params)
            
            async for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta.content:
                        yield delta.content
                        
        except Exception as e:
            logger.error(f"Error in Groq stream: {e}")
            raise ProviderError(
                message=f"Stream error: {str(e)}",
                provider="groq",
                error_type="stream_error"
            )
    
    async def embed(
        self,
        text: str,
        model: Optional[str] = None,
        **kwargs
    ) -> EmbeddingResponse:
        """Generate embedding.
        
        Note: Groq doesn't provide embeddings API.
        
        Args:
            text: Text to embed
            model: Not used
            **kwargs: Not used
            
        Raises:
            NotImplementedError: Groq doesn't support embeddings
        """
        raise NotImplementedError("Groq doesn't provide an embeddings API")
    
    async def embed_batch(
        self,
        texts: List[str],
        model: Optional[str] = None,
        **kwargs
    ) -> List[EmbeddingResponse]:
        """Generate embeddings for multiple texts.
        
        Note: Groq doesn't provide embeddings API.
        
        Args:
            texts: Texts to embed
            model: Not used
            **kwargs: Not used
            
        Raises:
            NotImplementedError: Groq doesn't support embeddings
        """
        raise NotImplementedError("Groq doesn't provide an embeddings API")
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List available Groq models.
        
        Returns:
            List of model information
        """
        try:
            response = await self.client.models.list()
            
            return [
                {
                    "id": model.id,
                    "created": model.created,
                    "owned_by": model.owned_by,
                }
                for model in response.data
            ]
            
        except Exception as e:
            logger.error(f"Groq list models error: {e}")
            # Return hardcoded list as fallback
            return [
                {"id": "llama-3.1-405b-reasoning", "name": "Llama 3.1 405B"},
                {"id": "llama-3.1-70b-versatile", "name": "Llama 3.1 70B"},
                {"id": "llama-3.1-8b-instant", "name": "Llama 3.1 8B"},
                {"id": "mixtral-8x7b-32768", "name": "Mixtral 8x7B"},
                {"id": "gemma-7b-it", "name": "Gemma 7B"},
            ]
