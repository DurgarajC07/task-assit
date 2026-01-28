"""Groq LLM provider (groq.com - not xAI)."""
import json
import logging
from typing import Optional

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from .base import BaseLLMProvider

logger = logging.getLogger(__name__)


class GrokProvider(BaseLLMProvider):
    """Groq LLM provider using OpenAI-compatible API.
    
    Uses Groq Cloud API (console.groq.com) with fast LLM inference.
    Supports models like llama-3.1-8b-instant, mixtral, etc.
    """

    def __init__(self, api_key: str, model: str = "llama-3.1-8b-instant"):
        """Initialize Groq provider.
        
        Args:
            api_key: Groq API key (from console.groq.com)
            model: Model to use (default: llama-3.1-8b-instant)
                   Available: llama-3.1-8b-instant, llama-3.1-70b-versatile,
                             mixtral-8x7b-32768, gemma-7b-it
        """
        super().__init__(api_key)
        if OpenAI is None:
            raise ImportError("openai package not installed. Run: pip install openai")
        
        # Groq API endpoint
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1"
        )
        self.model = model
        logger.info(f"Initialized Groq provider with model: {self.model}")

    async def classify_intent(
        self,
        user_message: str,
        system_prompt: str
    ) -> dict:
        """Classify user intent using Grok."""
        try:
            logger.debug(f"Classifying intent for message: {user_message[:100]}...")
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=2048,
                temperature=0.3,  # Lower temperature for more consistent classification
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ]
            )
            
            result_text = response.choices[0].message.content.strip()
            logger.debug(f"Raw LLM response: {result_text}")
            
            # Try to parse JSON response with multiple strategies
            try:
                # Strategy 1: Direct JSON parse
                try:
                    return json.loads(result_text)
                except json.JSONDecodeError:
                    pass
                
                # Strategy 2: Extract JSON from markdown code blocks
                if "```json" in result_text:
                    json_start = result_text.find("```json") + 7
                    json_end = result_text.find("```", json_start)
                    if json_end > json_start:
                        json_str = result_text[json_start:json_end].strip()
                        return json.loads(json_str)
                
                # Strategy 3: Find first JSON object
                json_start = result_text.find('{')
                json_end = result_text.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = result_text[json_start:json_end]
                    return json.loads(json_str)
                    
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Failed to parse JSON response: {e}")
            
            logger.warning("Could not extract valid JSON from LLM response")
            return {
                "intent": "UNCLEAR",
                "confidence": 0.0,
                "entities": {},
                "clarification_needed": True,
                "clarification_question": "I couldn't understand your request clearly. Could you rephrase it?"
            }
        except Exception as e:
            logger.error(f"Error in classify_intent: {e}", exc_info=True)
            return {
                "intent": "UNCLEAR",
                "confidence": 0.0,
                "entities": {},
                "clarification_needed": True,
                "clarification_question": f"I encountered an error processing your request. Please try again."
            }

    async def generate_response(
        self,
        user_message: str,
        system_prompt: str,
        context: Optional[dict] = None
    ) -> str:
        """Generate a response using Grok."""
        try:
            logger.debug(f"Generating response for message: {user_message[:100]}...")
            
            # Build messages with context if provided
            messages = [{"role": "system", "content": system_prompt}]
            
            if context and context.get("conversation_history"):
                # Add recent conversation history for better context
                for msg in context["conversation_history"][-5:]:
                    messages.append({
                        "role": msg.get("role", "user"),
                        "content": msg.get("message", "")
                    })
            
            messages.append({"role": "user", "content": user_message})
            
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=1024,
                temperature=0.7,  # Balanced temperature for natural responses
                messages=messages
            )
            
            response_text = response.choices[0].message.content.strip()
            logger.debug(f"Generated response: {response_text[:100]}...")
            return response_text
            
        except Exception as e:
            logger.error(f"Error in generate_response: {e}", exc_info=True)
            return f"I encountered an error while processing your request. Please try again."

    async def refine_intent(
        self,
        user_message: str,
        system_prompt: str
    ) -> dict:
        """Refine intent classification using Grok."""
        return await self.classify_intent(user_message, system_prompt)
