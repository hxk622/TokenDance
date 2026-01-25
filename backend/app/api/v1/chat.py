"""
Chat API endpoints - includes SSE streaming for real-time Agent responses.

This is the PRIMARY endpoint for sending messages to the Agent.
All message sending should go through this endpoint (not SSE task parameter).
"""
import base64
import io
import json
import logging
import os
import time

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.dependencies import (
    get_current_user,
    get_permission_service,
)
from app.core.redis import get_redis
from app.models.user import User
from app.repositories.message_repository import MessageRepository
from app.schemas.message import Attachment, ChatRequest, ConfirmRequest
from app.services.agent_stop_service import get_agent_stop_service
from app.services.permission_service import PermissionError, PermissionService
from app.services.session_service import SessionService
from app.services.sse_event_store import get_sse_event_store

# Document conversion imports
try:
    from markitdown import MarkItDown
    MARKITDOWN_AVAILABLE = True
except ImportError:
    MARKITDOWN_AVAILABLE = False
    logging.warning("markitdown not available - document parsing disabled")

# Agent Engine imports
try:
    from app.agent import (
        AgentContext,
        BasicAgent,
        create_working_memory,
    )
    from app.agent.agents.deep_research import DeepResearchAgent
    from app.agent.llm.base import BaseLLM
    from app.agent.llm.openrouter import create_openrouter_llm
    from app.agent.llm.router import TaskType, get_free_llm_for_task
    from app.agent.llm.vision_router import VisionTaskType, get_vision_model
    from app.agent.tools import ToolRegistry
    from app.agent.tools.init_tools import register_builtin_tools
    AGENT_ENGINE_AVAILABLE = True
except ImportError as e:
    AGENT_ENGINE_AVAILABLE = False
    logging.warning(f"Agent Engine not available: {e}")

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== Helper Functions ====================

def format_sse_event(event_type: str, data: dict[str, object]) -> str:
    """Format SSE event according to SSE spec

    Args:
        event_type: Event type (thinking, content, done, error, etc.)
        data: Event data dictionary

    Returns:
        str: Formatted SSE event string
    """
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


def get_session_service(db: AsyncSession = Depends(get_db)) -> SessionService:
    """Dependency to get SessionService instance."""
    return SessionService(db)


def parse_document_attachment(attachment: Attachment) -> str | None:
    """Parse document attachment and convert to markdown text.

    Args:
        attachment: Document attachment with base64 data URL

    Returns:
        Markdown text content or None if parsing failed
    """
    if not MARKITDOWN_AVAILABLE:
        logger.warning("markitdown not available, skipping document parsing")
        return None

    if not attachment.url or not attachment.url.startswith('data:'):
        logger.warning(f"Invalid document URL format for {attachment.name}")
        return None

    try:
        # Extract base64 data from data URL
        # Format: data:application/pdf;base64,XXXX...
        header, data = attachment.url.split(',', 1)
        file_bytes = base64.b64decode(data)

        # Determine file extension from name or MIME type
        file_ext = ''
        if attachment.name and '.' in attachment.name:
            file_ext = '.' + attachment.name.rsplit('.', 1)[-1].lower()
        elif 'pdf' in header:
            file_ext = '.pdf'
        elif 'word' in header or 'docx' in header:
            file_ext = '.docx'
        elif 'excel' in header or 'xlsx' in header or 'spreadsheet' in header:
            file_ext = '.xlsx'
        elif 'powerpoint' in header or 'pptx' in header or 'presentation' in header:
            file_ext = '.pptx'
        elif 'text/plain' in header:
            file_ext = '.txt'
        elif 'text/csv' in header:
            file_ext = '.csv'
        elif 'text/markdown' in header:
            file_ext = '.md'

        # Convert using markitdown
        md = MarkItDown()
        result = md.convert_stream(io.BytesIO(file_bytes), file_extension=file_ext)

        if result and result.text_content:
            logger.info(f"Successfully parsed document: {attachment.name} ({len(result.text_content)} chars)")
            return result.text_content
        else:
            logger.warning(f"markitdown returned empty content for {attachment.name}")
            return None

    except Exception as e:
        logger.error(f"Failed to parse document {attachment.name}: {e}")
        return None


