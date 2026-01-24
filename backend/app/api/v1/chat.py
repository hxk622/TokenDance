"""
Chat API endpoints - includes SSE streaming for real-time Agent responses.
"""
import base64
import io
import json
import logging
import tempfile

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.message import Attachment, ChatRequest, ConfirmRequest
from app.services.session_service import SessionService

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
    from app.agent.llm.base import BaseLLM
    from app.agent.llm.openrouter import create_openrouter_llm
    from app.agent.llm.router import TaskType, get_free_llm_for_task
    from app.agent.llm.vision_router import VisionTaskType, get_vision_model
    from app.agent.tools import ToolRegistry
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
        if attachment.name:
            file_ext = '.' + attachment.name.rsplit('.', 1)[-1].lower()
        elif 'pdf' in header:
            file_ext = '.pdf'
        elif 'word' in header or 'docx' in header:
            file_ext = '.docx'
        elif 'excel' in header or 'xlsx' in header:
            file_ext = '.xlsx'
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
    service: SessionService = Depends(get_session_service),
):
    """
    Send a message to the Agent and stream the response using SSE.

    Returns a Server-Sent Events stream with the following event types:
    - thinking: Agent reasoning process
    - tool_call: Tool execution start
    - tool_result: Tool execution result
    - content: Content chunks from Agent
    - confirm_required: HITL confirmation needed
    - done: Task completed
    - error: Error occurred
    """
    # Verify session exists
    session = await service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    async def event_stream():
        """Generate SSE events from Agent execution."""
        if not AGENT_ENGINE_AVAILABLE:
            # Fallback if Agent Engine is not available
            yield format_sse_event('error', {
                'message': 'Agent Engine not available',
                'type': 'ConfigurationError'
            })
            return

        try:
            # Create temporary workspace for this session
            # TODO: Use persistent workspace path from config
            with tempfile.TemporaryDirectory() as tmpdir:
                # Initialize Working Memory
                memory = await create_working_memory(
                    workspace_path=tmpdir,
                    session_id=session_id,
                    initial_task=request.content
                )

                # Create Agent Context
                context = AgentContext(
                    session_id=session_id,
                    user_id=str(session.user_id),
                    workspace_id=str(session.workspace_id)
                )

                # Create Tool Registry (empty for now)
                tools = ToolRegistry()

                # Process attachments: parse documents, keep images for vision
                attachments_for_agent, document_context = process_document_attachments(
                    request.attachments
                )

                # Build final user message with document context
                user_message = request.content
                if document_context:
                    user_message = f"{request.content}\n\n{document_context}"
                    logger.info(f"Added document context ({len(document_context)} chars) to user message")

                # 检查是否有图片附件
                has_images = len(attachments_for_agent) > 0

                # 根据是否有图片选择模型
                if has_images:
                    # 使用 Vision 模型
                    vision_model = get_vision_model(
                        task_type=VisionTaskType.CHART_ANALYSIS,  # 默认图表分析
                        max_cost=5.0  # 成本限制
                    )
                    llm: BaseLLM = create_openrouter_llm(model=vision_model, max_tokens=4096)
                    logger.info(f"Using Vision model: {vision_model}")
                else:
                    # 使用智能路由选择免费 LLM (OpenRouter)
                    llm = get_free_llm_for_task(task_type=TaskType.GENERAL, max_tokens=4096)

                # Create Agent (using BasicAgent for now)
                agent = BasicAgent(
                    context=context,
                    llm=llm,
                    tools=tools,
                    memory=memory,
                    db=service.db,
                    max_iterations=50
                )

                # Run Agent and stream events
                async for event in agent.run(
                    user_message,
                    attachments=attachments_for_agent if attachments_for_agent else None
                ):
                    # Convert SSEEvent to SSE format
                    yield format_sse_event(event.type.value, event.data)

        except Exception as e:
            logger.error(f"Error in Agent execution: {e}", exc_info=True)
            yield format_sse_event('error', {
                'message': str(e),
                'type': 'AgentExecutionError'
            })

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
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
        logger.warning("Working Memory modules not available, returning mock data")
        return {
            "session_id": session_id,
            "task_plan": {
                "content": "# Task Plan\n\n## 目标\n（任务目标待填写）\n\n## 当前进度\n- [ ] 等待开始",
                "metadata": {"status": "pending"}
            },
            "findings": {
                "content": "# Findings\n\n## 研究发现\n（暂无研究发现）",
                "metadata": {}
            },
            "progress": {
                "content": "# Progress Log\n\n## 执行记录\n（暂无执行记录）",
                "metadata": {}
            },
        }
    except Exception as e:
        logger.error(f"Error reading working memory: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read working memory: {str(e)}"
        ) from e
