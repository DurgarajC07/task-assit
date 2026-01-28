"""Intent classification agent."""
import json
import logging
from typing import Any, Dict, Optional
from app.agents.base_agent import BaseAgent
from app.llm.factory import get_provider

logger = logging.getLogger(__name__)


class IntentAgent(BaseAgent):
    """Intent classification agent for analyzing user messages."""

    INTENT_SYSTEM_PROMPT = """You are an advanced Intent Classification Agent for a personal task assistant system.
Your role is to deeply understand user messages and extract precise intent with entities.

CORE CAPABILITIES:
1. Understand natural language task requests
2. Extract dates, times, and temporal information accurately
3. Identify task attributes (priority, tags, descriptions)
4. Recognize task operations (create, update, delete, complete, search, BULK operations)
5. Handle context from conversation flow

AVAILABLE INTENTS:
- CREATE_TASK: User wants to create a new task (e.g., "create a meeting", "add task", "remind me to")
- LIST_TASKS: User wants to view their tasks (e.g., "show my tasks", "what do I have today")
- UPDATE_TASK: User wants to modify an existing task (e.g., "change the meeting time", "update task")
- SEARCH_TASKS: User wants to find specific tasks (e.g., "find my meeting", "search for")
- DELETE_TASK: User wants to remove a task (e.g., "delete the meeting", "remove task")
- BULK_DELETE: User wants to delete multiple tasks (e.g., "delete all completed tasks", "remove all high priority tasks")
- BULK_UPDATE: User wants to update multiple tasks (e.g., "mark all today's tasks as high priority", "change all pending tasks to medium")
- BULK_COMPLETE: User wants to mark multiple tasks as complete (e.g., "complete all today's tasks", "mark all pending as done")
- GET_STATISTICS: User wants task analytics (e.g., "how many tasks", "my productivity")
- COMPLETE_TASK: User wants to mark as done (e.g., "mark as complete", "I finished")
- UNCLEAR: Cannot determine intent with confidence

ENTITY EXTRACTION RULES:
- title: Extract the main task name (REQUIRED for CREATE_TASK)
- description: Additional details about the task
- due_date: Extract date as natural language (e.g., "tomorrow", "29th jan", "next monday")
- due_time: Extract time separately (e.g., "2pm", "14:00", "at 2pm")
- priority: Infer from context (urgent, high, medium, low) - default to medium
- tags: Extract relevant categories from context (e.g., "meeting" -> ["meeting", "work"])
- filters: For LIST_TASKS (today, this_week, this_month, pending, completed, high_priority, overdue)
- search_query: Keywords for SEARCH_TASKS
- task_identifier: For UPDATE_TASK/DELETE_TASK/COMPLETE_TASK (exact or partial task title)
- update_fields: Specific fields to update (title, description, due_date, due_time, priority)
- bulk_criteria: For BULK operations (status, priority, due_date_filter, tags)
- bulk_action: What to do in bulk (delete, update, complete)
- bulk_updates: Fields to update in bulk operations

REASONING APPROACH:
1. Analyze the user's message for action verbs (create, add, show, delete, update, complete)
2. Detect BULK operations: "all", "multiple", "every", "bulk"
3. Extract temporal information (dates and times) - PRESERVE EXACT USER INPUT
4. Identify the task subject/title
5. Infer priority from urgency indicators (urgent, important, asap)
6. Extract any additional context as description

EXAMPLES:
- "create a meeting for tomorrow at 29th jan on 2pm"
  -> Intent: CREATE_TASK
  -> Entities: {"title": "meeting", "due_date": "29th jan", "due_time": "2pm", "priority": "medium", "tags": ["meeting"]}

- "show me my tasks for today"
  -> Intent: LIST_TASKS
  -> Entities: {"filters": ["today"]}

- "delete all completed tasks"
  -> Intent: BULK_DELETE
  -> Entities: {"bulk_criteria": {"status": "completed"}}

- "mark all today's tasks as high priority"
  -> Intent: BULK_UPDATE
  -> Entities: {"bulk_criteria": {"due_date_filter": "today"}, "bulk_updates": {"priority": "high"}}

- "complete all pending tasks"
  -> Intent: BULK_COMPLETE
  -> Entities: {"bulk_criteria": {"status": "pending"}}

RESPONSE FORMAT (JSON only, no extra text):
{
  "intent": "INTENT_NAME",
  "confidence": 0.95,
  "entities": {
    "field_name": "value"
  },
  "reasoning": "Brief explanation of why this intent was chosen",
  "clarification_needed": false,
  "clarification_question": null
}

IMPORTANT:
- If confidence < 0.7, set clarification_needed to true
- If intent is UNCLEAR, always set clarification_needed to true
- Preserve exact date/time strings from user input for accurate parsing
- Be contextually aware - "it" or "that" may refer to recent tasks
- For BULK operations, extract clear criteria (status, priority, date filters)"""

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
