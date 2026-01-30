"""Agent orchestrator for coordinating multi-agent system."""
from typing import Any, Dict, Optional
import uuid
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.intent_agent import IntentAgent
from app.agents.task_agent import TaskManagementAgent
from app.agents.conversation_agent import ConversationAgent
from app.agents.memory_agent import MemoryAgent
from app.core.exceptions import IntentUnclearException

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Orchestrator for coordinating agents in task management flow."""

    def __init__(self, db: AsyncSession):
        """Initialize orchestrator.

        Args:
            db: Database session.
        """
        self.db = db
        self.intent_agent = IntentAgent()
        self.task_agent = TaskManagementAgent(db)
        self.conversation_agent = ConversationAgent()
        self.memory_agent = MemoryAgent(db)

    async def process_chat(
        self,
        user_id: uuid.UUID,
        message: str,
        session_id: Optional[uuid.UUID] = None,
    ) -> Dict[str, Any]:
        """Process a chat message through the agent pipeline.

        Flow:
        1. Gather user context (recent tasks, preferences)
        2. Store user message in memory
        3. Intent Agent analyzes message with context
        4. If clarification needed, ask user
        5. Task Agent executes operation
        6. Conversation Agent generates response with context
        7. Store response in memory

        Args:
            user_id: User ID.
            message: User message.
            session_id: Optional session ID.

        Returns:
            Response with message and data.
        """
        if not session_id:
            session_id = uuid.uuid4()

        try:
            logger.info(f"Processing chat for user {user_id}: {message}")
            
            # Step 0: Gather user context for better understanding
            user_context = await self.memory_agent.get_user_context(user_id)
            conversation_history = await self.memory_agent.get_conversation_history(
                user_id, session_id, limit=10  # Increased from 5 to 10 for better memory
            )
            logger.debug(f"User context retrieved: {user_context.get('success')}")
            
            # Step 1: Store user message
            await self.memory_agent.store_conversation(
                user_id=user_id,
                session_id=session_id,
                role="user",
                message=message,
            )
            logger.debug("User message stored in memory")

            # Step 2: Analyze intent with conversation context
            intent_context = {
                "conversation_history": conversation_history.get("data", {}).get("messages", []),
                "recent_tasks": user_context.get("data", {}).get("recent_tasks", []),
            }
            intent_result = await self.intent_agent.execute(message, context=intent_context)
            logger.info(f"Intent analysis result: {intent_result}")

            if not intent_result.get("success"):
                return {
                    "success": False,
                    "error": "Failed to understand your request",
                    "session_id": str(session_id),
                }

            intent = intent_result.get("intent")
            confidence = intent_result.get("confidence", 0.0)
            entities = intent_result.get("entities", {})
            clarification_needed = intent_result.get("clarification_needed", False)
            clarification_question = intent_result.get(
                "clarification_question"
            )

            logger.info(f"Intent: {intent}, Confidence: {confidence}, Entities: {entities}")

            # REASONING: If user says just "create it" or provides a title after AI asked for clarification
            # Check if AI just asked a clarification question
            if intent == "CREATE_TASK" and not entities.get("title"):
                # Look at last AI message
                conv_history = intent_context.get("conversation_history", [])
                if conv_history:
                    last_ai_msg = next((m for m in reversed(conv_history) if m.get("role") == "assistant"), None)
                    if last_ai_msg and ("specify" in last_ai_msg.get("message", "").lower() or 
                                       "what task" in last_ai_msg.get("message", "").lower()):
                        # User is answering the clarification - treat their message as the task title
                        entities["title"] = message.strip()
                        logger.info(f"Extracted title from clarification response: {entities['title']}")

            # Step 3: Check if clarification needed
            if clarification_needed or confidence < 0.6:
                logger.info(f"Clarification needed (confidence: {confidence})")
                response_msg = clarification_question or (
                    "Could you provide more details about what you'd like to do?"
                )
                await self.memory_agent.store_conversation(
                    user_id=user_id,
                    session_id=session_id,
                    role="assistant",
                    message=response_msg,
                    intent=intent,
                )

                return {
                    "success": True,
                    "message": response_msg,
                    "intent": intent,
                    "session_id": str(session_id),
                    "requires_clarification": True,
                }

            # Step 4: Execute task operation
            logger.info(f"Executing task operation for intent: {intent}")
            task_result = await self._execute_task_operation(
                user_id,
                intent,
                entities,
            )
            logger.info(f"Task operation result: {task_result}")

            # Step 5: Generate conversational response
            logger.info("Generating conversational response")
            
            # Build rich context for conversation agent
            conversation_context = {
                "conversation_history": conversation_history.get("data", {}).get("messages", []),
                "user_context": user_context.get("data", {}),
                "recent_tasks": user_context.get("data", {}).get("recent_tasks", []),
            }
            
            response_result = await self.conversation_agent.execute(
                user_message=message,
                intent=intent,
                action_result=task_result,
                context=conversation_context,
            )

            response_message = response_result.get(
                "message",
                "Operation completed",
            )
            logger.info(f"Response generated: {response_message[:100]}...")

            # Step 6: Store assistant response
            await self.memory_agent.store_conversation(
                user_id=user_id,
                session_id=session_id,
                role="assistant",
                message=response_message,
                intent=intent,
                entities=entities,
            )
            logger.debug("Assistant response stored in memory")

            return {
                "success": True,
                "message": response_message,
                "intent": intent,
                "data": task_result.get("data"),
                "session_id": str(session_id),
            }

        except Exception as e:
            logger.error(f"Error in process_chat: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "session_id": str(session_id),
            }

    async def _execute_task_operation(
        self,
        user_id: uuid.UUID,
        intent: str,
        entities: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute the appropriate task operation based on intent.

        Args:
            user_id: User ID.
            intent: Detected intent.
            entities: Extracted entities.

        Returns:
            Task operation result.
        """
        logger.info(f"Executing task operation: intent={intent}, entities={entities}")
        
        if intent == "CREATE_TASK":
            return await self.task_agent.execute(
                action="create",
                user_id=user_id,
                task_data=entities,
            )

        elif intent == "LIST_TASKS":
            filters = {}
            if entities.get("filters"):
                for filter_item in entities.get("filters", []):
                    filters["filter_type"] = filter_item
            if entities.get("status"):
                filters["status"] = entities["status"]
            if entities.get("priority"):
                filters["priority"] = entities["priority"]

            return await self.task_agent.execute(
                action="list",
                user_id=user_id,
                filters=filters,
            )

        elif intent == "UPDATE_TASK":
            # Find task by identifier
            task_identifier = entities.get("task_identifier")
            if not task_identifier:
                # Try to get most recent task from context
                if user_context.get("data", {}).get("recent_tasks"):
                    recent_task = user_context["data"]["recent_tasks"][0]
                    task_identifier = recent_task.get("title")
                    logger.info(f"No task_identifier provided, using most recent task: {task_identifier}")
                
                if not task_identifier:
                    return {
                        "success": False,
                        "error": "Please specify which task to update",
                    }

            # Get task
            get_result = await self.task_agent.get_task(
                user_id,
                task_identifier=task_identifier,
            )
            if not get_result.get("success"):
                return get_result

            task_id = uuid.UUID(get_result["data"]["id"])
            existing_task = get_result["data"]

            # Smart update: Merge new information with existing data
            updates = {}
            if entities.get("title"):
                updates["title"] = entities["title"]
            
            # Smart description handling: intelligently merge descriptions
            if entities.get("description"):
                new_desc = entities["description"].strip()
                existing_desc = existing_task.get("description", "").strip()
                
                if not existing_desc:
                    # No existing description - use new one
                    updates["description"] = new_desc
                    logger.info("No existing description, using new description")
                else:
                    # Check if new description is already in existing (avoid duplicates)
                    if new_desc.lower() in existing_desc.lower():
                        logger.info("New description already exists in task, skipping update")
                        # Don't update - content already there
                    elif existing_desc.lower() in new_desc.lower():
                        # New description contains and expands on existing - replace
                        updates["description"] = new_desc
                        logger.info("New description expands existing, replacing")
                    else:
                        # Append new information with clear separation
                        updates["description"] = f"{existing_desc}\n\n{new_desc}"
                        logger.info(f"Appending new description to existing: {len(existing_desc)} + {len(new_desc)} chars")
            
            if entities.get("priority"):
                updates["priority"] = entities["priority"]
            if entities.get("due_date"):
                updates["due_date"] = entities["due_date"]
                if entities.get("due_time"):
                    updates["due_time"] = entities["due_time"]
            if entities.get("tags"):
                # Merge tags instead of replacing
                existing_tags = existing_task.get("tags", [])
                new_tags = entities["tags"]
                updates["tags"] = list(set(existing_tags + new_tags))
            if entities.get("status"):
                updates["status"] = entities["status"]

            return await self.task_agent.execute(
                action="update",
                user_id=user_id,
                task_id=task_id,
                updates=updates,
            )

        elif intent == "COMPLETE_TASK":
            task_identifier = entities.get("task_identifier")
            if not task_identifier:
                return {
                    "success": False,
                    "error": "Please specify which task to complete",
                }

            get_result = await self.task_agent.get_task(
                user_id,
                task_identifier=task_identifier,
            )
            if not get_result.get("success"):
                return get_result

            task_id = uuid.UUID(get_result["data"]["id"])

            return await self.task_agent.execute(
                action="complete",
                user_id=user_id,
                task_id=task_id,
                completion_action=entities.get("completion_action", "complete"),
            )

        elif intent == "SEARCH_TASKS":
            query = entities.get("search_query", "")
            return await self.task_agent.execute(
                action="search",
                user_id=user_id,
                query=query,
            )

        elif intent == "DELETE_TASK":
            task_identifier = entities.get("task_identifier")
            if not task_identifier:
                return {
                    "success": False,
                    "error": "Please specify which task to delete",
                }

            get_result = await self.task_agent.get_task(
                user_id,
                task_identifier=task_identifier,
            )
            if not get_result.get("success"):
                return get_result

            task_id = uuid.UUID(get_result["data"]["id"])

            return await self.task_agent.execute(
                action="delete",
                user_id=user_id,
                task_id=task_id,
            )

        elif intent == "GET_STATISTICS":
            return await self.task_agent.execute(
                action="statistics",
                user_id=user_id,
            )

        elif intent == "BULK_DELETE":
            criteria = entities.get("bulk_criteria", {})
            logger.info(f"Bulk delete with criteria: {criteria}")
            return await self.task_agent.execute(
                action="bulk_delete",
                user_id=user_id,
                criteria=criteria,
            )

        elif intent == "BULK_UPDATE":
            criteria = entities.get("bulk_criteria", {})
            updates = entities.get("bulk_updates", {})
            logger.info(f"Bulk update with criteria: {criteria}, updates: {updates}")
            return await self.task_agent.execute(
                action="bulk_update",
                user_id=user_id,
                criteria=criteria,
                updates=updates,
            )

        elif intent == "BULK_COMPLETE":
            criteria = entities.get("bulk_criteria", {})
            logger.info(f"Bulk complete with criteria: {criteria}")
            return await self.task_agent.execute(
                action="bulk_complete",
                user_id=user_id,
                criteria=criteria,
            )

        else:
            return {
                "success": False,
                "error": f"Unknown intent: {intent}",
            }
