"""Intent classification agent."""
import json
import logging
from typing import Any, Dict, Optional
from app.agents.base_agent import BaseAgent
from app.llm.factory import get_provider

logger = logging.getLogger(__name__)


class IntentAgent(BaseAgent):
    """Intent classification agent for analyzing user messages."""

    INTENT_SYSTEM_PROMPT = """You are an Intent Classification Agent for a task management system.
Your role is to analyze user messages and determine their intent with high accuracy.

Available Intents:
- CREATE_TASK: User wants to create a new task
- LIST_TASKS: User wants to view their tasks (possibly with filters)
- UPDATE_TASK: User wants to modify an existing task
- SEARCH_TASKS: User wants to search for specific tasks
- DELETE_TASK: User wants to remove a task
- GET_STATISTICS: User wants task analytics or summaries
- COMPLETE_TASK: User wants to mark a task as complete
- UNCLEAR: Cannot determine intent with confidence

Extract entities for the detected intent:
- title: Task title/name
- description: Task details
- due_date: When the task is due (preserve exact user input for date parsing)
- priority: low, medium, high, or urgent
- tags: Array of relevant tags
- filters: For LIST_TASKS (today, this_week, this_month, pending, completed, high_priority, overdue)
- search_query: Keywords for SEARCH_TASKS
- task_identifier: For UPDATE_TASK or DELETE_TASK (title or partial description)
- update_fields: What fields to update
- completion_action: "complete" or "incomplete" for COMPLETE_TASK

Respond ONLY with valid JSON in this exact format:
{
  "intent": "INTENT_NAME",
  "confidence": 0.95,
  "entities": {
    "field_name": "value"
  },
  "clarification_needed": false,
  "clarification_question": null
}

If you need clarification, set clarification_needed to true and provide a helpful question.
If the intent is UNCLEAR, also set clarification_needed to true."""

    def __init__(self):
        """Initialize intent agent."""
        super().__init__("IntentAgent")

    async def execute(self, message: str, context: Optional[Dict] = None) -> Dict[
        str, Any
    ]:
        """Analyze message and classify intent.

        Args:
            message: User message to analyze.
            context: Optional conversation context.

        Returns:
            Dictionary with intent classification results.
        """
        try:
            logger.info(f"IntentAgent analyzing message: {message}")
            provider = get_provider()
            result = await provider.classify_intent(message, self.INTENT_SYSTEM_PROMPT)
            
            logger.info(f"IntentAgent result - Intent: {result.get('intent')}, Confidence: {result.get('confidence')}, Clarification: {result.get('clarification_needed')}")

            return {
                "success": True,
                "intent": result.get("intent", "UNCLEAR"),
                "confidence": result.get("confidence", 0.0),
                "entities": result.get("entities", {}),
                "clarification_needed": result.get("clarification_needed", False),
                "clarification_question": result.get("clarification_question"),
            }

        except json.JSONDecodeError as e:
            logger.error(f"IntentAgent JSON decode error: {e}")
            return {
                "success": False,
                "error": "Failed to parse intent response",
                "intent": "UNCLEAR",
                "confidence": 0.0,
            }
        except Exception as e:
            logger.error(f"IntentAgent error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "intent": "UNCLEAR",
                "confidence": 0.0,
            }

    async def refine_intent(
        self,
        message: str,
        initial_intent: str,
        user_clarification: str,
    ) -> Dict[str, Any]:
        """Refine intent based on user clarification.

        Args:
            message: Original user message.
            initial_intent: Initial intent classification.
            user_clarification: User's clarifying input.

        Returns:
            Refined intent classification.
        """
        context_message = f"""Original message: "{message}"
Initial intent: {initial_intent}
User clarification: "{user_clarification}"

Now re-analyze with this clarification."""

        try:
            provider = get_provider()
            result = await provider.refine_intent(context_message, self.INTENT_SYSTEM_PROMPT)

            return {
                "success": True,
                "intent": result.get("intent", "UNCLEAR"),
                "confidence": result.get("confidence", 0.0),
                "entities": result.get("entities", {}),
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "intent": "UNCLEAR",
                "confidence": 0.0,
            }
