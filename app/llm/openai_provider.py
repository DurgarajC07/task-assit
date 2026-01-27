"""OpenAI LLM provider."""
import json
from typing import Optional

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from .base import BaseLLMProvider


class OpenAIProvider(BaseLLMProvider):
    """OpenAI LLM provider using OpenAI API."""

    def __init__(self, api_key: str):
        """Initialize OpenAI provider."""
        super().__init__(api_key)
        if OpenAI is None:
            raise ImportError("openai package not installed. Run: pip install openai")
        
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4-turbo"

    async def classify_intent(
        self,
        user_message: str,
        system_prompt: str
    ) -> dict:
        """Classify user intent using OpenAI."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=1024,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ]
            )
            
            result_text = response.choices[0].message.content
            
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
        """Generate a response using OpenAI."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=1024,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ]
            )
            
            return response.choices[0].message.content
        except Exception as e:
            return f"I encountered an error: {str(e)}"

    async def refine_intent(
        self,
        user_message: str,
        system_prompt: str
    ) -> dict:
        """Refine intent classification using OpenAI."""
        return await self.classify_intent(user_message, system_prompt)
