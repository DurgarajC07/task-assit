"""Chat service."""
import uuid
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.orchestrator import AgentOrchestrator

logger = logging.getLogger(__name__)


class ChatService:
    """Chat service for natural language task processing."""

    def __init__(self, db: AsyncSession):
        """Initialize chat service.

        Args:
            db: Database session.
        """
        self.db = db
        self.orchestrator = AgentOrchestrator(db)

    async def process_message(
        self,
        user_id: uuid.UUID,
        message: str,
        session_id: uuid.UUID = None,
    ):
        """Process user message through agent pipeline.

        Args:
            user_id: User ID.
            message: User message.
            session_id: Optional session ID.

        Returns:
            Response from orchestrator.
        """
        logger.info(f"Processing message for user {user_id}: {message}")
        try:
            result = await self.orchestrator.process_chat(
                user_id=user_id,
                message=message,
                session_id=session_id,
            )
            logger.info(f"Orchestrator result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            return {
                "success": False,
                "message": "Sorry, I encountered an error processing your request.",
                "error": str(e)
            }

    async def get_history(
        self,
        user_id: uuid.UUID,
        session_id: uuid.UUID,
        limit: int = 10,
    ):
        """Get conversation history.

        Args:
            user_id: User ID.
            session_id: Session ID.
            limit: Number of messages to retrieve.

        Returns:
            Conversation history.
        """
        return await self.orchestrator.memory_agent.execute(
            action="get_history",
            user_id=user_id,
            session_id=session_id,
            limit=limit,
        )
