"""Tool registry for dynamic agent tool management.

Provides a centralized registry for registering, discovering, and executing
tools that agents can use. Supports both built-in and custom tools.
"""
from typing import Dict, List, Optional, Callable, Any, Type
from pydantic import BaseModel, Field
from enum import Enum
import inspect
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ToolParameterType(str, Enum):
    """Supported parameter types for tools."""
    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


class ToolParameter(BaseModel):
    """Tool parameter definition."""
    name: str
    type: ToolParameterType
    description: str
    required: bool = True
    default: Optional[Any] = None
    enum: Optional[List[Any]] = None


class ToolDefinition(BaseModel):
    """Tool definition with metadata."""
    name: str
    description: str
    parameters: List[ToolParameter]
    category: str = "general"
    requires_auth: bool = False
    is_async: bool = False


class ToolResult(BaseModel):
    """Result from tool execution."""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    execution_time_ms: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ToolRegistry:
    """Registry for managing agent tools."""
    
    def __init__(self):
        """Initialize tool registry."""
        self._tools: Dict[str, Callable] = {}
        self._definitions: Dict[str, ToolDefinition] = {}
        self._register_builtin_tools()
    
    def register_tool(
        self,
        name: str,
        func: Callable,
        description: str,
        parameters: List[ToolParameter],
        category: str = "general",
        requires_auth: bool = False
    ) -> None:
        """Register a tool.
        
        Args:
            name: Tool name (unique identifier)
            func: Tool function to execute
            description: Tool description
            parameters: List of parameters
            category: Tool category
            requires_auth: Whether tool requires authentication
        """
        if name in self._tools:
            logger.warning(f"Tool '{name}' already registered, overwriting")
        
        # Check if function is async
        is_async = inspect.iscoroutinefunction(func)
        
        # Create definition
        definition = ToolDefinition(
            name=name,
            description=description,
            parameters=parameters,
            category=category,
            requires_auth=requires_auth,
            is_async=is_async
        )
        
        self._tools[name] = func
        self._definitions[name] = definition
        
        logger.info(f"Registered tool: {name} (async={is_async})")
    
    def unregister_tool(self, name: str) -> bool:
        """Unregister a tool.
        
        Args:
            name: Tool name
            
        Returns:
            True if unregistered, False if not found
        """
        if name in self._tools:
            del self._tools[name]
            del self._definitions[name]
            logger.info(f"Unregistered tool: {name}")
            return True
        return False
    
    def get_tool(self, name: str) -> Optional[Callable]:
        """Get tool function.
        
        Args:
            name: Tool name
            
        Returns:
            Tool function or None
        """
        return self._tools.get(name)
    
    def get_definition(self, name: str) -> Optional[ToolDefinition]:
        """Get tool definition.
        
        Args:
            name: Tool name
            
        Returns:
            Tool definition or None
        """
        return self._definitions.get(name)
    
    def list_tools(
        self,
        category: Optional[str] = None,
        requires_auth: Optional[bool] = None
    ) -> List[ToolDefinition]:
        """List all registered tools.
        
        Args:
            category: Filter by category
            requires_auth: Filter by auth requirement
            
        Returns:
            List of tool definitions
        """
        tools = list(self._definitions.values())
        
        if category:
            tools = [t for t in tools if t.category == category]
        
        if requires_auth is not None:
            tools = [t for t in tools if t.requires_auth == requires_auth]
        
        return tools
    
    def get_categories(self) -> List[str]:
        """Get all tool categories.
        
        Returns:
            List of categories
        """
        return list(set(t.category for t in self._definitions.values()))
    
    async def execute_tool(
        self,
        name: str,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ToolResult:
        """Execute a tool.
        
        Args:
            name: Tool name
            parameters: Tool parameters
            context: Optional execution context
            
        Returns:
            Tool execution result
        """
        start_time = datetime.utcnow()
        
        # Get tool
        tool = self.get_tool(name)
        if not tool:
            return ToolResult(
                success=False,
                error=f"Tool '{name}' not found",
                execution_time_ms=0
            )
        
        # Get definition
        definition = self.get_definition(name)
        
        try:
            # Validate required parameters
            required_params = {p.name for p in definition.parameters if p.required}
            provided_params = set(parameters.keys())
            missing_params = required_params - provided_params
            
            if missing_params:
                return ToolResult(
                    success=False,
                    error=f"Missing required parameters: {', '.join(missing_params)}",
                    execution_time_ms=0
                )
            
            # Execute tool
            if definition.is_async:
                if context:
                    result = await tool(**parameters, context=context)
                else:
                    result = await tool(**parameters)
            else:
                if context:
                    result = tool(**parameters, context=context)
                else:
                    result = tool(**parameters)
            
            # Calculate execution time
            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            return ToolResult(
                success=True,
                data=result,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            logger.error(f"Error executing tool '{name}': {e}", exc_info=True)
            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            return ToolResult(
                success=False,
                error=str(e),
                execution_time_ms=execution_time
            )
    
    def _register_builtin_tools(self) -> None:
        """Register built-in tools."""
        
        # Search tool
        def search_web(query: str, max_results: int = 5) -> Dict[str, Any]:
            """Search the web for information."""
            # Placeholder - integrate with actual search API
            return {
                "query": query,
                "results": [],
                "message": "Search functionality not yet implemented"
            }
        
        self.register_tool(
            name="search_web",
            func=search_web,
            description="Search the web for information",
            parameters=[
                ToolParameter(
                    name="query",
                    type=ToolParameterType.STRING,
                    description="Search query"
                ),
                ToolParameter(
                    name="max_results",
                    type=ToolParameterType.INTEGER,
                    description="Maximum number of results",
                    required=False,
                    default=5
                )
            ],
            category="search"
        )
        
        # Calculator tool
        def calculate(expression: str) -> Dict[str, Any]:
            """Evaluate a mathematical expression."""
            try:
                # Safe evaluation of mathematical expressions
                import ast
                import operator
                
                ops = {
                    ast.Add: operator.add,
                    ast.Sub: operator.sub,
                    ast.Mult: operator.mul,
                    ast.Div: operator.truediv,
                    ast.Pow: operator.pow,
                    ast.USub: operator.neg,
                }
                
                def eval_expr(node):
                    if isinstance(node, ast.Num):
                        return node.n
                    elif isinstance(node, ast.BinOp):
                        return ops[type(node.op)](eval_expr(node.left), eval_expr(node.right))
                    elif isinstance(node, ast.UnaryOp):
                        return ops[type(node.op)](eval_expr(node.operand))
                    else:
                        raise ValueError(f"Unsupported operation: {type(node)}")
                
                result = eval_expr(ast.parse(expression, mode='eval').body)
                return {"result": result, "expression": expression}
            except Exception as e:
                return {"error": str(e), "expression": expression}
        
        self.register_tool(
            name="calculate",
            func=calculate,
            description="Evaluate mathematical expressions",
            parameters=[
                ToolParameter(
                    name="expression",
                    type=ToolParameterType.STRING,
                    description="Mathematical expression to evaluate"
                )
            ],
            category="utility"
        )
        
        # Get current time tool
        def get_current_time(timezone: str = "UTC") -> Dict[str, Any]:
            """Get current time in specified timezone."""
            from datetime import datetime
            return {
                "time": datetime.utcnow().isoformat(),
                "timezone": timezone
            }
        
        self.register_tool(
            name="get_current_time",
            func=get_current_time,
            description="Get current time in specified timezone",
            parameters=[
                ToolParameter(
                    name="timezone",
                    type=ToolParameterType.STRING,
                    description="Timezone (e.g., UTC, EST)",
                    required=False,
                    default="UTC"
                )
            ],
            category="utility"
        )


# Global tool registry instance
_tool_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """Get global tool registry instance.
    
    Returns:
        Tool registry singleton
    """
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
    return _tool_registry
