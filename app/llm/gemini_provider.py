"""Google Gemini LLM provider."""
import json
from typing import Optional

try:
    from google import genai
except ImportError:
    genai = None

from .base import BaseLLMProvider


class GeminiProvider(BaseLLMProvider):
    """Google Gemini LLM provider using Google API."""

    def __init__(self, api_key: str):
        """Initialize Gemini provider."""
        super().__init__(api_key)
        if genai is None:
            raise ImportError("google-generativeai package not installed. Run: pip install google-genai")
        
        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-2.0-flash-exp"

    async def classify_intent(
        self,
        user_message: str,
        system_prompt: str
    ) -> dict:
        """Classify user intent using Gemini."""
        try:
            full_prompt = f"{system_prompt}\n\nUser message: {user_message}"
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=full_prompt
            )
            
            response_text = response.text if hasattr(response, 'text') else str(response)
            if not response_text:
                return {
                    "intent": "UNCLEAR",
                    "confidence": 0.0,
                    "entities": {},
                    "clarification_needed": True,
                    "clarification_question": "Gemini did not generate a response."
                }
            
            # Parse JSON response
            try:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    return json.loads(json_str)
            except (json.JSONDecodeError, ValueError):
                pass
            
            return {
                "intent": "UNCLEAR",
                "confidence": 0.0,
                "entities": {},
                "clarification_needed": True,
                "clarification_question": "I couldn't understand your request clearly."
            }
        except Exception as e:
            return {
                "intent": "UNCLEAR",
                "confidence": 0.0,
                "entities": {},
                "clarification_needed": True,
                "clarification_question": f"Error processing request: {str(e)}"
            }

    async def generate_response(
        self,
        user_message: str,
        system_prompt: str,
        context: Optional[dict] = None
    ) -> str:
        """Generate a response using Gemini."""
        try:
            full_prompt = f"{system_prompt}\n\nUser: {user_message}"
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=full_prompt
            )
            
            response_text = response.text if hasattr(response, 'text') else str(response)
            if not response_text:
                return "I couldn't generate a response."
            
            return response_text
        except Exception as e:
            return f"I encountered an error: {str(e)}"

    async def refine_intent(
        self,
        user_message: str,
        system_prompt: str
    ) -> dict:
        """Refine intent classification using Gemini."""
        return await self.classify_intent(user_message, system_prompt)
