from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.repositories.session_repository import SessionRepository
from app.services.permission_service import PermissionService
from app.agent.working_memory.three_files import ThreeFilesManager
from app.filesystem import AgentFileSystem

router = APIRouter(prefix="/working-memory", tags=["Working Memory"])


@router.get("/sessions/{session_id}")
async def get_working_memory(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get working memory for a session (three files)"""
    
    # Verify session exists and user has access
    session_repo = SessionRepository(db)
    session = await session_repo.get_by_id(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Check workspace access
    permission_service = PermissionService(db)
    has_access = await permission_service.check_workspace_access(
        user_id=current_user.id,
        workspace_id=session.workspace_id
    )
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this workspace"
        )
    
    # Get working memory
    filesystem = AgentFileSystem()
    memory_manager = ThreeFilesManager(filesystem, session_id)
    
    data = memory_manager.read_all()
    
    return {
        "session_id": session_id,
        "task_plan": {
            "metadata": data["task_plan"]["metadata"],
            "content": data["task_plan"]["content"]
        },
        "findings": {
            "metadata": data["findings"]["metadata"],
            "content": data["findings"]["content"]
        },
        "progress": {
            "metadata": data["progress"]["metadata"],
            "content": data["progress"]["content"]
        },
        "file_paths": memory_manager.get_file_paths()
    }


@router.get("/sessions/{session_id}/task-plan")
async def get_task_plan(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get task plan for a session"""
    
    # Verify session exists and user has access
    session_repo = SessionRepository(db)
    session = await session_repo.get_by_id(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Check workspace access
    permission_service = PermissionService(db)
    has_access = await permission_service.check_workspace_access(
        user_id=current_user.id,
        workspace_id=session.workspace_id
    )
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this workspace"
        )
    
    # Get task plan
    filesystem = AgentFileSystem()
    memory_manager = ThreeFilesManager(filesystem, session_id)
    
    data = memory_manager.read_task_plan()
    
    return {
        "session_id": session_id,
        "metadata": data["metadata"],
        "content": data["content"]
    }


@router.put("/sessions/{session_id}/task-plan")
async def update_task_plan(
    session_id: str,
    content: str,
    append: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update task plan for a session"""
    
    # Verify session exists and user has access
    session_repo = SessionRepository(db)
    session = await session_repo.get_by_id(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Check workspace access
    permission_service = PermissionService(db)
    has_access = await permission_service.check_workspace_access(
        user_id=current_user.id,
        workspace_id=session.workspace_id
    )
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this workspace"
        )
    
    # Update task plan
    filesystem = AgentFileSystem()
    memory_manager = ThreeFilesManager(filesystem, session_id)
    
    memory_manager.update_task_plan(content, append=append)
    
    return {
        "status": "success",
        "message": "Task plan updated"
    }


@router.get("/sessions/{session_id}/findings")
async def get_findings(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get findings for a session"""
    
    # Verify session exists and user has access
    session_repo = SessionRepository(db)
    session = await session_repo.get_by_id(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Check workspace access
    permission_service = PermissionService(db)
    has_access = await permission_service.check_workspace_access(
        user_id=current_user.id,
        workspace_id=session.workspace_id
    )
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this workspace"
        )
    
    # Get findings
    filesystem = AgentFileSystem()
    memory_manager = ThreeFilesManager(filesystem, session_id)
    
    data = memory_manager.read_findings()
    
    return {
        "session_id": session_id,
        "metadata": data["metadata"],
        "content": data["content"]
    }


@router.post("/sessions/{session_id}/findings")
async def add_finding(
    session_id: str,
    finding: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add a new finding to the findings file"""
    
    # Verify session exists and user has access
    session_repo = SessionRepository(db)
    session = await session_repo.get_by_id(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Check workspace access
    permission_service = PermissionService(db)
    has_access = await permission_service.check_workspace_access(
        user_id=current_user.id,
        workspace_id=session.workspace_id
    )
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this workspace"
        )
    
    # Add finding
    filesystem = AgentFileSystem()
    memory_manager = ThreeFilesManager(filesystem, session_id)
    
    memory_manager.update_findings(finding)
    
    return {
        "status": "success",
        "message": "Finding added"
    }


@router.get("/sessions/{session_id}/progress")
async def get_progress(
    session_id: str,
    last_n_chars: int = 500,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get progress log for a session"""
    
    # Verify session exists and user has access
    session_repo = SessionRepository(db)
    session = await session_repo.get_by_id(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Check workspace access
    permission_service = PermissionService(db)
    has_access = await permission_service.check_workspace_access(
        user_id=current_user.id,
        workspace_id=session.workspace_id
    )
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this workspace"
        )
    
    # Get progress
    filesystem = AgentFileSystem()
    memory_manager = ThreeFilesManager(filesystem, session_id)
    
    data = memory_manager.read_progress()
    
    # Return last N characters if requested
    content = data["content"]
    if last_n_chars > 0 and len(content) > last_n_chars:
        content = "..." + content[-last_n_chars:]
    
    return {
        "session_id": session_id,
        "metadata": data["metadata"],
        "content": content
    }


@router.get("/sessions/{session_id}/summary")
async def get_memory_summary(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get working memory summary for context injection"""
    
    # Verify session exists and user has access
    session_repo = SessionRepository(db)
    session = await session_repo.get_by_id(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Check workspace access
    permission_service = PermissionService(db)
    has_access = await permission_service.check_workspace_access(
        user_id=current_user.id,
        workspace_id=session.workspace_id
    )
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this workspace"
        )
    
    # Get summary
    filesystem = AgentFileSystem()
    memory_manager = ThreeFilesManager(filesystem, session_id)
    
    summary = memory_manager.get_context_summary()
    
    return {
        "session_id": session_id,
        "summary": summary
    }
