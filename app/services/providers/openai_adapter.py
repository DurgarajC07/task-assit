"""OpenAI provider adapter.

Supports:
- GPT-3.5 Turbo
- GPT-4, GPT-4 Turbo, GPT-4 Vision
- Function calling and tools
- Streaming responses
- Text embeddings
"""
from typing import List, Optional, Dict, Any, AsyncIterator
import asyncio
import logging
from openai import AsyncOpenAI, OpenAIError, RateLimitError as OpenAIRateLimit, AuthenticationError as OpenAIAuthError

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
    ModelNotFoundError,
    ProviderTimeoutError,
)

logger = logging.getLogger(__name__)


class OpenAIAdapter(ProviderAdapter):
    """OpenAI API adapter."""
    
    def __init__(self, config: ProviderConfig):
        """Initialize OpenAI adapter.
        
        Args:
            config: Provider configuration with api_key
        """
        super().__init__(config)
        
        # Initialize OpenAI client
        self.client = AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            organization=config.organization,
            timeout=config.timeout,
            max_retries=config.max_retries,
        )
        
        logger.info("OpenAI adapter initialized")
    
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
        """Send chat completion request to OpenAI.
        
        Args:
            messages: List of chat messages
            model: Model identifier (gpt-3.5-turbo, gpt-4, etc.)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            top_p: Nucleus sampling
            functions: Function definitions (legacy)
            function_call: Function call mode
            tools: Tool definitions
            tool_choice: Tool choice mode
            **kwargs: Additional parameters (presence_penalty, frequency_penalty, etc.)
            
        Returns:
            ChatResponse with model output
        """
        try:
            # Convert messages to OpenAI format
            openai_messages = self._convert_messages(messages)
            
            # Build request parameters
            params = {
                "model": model,
                "messages": openai_messages,
                "temperature": temperature,
            }
            
            if max_tokens:
                params["max_tokens"] = max_tokens
            if top_p:
                params["top_p"] = top_p
            
            # Add functions/tools if provided
            if tools:
                params["tools"] = tools
                if tool_choice:
                    params["tool_choice"] = tool_choice
            elif functions:
                params["functions"] = functions
                if function_call:
                    params["function_call"] = function_call
            
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
                function_call=message.function_call.model_dump() if message.function_call else None,
                tool_calls=[tc.model_dump() for tc in message.tool_calls] if message.tool_calls else None,
                usage={
                    "tokens_input": response.usage.prompt_tokens,
                    "tokens_output": response.usage.completion_tokens,
                    "tokens_total": response.usage.total_tokens,
                } if response.usage else None,
                model=response.model,
            )
            
        except OpenAIRateLimit as e:
            logger.warning(f"OpenAI rate limit hit: {e}")
            raise RateLimitError(
                message=str(e),
                provider="openai",
                status_code=429,
                error_type="rate_limit"
            )
        except OpenAIAuthError as e:
            logger.error(f"OpenAI authentication failed: {e}")
            raise AuthenticationError(
                message=str(e),
                provider="openai",
                status_code=401,
                error_type="authentication"
            )
        except asyncio.TimeoutError as e:
            logger.error(f"OpenAI request timeout: {e}")
            raise ProviderTimeoutError(
                message="Request timed out",
                provider="openai",
                error_type="timeout"
            )
        except OpenAIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise ProviderError(
                message=str(e),
                provider="openai",
                error_type="api_error"
            )
        except Exception as e:
            logger.error(f"Unexpected error in OpenAI chat: {e}")
            raise ProviderError(
                message=f"Unexpected error: {str(e)}",
                provider="openai",
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
        """Stream chat completion from OpenAI.
        
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
            openai_messages = self._convert_messages(messages)
            
            # Build request parameters
            params = {
                "model": model,
                "messages": openai_messages,
                "temperature": temperature,
                "stream": True,
            }
            
            if max_tokens:
                params["max_tokens"] = max_tokens
            if top_p:
                params["top_p"] = top_p
            
            # Add functions/tools
            if tools:
                params["tools"] = tools
                if tool_choice:
                    params["tool_choice"] = tool_choice
            elif functions:
                params["functions"] = functions
                if function_call:
                    params["function_call"] = function_call
            
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
            logger.error(f"Error in OpenAI stream: {e}")
            raise ProviderError(
                message=f"Stream error: {str(e)}",
                provider="openai",
                error_type="stream_error"
            )
    
    async def embed(
        self,
        text: str,
        model: Optional[str] = None,
        **kwargs
    ) -> EmbeddingResponse:
        """Generate embedding using OpenAI.
        
        Args:
            text: Text to embed
            model: Embedding model (default: text-embedding-ada-002)
            **kwargs: Additional parameters
            
        Returns:
            EmbeddingResponse with vector
        """
        try:
            model = model or "text-embedding-ada-002"
            
            response = await self.client.embeddings.create(
                input=text,
                model=model,
                **kwargs
            )
            
            return EmbeddingResponse(
                embedding=response.data[0].embedding,
                model=response.model,
                usage={
                    "tokens_input": response.usage.prompt_tokens,
                    "tokens_total": response.usage.total_tokens,
                } if response.usage else None,
            )
            
        except Exception as e:
            logger.error(f"OpenAI embedding error: {e}")
            raise ProviderError(
                message=f"Embedding error: {str(e)}",
                provider="openai",
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
        try:
            model = model or "text-embedding-ada-002"
            
            response = await self.client.embeddings.create(
                input=texts,
                model=model,
                **kwargs
            )
            
            return [
                EmbeddingResponse(
                    embedding=item.embedding,
                    model=response.model,
                    usage={
                        "tokens_input": response.usage.prompt_tokens // len(texts),
                        "tokens_total": response.usage.total_tokens // len(texts),
                    } if response.usage else None,
                )
                for item in response.data
            ]
            
        except Exception as e:
            logger.error(f"OpenAI batch embedding error: {e}")
            raise ProviderError(
                message=f"Batch embedding error: {str(e)}",
                provider="openai",
                error_type="embedding_error"
            )
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List available OpenAI models.
        
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
            logger.error(f"OpenAI list models error: {e}")
            raise ProviderError(
                message=f"List models error: {str(e)}",
                provider="openai",
                error_type="list_error"
            )
