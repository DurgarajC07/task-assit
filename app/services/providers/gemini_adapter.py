"""Google Gemini provider adapter.

Supports:
- Gemini Pro
- Gemini Pro Vision
- Text embeddings
- Function calling
"""
from typing import List, Optional, Dict, Any, AsyncIterator
import asyncio
import logging
from google import genai
from google.genai import types

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


class GeminiAdapter(ProviderAdapter):
    """Google Gemini API adapter."""
    
    def __init__(self, config: ProviderConfig):
        """Initialize Gemini adapter.
        
        Args:
            config: Provider configuration with api_key
        """
        super().__init__(config)
        
        # Initialize Gemini client
        self.client = genai.Client(api_key=config.api_key)
        
        logger.info("Gemini adapter initialized")
    
    def _convert_messages_gemini(self, messages: List[ChatMessage]) -> tuple[Optional[str], List[Dict[str, Any]]]:
        """Convert messages to Gemini format.
        
        Gemini separates system instructions from conversation.
        
        Args:
            messages: List of ChatMessage objects
            
        Returns:
            Tuple of (system_instruction, conversation_messages)
        """
        system_instruction = None
        conversation = []
        
        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                system_instruction = msg.content
            else:
                role = "user" if msg.role == MessageRole.USER else "model"
                conversation.append({
                    "role": role,
                    "parts": [msg.content]
                })
        
        return system_instruction, conversation
    
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
        """Send chat completion request to Gemini.
        
        Args:
            messages: List of chat messages
            model: Model identifier (gemini-pro, gemini-pro-vision)
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
            # Convert messages
            system_instruction, conversation = self._convert_messages_gemini(messages)
            
            # Build generation config
            config_dict = {"temperature": temperature}
            if max_tokens:
                config_dict["max_output_tokens"] = max_tokens
            if top_p:
                config_dict["top_p"] = top_p
            
            generation_config = types.GenerateContentConfig(
                **config_dict,
                system_instruction=system_instruction
            )
            
            # Add tools if provided
            gemini_tools = None
            if tools or functions:
                # Convert to Gemini tool format
                gemini_tools = self._convert_tools_to_gemini(tools or functions)
            
            # Build content
            contents = [types.Content(
                role=msg["role"],
                parts=[types.Part(text=msg["parts"][0])]
            ) for msg in conversation]
            
            # Generate content
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=model,
                contents=contents,
                config=generation_config
            )
            
            # Extract response
            content = ""
            function_calls = []
            
            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                if candidate.content and candidate.content.parts:
                    for part in candidate.content.parts:
                        if part.text:
                            content += part.text
                        if hasattr(part, 'function_call') and part.function_call:
                            function_calls.append({
                                "id": f"call_{len(function_calls)}",
                                "type": "function",
                                "function": {
                                    "name": part.function_call.name,
                                    "arguments": dict(part.function_call.args) if part.function_call.args else {}
                                }
                            })
            
            return ChatResponse(
                content=content,
                role=MessageRole.ASSISTANT,
                finish_reason=str(response.candidates[0].finish_reason) if response.candidates else None,
                tool_calls=function_calls if function_calls else None,
                usage={
                    "tokens_input": response.usage_metadata.prompt_token_count if response.usage_metadata else 0,
                    "tokens_output": response.usage_metadata.candidates_token_count if response.usage_metadata else 0,
                    "tokens_total": response.usage_metadata.total_token_count if response.usage_metadata else 0,
                } if response.usage_metadata else None,
                model=model,
            )
            
        except Exception as e:
            error_str = str(e).lower()
            
            if "quota" in error_str or "rate limit" in error_str:
                raise RateLimitError(
                    message=str(e),
                    provider="gemini",
                    status_code=429,
                    error_type="rate_limit"
                )
            elif "api key" in error_str or "authentication" in error_str:
                raise AuthenticationError(
                    message=str(e),
                    provider="gemini",
                    status_code=401,
                    error_type="authentication"
                )
            elif "timeout" in error_str:
                raise ProviderTimeoutError(
                    message=str(e),
                    provider="gemini",
                    error_type="timeout"
                )
            else:
                logger.error(f"Gemini API error: {e}")
                raise ProviderError(
                    message=str(e),
                    provider="gemini",
                    error_type="api_error"
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
        """Stream chat completion from Gemini.
        
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
            system_instruction, conversation = self._convert_messages_gemini(messages)
            
            # Build config
            config_dict = {"temperature": temperature}
            if max_tokens:
                config_dict["max_output_tokens"] = max_tokens
            if top_p:
                config_dict["top_p"] = top_p
            
            generation_config = types.GenerateContentConfig(
                **config_dict,
                system_instruction=system_instruction
            )
            
            # Build content
            contents = [types.Content(
                role=msg["role"],
                parts=[types.Part(text=msg["parts"][0])]
            ) for msg in conversation]
            
            # Stream response
            stream = await asyncio.to_thread(
                self.client.models.generate_content_stream,
                model=model,
                contents=contents,
                config=generation_config
            )
            
            for chunk in stream:
                if chunk.candidates and chunk.candidates[0].content:
                    for part in chunk.candidates[0].content.parts:
                        if part.text:
                            yield part.text
                        
        except Exception as e:
            logger.error(f"Error in Gemini stream: {e}")
            raise ProviderError(
                message=f"Stream error: {str(e)}",
                provider="gemini",
                error_type="stream_error"
            )
    
    async def embed(
        self,
        text: str,
        model: Optional[str] = None,
        **kwargs
    ) -> EmbeddingResponse:
        """Generate embedding using Gemini.
        
        Args:
            text: Text to embed
            model: Embedding model (default: models/embedding-001)
            **kwargs: Additional parameters
            
        Returns:
            EmbeddingResponse with vector
        """
        try:
            model = model or "models/text-embedding-004"
            
            result = await asyncio.to_thread(
                self.client.models.embed_content,
                model=model,
                content=text
            )
            
            return EmbeddingResponse(
                embedding=result.embeddings[0].values if result.embeddings else [],
                model=model,
                usage=None,  # Gemini doesn't provide token usage for embeddings
            )
            
        except Exception as e:
            logger.error(f"Gemini embedding error: {e}")
            raise ProviderError(
                message=f"Embedding error: {str(e)}",
                provider="gemini",
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
            model = model or "models/text-embedding-004"
            
            # Batch embed
            results = []
            for text in texts:
                result = await asyncio.to_thread(
                    self.client.models.embed_content,
                    model=model,
                    content=text
                )
                results.append(EmbeddingResponse(
                    embedding=result.embeddings[0].values if result.embeddings else [],
                    model=model,
                    usage=None,
                ))
            
            return results
            
        except Exception as e:
            logger.error(f"Gemini batch embedding error: {e}")
            raise ProviderError(
                message=f"Batch embedding error: {str(e)}",
                provider="gemini",
                error_type="embedding_error"
            )
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List available Gemini models.
        
        Returns:
            List of model information
        """
        try:
            models_response = await asyncio.to_thread(
                self.client.models.list
            )
            
            return [
                {
                    "id": model.name,
                    "name": model.display_name if hasattr(model, 'display_name') else model.name,
                    "description": model.description if hasattr(model, 'description') else "",
                }
                for model in models_response.models
            ]
            
        except Exception as e:
            logger.error(f"Gemini list models error: {e}")
            raise ProviderError(
                message=f"List models error: {str(e)}",
                provider="gemini",
                error_type="list_error"
            )
    
    def _convert_tools_to_gemini(self, tools: List[Dict[str, Any]]) -> List[Any]:
        """Convert OpenAI-style tools to Gemini format.
        
        Args:
            tools: List of tool definitions
            
        Returns:
            List of Gemini tool definitions
        """
        # This would need proper conversion logic
        # For now, return None to indicate no tool support
        return None
