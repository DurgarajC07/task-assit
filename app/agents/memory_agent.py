"""Memory agent for context and history management."""
from typing import Any, Dict, List, Optional
import uuid
from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.base_agent import BaseAgent
from app.models import ConversationHistory, MessageRole, User, Task
from app.core.exceptions import UserNotFoundException


class MemoryAgent(BaseAgent):
    """Memory agent for conversation history and user context management."""

    def __init__(self, db: AsyncSession):
        """Initialize memory agent.

        Args:
            db: Database session.
        """
        super().__init__("MemoryAgent")
        self.db = db

    async def execute(self, *args, **kwargs) -> Dict[str, Any]:
        """Execute memory operation.

        Args:
            **kwargs: Operation parameters.

        Returns:
            Result dictionary.
        """
        action = kwargs.get("action")
        if action == "store_conversation":
            return await self.store_conversation(
                kwargs.get("user_id"),
                kwargs.get("session_id"),
                kwargs.get("role"),
                kwargs.get("message"),
                kwargs.get("intent"),
                kwargs.get("entities"),
            )
        elif action == "get_history":
            return await self.get_conversation_history(
                kwargs.get("user_id"),
                kwargs.get("session_id"),
                kwargs.get("limit", 10),
            )
        elif action == "get_context":
            return await self.get_user_context(kwargs.get("user_id"))
        else:
            return {"success": False, "error": f"Unknown action: {action}"}

    async def store_conversation(
        self,
        user_id: uuid.UUID,
        session_id: uuid.UUID,
        role: str,
        message: str,
        intent: Optional[str] = None,
        entities: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Store a conversation message.

        Args:
            user_id: User ID.
            session_id: Session ID.
            role: Message role (user/assistant).
            message: Message content.
            intent: Detected intent (optional).
            entities: Extracted entities (optional).

        Returns:
            Success confirmation.
        """
        try:
            conversation = ConversationHistory(
                user_id=user_id,
                session_id=session_id,
                role=MessageRole(role),
                message=message,
                intent=intent,
                entities=entities or {},
            )

            self.db.add(conversation)
            await self.db.commit()

            return {"success": True, "message_id": str(conversation.id)}

        except Exception as e:
            await self.db.rollback()
            return {"success": False, "error": str(e)}

    async def get_conversation_history(
        self,
        user_id: uuid.UUID,
        session_id: uuid.UUID,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """Retrieve conversation history for a session.

        Args:
            user_id: User ID.
            session_id: Session ID.
            limit: Maximum messages to retrieve.

        Returns:
            Conversation history.
        """
        try:
            result = await self.db.execute(
                select(ConversationHistory)
                .where(
                    and_(
                        ConversationHistory.user_id == user_id,
                        ConversationHistory.session_id == session_id,
                    )
                )
                .order_by(ConversationHistory.created_at.desc())
                .limit(limit)
            )

            messages = result.scalars().all()
            messages.reverse()  # Return in chronological order

            return {
                "success": True,
                "data": {
                    "messages": [
                        {
                            "id": str(msg.id),
                            "role": msg.role.value,
                            "message": msg.message,
                            "intent": msg.intent,
                            "entities": msg.entities,
                            "created_at": msg.created_at.isoformat(),
                        }
                        for msg in messages
                    ],
                    "session_id": str(session_id),
                    "total_messages": len(messages),
                },
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_user_context(
        self,
        user_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """Get user context for task management.

        Args:
            user_id: User ID.

        Returns:
            User context data.
        """
        try:
            # Get user
            user_result = await self.db.execute(
                select(User).where(User.id == user_id)
            )
            user = user_result.scalar_one_or_none()

            if not user:
                raise UserNotFoundException()

            # Get recent tasks
            tasks_result = await self.db.execute(
                select(Task).where(Task.user_id == user_id)
                .order_by(Task.created_at.desc())
                .limit(5)
            )
            recent_tasks = tasks_result.scalars().all()

            # Get statistics
            from app.agents.task_agent import TaskManagementAgent

            task_agent = TaskManagementAgent(self.db)
            stats_result = await task_agent.get_statistics(user_id)

            return {
                "success": True,
                "data": {
                    "user": {
                        "id": str(user.id),
                        "username": user.username,
                        "email": user.email,
                        "preferences": user.preferences,
                    },
                    "recent_tasks": [
                        {
                            "id": str(t.id),
                            "title": t.title,
                            "description": t.description,
                            "status": t.status.value,
                            "priority": t.priority.value,
                            "due_date": t.due_date.isoformat() if t.due_date else None,
                            "created_at": t.created_at.isoformat() if hasattr(t, 'created_at') and t.created_at else None,
                        }
                        for t in recent_tasks
                    ],
                    "statistics": stats_result.get("data", {}),
                    "context_time": datetime.utcnow().isoformat(),
                },
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_user_preferences(
        self,
        user_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """Get user preferences.

        Args:
            user_id: User ID.

        Returns:
            User preferences.
        """
        try:
            result = await self.db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()

            if not user:
                raise UserNotFoundException()

            return {
                "success": True,
                "data": user.preferences or {},
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def update_user_preferences(
        self,
        user_id: uuid.UUID,
        preferences: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update user preferences.

        Args:
            user_id: User ID.
            preferences: Preferences to update.

        Returns:
            Updated preferences.
        """
        try:
            result = await self.db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()

            if not user:
                raise UserNotFoundException()

            # Merge preferences
            user.preferences = {**(user.preferences or {}), **preferences}
            user.updated_at = datetime.utcnow()

            await self.db.commit()

            return {
                "success": True,
                "data": user.preferences,
            }

        except Exception as e:
            await self.db.rollback()
            return {"success": False, "error": str(e)}
