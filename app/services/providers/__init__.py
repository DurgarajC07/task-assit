"""Provider adapters package.

Exports all provider adapters and factory.
"""
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

from app.services.providers.openai_adapter import OpenAIAdapter
from app.services.providers.anthropic_adapter import AnthropicAdapter
from app.services.providers.gemini_adapter import GeminiAdapter
from app.services.providers.groq_adapter import GroqAdapter
from app.services.providers.ollama_adapter import OllamaAdapter

__all__ = [
    # Base classes
    "ProviderAdapter",
    "ProviderConfig",
    "ChatMessage",
    "ChatResponse",
    "EmbeddingResponse",
    "MessageRole",
    # Exceptions
    "ProviderError",
    "RateLimitError",
    "AuthenticationError",
    "InvalidRequestError",
    "ModelNotFoundError",
    "ProviderTimeoutError",
    # Adapters
    "OpenAIAdapter",
    "AnthropicAdapter",
    "GeminiAdapter",
    "GroqAdapter",
    "OllamaAdapter",
]