def process_document_attachments(attachments: list[Attachment] | None) -> tuple[list[dict[str, str | None]], str]:
    """Process document attachments and return agent attachments + context.

    Args:
        attachments: List of attachments from request

    Returns:
        Tuple of (attachments_for_agent, document_context)
        - attachments_for_agent: Image attachments to pass to agent
        - document_context: Parsed document text to prepend to user message
    """
    if not attachments:
        return [], ""

    agent_attachments = []
    document_texts = []

    for att in attachments:
        if att.type == "image":
            # Pass images directly to agent for vision processing
            agent_attachments.append({
                "type": att.type,
                "url": att.url,
                "name": att.name
            })
        elif att.type == "document":
            # Parse documents and convert to text context
            parsed_text = parse_document_attachment(att)
            if parsed_text:
                document_texts.append(f"## Document: {att.name or 'Unnamed'}\n\n{parsed_text}")
            else:
                # If parsing failed, still note the document
                document_texts.append(f"## Document: {att.name or 'Unnamed'}\n\n[Document parsing failed]")

    # Build document context
    document_context = ""
    if document_texts:
        document_context = "\n\n---\n\n# Attached Documents\n\n" + "\n\n---\n\n".join(document_texts) + "\n\n---\n\n"

    return agent_attachments, document_context


