"""Agent manager for loading and executing database-defined agents.

Manages agent lifecycle, tool registration, and execution orchestration.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import logging

from app.models.agent import Agent, AgentTool, AgentRun, AgentRunStatus
from app.services.orchestrator.tool_registry import get_tool_registry, ToolDefinition
from app.services.provider_service import ProviderService
from app.services.providers.adapter import ChatMessage, ProviderAdapter

logger = logging.getLogger(__name__)


class AgentManager:
    """Manager for AI agents."""
    
    def __init__(self, db: AsyncSession):
        """Initialize agent manager.
        
        Args:
            db: Database session
        """
        self.db = db
        self.tool_registry = get_tool_registry()
        self.provider_service = ProviderService(db)
    
    async def get_agent(
        self,
        agent_id: UUID,
        tenant_id: UUID
    ) -> Optional[Agent]:
        """Get agent by ID.
        
        Args:
            agent_id: Agent UUID
            tenant_id: Tenant UUID (for isolation)
            
        Returns:
            Agent or None
        """
        result = await self.db.execute(
            select(Agent).where(
                and_(
                    Agent.id == agent_id,
                    Agent.tenant_id == tenant_id,
                    Agent.deleted_at.is_(None)
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def list_agents(
        self,
        tenant_id: UUID,
        is_active: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Agent]:
        """List agents for tenant.
        
        Args:
            tenant_id: Tenant UUID
            is_active: Filter by active status
            limit: Maximum results
            offset: Results offset
            
        Returns:
            List of agents
        """
        conditions = [
            Agent.tenant_id == tenant_id,
            Agent.deleted_at.is_(None)
        ]
        
        if is_active is not None:
            conditions.append(Agent.is_active == is_active)
        
        result = await self.db.execute(
            select(Agent)
            .where(and_(*conditions))
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())
    
    async def get_agent_tools(
        self,
        agent_id: UUID
    ) -> List[AgentTool]:
        """Get tools configured for agent.
        
        Args:
            agent_id: Agent UUID
            
        Returns:
            List of agent tools
        """
        result = await self.db.execute(
            select(AgentTool).where(
                and_(
                    AgentTool.agent_id == agent_id,
                    AgentTool.is_enabled == True
                )
            )
        )
        return list(result.scalars().all())
    
    async def create_agent_run(
        self,
        agent_id: UUID,
        user_id: UUID,
        input_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentRun:
        """Create an agent run execution record.
        
        Args:
            agent_id: Agent UUID
            user_id: User UUID
            input_data: Input data for agent
            metadata: Optional metadata
            
        Returns:
            Created agent run
        """
        agent_run = AgentRun(
            agent_id=agent_id,
            user_id=user_id,
            status=AgentRunStatus.PENDING,
            input_data=input_data,
            metadata=metadata or {}
        )
        
        self.db.add(agent_run)
        await self.db.commit()
        await self.db.refresh(agent_run)
        
        logger.info(f"Created agent run {agent_run.id} for agent {agent_id}")
        return agent_run
    
    async def execute_agent(
        self,
        agent_id: UUID,
        tenant_id: UUID,
        user_id: UUID,
        input_text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute an agent with input.
        
        Args:
            agent_id: Agent UUID
            tenant_id: Tenant UUID
            user_id: User UUID
            input_text: Input text/prompt
            context: Optional execution context
            
        Returns:
            Execution result
        """
        # Get agent
        agent = await self.get_agent(agent_id, tenant_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")
        
        if not agent.is_active:
            raise ValueError(f"Agent {agent_id} is not active")
        
        # Create run record
        agent_run = await self.create_agent_run(
            agent_id=agent_id,
            user_id=user_id,
            input_data={"input": input_text, "context": context or {}}
        )
        
        try:
            # Update status to running
            agent_run.status = AgentRunStatus.RUNNING
            agent_run.started_at = datetime.utcnow()
            await self.db.commit()
            
            # Get provider adapter
            adapter = await self._get_agent_adapter(agent)
            
            # Get agent tools
            agent_tools = await self.get_agent_tools(agent_id)
            tool_definitions = [
                self.tool_registry.get_definition(tool.tool_name)
                for tool in agent_tools
            ]
            tool_definitions = [td for td in tool_definitions if td]
            
            # Build system prompt with agent instructions
            system_prompt = self._build_system_prompt(agent, tool_definitions)
            
            # Build messages
            messages = [
                ChatMessage(role="system", content=system_prompt),
                ChatMessage(role="user", content=input_text)
            ]
            
            # Execute with provider
            start_time = datetime.utcnow()
            response = await adapter.chat(
                messages=messages,
                temperature=agent.temperature,
                max_tokens=agent.max_tokens or 2000
            )
            execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            # Update run with results
            agent_run.status = AgentRunStatus.COMPLETED
            agent_run.completed_at = datetime.utcnow()
            agent_run.output_data = {
                "output": response.content,
                "model": response.model,
                "finish_reason": response.finish_reason
            }
            agent_run.execution_time_ms = execution_time_ms
            agent_run.tokens_used = response.total_tokens
            await self.db.commit()
            
            logger.info(
                f"Agent run {agent_run.id} completed: "
                f"{response.total_tokens} tokens, {execution_time_ms}ms"
            )
            
            return {
                "run_id": str(agent_run.id),
                "status": "completed",
                "output": response.content,
                "tokens_used": response.total_tokens,
                "execution_time_ms": execution_time_ms,
                "model": response.model
            }
            
        except Exception as e:
            logger.error(f"Agent run {agent_run.id} failed: {e}", exc_info=True)
            
            # Update run with error
            agent_run.status = AgentRunStatus.FAILED
            agent_run.completed_at = datetime.utcnow()
            agent_run.error_message = str(e)
            await self.db.commit()
            
            return {
                "run_id": str(agent_run.id),
                "status": "failed",
                "error": str(e)
            }
    
    async def _get_agent_adapter(self, agent: Agent) -> ProviderAdapter:
        """Get provider adapter for agent.
        
        Args:
            agent: Agent
            
        Returns:
            Provider adapter
        """
        if agent.provider_id:
            return await self.provider_service.create_adapter(agent.provider_id)
        else:
            # Use tenant default
            provider = await self.provider_service.get_default_provider(agent.tenant_id)
            if not provider:
                raise ValueError(f"No default provider for tenant {agent.tenant_id}")
            return await self.provider_service.create_adapter(provider.id)
    
    def _build_system_prompt(
        self,
        agent: Agent,
        tools: List[ToolDefinition]
    ) -> str:
        """Build system prompt for agent.
        
        Args:
            agent: Agent
            tools: Available tools
            
        Returns:
            System prompt
        """
        prompt_parts = []
        
        # Add agent description
        if agent.description:
            prompt_parts.append(agent.description)
        
        # Add instructions
        if agent.instructions:
            prompt_parts.append(f"\nInstructions:\n{agent.instructions}")
        
        # Add tool information
        if tools:
            tool_info = "\n\nAvailable Tools:\n"
            for tool in tools:
                tool_info += f"- {tool.name}: {tool.description}\n"
            prompt_parts.append(tool_info)
        
        return "\n".join(prompt_parts)
    
    async def get_agent_runs(
        self,
        agent_id: UUID,
        limit: int = 50,
        offset: int = 0
    ) -> List[AgentRun]:
        """Get execution history for agent.
        
        Args:
            agent_id: Agent UUID
            limit: Maximum results
            offset: Results offset
            
        Returns:
            List of agent runs
        """
        result = await self.db.execute(
            select(AgentRun)
            .where(AgentRun.agent_id == agent_id)
            .order_by(AgentRun.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())
    
    async def get_run_stats(
        self,
        agent_id: UUID
    ) -> Dict[str, Any]:
        """Get execution statistics for agent.
        
        Args:
            agent_id: Agent UUID
            
        Returns:
            Statistics summary
        """
        from sqlalchemy import func
        
        result = await self.db.execute(
            select(
                func.count(AgentRun.id).label('total_runs'),
                func.sum(case((AgentRun.status == AgentRunStatus.COMPLETED, 1), else_=0)).label('completed'),
                func.sum(case((AgentRun.status == AgentRunStatus.FAILED, 1), else_=0)).label('failed'),
                func.avg(AgentRun.execution_time_ms).label('avg_execution_time_ms'),
                func.sum(AgentRun.tokens_used).label('total_tokens')
            ).where(AgentRun.agent_id == agent_id)
        )
        
        row = result.first()
        
        return {
            "total_runs": row.total_runs or 0,
            "completed": row.completed or 0,
            "failed": row.failed or 0,
            "success_rate": (row.completed / row.total_runs * 100) if row.total_runs else 0,
            "avg_execution_time_ms": float(row.avg_execution_time_ms or 0),
            "total_tokens": row.total_tokens or 0
        }


# Import case for SQL
from sqlalchemy import case
