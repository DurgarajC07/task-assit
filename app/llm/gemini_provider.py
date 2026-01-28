"""Google Gemini LLM provider."""
import json
from typing import Optional

try:
    # The new SDK is google-genai, but it is still imported from 'google'
    from google import genai
    from google.genai import types # Added for configuration types
except ImportError:
    genai = None

from .base import BaseLLMProvider


class GeminiProvider(BaseLLMProvider):
    """Google Gemini LLM provider using Google API."""

    def __init__(self, api_key: str):
        """Initialize Gemini provider."""
        super().__init__(api_key)
        if genai is None:
            raise ImportError("google-genai package not installed. Run: pip install google-genai")
        
        # New SDK Client initialization
        self.client = genai.Client(api_key=api_key)
        # Using the standard 2.0 Flash model name
        self.model_name = "gemini-3-flash-preview"

    async def classify_intent(
        self,
        user_message: str,
        system_prompt: str
    ) -> dict:
        """Classify user intent using Gemini."""
        try:
            # New SDK uses .aio for async calls
            # System instructions are now passed via the config object
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=user_message,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json" # Forces JSON mode
                )
            )
            
            response_text = response.text
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
                # With response_mime_type="application/json", the model usually 
                # returns clean JSON, but we keep the safety check.
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
            # Using .aio for the async call and passing system_instruction in config
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=user_message,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt
                )
            )
            
            return response.text or "I couldn't generate a response."
        except Exception as e:
            return f"I encountered an error: {str(e)}"

    async def refine_intent(
        self,
        user_message: str,
        system_prompt: str
    ) -> dict:
        """Refine intent classification using Gemini."""
        return await self.classify_intent(user_message, system_prompt)