@router.post("/{session_id}/message")
async def send_message(
    session_id: str,
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    permission_service: PermissionService = Depends(get_permission_service),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    settings: Settings = Depends(get_settings),
):
    """
    Send a message to the Agent and stream the response using SSE.

    This is the PRIMARY endpoint for sending messages. Features:
    - Authentication required
    - Permission checking
    - Message persistence to database
    - Session status management
    - DeepResearchAgent with full tool support
    - Event storage to Redis for replay
    - Attachment support (images + documents)

    Returns a Server-Sent Events stream with the following event types:
    - session_started: Agent started processing
    - skill_matched: Task type identified
    - thinking/agent_thinking: Agent reasoning process
    - tool_call/agent_tool_call: Tool execution start
    - tool_result/agent_tool_result: Tool execution result
    - content/agent_message: Content chunks from Agent
    - confirm_required: HITL confirmation needed
    - done: Task completed
    - session_completed: Session finished successfully
    - session_failed: Session encountered error
    - error: Error occurred
    """
    # Check session access permission
    try:
        await permission_service.check_session_access(current_user, session_id)
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from e

    # Get session service and verify session exists
    session_service = SessionService(db)
    session = await session_service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    # Check if session is already running
    from app.models.session import SessionStatus
    if session.status == SessionStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Session is already running. Please wait or stop the current execution.",
        )

    # Get event store for replay support
    event_store = get_sse_event_store(redis)

    async def event_stream():
        """Generate SSE events from Agent execution with full features."""
        if not AGENT_ENGINE_AVAILABLE:
            yield format_sse_event('error', {
                'message': 'Agent Engine not available',
                'type': 'ConfigurationError'
            })
            return

        message_repo = MessageRepository(db)
        stop_service = get_agent_stop_service(redis)
        total_tokens = 0

        async def emit_event(event_type: str, data: dict) -> str:
            """Emit event, store it in Redis, and return formatted SSE."""
            seq = await event_store.store_event(session_id, event_type, data)
            return format_sse_event(event_type, {**data, '_seq': seq})

        try:
            # Mark session as RUNNING
            await session_service.start_session(session_id)

            # Process attachments: parse documents, keep images for vision
            attachments_for_agent, document_context = process_document_attachments(
                request.attachments
            )

            # Build final user message with document context
            user_message = request.content
            if document_context:
                user_message = f"{request.content}\n\n{document_context}"
                logger.info(f"Added document context ({len(document_context)} chars) to user message")

            # Send session started event
            yield await emit_event('session_started', {
                'session_id': session_id,
                'task': request.content,
                'has_attachments': len(attachments_for_agent) > 0 or bool(document_context),
                'timestamp': time.time(),
            })

            # Use persistent workspace path
            workspace_path = os.path.join(
                settings.SESSIONS_DATA_PATH,
                str(session.workspace_id),
                session_id
            )
            os.makedirs(workspace_path, exist_ok=True)

            # Save user message to database
            await message_repo.create_user_message(
                session_id=session_id,
                content=user_message,
            )

            # Initialize Working Memory
            memory = await create_working_memory(
                workspace_path=workspace_path,
                session_id=session_id,
                initial_task=user_message
            )

            # Create Agent Context
            context = AgentContext(
                session_id=session_id,
                user_id=str(current_user.id),
                workspace_id=str(session.workspace_id)
            )

            # Create Tool Registry and register built-in tools
            tools = ToolRegistry()
            register_builtin_tools(tools)

            # Check if we have images - use Vision model
            has_images = len(attachments_for_agent) > 0

            if has_images:
                # Use Vision model for image analysis
                vision_model = get_vision_model(
                    task_type=VisionTaskType.CHART_ANALYSIS,
                    max_cost=5.0
                )
                llm: BaseLLM = create_openrouter_llm(model=vision_model, max_tokens=4096)
                logger.info(f"Using Vision model: {vision_model}")

                # Send skill matched event
                yield await emit_event('skill_matched', {
                    'skill_id': 'vision_analysis',
                    'skill_name': 'vision_analysis',
                    'display_name': '图像分析',
                    'description': '分析图片内容',
                    'icon': 'image',
                    'color': '#00D9FF',
                    'confidence': 1.0,
                    'timestamp': time.time(),
                })

                # Use BasicAgent for vision tasks
                agent = BasicAgent(
                    context=context,
                    llm=llm,
                    tools=tools,
                    memory=memory,
                    db=db,
                    max_iterations=50
                )
            else:
                # Use DeepResearchAgent for text tasks
                llm = get_free_llm_for_task(
                    task_type=TaskType.DEEP_RESEARCH,
                    max_tokens=8192
                )

                # Send skill matched event
                yield await emit_event('skill_matched', {
                    'skill_id': 'deep_research',
                    'skill_name': 'deep_research',
                    'display_name': '深度研究',
                    'description': '深度研究技能，用于复杂信息检索和分析',
                    'icon': 'search',
                    'color': '#00D9FF',
                    'confidence': 1.0,
                    'timestamp': time.time(),
                })

                # Use DeepResearchAgent
                agent = DeepResearchAgent(
                    context=context,
                    llm=llm,
                    tools=tools,
                    memory=memory,
                    db=db,
                    max_iterations=50
                )

            # Collect assistant response for saving
            assistant_content_parts = []
            assistant_thinking = None
            assistant_tool_calls = []
            iteration_count = 0

            # Run Agent and stream events
            async for event in agent.run(
                user_message,
                attachments=attachments_for_agent if attachments_for_agent else None
            ):
                # Check stop signal periodically
                iteration_count += 1
                if iteration_count % 5 == 0:
                    if await stop_service.should_stop(session_id):
                        logger.info(f"Stop signal received for session {session_id}")
                        await stop_service.clear_stop_signal(session_id)
                        agent.stopped = True
                        break

                # Emit event with storage
                event_type = event.type.value if hasattr(event.type, 'value') else str(event.type)
                yield await emit_event(event_type, event.data)

                # Collect response data for message saving
                if event_type in ('thinking', 'agent_thinking'):
                    assistant_thinking = event.data.get('content', '')
                elif event_type in ('content', 'agent_message'):
                    assistant_content_parts.append(event.data.get('content', ''))
                elif event_type in ('tool_call', 'agent_tool_call'):
                    assistant_tool_calls.append({
                        'id': event.data.get('id'),
                        'name': event.data.get('name'),
                        'args': event.data.get('args'),
                        'status': event.data.get('status'),
                    })
                elif event_type in ('tool_result', 'agent_tool_result'):
                    tool_id = event.data.get('id')
                    for tc in assistant_tool_calls:
                        if tc.get('id') == tool_id:
                            tc['status'] = 'success' if event.data.get('success') else 'error'
                            tc['result'] = event.data.get('result')
                            break
                elif event_type == 'done':
                    total_tokens = event.data.get('tokens_used', 0)

            # Save assistant message to database
            assistant_content = ''.join(assistant_content_parts)
            if assistant_content or assistant_tool_calls:
                await message_repo.create_assistant_message(
                    session_id=session_id,
                    content=assistant_content if assistant_content else None,
                    thinking=assistant_thinking,
                    tool_calls=assistant_tool_calls if assistant_tool_calls else None,
                    tokens_used=total_tokens,
                )

            # Mark session as COMPLETED
            await session_service.complete_session(
                session_id,
                total_tokens_used=total_tokens,
            )

            # Send session completed event
            yield await emit_event('session_completed', {
                'session_id': session_id,
                'status': 'completed',
                'total_tokens': total_tokens,
                'timestamp': time.time(),
            })

        except Exception as e:
            logger.error(f"Error in Agent execution: {e}", exc_info=True)

            # Mark session as FAILED
            try:
                await session_service.fail_session(
                    session_id,
                    error_message=str(e),
                )
            except Exception as fail_err:
                logger.error(f"Failed to mark session as failed: {fail_err}")

            # Send error events
            yield await emit_event('session_failed', {
                'session_id': session_id,
                'error': str(e),
                'timestamp': time.time(),
            })
            yield format_sse_event('error', {
                'message': str(e),
                'type': 'AgentExecutionError'
            })

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/{session_id}/confirm")
async def confirm_action(
    session_id: str,
    request: ConfirmRequest,
    service: SessionService = Depends(get_session_service),
):
    """
    Confirm or reject a HITL (Human-in-the-Loop) action.

    This endpoint is used when the Agent requests user confirmation
    for high-risk operations.
    """
    # Verify session exists
    session = await service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    # TODO: Implement HITL confirmation handling
    # This will integrate with Agent Engine's state machine

    return {
        "status": "confirmed" if request.confirmed else "rejected",
        "action_id": request.action_id,
        "message": "Confirmation received. Agent will continue execution."
        if request.confirmed
        else "Action rejected. Agent will skip this operation.",
    }


