"""Conversation manager for multi-turn AI chat with context.

Manages conversation history, context windows, and provider interactions
for seamless multi-turn conversations.
"""
from typing import List, Optional, Dict, Any, AsyncIterator
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import logging

from app.models.conversation import Conversation, Message, MessageRole
from app.services.providers.adapter import ChatMessage, ChatResponse, ProviderAdapter
from app.services.provider_service import ProviderService
from app.services.orchestrator.usage_tracker import UsageTracker

logger = logging.getLogger(__name__)


class ConversationManager:
    """Manager for AI conversations."""
    
    def __init__(self, db: AsyncSession):
        """Initialize conversation manager.
        
        Args:
            db: Database session
        """
        self.db = db
        self.provider_service = ProviderService(db)
        self.usage_tracker = UsageTracker(db)
    
    async def create_conversation(
        self,
        tenant_id: UUID,
        user_id: UUID,
        title: Optional[str] = None,
        agent_id: Optional[UUID] = None,
        provider_id: Optional[UUID] = None,
        model_id: Optional[UUID] = None,
        system_prompt: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Conversation:
        """Create a new conversation.
        
        Args:
            tenant_id: Tenant UUID
            user_id: User UUID
            title: Optional conversation title
            agent_id: Optional agent UUID
            provider_id: Optional provider config UUID
            model_id: Optional model UUID
            system_prompt: Optional system prompt
            metadata: Optional metadata
            
        Returns:
            Created conversation
        """
        conversation = Conversation(
            tenant_id=tenant_id,
            user_id=user_id,
            title=title or f"Conversation {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
            agent_id=agent_id,
            provider_id=provider_id,
            model_id=model_id,
            system_prompt=system_prompt,
            message_count=0,
            total_tokens=0,
            metadata=metadata or {}
        )
        
        self.db.add(conversation)
        await self.db.commit()
        await self.db.refresh(conversation)
        
        logger.info(f"Created conversation {conversation.id}")
        return conversation
    
    async def add_message(
        self,
        conversation_id: UUID,
        role: MessageRole,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        """Add a message to conversation.
        
        Args:
            conversation_id: Conversation UUID
            role: Message role
            content: Message content
            metadata: Optional metadata
            
        Returns:
            Created message
        """
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            metadata=metadata or {}
        )
        
        self.db.add(message)
        
        # Update conversation
        conversation = await self.get_conversation(conversation_id)
        if conversation:
            conversation.message_count += 1
            conversation.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(message)
        
        return message
    
    async def get_conversation(
        self,
        conversation_id: UUID
    ) -> Optional[Conversation]:
        """Get conversation by ID.
        
        Args:
            conversation_id: Conversation UUID
            
        Returns:
            Conversation or None
        """
        result = await self.db.execute(
            select(Conversation).where(
                and_(
                    Conversation.id == conversation_id,
                    Conversation.deleted_at.is_(None)
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_messages(
        self,
        conversation_id: UUID,
        limit: Optional[int] = None,
        include_system: bool = True
    ) -> List[Message]:
        """Get conversation messages.
        
        Args:
            conversation_id: Conversation UUID
            limit: Optional limit (gets most recent)
            include_system: Include system messages
            
        Returns:
            List of messages in chronological order
        """
        query = select(Message).where(
            Message.conversation_id == conversation_id
        )
        
        if not include_system:
            query = query.where(Message.role != MessageRole.SYSTEM)
        
        query = query.order_by(Message.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        result = await self.db.execute(query)
        messages = list(result.scalars().all())
        
        # Return in chronological order
        return list(reversed(messages))
    
    async def send_message(
        self,
        conversation_id: UUID,
        content: str,
        stream: bool = False
    ) -> ChatResponse:
        """Send a message and get AI response.
        
        Args:
            conversation_id: Conversation UUID
            content: User message content
            stream: Whether to stream response
            
        Returns:
            AI response
        """
        # Get conversation
        conversation = await self.get_conversation(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        # Add user message
        await self.add_message(
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=content
        )
        
        # Get provider adapter
        adapter = await self._get_adapter(conversation)
        
        # Build message history
        messages = await self._build_message_history(conversation)
        
        # Add current message
        messages.append(ChatMessage(
            role="user",
            content=content
        ))
        
        # Get AI response
        start_time = datetime.utcnow()
        
        if stream:
            # TODO: Implement streaming
            raise NotImplementedError("Streaming not yet implemented")
        else:
            response = await adapter.chat(
                messages=messages,
                temperature=0.7,
                max_tokens=2000
            )
        
        execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        # Add assistant message
        await self.add_message(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=response.content,
            metadata={
                "model": response.model,
                "finish_reason": response.finish_reason,
                "input_tokens": response.input_tokens,
                "output_tokens": response.output_tokens
            }
        )
        
        # Update conversation totals
        conversation.total_tokens += response.total_tokens
        await self.db.commit()
        
        # Track usage
        await self.usage_tracker.track_completion(
            tenant_id=conversation.tenant_id,
            user_id=conversation.user_id,
            provider=adapter.__class__.__name__.replace("Adapter", "").lower(),
            model=response.model,
            prompt_tokens=response.input_tokens,
            completion_tokens=response.output_tokens,
            total_tokens=response.total_tokens,
            execution_time_ms=execution_time_ms,
            agent_id=conversation.agent_id,
            conversation_id=conversation_id
        )
        
        return response
    
    async def _get_adapter(self, conversation: Conversation) -> ProviderAdapter:
        """Get provider adapter for conversation.
        
        Args:
            conversation: Conversation
            
        Returns:
            Provider adapter
        """
        if conversation.provider_id:
            # Use specific provider from conversation
            return await self.provider_service.create_adapter(
                conversation.provider_id
            )
        else:
            # Use tenant default provider
            provider = await self.provider_service.get_default_provider(
                conversation.tenant_id
            )
            if not provider:
                raise ValueError(f"No default provider for tenant {conversation.tenant_id}")
            return await self.provider_service.create_adapter(provider.id)
    
    async def _build_message_history(
        self,
        conversation: Conversation,
        max_messages: int = 20
    ) -> List[ChatMessage]:
        """Build message history for AI context.
        
        Args:
            conversation: Conversation
            max_messages: Maximum messages to include
            
        Returns:
            List of chat messages
        """
        messages = []
        
        # Add system prompt if present
        if conversation.system_prompt:
            messages.append(ChatMessage(
                role="system",
                content=conversation.system_prompt
            ))
        
        # Get recent messages
        recent_messages = await self.get_messages(
            conversation_id=conversation.id,
            limit=max_messages,
            include_system=False
        )
        
        # Convert to ChatMessage format
        for msg in recent_messages:
            messages.append(ChatMessage(
                role=msg.role.value,
                content=msg.content
            ))
        
        return messages
    
    async def delete_conversation(
        self,
        conversation_id: UUID
    ) -> bool:
        """Soft delete conversation.
        
        Args:
            conversation_id: Conversation UUID
            
        Returns:
            True if deleted, False if not found
        """
        conversation = await self.get_conversation(conversation_id)
        if not conversation:
            return False
        
        conversation.soft_delete()
        await self.db.commit()
        
        logger.info(f"Deleted conversation {conversation_id}")
        return True
