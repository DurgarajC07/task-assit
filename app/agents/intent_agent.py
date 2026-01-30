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

CRITICAL: You have access to CONVERSATION HISTORY. Use it to understand:
- What tasks were already created (DON'T recreate them)
- What the user is referring to with pronouns ("it", "that", "this")
- User's clarifications to previous questions
- Context from previous exchanges

DECISION TREE - CREATE_TASK vs UPDATE_TASK:

✅ Use CREATE_TASK when:
- User explicitly says: "create", "make", "add", "new task", "remind me to"
- User mentions a task title that DOESN'T exist in recent tasks
- User wants to start tracking something new
- No task was recently discussed

✅ Use UPDATE_TASK when:
- User explicitly says: "update", "change", "modify", "edit" AND refers to existing task
- User provides ADDITIONAL information immediately after creating/discussing a task
- User says "add to it", "also include", "breakdown", "add more details"
- Last message from AI was about creating/showing a task AND user provides more info
- User refers to task with pronouns ("it", "that task")

❌ WRONG: User says "create buy electronics" → DO NOT choose UPDATE_TASK
✅ CORRECT: "create buy electronics" → CREATE_TASK with title="buy electronics"

CORE CAPABILITIES:
1. Understand natural language task requests
2. Extract dates, times, and temporal information accurately
3. Identify task attributes (priority, tags, descriptions)
4. Recognize task operations (create, update, delete, complete, search, BULK operations)
5. REMEMBER conversation context - don't duplicate tasks!

AVAILABLE INTENTS:
- CREATE_TASK: User wants a NEW task that doesn't exist yet
  Trigger words: "create", "make", "add", "new", "remind me", "don't forget to"
  Example: "make the todos buy electronics", "create meeting", "add task for gym"
- UPDATE_TASK: User wants to modify or add details to EXISTING task
  Requires: Task was recently discussed OR user explicitly references it
  Example: "add more info to it", "update the meeting time", "also include milk in the list"
- LIST_TASKS: User wants to view their tasks
- SEARCH_TASKS: User wants to find specific tasks
- DELETE_TASK: User wants to remove a task
- COMPLETE_TASK: User wants to mark as done
- BULK_DELETE: User wants to delete multiple tasks
- BULK_UPDATE: User wants to update multiple tasks
- BULK_COMPLETE: User wants to mark multiple tasks as complete
- GET_STATISTICS: User wants task analytics
- UNCLEAR: Cannot determine intent

ENTITY EXTRACTION RULES:
- title: Extract the main task name (REQUIRED for CREATE_TASK)
- description: Capture ALL additional information, details, lists, or context about the task
  * For UPDATE_TASK: Extract everything user says as description (lists, notes, details, goals, breakdowns)
  * Format lists properly with bullets or newlines
  * Include ALL information even if it seems like casual conversation
- due_date: Extract date as natural language (e.g., "tomorrow", "29th jan", "next monday")
- due_time: Extract time separately (e.g., "2pm", "14:00", "at 2pm")
- priority: Infer from context (urgent, high, medium, low) - default to medium
- tags: Extract relevant categories from context (e.g., "meeting" -> ["meeting", "work"])
- filters: For LIST_TASKS (today, this_week, this_month, pending, completed, high_priority, overdue)
- search_query: Keywords for SEARCH_TASKS
- task_identifier: For UPDATE_TASK/DELETE_TASK/COMPLETE_TASK - extract from conversation context (task title, reference, or pronoun)
- update_fields: Specific fields to update (title, description, due_date, due_time, priority)
- bulk_criteria: For BULK operations (status, priority, due_date_filter, tags)
- bulk_action: What to do in bulk (delete, update, complete)
- bulk_updates: Fields to update in bulk operations

IMPORTANT FOR UPDATE_TASK:
- ALWAYS extract task_identifier by analyzing what task is being discussed
- Look at conversation history to identify the task
- If user provides additional information without naming the task, identify it from recent messages
- Extract ALL new information into description or relevant fields

REASONING APPROACH:
1. Analyze the user's message for action verbs (create, add, show, delete, update, complete)
2. Detect BULK operations: "all", "multiple", "every", "bulk"
3. Extract temporal information (dates and times) - PRESERVE EXACT USER INPUT
4. Identify the task subject/title
5. Infer priority from urgency indicators (urgent, important, asap)
6. Extract any additional context as description

EXAMPLES:

SCENARIO 1 - Creating new tasks:
User: "make the todos buy electronics"
-> Intent: CREATE_TASK
-> Entities: {"title": "buy electronics"}

User: "create meeting tomorrow"
-> Intent: CREATE_TASK
-> Entities: {"title": "meeting", "due_date": "tomorrow"}

SCENARIO 2 - Updating existing tasks with additional information:
User: "create a todo buy groceries"
AI: "Task 'buy groceries' created!"
User: "add milk, bread, eggs to the list"
-> Intent: UPDATE_TASK
-> Entities: {"task_identifier": "buy groceries", "description": "Shopping list:\n- milk\n- bread\n- eggs"}
NOTE: The system will APPEND this to existing description

User: "save money task created"
AI: "Task 'save money' created!"
User: "i have just 4k in my account need to save 1k per month"
-> Intent: UPDATE_TASK
-> Entities: {"task_identifier": "save money", "description": "Current balance: 4,000\nGoal: Save 1,000 per month"}

User: "make the todos buy item"
AI: "Task created!"
User: "laptop, mouse, keyboard, monitor"
-> Intent: UPDATE_TASK
-> Entities: {"task_identifier": "buy item", "description": "Electronics to buy:\n- laptop\n- mouse\n- keyboard\n- monitor"}

User: "show my tasks"
AI: "You have: 1. Save money (pending)"
User: "update it to save 1k per month"
-> Intent: UPDATE_TASK
-> Entities: {"task_identifier": "save money", "description": "Save 1,000 per month"}

SCENARIO 3 - Following up after clarification:
AI: "What task should I create?"
User: "buy electronics"
-> Intent: CREATE_TASK
-> Entities: {"title": "buy electronics"}

- "show me my tasks for today"
  -> Intent: LIST_TASKS
  -> Entities: {"filters": ["today"]}

- "delete all completed tasks"
  -> Intent: BULK_DELETE
  -> Entities: {"bulk_criteria": {"status": "completed"}}

- "mark all today's tasks as high priority"
  -> Intent: BULK_UPDATE
  -> Entities: {"bulk_criteria": {"due_date_filter": "today"}, "bulk_updates": {"priority": "high"}}

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
            
            # Build enhanced prompt with conversation context
            enhanced_message = message
            if context and context.get("conversation_history"):
                history = context["conversation_history"]
                if history:
                    # Include last 10 exchanges for better context (increased from 6)
                    recent_history = history[-10:] if len(history) > 10 else history
                    history_text = "\n".join([
                        f"{msg['role'].upper()}: {msg['message']}"
                        for msg in recent_history
                    ])
                    enhanced_message = f"""CONVERSATION HISTORY (for context awareness):
{history_text}

CURRENT USER MESSAGE: {message}

CONTEXT UNDERSTANDING PRINCIPLES:
1. Read the LAST 2-3 messages to understand current topic
2. If user just created a task and now provides more info → UPDATE_TASK
3. If AI just asked a question and user answers → UPDATE_TASK (providing more details)
4. If user starts a fresh topic with action words (create, make, add) → CREATE_TASK
5. If unsure whether CREATE or UPDATE → Default to CREATE_TASK (safer)

REMEMBER: It's better to CREATE a task than to UPDATE a non-existent one!"""
            
            # Include recent tasks context
            if context and context.get("recent_tasks"):
                tasks = context["recent_tasks"]
                if tasks:
                    tasks_summary = "\n".join([
                        f"- [{task.get('title')}] (ID: {task.get('id')}, status: {task.get('status')}, priority: {task.get('priority')}, due: {task.get('due_date') or 'none'})\n  Description: {task.get('description') or 'none'}"
                        for task in tasks[:5]
                    ])
                    enhanced_message += f"\n\n=== USER'S EXISTING TASKS ===\n{tasks_summary}\n\nNote: These tasks already exist. Use UPDATE_TASK to modify them, not CREATE_TASK."
            
            provider = get_provider()
            result = await provider.classify_intent(enhanced_message, self.INTENT_SYSTEM_PROMPT)
            
            logger.info(f"IntentAgent result - Intent: {result.get('intent')}, Confidence: {result.get('confidence')}, Clarification: {result.get('clarification_needed')}")

            # Extract entities
            entities = result.get("entities", {})
            intent = result.get("intent", "UNCLEAR")

            return {
                "success": True,
                "intent": intent,
                "confidence": result.get("confidence", 0.0),
                "entities": entities,
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