@router.post("/{session_id}/stop", status_code=status.HTTP_200_OK)
async def stop_generation(
    session_id: str,
    service: SessionService = Depends(get_session_service),
):
    """
    Stop the current Agent execution for this session.

    This gracefully terminates the Agent's current task.
    """
    # Verify session exists
    session = await service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    # TODO: Implement stop signal to Agent Engine
    # This will set a flag that Agent checks during its loop

    return {
        "status": "stopped",
        "message": "Agent execution stopped successfully.",
    }


@router.get("/{session_id}/working-memory")
async def get_working_memory(
    session_id: str,
    service: SessionService = Depends(get_session_service),
):
    """
    Get Working Memory (Three Files) content for a session.

    Returns the contents of:
    - task_plan.md - Task roadmap and objectives
    - findings.md - Research findings and decisions
    - progress.md - Execution logs and errors

    This implements the Manus "Three Files Working Memory" pattern.
    """
    # Verify session exists
    session = await service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    try:
        # Try to get real Working Memory from filesystem
        from app.agent.working_memory import ThreeFilesManager
        from app.core.config import settings
        from app.filesystem import AgentFileSystem

        # Initialize filesystem (using workspace_id from session)
        workspace_path = settings.WORKSPACE_ROOT_PATH or "/tmp/tokendance/workspaces"
        fs = AgentFileSystem(
            workspace_root=workspace_path,
            org_id=str(session.workspace_id),  # Using workspace_id as org for now
            team_id="default",
            workspace_id=str(session.workspace_id)
        )

        # Get Three Files Manager
        three_files = ThreeFilesManager(fs, session_id)

        # Read all files
        data = three_files.read_all()

        return {
            "session_id": session_id,
            "task_plan": {
                "content": data["task_plan"]["content"],
                "metadata": data["task_plan"].get("metadata", {})
            },
            "findings": {
                "content": data["findings"]["content"],
                "metadata": data["findings"].get("metadata", {})
            },
            "progress": {
                "content": data["progress"]["content"],
                "metadata": data["progress"].get("metadata", {})
            },
        }

    except ImportError:
        # Fallback if filesystem modules not available
        logger.error("Working Memory modules not available")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Working Memory service is not available. Please ensure the agent engine is properly configured."
        )
    except Exception as e:
        logger.error(f"Error reading working memory: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read working memory: {str(e)}"
        ) from e
