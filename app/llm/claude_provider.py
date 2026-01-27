"""Anthropic Claude LLM provider."""
import json
from typing import Optional
from anthropic import Anthropic
from .base import BaseLLMProvider


class ClaudeProvider(BaseLLMProvider):
    """Claude LLM provider using Anthropic API."""

    def __init__(self, api_key: str):
        """Initialize Claude provider."""
        super().__init__(api_key)
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-20241022"

    async def classify_intent(
        self,
        user_message: str,
        system_prompt: str
    ) -> dict:
        """Classify user intent using Claude."""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_message}
                ]
            )
            
            result_text = response.content[0].text
            
            # Parse JSON response
            try:
                json_start = result_text.find('{')
                json_end = result_text.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = result_text[json_start:json_end]
                    return json.loads(json_str)
            except (json.JSONDecodeError, ValueError):
                pass
            
            return {
                "intent": "UNCLEAR",
                "confidence": 0.0,
                "entities": {},
                "clarification_needed": True,
                "clarification_message": "I couldn't understand your request clearly."
            }
        except Exception as e:
            return {
                "intent": "UNCLEAR",
                "confidence": 0.0,
                "entities": {},
                "clarification_needed": True,
                "clarification_message": f"Error processing request: {str(e)}"
            }

    async def generate_response(
        self,
        user_message: str,
        system_prompt: str,
        context: Optional[dict] = None
    ) -> str:
        """Generate a response using Claude."""
        try:
            messages = [{"role": "user", "content": user_message}]
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=system_prompt,
                messages=messages
            )
            
            return response.content[0].text
        except Exception as e:
            return f"I encountered an error: {str(e)}"

    async def refine_intent(
        self,
        user_message: str,
        system_prompt: str
    ) -> dict:
        """Refine intent classification using Claude."""
        return await self.classify_intent(user_message, system_prompt)
