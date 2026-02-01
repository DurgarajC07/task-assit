"""Provider factory for creating provider adapters.

Factory creates the appropriate provider adapter based on provider type
and handles credential decryption.
"""
import logging
from typing import Dict, Type

from app.services.providers.adapter import ProviderAdapter, ProviderConfig
from app.services.providers.openai_adapter import OpenAIAdapter
from app.services.providers.anthropic_adapter import AnthropicAdapter
from app.services.providers.gemini_adapter import GeminiAdapter
from app.services.providers.groq_adapter import GroqAdapter
from app.services.providers.ollama_adapter import OllamaAdapter

logger = logging.getLogger(__name__)


class ProviderFactory:
    """Factory for creating provider adapters."""
    
    # Registry of available providers
    _providers: Dict[str, Type[ProviderAdapter]] = {
        "openai": OpenAIAdapter,
        "anthropic": AnthropicAdapter,
        "gemini": GeminiAdapter,
        "google": GeminiAdapter,  # Alias
        "groq": GroqAdapter,
        "ollama": OllamaAdapter,
    }
    
    @classmethod
    def create(cls, provider_type: str, config: ProviderConfig) -> ProviderAdapter:
        """Create a provider adapter.
        
        Args:
            provider_type: Type of provider (openai, anthropic, etc.)
            config: Provider configuration
            
        Returns:
            ProviderAdapter instance
            
        Raises:
            ValueError: If provider type is not supported
        """
        provider_type_lower = provider_type.lower()
        
        if provider_type_lower not in cls._providers:
            supported = ", ".join(cls._providers.keys())
            raise ValueError(
                f"Unsupported provider type: {provider_type}. "
                f"Supported providers: {supported}"
            )
        
        adapter_class = cls._providers[provider_type_lower]
        logger.info(f"Creating {provider_type} adapter")
        
        return adapter_class(config)
    
    @classmethod
    def register_provider(
        cls,
        provider_type: str,
        adapter_class: Type[ProviderAdapter]
    ):
        """Register a new provider adapter.
        
        Args:
            provider_type: Provider type identifier
            adapter_class: Adapter class to register
        """
        cls._providers[provider_type.lower()] = adapter_class
        logger.info(f"Registered provider: {provider_type}")
    
    @classmethod
    def list_providers(cls) -> list[str]:
        """List all registered provider types.
        
        Returns:
            List of provider type identifiers
        """
        return list(cls._providers.keys())
    
    @classmethod
    def is_supported(cls, provider_type: str) -> bool:
        """Check if a provider type is supported.
        
        Args:
            provider_type: Provider type to check
            
        Returns:
            True if supported, False otherwise
        """
        return provider_type.lower() in cls._providers


# Convenience function
def create_provider(provider_type: str, config: ProviderConfig) -> ProviderAdapter:
    """Create a provider adapter.
    
    Args:
        provider_type: Type of provider
        config: Provider configuration
        
    Returns:
        ProviderAdapter instance
    """
    return ProviderFactory.create(provider_type, config)
