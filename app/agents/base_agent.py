"""Base agent class."""
from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseAgent(ABC):
    """Abstract base class for all agents."""

    def __init__(self, name: str):
        """Initialize base agent.

        Args:
            name: Agent identifier name.
        """
        self.name = name

    @abstractmethod
    async def execute(self, *args, **kwargs) -> Dict[str, Any]:
        """Execute agent logic.

        Args:
            *args: Positional arguments.
            **kwargs: Keyword arguments.

        Returns:
            Result dictionary with agent output.
        """
        pass

    def __repr__(self) -> str:
        """String representation."""
        return f"<{self.__class__.__name__}(name={self.name})>"
