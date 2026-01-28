"""LLM provider factory for dynamic provider selection."""
from typing import Optional
from enum import Enum
import logging

from app.config import settings
from .base import BaseLLMProvider
from .claude_provider import ClaudeProvider
from .openai_provider import OpenAIProvider
from .gemini_provider import GeminiProvider
from .grok_provider import GrokProvider

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    
    CLAUDE = "claude"
    OPENAI = "openai"
    GEMINI = "gemini"
    GROK = "grok"


def get_llm_provider(provider: Optional[str] = None) -> BaseLLMProvider:
    """Get LLM provider instance based on configuration.
    
    Args:
        provider: Optional provider name override (claude, openai, gemini, grok)
                 If not provided, uses LLM_PROVIDER from environment
    
    Returns:
        BaseLLMProvider instance configured with appropriate API key
        
    Raises:
        ValueError: If provider is invalid or API key is missing
        ImportError: If provider dependencies are not installed
    """
    provider_name = (provider or settings.llm_provider or "claude").lower()
    
    logger.info(f"Initializing LLM provider: {provider_name}")
    
    if provider_name == LLMProvider.CLAUDE:
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
        return ClaudeProvider(settings.anthropic_api_key)
    
    elif provider_name == LLMProvider.OPENAI:
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        return OpenAIProvider(settings.openai_api_key)
    
    elif provider_name == LLMProvider.GEMINI:
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")
        return GeminiProvider(settings.gemini_api_key)
    
    elif provider_name == LLMProvider.GROK:
        if not settings.grok_api_key:
            raise ValueError("GROK_API_KEY environment variable is not set")
        # Use model from settings if available, otherwise default
        model = getattr(settings, 'llm_model', 'llama-3.1-8b-instant')
        return GrokProvider(settings.grok_api_key, model=model)
    
    else:
        raise ValueError(
            f"Unknown LLM provider: {provider_name}. "
            f"Supported providers: {', '.join([p.value for p in LLMProvider])}"
        )


# Global provider instance (lazy initialized)
_provider_instance: Optional[BaseLLMProvider] = None


def get_provider() -> BaseLLMProvider:
    """Get or initialize the global LLM provider instance.
    
    Returns:
        BaseLLMProvider instance
    """
    global _provider_instance
    
    if _provider_instance is None:
        _provider_instance = get_llm_provider()
    
    return _provider_instance


def reset_provider() -> None:
    """Reset the global provider instance (useful for testing)."""
    global _provider_instance
    _provider_instance = None
