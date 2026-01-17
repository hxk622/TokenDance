
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.tools.init_tools import (
    get_tool_categories,
    get_tool_descriptions,
    register_builtin_tools,
)
from app.agent.tools.registry import get_global_registry
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/tools", tags=["Tools"])


@router.get("", response_model=list[dict])
async def list_tools(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all available tools"""
    registry = get_global_registry()

    # Register tools if not already done
    if len(registry) == 0:
        register_builtin_tools(registry)

    tools = []
    for tool_name in registry.list_names():
        tool = registry.get(tool_name)
        tools.append({
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters,
            "risk_level": tool.risk_level.value if hasattr(tool, 'risk_level') else "UNKNOWN",
            "requires_confirmation": tool.requires_confirmation if hasattr(tool, 'requires_confirmation') else False,
            "operation_categories": [cat.value for cat in tool.operation_categories] if hasattr(tool, 'operation_categories') else []
        })

    return tools


@router.get("/{tool_name}", response_model=dict)
async def get_tool(
    tool_name: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get tool details by name"""
    registry = get_global_registry()

    # Register tools if not already done
    if len(registry) == 0:
        register_builtin_tools(registry)

    if not registry.has(tool_name):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool '{tool_name}' not found"
        )

    tool = registry.get(tool_name)

    return {
        "name": tool.name,
        "description": tool.description,
        "parameters": tool.parameters,
        "risk_level": tool.risk_level.value if hasattr(tool, 'risk_level') else "UNKNOWN",
        "requires_confirmation": tool.requires_confirmation if hasattr(tool, 'requires_confirmation') else False,
        "operation_categories": [cat.value for cat in tool.operation_categories] if hasattr(tool, 'operation_categories') else []
    }


@router.get("/categories/list", response_model=dict)
async def list_tool_categories(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List tool categories"""
    return get_tool_categories()


@router.get("/descriptions/list", response_model=dict)
async def list_tool_descriptions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List tool descriptions"""
    return get_tool_descriptions()


@router.post("/register", response_model=dict)
async def register_tool(
    tool_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Register a custom tool (placeholder for future implementation)"""
    # TODO: Implement custom tool registration
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Custom tool registration not yet implemented"
    )
