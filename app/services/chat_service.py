"""Chat service."""
import uuid
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.orchestrator.conversation_manager import ConversationManager
from app.models.conversation import Conversation

logger = logging.getLogger(__name__)


class ChatService:
    """Chat service for natural language task processing."""

    def __init__(self, db: AsyncSession):
        """Initialize chat service.

        Args:
            db: Database session.
        """
        self.db = db
        self.conversation_manager = ConversationManager(db)

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
            # Use NEW conversation manager for chat processing
            # Get or create conversation
            from app.core.tenant_context import get_tenant_context
            tenant_id = get_tenant_context()
            
            if session_id:
                # Get existing conversation
                conversation = await self.conversation_manager.db.get(Conversation, session_id)
            else:
                # Create new conversation
                conversation = await self.conversation_manager.create_conversation(
                    tenant_id=tenant_id,
                    user_id=user_id,
                    title="Chat Session"
                )
                session_id = conversation.id
            
            # Send message and get response
            response = await self.conversation_manager.send_message(
                conversation_id=session_id,
                content=message,
                role="user"
            )
            
            logger.info(f"Conversation manager result: {response}")
            return {
                "success": True,
                "message": response.content if hasattr(response, 'content') else str(response),
                "data": {
                    "session_id": str(session_id),
                    "conversation_id": str(session_id)
                }
            }
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
        try:
            messages = await self.conversation_manager.get_messages(
                conversation_id=session_id,
                limit=limit
            )
            return {
                "success": True,
                "messages": [
                    {
                        "role": msg.role,
                        "content": msg.content,
                        "created_at": msg.created_at.isoformat()
                    }
                    for msg in messages
                ]
            }
        except Exception as e:
            logger.error(f"Error getting history: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "messages": []
            }
