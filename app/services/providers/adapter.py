"""Base provider adapter interface.

All LLM provider adapters must implement this interface to ensure
consistent behavior across different AI providers.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, AsyncIterator, Any
from dataclasses import dataclass
from enum import Enum


class MessageRole(str, Enum):
    """Message roles in conversation."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"
    TOOL = "tool"


@dataclass
class ChatMessage:
    """Standard chat message format."""
    role: MessageRole
    content: str
    name: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None


@dataclass
class ChatResponse:
    """Standard chat response format."""
    content: str
    role: MessageRole = MessageRole.ASSISTANT
    finish_reason: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    usage: Optional[Dict[str, int]] = None  # tokens_input, tokens_output, tokens_total
    model: Optional[str] = None


@dataclass
class EmbeddingResponse:
    """Standard embedding response format."""
    embedding: List[float]
    model: str
    usage: Optional[Dict[str, int]] = None


@dataclass
class ProviderConfig:
    """Configuration for a provider adapter."""
    provider_type: str
    api_key: str
    base_url: Optional[str] = None
    organization: Optional[str] = None
    api_version: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3
    additional_params: Optional[Dict[str, Any]] = None


class ProviderAdapter(ABC):
    """Base class for all LLM provider adapters.
    
    Each provider (OpenAI, Anthropic, etc.) must implement this interface
    to provide a consistent API across different providers.
    """
    
    def __init__(self, config: ProviderConfig):
        """Initialize provider adapter.
        
        Args:
            config: Provider configuration
        """
        self.config = config
        self.provider_type = config.provider_type
    
    @abstractmethod
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
        """Send chat completion request.
        
        Args:
            messages: List of chat messages
            model: Model identifier
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            top_p: Nucleus sampling parameter
            functions: Available functions (legacy)
            function_call: Function call mode
            tools: Available tools
            tool_choice: Tool choice mode
            **kwargs: Additional provider-specific parameters
            
        Returns:
            ChatResponse with model output
            
        Raises:
            ProviderError: If request fails
        """
        pass
    
    @abstractmethod
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
        """Stream chat completion response.
        
        Args:
            messages: List of chat messages
            model: Model identifier
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            top_p: Nucleus sampling parameter
            functions: Available functions
            function_call: Function call mode
            tools: Available tools
            tool_choice: Tool choice mode
            **kwargs: Additional provider-specific parameters
            
        Yields:
            Content chunks as they arrive
            
        Raises:
            ProviderError: If stream fails
        """
        pass
    
    @abstractmethod
    async def embed(
        self,
        text: str,
        model: Optional[str] = None,
        **kwargs
    ) -> EmbeddingResponse:
        """Generate embedding for text.
        
        Args:
            text: Text to embed
            model: Embedding model identifier
            **kwargs: Additional provider-specific parameters
            
        Returns:
            EmbeddingResponse with vector
            
        Raises:
            ProviderError: If request fails
        """
        pass
    
    @abstractmethod
    async def embed_batch(
        self,
        texts: List[str],
        model: Optional[str] = None,
        **kwargs
    ) -> List[EmbeddingResponse]:
        """Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            model: Embedding model identifier
            **kwargs: Additional provider-specific parameters
            
        Returns:
            List of EmbeddingResponse
            
        Raises:
            ProviderError: If request fails
        """
        pass
    
    @abstractmethod
    async def list_models(self) -> List[Dict[str, Any]]:
        """List available models from provider.
        
        Returns:
            List of model information dictionaries
            
        Raises:
            ProviderError: If request fails
        """
        pass
    
    async def validate_credentials(self) -> bool:
        """Validate provider credentials.
        
        Returns:
            True if credentials are valid, False otherwise
        """
        try:
            await self.list_models()
            return True
        except Exception:
            return False
    
    def _convert_messages(self, messages: List[ChatMessage]) -> List[Dict[str, Any]]:
        """Convert ChatMessage objects to provider format.
        
        Args:
            messages: List of ChatMessage objects
            
        Returns:
            List of message dictionaries
        """
        result = []
        for msg in messages:
            message_dict = {
                "role": msg.role.value,
                "content": msg.content
            }
            
            if msg.name:
                message_dict["name"] = msg.name
            if msg.function_call:
                message_dict["function_call"] = msg.function_call
            if msg.tool_calls:
                message_dict["tool_calls"] = msg.tool_calls
            
            result.append(message_dict)
        
        return result


class ProviderError(Exception):
    """Base exception for provider errors."""
    
    def __init__(
        self,
        message: str,
        provider: str,
        status_code: Optional[int] = None,
        error_type: Optional[str] = None
    ):
        """Initialize provider error.
        
        Args:
            message: Error message
            provider: Provider name
            status_code: HTTP status code if applicable
            error_type: Error type from provider
        """
        super().__init__(message)
        self.message = message
        self.provider = provider
        self.status_code = status_code
        self.error_type = error_type


class RateLimitError(ProviderError):
    """Exception for rate limit errors."""
    pass


class AuthenticationError(ProviderError):
    """Exception for authentication errors."""
    pass


class InvalidRequestError(ProviderError):
    """Exception for invalid request errors."""
    pass


class ModelNotFoundError(ProviderError):
    """Exception for model not found errors."""
    pass


class ProviderTimeoutError(ProviderError):
    """Exception for timeout errors."""
    pass
