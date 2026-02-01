"""Anthropic (Claude) provider adapter.

Supports:
- Claude 3 Opus, Sonnet, Haiku
- Claude 2.1, 2.0
- Streaming responses
- Tool use (function calling)
"""
from typing import List, Optional, Dict, Any, AsyncIterator
import asyncio
import logging
from anthropic import AsyncAnthropic, APIError, RateLimitError as AnthropicRateLimit, AuthenticationError as AnthropicAuthError

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
    InvalidRequestError,
    ProviderTimeoutError,
)

logger = logging.getLogger(__name__)


class AnthropicAdapter(ProviderAdapter):
    """Anthropic (Claude) API adapter."""
    
    def __init__(self, config: ProviderConfig):
        """Initialize Anthropic adapter.
        
        Args:
            config: Provider configuration with api_key
        """
        super().__init__(config)
        
        # Initialize Anthropic client
        self.client = AsyncAnthropic(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout,
            max_retries=config.max_retries,
        )
        
        logger.info("Anthropic adapter initialized")
    
    def _convert_messages_anthropic(self, messages: List[ChatMessage]) -> tuple[Optional[str], List[Dict[str, Any]]]:
        """Convert messages to Anthropic format.
        
        Anthropic separates system message from conversation.
        
        Args:
            messages: List of ChatMessage objects
            
        Returns:
            Tuple of (system_prompt, conversation_messages)
        """
        system_prompt = None
        conversation = []
        
        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                # Extract system message
                system_prompt = msg.content
            else:
                # Convert to Anthropic format
                conversation.append({
                    "role": "user" if msg.role == MessageRole.USER else "assistant",
                    "content": msg.content
                })
        
        return system_prompt, conversation
    
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
        """Send chat completion request to Anthropic.
        
        Args:
            messages: List of chat messages
            model: Model identifier (claude-3-opus, claude-3-sonnet, etc.)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate (required by Anthropic)
            top_p: Nucleus sampling
            functions: Not used (Anthropic uses tools)
            function_call: Not used
            tools: Tool definitions
            tool_choice: Tool choice mode
            **kwargs: Additional parameters
            
        Returns:
            ChatResponse with model output
        """
        try:
            # Convert messages
            system_prompt, conversation = self._convert_messages_anthropic(messages)
            
            # Build request parameters
            params = {
                "model": model,
                "messages": conversation,
                "temperature": temperature,
                "max_tokens": max_tokens or 4096,  # Anthropic requires max_tokens
            }
            
            if system_prompt:
                params["system"] = system_prompt
            if top_p:
                params["top_p"] = top_p
            
            # Add tools if provided
            if tools:
                params["tools"] = tools
                if tool_choice:
                    # Convert tool_choice format if needed
                    if tool_choice == "auto":
                        params["tool_choice"] = {"type": "auto"}
                    elif tool_choice == "required":
                        params["tool_choice"] = {"type": "any"}
                    else:
                        params["tool_choice"] = tool_choice
            
            # Add additional parameters
            params.update(kwargs)
            
            # Make request
            response = await self.client.messages.create(**params)
            
            # Extract content
            content = ""
            tool_calls = []
            
            for block in response.content:
                if block.type == "text":
                    content += block.text
                elif block.type == "tool_use":
                    tool_calls.append({
                        "id": block.id,
                        "type": "function",
                        "function": {
                            "name": block.name,
                            "arguments": block.input
                        }
                    })
            
            return ChatResponse(
                content=content,
                role=MessageRole.ASSISTANT,
                finish_reason=response.stop_reason,
                tool_calls=tool_calls if tool_calls else None,
                usage={
                    "tokens_input": response.usage.input_tokens,
                    "tokens_output": response.usage.output_tokens,
                    "tokens_total": response.usage.input_tokens + response.usage.output_tokens,
                } if response.usage else None,
                model=response.model,
            )
            
        except AnthropicRateLimit as e:
            logger.warning(f"Anthropic rate limit hit: {e}")
            raise RateLimitError(
                message=str(e),
                provider="anthropic",
                status_code=429,
                error_type="rate_limit"
            )
        except AnthropicAuthError as e:
            logger.error(f"Anthropic authentication failed: {e}")
            raise AuthenticationError(
                message=str(e),
                provider="anthropic",
                status_code=401,
                error_type="authentication"
            )
        except asyncio.TimeoutError as e:
            logger.error(f"Anthropic request timeout: {e}")
            raise ProviderTimeoutError(
                message="Request timed out",
                provider="anthropic",
                error_type="timeout"
            )
        except APIError as e:
            logger.error(f"Anthropic API error: {e}")
            raise ProviderError(
                message=str(e),
                provider="anthropic",
                error_type="api_error"
            )
        except Exception as e:
            logger.error(f"Unexpected error in Anthropic chat: {e}")
            raise ProviderError(
                message=f"Unexpected error: {str(e)}",
                provider="anthropic",
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
        """Stream chat completion from Anthropic.
        
        Args:
            messages: List of chat messages
            model: Model identifier
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            top_p: Nucleus sampling
            functions: Not used
            function_call: Not used
            tools: Tool definitions
            tool_choice: Tool choice mode
            **kwargs: Additional parameters
            
        Yields:
            Content chunks as they arrive
        """
        try:
            # Convert messages
            system_prompt, conversation = self._convert_messages_anthropic(messages)
            
            # Build request parameters
            params = {
                "model": model,
                "messages": conversation,
                "temperature": temperature,
                "max_tokens": max_tokens or 4096,
            }
            
            if system_prompt:
                params["system"] = system_prompt
            if top_p:
                params["top_p"] = top_p
            
            # Add tools if provided
            if tools:
                params["tools"] = tools
                if tool_choice:
                    if tool_choice == "auto":
                        params["tool_choice"] = {"type": "auto"}
                    elif tool_choice == "required":
                        params["tool_choice"] = {"type": "any"}
                    else:
                        params["tool_choice"] = tool_choice
            
            # Add additional parameters
            params.update(kwargs)
            
            # Stream response
            async with self.client.messages.stream(**params) as stream:
                async for text in stream.text_stream:
                    yield text
                        
        except Exception as e:
            logger.error(f"Error in Anthropic stream: {e}")
            raise ProviderError(
                message=f"Stream error: {str(e)}",
                provider="anthropic",
                error_type="stream_error"
            )
    
    async def embed(
        self,
        text: str,
        model: Optional[str] = None,
        **kwargs
    ) -> EmbeddingResponse:
        """Generate embedding.
        
        Note: Anthropic doesn't provide an embedding API.
        This raises NotImplementedError.
        
        Args:
            text: Text to embed
            model: Not used
            **kwargs: Not used
            
        Raises:
            NotImplementedError: Anthropic doesn't support embeddings
        """
        raise NotImplementedError("Anthropic doesn't provide an embedding API")
    
    async def embed_batch(
        self,
        texts: List[str],
        model: Optional[str] = None,
        **kwargs
    ) -> List[EmbeddingResponse]:
        """Generate embeddings for multiple texts.
        
        Note: Anthropic doesn't provide an embedding API.
        This raises NotImplementedError.
        
        Args:
            texts: Texts to embed
            model: Not used
            **kwargs: Not used
            
        Raises:
            NotImplementedError: Anthropic doesn't support embeddings
        """
        raise NotImplementedError("Anthropic doesn't provide an embedding API")
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List available Anthropic models.
        
        Note: Anthropic doesn't have a list models endpoint.
        Returns hardcoded list of known models.
        
        Returns:
            List of model information
        """
        # Hardcoded list of Claude models
        return [
            {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus", "context_window": 200000},
            {"id": "claude-3-sonnet-20240229", "name": "Claude 3 Sonnet", "context_window": 200000},
            {"id": "claude-3-haiku-20240307", "name": "Claude 3 Haiku", "context_window": 200000},
            {"id": "claude-2.1", "name": "Claude 2.1", "context_window": 200000},
            {"id": "claude-2.0", "name": "Claude 2.0", "context_window": 100000},
        ]
