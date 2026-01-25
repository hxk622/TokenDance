"""
Project API endpoints - Project-First architecture.

Core endpoints:
- /projects: CRUD operations for projects
- /projects/{id}/conversations: Conversation management
- /projects/{id}/chat: Chat within a project (SSE streaming)
"""
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.project import ProjectStatus, ProjectType
from app.schemas.conversation import (
    ChatMessage,
    ConversationCreate,
    ConversationList,
    ConversationResponse,
)
from app.schemas.project import (
    ProjectCreate,
    ProjectDetail,
    ProjectList,
    ProjectResponse,
    ProjectUpdate,
)
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])
logger = logging.getLogger(__name__)


# ============ Project CRUD ============


@router.post("", response_model=ProjectResponse)
async def create_project(
    data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """
    Create a new project.

    A project is the core work unit in the Project-First architecture.
    It can be one of several types:
    - research: Deep research tasks
    - document: Document writing
    - slides: PPT generation
    - code: Code projects
    - data_analysis: Data analysis tasks
    - quick_task: Lightweight projects for quick questions (default)
    """
    service = ProjectService(db)
    project = await service.create_project(data)
    return ProjectResponse.model_validate(project)


@router.get("", response_model=ProjectList)
async def list_projects(
    workspace_id: str = Query(..., description="Workspace ID"),
    status: ProjectStatus | None = Query(None, description="Filter by status"),
    project_type: ProjectType | None = Query(None, description="Filter by type"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> ProjectList:
    """
    List projects in a workspace with pagination.

    By default, archived projects are excluded.
    """
    service = ProjectService(db)
    projects, total = await service.list_projects(
        workspace_id=workspace_id,
        limit=limit,
        offset=offset,
        status=status,
        project_type=project_type,
    )
    return ProjectList(
        items=[ProjectResponse.model_validate(p) for p in projects],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{project_id}", response_model=ProjectDetail)
async def get_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> ProjectDetail:
    """
    Get project details by ID.

    Includes full context (decisions, failures, findings) and settings.
    """
    service = ProjectService(db)
    project = await service.get_project(
        project_id,
        include_conversations=False,
        include_artifacts=False,
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectDetail.model_validate(project)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    data: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """
    Update project fields.

    Can update title, description, status, context, and settings.
    """
    service = ProjectService(db)
    project = await service.update_project(project_id, data)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectResponse.model_validate(project)


@router.delete("/{project_id}")
async def archive_project(
    project_id: str,
    hard_delete: bool = Query(False, description="Hard delete instead of archive"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """
    Archive or delete a project.

    By default, projects are soft-deleted (archived).
    Use hard_delete=true to permanently delete.
    """
    service = ProjectService(db)
    if hard_delete:
        success = await service.delete_project(project_id)
        if not success:
            raise HTTPException(status_code=404, detail="Project not found")
        return {"status": "deleted", "project_id": project_id}
    else:
        project = await service.archive_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return {"status": "archived", "project_id": project_id}


# ============ Conversation Management ============


@router.post("/{project_id}/conversations", response_model=ConversationResponse)
async def create_conversation(
    project_id: str,
    data: ConversationCreate | None = None,
    db: AsyncSession = Depends(get_db),
) -> ConversationResponse:
    """
    Create a new conversation within a project.

    A conversation represents a multi-turn interaction focused on a specific purpose:
    - general: General discussion or questions
    - initial_draft: Creating the initial artifact
    - refinement: Refining/editing existing artifact
    - review: Reviewing and providing feedback
    - export: Preparing for export/delivery

    Optionally, include selection context for in-place editing.
    """
    service = ProjectService(db)
    conversation = await service.create_conversation(project_id, data)
    if not conversation:
        raise HTTPException(status_code=404, detail="Project not found")

    return ConversationResponse(
        id=conversation.id,
        project_id=conversation.project_id,
        title=conversation.title,
        purpose=conversation.purpose,
        status=conversation.status,
        tokens_used=conversation.tokens_used,
        message_count=len(conversation.messages) if conversation.messages else 0,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        completed_at=conversation.completed_at,
    )


@router.get("/{project_id}/conversations", response_model=ConversationList)
async def list_conversations(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> ConversationList:
    """
    List all conversations in a project.
    """
    service = ProjectService(db)
    project = await service.get_project(project_id, include_conversations=True)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    conversations = project.conversations or []
    return ConversationList(
        items=[
            ConversationResponse(
                id=c.id,
                project_id=c.project_id,
                title=c.title,
                purpose=c.purpose,
                status=c.status,
                tokens_used=c.tokens_used,
                message_count=len(c.messages) if c.messages else 0,
                created_at=c.created_at,
                updated_at=c.updated_at,
                completed_at=c.completed_at,
            )
            for c in conversations
        ],
        total=len(conversations),
    )


# ============ Chat Endpoint ============


@router.post("/{project_id}/chat")
async def chat_in_project(
    project_id: str,
    data: ChatMessage,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Send a chat message within a project.

    This endpoint:
    1. Gets or creates a conversation
    2. Creates a Session for SSE streaming
    3. Returns session_id for frontend to connect to /sessions/{session_id}/stream

    The frontend should:
    1. Call this endpoint to get session_id
    2. Connect to SSE stream: /api/v1/sessions/{session_id}/stream?task={message}
    3. Receive real-time execution updates
    """
    service = ProjectService(db)

    # Get project
    project = await service.get_project(project_id, include_artifacts=True)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get or create conversation
    conversation = await service.get_or_create_conversation(
        project_id=project_id,
        conversation_id=data.conversation_id,
        selection=data.selection,
    )
    if not conversation:
        raise HTTPException(status_code=500, detail="Failed to create conversation")

    # Create a Session for SSE streaming
    session = await service.create_session_for_conversation(
        project_id=project_id,
        conversation_id=conversation.id,
        task=data.message,
    )
    if not session:
        raise HTTPException(status_code=500, detail="Failed to create session")

    # Build context info for response
    context = await service.get_context_for_llm(project_id)

    return {
        "status": "ready",
        "project_id": project_id,
        "conversation_id": conversation.id,
        "session_id": session.id,  # Key: Frontend uses this for SSE connection
        "message": data.message,
        "context_available": {
            "intent": bool(context.get("intent")),
            "decisions_count": len(context.get("decisions", [])),
            "failures_count": len(context.get("failures", [])),
            "findings_count": len(context.get("key_findings", [])),
            "artifacts_count": len(context.get("artifacts", [])),
        },
        "selection": data.selection.model_dump() if data.selection else None,
        "sse_endpoint": f"/api/v1/sessions/{session.id}/stream",
    }


# ============ Context Management ============


@router.post("/{project_id}/context/decision")
async def add_decision(
    project_id: str,
    decision: str = Query(..., description="The decision made"),
    reason: str | None = Query(None, description="Reason for the decision"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Add a decision to the project context.

    Decisions are preserved across all conversations for Plan Recitation.
    """
    service = ProjectService(db)
    project = await service.add_decision(project_id, decision, reason)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {
        "status": "added",
        "decision": decision,
        "total_decisions": len(project.context.get("decisions", [])),
    }


@router.post("/{project_id}/context/failure")
async def add_failure(
    project_id: str,
    failure_type: str = Query(..., description="Type of failure"),
    message: str = Query(..., description="Error message"),
    learning: str | None = Query(None, description="Lesson learned"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Add a failure record to the project context (Keep the Failures).

    Failures are preserved across all conversations to prevent repeating mistakes.
    """
    service = ProjectService(db)
    project = await service.add_failure(project_id, failure_type, message, learning)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {
        "status": "added",
        "failure_type": failure_type,
        "total_failures": len(project.context.get("failures", [])),
    }


@router.post("/{project_id}/context/finding")
async def add_finding(
    project_id: str,
    finding: str = Query(..., description="The key finding"),
    source: str | None = Query(None, description="Source of the finding"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Add a key finding to the project context.

    Findings are preserved for reference in subsequent conversations.
    """
    service = ProjectService(db)
    project = await service.add_finding(project_id, finding, source)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {
        "status": "added",
        "finding": finding,
        "total_findings": len(project.context.get("key_findings", [])),
    }


@router.get("/{project_id}/context")
async def get_project_context(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Get the full project context.

    Returns intent, decisions, failures, findings, and artifact summaries.
    This is what gets passed to the LLM for context.
    """
    service = ProjectService(db)
    context = await service.get_context_for_llm(project_id)
    if not context:
        raise HTTPException(status_code=404, detail="Project not found")
    return context
