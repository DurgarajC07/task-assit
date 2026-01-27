"""Base LLM provider interface."""
from abc import ABC, abstractmethod
from typing import Optional


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, api_key: str):
        """Initialize LLM provider.
        
        Args:
            api_key: API key for the provider
        """
        self.api_key = api_key

    @abstractmethod
    async def classify_intent(
        self, 
        user_message: str,
        system_prompt: str
    ) -> dict:
        """Classify user intent using the LLM.
        
        Args:
            user_message: User's input message
            system_prompt: System prompt for intent classification
            
        Returns:
            Dictionary with classification results
        """
        pass

    @abstractmethod
    async def generate_response(
        self,
        user_message: str,
        system_prompt: str,
        context: Optional[dict] = None
    ) -> str:
        """Generate a response using the LLM.
        
        Args:
            user_message: User's input message
            system_prompt: System prompt for response generation
            context: Optional context for the response
            
        Returns:
            Generated response string
        """
        pass

    @abstractmethod
    async def refine_intent(
        self,
        user_message: str,
        system_prompt: str
    ) -> dict:
        """Refine intent classification.
        
        Args:
            user_message: User's clarification message
            system_prompt: System prompt for refinement
            
        Returns:
            Refined classification results
        """
        pass
