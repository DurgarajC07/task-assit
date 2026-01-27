"""Conversation agent for generating natural language responses."""
import json
from typing import Any, Dict, Optional
from app.agents.base_agent import BaseAgent
from app.llm.factory import get_provider


class ConversationAgent(BaseAgent):
    """Conversation agent for generating natural language responses."""

    CONVERSATION_SYSTEM_PROMPT = """You are a friendly Task Assistant helping users manage their tasks.
Generate natural, concise responses based on the action performed.

Guidelines:
- Be conversational but professional
- Confirm actions clearly
- Use emojis sparingly (only for celebrations like task completion with ✓)
- When listing tasks, format them clearly with bullet points
- For errors, be helpful and suggest solutions
- Keep responses concise (2-3 sentences for simple actions)
- Ask clarifying questions when needed
- Be encouraging and positive

Context includes:
- User's original message
- Detected intent
- Action performed (success or failure)
- Result data (task details, list of tasks, statistics, etc.)

Generate appropriate responses for:
- Task created/updated/completed/deleted successfully
- Task list results (format with priorities and due dates)
- Search results
- Statistics summaries
- Errors (with helpful suggestions)
- Clarification requests
- When data is empty or no results found

Keep responses brief and actionable."""

    def __init__(self):
        """Initialize conversation agent."""
        super().__init__("ConversationAgent")

    async def execute(
        self,
        user_message: str,
        intent: str,
        action_result: Dict[str, Any],
        context: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Generate a conversational response.

        Args:
            user_message: Original user message.
            intent: Detected intent.
            action_result: Result from task agent.
            context: Optional additional context.

        Returns:
            Response dictionary with message.
        """
        try:
            # Build context message
            context_msg = f"""
User said: "{user_message}"
Detected Intent: {intent}
Action Result: {json.dumps(action_result, indent=2, default=str)}

Generate a natural, helpful response to the user based on the action result."""

            provider = get_provider()
            response_text = await provider.generate_response(
                context_msg,
                self.CONVERSATION_SYSTEM_PROMPT
            )

            return {
                "success": True,
                "message": response_text,
                "intent": intent,
            }

        except Exception as e:
            # Fallback response
            return {
                "success": False,
                "message": self._generate_fallback_response(intent, action_result),
                "error": str(e),
            }

    async def ask_clarification(
        self,
        clarification_question: str,
    ) -> Dict[str, Any]:
        """Generate a clarification question response.

        Args:
            clarification_question: Clarification question.

        Returns:
            Response dictionary.
        """
        return {
            "success": True,
            "message": clarification_question,
            "is_clarification": True,
        }

    @staticmethod
    def _generate_fallback_response(
        intent: str,
        action_result: Dict[str, Any],
    ) -> str:
        """Generate a fallback response when API fails.

        Args:
            intent: Intent type.
            action_result: Action result.

        Returns:
            Fallback response message.
        """
        if not action_result.get("success"):
            return f"I encountered an issue: {action_result.get('error', 'Something went wrong')}. Could you try again or provide more details?"

        if intent == "CREATE_TASK":
            task = action_result.get("data", {})
            return f"✓ Task '{task.get('title', 'Task')}' created successfully!"

        elif intent == "LIST_TASKS":
            data = action_result.get("data", {})
            count = len(data.get("tasks", []))
            return f"You have {count} task(s) matching your criteria."

        elif intent == "UPDATE_TASK":
            task = action_result.get("data", {})
            return f"✓ Task '{task.get('title', 'Task')}' updated successfully!"

        elif intent == "COMPLETE_TASK":
            task = action_result.get("data", {})
            return f"✓ Great! Task '{task.get('title', 'Task')}' is now complete!"

        elif intent == "DELETE_TASK":
            return action_result.get("message", "Task deleted successfully!")

        elif intent == "SEARCH_TASKS":
            data = action_result.get("data", {})
            count = data.get("total_results", 0)
            return f"Found {count} task(s) matching '{data.get('search_query', '')}'."

        elif intent == "GET_STATISTICS":
            stats = action_result.get("data", {})
            return f"You have {stats.get('total_tasks', 0)} total tasks. Completion rate: {stats.get('completion_rate', 0)}%"

        else:
            return "Done! Is there anything else you'd like me to help with?"
