"""
SSE (Server-Sent Events) Stream API

Provides real-time streaming of Agent execution events.
"""
import asyncio
import json
import logging
import time
from collections.abc import AsyncGenerator
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.dependencies import (
    get_current_user,
    get_current_user_from_token,
    get_permission_service,
    get_user_repo,
)
from app.core.logging import get_logger
from app.core.redis import get_redis
from app.models.artifact import ArtifactType
from app.models.user import User
from app.repositories.artifact_repository import ArtifactRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.user_repository import UserRepository
from app.services.agent_stop_service import get_agent_stop_service
from app.services.object_storage import get_object_storage
from app.services.permission_service import PermissionError, PermissionService
from app.services.session_service import SessionService
from app.services.sse_event_store import SSEEventStore, get_sse_event_store
from app.services.sse_token_service import get_sse_token_service

# Agent Engine imports
try:
    from app.agent import (
        AgentContext,
        create_working_memory,
    )
    from app.agent.agents.deep_research import DeepResearchAgent
    from app.agent.checkpoint import CheckpointManager  # Manus 无限记忆模式
    from app.filesystem import AgentFileSystem
    from app.agent.llm.router import TaskType, get_free_llm_for_task
    from app.agent.tools import ToolRegistry
    from app.agent.tools.init_tools import register_builtin_tools
    AGENT_ENGINE_AVAILABLE = True
except ImportError as e:
    AGENT_ENGINE_AVAILABLE = False
    logging.warning(f"Agent Engine not available: {e}")

logger = get_logger(__name__)
router = APIRouter()


class SSEEventType(str, Enum):
    """SSE Event Types - 前后端统一定义

    详细规范见: docs/architecture/SSE-Events-Spec.md
    """
    # Session events
    SESSION_STARTED = "session_started"
    SESSION_COMPLETED = "session_completed"
    SESSION_FAILED = "session_failed"

    # Skill events
    SKILL_MATCHED = "skill_matched"
    SKILL_COMPLETED = "skill_completed"

    # Agent events
    AGENT_THINKING = "agent_thinking"
    AGENT_TOOL_CALL = "agent_tool_call"
    AGENT_TOOL_RESULT = "agent_tool_result"
    AGENT_MESSAGE = "agent_message"
    AGENT_ERROR = "agent_error"

    # Workflow planning events (task decomposition)
    PLAN_CREATED = "plan_created"
    NODE_CREATED = "node_created"
    EDGE_CREATED = "edge_created"
    PLAN_FINALIZED = "plan_finalized"

    # Workflow node execution events
    NODE_STARTED = "node_started"
    NODE_COMPLETED = "node_completed"
    NODE_FAILED = "node_failed"

    # File events
    FILE_CREATED = "file_created"
    FILE_MODIFIED = "file_modified"
    FILE_DELETED = "file_deleted"
    FILE_READ = "file_read"

    # Browser events
    BROWSER_OPENED = "browser_opened"
    BROWSER_NAVIGATED = "browser_navigated"
    BROWSER_ACTION = "browser_action"
    BROWSER_SCREENSHOT = "browser_screenshot"
    BROWSER_CLOSED = "browser_closed"

    # HITL (Human-in-the-Loop) events
    HITL_REQUEST = "hitl_request"
    HITL_TIMEOUT = "hitl_timeout"

    # Artifact events
    ARTIFACT_CREATED = "artifact_created"
    ARTIFACT_UPDATED = "artifact_updated"

    # Progress events
    PROGRESS_UPDATE = "progress_update"
    ITERATION_START = "iteration_start"

    # Token/Cost events
    TOKEN_USAGE = "token_usage"

    # System events
    PING = "ping"
    ERROR = "error"

    # P1-3: Replay events (sent on reconnection)
    REPLAY_START = "replay_start"
    REPLAY_END = "replay_end"


def format_sse(event: str, data: dict | None, seq: int | None = None) -> str:
    """Format data as SSE message with optional sequence number.

    Args:
        event: SSE event type
        data: Event data (dict or None). If None, sends empty object.
        seq: Optional sequence number for event replay

    Returns:
        Formatted SSE message string
    """
    # Ensure data is never None or undefined
    if data is None:
        data = {}

    # Validate data is a dict
    if not isinstance(data, dict):
        logger.warning(
            "sse_invalid_data_type",
            event=event,
            data_type=type(data).__name__,
        )
        data = {"error": "Invalid data type", "original_type": type(data).__name__}

    # Add sequence number if provided
    if seq is not None:
        data = {**data, "_seq": seq}

    # Serialize to JSON with error handling
    try:
        json_data = json.dumps(data, ensure_ascii=False)
    except (TypeError, ValueError) as e:
        logger.error(
            "sse_json_serialization_error",
            event=event,
            error=str(e),
        )
        # Fallback to safe error message
        json_data = json.dumps({
            "error": "Failed to serialize event data",
            "event_type": event,
        })

    return f"event: {event}\ndata: {json_data}\n\n"


# ==================== P1-1: SSE Token Exchange ====================

class SSETokenRequest(BaseModel):
    """Request for SSE token exchange."""
    session_id: str


class SSETokenResponse(BaseModel):
    """Response with short-lived SSE token."""
    sse_token: str
    expires_in: int = 300  # seconds


@router.post("/sse-token", response_model=SSETokenResponse)
async def create_sse_token(
    request: SSETokenRequest,
    current_user: User = Depends(get_current_user),
    permission_service: PermissionService = Depends(get_permission_service),
    redis: Redis = Depends(get_redis),
):
    """
    P1-1: Exchange access token for short-lived SSE token.

    This avoids exposing JWT tokens in SSE connection URLs.
    The returned SSE token:
    - Is valid for 5 minutes
    - Can only be used for the specified session
    - Is single-use (consumed on first SSE connection)

    Usage:
    1. POST /api/v1/sessions/sse-token with {session_id: "..."}
    2. Use returned sse_token in SSE connection URL: ?sse_token=...
    """
    # Check session access permission
    try:
        await permission_service.check_session_access(current_user, request.session_id)
    except PermissionError as e:
        raise HTTPException(
            status_code=403,
            detail=str(e),
        ) from e

    # Create SSE token
    sse_service = await get_sse_token_service(redis)
    token = await sse_service.create_sse_token(
        user_id=str(current_user.id),
        session_id=request.session_id,
    )

    return SSETokenResponse(sse_token=token)


# ==================== P1-2: Stop Signal ====================

class StopResponse(BaseModel):
    """Response from stop request."""
    status: str
    message: str


@router.post("/{session_id}/stop", response_model=StopResponse)
async def stop_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    permission_service: PermissionService = Depends(get_permission_service),
    redis: Redis = Depends(get_redis),
    db: AsyncSession = Depends(get_db),
):
    """
    P1-2: Request agent to stop execution.

    Sets a stop flag in Redis that the agent checks periodically.
    The agent will gracefully terminate and update session status to CANCELLED.
    """
    # Check session access permission
    try:
        await permission_service.check_session_access(current_user, session_id)
    except PermissionError as e:
        raise HTTPException(
            status_code=403,
            detail=str(e),
        ) from e

    # Set stop signal
    stop_service = get_agent_stop_service(redis)
    await stop_service.request_stop(session_id, str(current_user.id))

    return StopResponse(
        status="stop_requested",
        message="Stop signal sent. Agent will terminate gracefully.",
    )


async def mock_agent_execution_stream(session_id: str) -> AsyncGenerator[str, None]:
    """
    Mock agent execution stream for demonstration.

    In production, this would:
    1. Subscribe to Redis pub/sub for session events
    2. Stream events as they occur
    3. Handle reconnection and keepalive
    """

    # Send session started
    yield format_sse(SSEEventType.SESSION_STARTED, {
        "session_id": session_id,
        "timestamp": time.time(),
    })

    # Simulate skill matching
    yield format_sse(SSEEventType.SKILL_MATCHED, {
        "skill_id": "deep_research",
        "skill_name": "deep_research",
        "display_name": "Deep Research",
        "description": "深度研究技能，用于复杂信息检索和分析",
        "icon": "search",
        "color": "blue",
        "confidence": 0.92,
        "timestamp": time.time(),
    })
    await asyncio.sleep(0.3)

    # Simulate workflow execution
    nodes = [
        {"id": "1", "type": "manus", "label": "搜索市场数据"},
        {"id": "2", "type": "manus", "label": "分析竞品"},
        {"id": "3", "type": "coworker", "label": "生成报告"},
    ]

    for node in nodes:
        # Node started
        yield format_sse(SSEEventType.NODE_STARTED, {
            "node_id": node["id"],
            "node_type": node["type"],
            "label": node["label"],
            "status": "active",
            "timestamp": time.time(),
        })

        # Agent thinking
        yield format_sse(SSEEventType.AGENT_THINKING, {
            "content": f"正在执行: {node['label']}...",
            "node_id": node["id"],
            "timestamp": time.time(),
        })
        await asyncio.sleep(0.5)

        # Tool call
        if node["type"] == "manus":
            yield format_sse(SSEEventType.AGENT_TOOL_CALL, {
                "tool_name": "web_search" if node["id"] == "1" else "analyze_data",
                "arguments": {"query": "AI Agent market analysis"} if node["id"] == "1" else {"data_source": "search_results"},
                "node_id": node["id"],
                "timestamp": time.time(),
            })
            await asyncio.sleep(0.3)

            # Tool result
            yield format_sse(SSEEventType.AGENT_TOOL_RESULT, {
                "tool_name": "web_search" if node["id"] == "1" else "analyze_data",
                "success": True,
                "result": {"found": 3, "sources": ["report1", "report2", "report3"]} if node["id"] == "1" else {"insights": ["insight1", "insight2"]},
                "node_id": node["id"],
                "timestamp": time.time(),
            })
        elif node["type"] == "coworker":
            # File operations
            yield format_sse(SSEEventType.FILE_CREATED, {
                "path": "findings.md",
                "action": "created",
                "timestamp": time.time(),
            })
            await asyncio.sleep(0.2)

            yield format_sse(SSEEventType.FILE_MODIFIED, {
                "path": "report.md",
                "action": "modified",
                "timestamp": time.time(),
            })

        await asyncio.sleep(0.5)

        # Node completed
        yield format_sse(SSEEventType.NODE_COMPLETED, {
            "node_id": node["id"],
            "node_type": node["type"],
            "label": node["label"],
            "status": "success",
            "duration_ms": 1000,
            "timestamp": time.time(),
        })

        await asyncio.sleep(0.3)

    # Final message
    yield format_sse(SSEEventType.AGENT_MESSAGE, {
        "content": "任务执行完成！已生成研究报告。",
        "role": "assistant",
        "timestamp": time.time(),
    })

    # Skill completed
    yield format_sse(SSEEventType.SKILL_COMPLETED, {
        "skill_id": "deep_research",
        "status": "success",
        "duration_ms": 3500,
        "timestamp": time.time(),
    })

    # Session completed
    yield format_sse(SSEEventType.SESSION_COMPLETED, {
        "session_id": session_id,
        "status": "completed",
        "timestamp": time.time(),
    })


async def keepalive_generator(
    stream: AsyncGenerator[str, None],
    interval: int = 15,
) -> AsyncGenerator[str, None]:
    """
    Wrap a stream with keepalive pings.

    Sends ping events every `interval` seconds to keep connection alive.
    """
    last_ping = time.time()

    async for event in stream:
        yield event

        # Check if we need to send a keepalive
        now = time.time()
        if now - last_ping >= interval:
            yield format_sse(SSEEventType.PING, {"timestamp": now})
            last_ping = now


@router.api_route("/{session_id}/stream", methods=["GET", "HEAD"])
async def stream_session_events(
    session_id: str,
    request: Request,
    task: str | None = Query(None, description="Task to execute"),
    token: str | None = Query(None, description="JWT auth token (deprecated, use sse_token)"),
    sse_token: str | None = Query(None, description="P1-1: Short-lived SSE token from /sse-token"),
    last_seq: int | None = Query(None, description="P1-3: Last received sequence number for replay"),
    user_repo: UserRepository = Depends(get_user_repo),
    permission_service: PermissionService = Depends(get_permission_service),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    settings: Settings = Depends(get_settings),
):
    """
    Stream SSE events for a session.

    P1-1: Supports both JWT token (deprecated) and short-lived SSE token.
    P1-3: Supports event replay via last_seq parameter.

    If task is provided, starts Agent execution.
    Otherwise, returns mock stream for demo purposes.

    Events include:
    - agent_thinking: Agent's reasoning process
    - agent_tool_call: Tool invocation
    - agent_tool_result: Tool execution result
    - agent_message: Final message
    - node_started/completed/failed: Workflow node status
    - file_created/modified/deleted: Coworker file operations
    - session_started/completed/failed: Session lifecycle
    - replay_start/replay_end: P1-3 event replay markers
    - ping: Keepalive

    Usage (recommended - P1-1):
        1. POST /api/v1/sessions/sse-token to get short-lived token
        2. const eventSource = new EventSource(`/api/v1/sessions/${sessionId}/stream?sse_token=${sseToken}`);

    Usage (reconnection - P1-3):
        const eventSource = new EventSource(`/api/v1/sessions/${sessionId}/stream?sse_token=${sseToken}&last_seq=${lastSeq}`);
    """
    # Handle HEAD requests - browsers send these to check if SSE endpoint is available
    if request.method == "HEAD":
        return Response(
            status_code=200,
            headers={
                "Content-Type": "text/event-stream",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    # P1-1: Authenticate using SSE token (preferred) or JWT token (deprecated)
    current_user = None

    if sse_token:
        # Validate SSE token
        sse_service = await get_sse_token_service(redis)
        token_data = await sse_service.validate_sse_token(
            sse_token,
            session_id,
            consume=True,  # Single-use
        )
        if not token_data:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired SSE token",
                headers={"X-Error-Type": "InvalidSSEToken"},
            )
        # Get user from token data
        user_id = token_data.get("user_id")
        current_user = await user_repo.get_by_id(user_id)
        if not current_user:
            raise HTTPException(
                status_code=401,
                detail="User not found",
            )
    elif token:
        # Fallback to JWT token (deprecated)
        logger.warning(
            "sse_using_deprecated_jwt_token",
            session_id=session_id,
        )
        current_user = await get_current_user_from_token(token, user_repo)
    else:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Provide sse_token or token parameter.",
        )

    # P0-4: Check session access permission
    try:
        await permission_service.check_session_access(current_user, session_id)
    except PermissionError as e:
        logger.warning(
            "sse_session_access_denied",
            session_id=session_id,
            user_id=str(current_user.id),
            error=str(e),
        )
        raise HTTPException(
            status_code=403,
            detail=str(e),
            headers={
                "X-Error-Type": "PermissionDenied",
                "Cache-Control": "no-store",
            }
        ) from e

    # Verify session exists
    session_service = SessionService(db)
    session = await session_service.get_session(session_id)

    if not session:
        logger.warning(
            "sse_session_not_found",
            session_id=session_id,
            user_id=str(current_user.id),
            client_ip=request.client.host if request.client else "unknown",
        )
        raise HTTPException(
            status_code=404,
            detail=f"Session {session_id} not found",
            headers={
                "X-Error-Type": "SessionNotFound",
                "Cache-Control": "no-store",
            }
        )

    # P1-3: Get event store for replay and storage
    event_store = get_sse_event_store(redis)

    logger.info(
        "sse_stream_started",
        session_id=session_id,
        task=task,
        last_seq=last_seq,
        client_ip=request.client.host if request.client else "unknown",
    )

    async def event_generator():
        try:
            # P1-3: Replay missed events if last_seq is provided
            if last_seq is not None:
                yield format_sse(SSEEventType.REPLAY_START, {
                    "last_seq": last_seq,
                    "timestamp": time.time(),
                })

                missed_events = await event_store.get_events_since(
                    session_id,
                    last_seq,
                    max_events=100,
                )

                for event in missed_events:
                    yield format_sse(
                        event["event"],
                        event["data"],
                        seq=event["seq"],
                    )

                yield format_sse(SSEEventType.REPLAY_END, {
                    "replayed_count": len(missed_events),
                    "timestamp": time.time(),
                })

            # If task is provided and Agent Engine is available, run real agent
            # BUG FIX: Only start Agent if session is PENDING to prevent
            # SSE reconnection from re-triggering Agent execution
            from app.models.session import SessionStatus

            should_start_agent = (
                task and
                AGENT_ENGINE_AVAILABLE and
                session.status == SessionStatus.PENDING
            )

            if should_start_agent:
                logger.info(
                    "sse_starting_agent",
                    session_id=session_id,
                    task=task[:100] if task else None,
                )
                async for event in run_agent_stream_with_store(
                    session_id, task, session.workspace_id, str(current_user.id),
                    db, redis, settings, event_store
                ):
                    if await request.is_disconnected():
                        logger.info("sse_client_disconnected", session_id=session_id)
                        # P0-1: Cancel session on disconnect
                        await session_service.cancel_session(session_id)
                        break
                    yield event
            elif task and session.status != SessionStatus.PENDING:
                # Session already running or completed - don't re-trigger
                logger.info(
                    "sse_skipping_agent_already_processed",
                    session_id=session_id,
                    session_status=session.status.value,
                )
                # Send current session status to frontend so it can close connection
                if session.status == SessionStatus.COMPLETED:
                    yield format_sse(SSEEventType.SESSION_COMPLETED.value, {
                        "session_id": session_id,
                        "status": "completed",
                        "timestamp": time.time(),
                    })
                elif session.status == SessionStatus.FAILED:
                    yield format_sse(SSEEventType.SESSION_FAILED.value, {
                        "session_id": session_id,
                        "status": "failed",
                        "timestamp": time.time(),
                    })
                elif session.status == SessionStatus.CANCELLED:
                    yield format_sse(SSEEventType.SESSION_COMPLETED.value, {
                        "session_id": session_id,
                        "status": "cancelled",
                        "timestamp": time.time(),
                    })
                # For RUNNING status, don't send anything - let the original stream continue
            else:
                # Use mock stream for demo
                stream = mock_agent_execution_stream(session_id)
                async for event in keepalive_generator(stream):
                    if await request.is_disconnected():
                        logger.info("sse_client_disconnected", session_id=session_id)
                        break
                    yield event

        except asyncio.CancelledError:
            logger.info("sse_stream_cancelled", session_id=session_id)
            # P0-1: Cancel session on stream cancellation
            await session_service.cancel_session(session_id)
        except Exception as e:
            logger.error("sse_stream_error", session_id=session_id, error=str(e))
            yield format_sse(SSEEventType.ERROR, {"message": str(e)})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


async def run_agent_stream(
    session_id: str,
    task: str,
    workspace_id: str,
    user_id: str,
    db: AsyncSession,
    settings: Settings,
) -> AsyncGenerator[str, None]:
    """
    Run Agent and stream events.

    P0 fixes applied:
    - P0-1: Update session status (RUNNING -> COMPLETED/FAILED)
    - P0-2: Use persistent workspace path instead of temp directory
    - P0-3: Save messages to database
    - P0-4: Permission check done in caller (stream_session_events)
    """
    import os


    session_service = SessionService(db)
    message_repo = MessageRepository(db)
    total_tokens = 0

    # P0-1: Mark session as RUNNING
    await session_service.start_session(session_id)

    # Send session started
    yield format_sse(SSEEventType.SESSION_STARTED, {
        "session_id": session_id,
        "task": task,
        "timestamp": time.time(),
    })

    # P2: Send skill matched event so frontend knows the task type
    yield format_sse(SSEEventType.SKILL_MATCHED, {
        "skill_id": "deep_research",
        "skill_name": "deep_research",
        "display_name": "深度研究",
        "description": "深度研究技能，用于复杂信息检索和分析",
        "icon": "search",
        "color": "#00D9FF",
        "confidence": 1.0,
        "timestamp": time.time(),
    })

    try:
        # P0-2: Use persistent workspace path instead of temp directory
        workspace_path = os.path.join(
            settings.SESSIONS_DATA_PATH,
            workspace_id,
            session_id
        )
        os.makedirs(workspace_path, exist_ok=True)

        # P0-3: Save user message to database
        await message_repo.create_user_message(
            session_id=session_id,
            content=task,
        )

        # Initialize Working Memory with persistent path
        memory = await create_working_memory(
            workspace_path=workspace_path,
            session_id=session_id,
            initial_task=task
        )

        # Create Agent Context
        context = AgentContext(
            session_id=session_id,
            user_id=user_id,
            workspace_id=workspace_id
        )

        # Create Tool Registry and register built-in tools
        tools = ToolRegistry()
        register_builtin_tools(tools)

        # 使用智能路由选择免费 LLM
        llm = get_free_llm_for_task(
            task_type=TaskType.GENERAL,
            max_tokens=4096
        )

        # Create Agent (using DeepResearchAgent for Timeline events)
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

        # Run Agent and stream events
        async for event in agent.run(task):
            # Convert agent event to SSE format
            yield format_sse(event.type.value, event.data)

            # P0-3: Collect response data for message saving
            event_type = event.type.value if hasattr(event.type, 'value') else str(event.type)

            if event_type == 'thinking':
                assistant_thinking = event.data.get('content', '')
            elif event_type == 'content':
                assistant_content_parts.append(event.data.get('content', ''))
            elif event_type == 'tool_call':
                assistant_tool_calls.append({
                    'id': event.data.get('id'),
                    'name': event.data.get('name'),
                    'args': event.data.get('args'),
                    'status': event.data.get('status'),
                })
            elif event_type == 'tool_result':
                # Update tool call status
                tool_id = event.data.get('id')
                for tc in assistant_tool_calls:
                    if tc.get('id') == tool_id:
                        tc['status'] = 'success' if event.data.get('success') else 'error'
                        tc['result'] = event.data.get('result')
                        break
            elif event_type == 'done':
                total_tokens = event.data.get('tokens_used', 0)

        # P0-3: Save assistant message to database
        assistant_content = ''.join(assistant_content_parts)
        if assistant_content or assistant_tool_calls:
            await message_repo.create_assistant_message(
                session_id=session_id,
                content=assistant_content if assistant_content else None,
                thinking=assistant_thinking,
                tool_calls=assistant_tool_calls if assistant_tool_calls else None,
                tokens_used=total_tokens,
            )

        # P0-1: Mark session as COMPLETED with token count
        await session_service.complete_session(
            session_id,
            total_tokens_used=total_tokens,
        )

        # Session completed
        yield format_sse(SSEEventType.SESSION_COMPLETED, {
            "session_id": session_id,
            "status": "completed",
            "total_tokens": total_tokens,
            "timestamp": time.time(),
        })

    except Exception as e:
        logger.error(f"Agent execution error: {e}", exc_info=True)

        # P0-1: Mark session as FAILED
        await session_service.fail_session(
            session_id,
            error_message=str(e),
        )

        yield format_sse(SSEEventType.SESSION_FAILED, {
            "session_id": session_id,
            "error": str(e),
            "timestamp": time.time(),
        })


async def run_agent_stream_with_store(
    session_id: str,
    task: str,
    workspace_id: str,
    user_id: str,
    db: AsyncSession,
    redis: Redis,
    settings: Settings,
    event_store: SSEEventStore,
) -> AsyncGenerator[str, None]:
    """
    Run Agent and stream events with P1 enhancements:
    - P1-2: Check stop signal periodically
    - P1-3: Store events for replay
    - P1-4: Atomic session status updates
    """
    import os


    session_service = SessionService(db)
    message_repo = MessageRepository(db)
    stop_service = get_agent_stop_service(redis)
    total_tokens = 0

    async def emit_event(event_type: str, data: dict) -> str:
        """Emit event, store it, and return formatted SSE."""
        seq = await event_store.store_event(session_id, event_type, data)
        return format_sse(event_type, data, seq=seq)

    # P0-1: Mark session as RUNNING
    await session_service.start_session(session_id)

    # Send session started
    yield await emit_event(SSEEventType.SESSION_STARTED, {
        "session_id": session_id,
        "task": task,
        "timestamp": time.time(),
    })

    # P2: Send skill matched event so frontend knows the task type
    # Currently all tasks use DeepResearchAgent
    yield await emit_event(SSEEventType.SKILL_MATCHED, {
        "skill_id": "deep_research",
        "skill_name": "deep_research",
        "display_name": "深度研究",
        "description": "深度研究技能，用于复杂信息检索和分析",
        "icon": "search",
        "color": "#00D9FF",
        "confidence": 1.0,
        "timestamp": time.time(),
    })

    try:
        # P0-2: Use persistent workspace path
        workspace_path = os.path.join(
            settings.SESSIONS_DATA_PATH,
            workspace_id,
            session_id
        )
        os.makedirs(workspace_path, exist_ok=True)

        # P0-3: Save user message to database
        await message_repo.create_user_message(
            session_id=session_id,
            content=task,
        )

        # Initialize Working Memory
        memory = await create_working_memory(
            workspace_path=workspace_path,
            session_id=session_id,
            initial_task=task
        )

        # Create Agent Context
        context = AgentContext(
            session_id=session_id,
            user_id=user_id,
            workspace_id=workspace_id
        )

        # Create Tool Registry and register built-in tools
        tools = ToolRegistry()
        register_builtin_tools(tools)

        # Get LLM
        llm = get_free_llm_for_task(
            task_type=TaskType.GENERAL,
            max_tokens=4096
        )

        # Create Agent (using DeepResearchAgent for Timeline events)
        agent = DeepResearchAgent(
            context=context,
            llm=llm,
            tools=tools,
            memory=memory,
            db=db,
            max_iterations=50
        )

        # Manus 无限记忆模式: 检查并从检查点恢复
        try:
            checkpoint_fs = AgentFileSystem(workspace_path)
            checkpoint_manager = CheckpointManager(
                fs=checkpoint_fs,
                save_interval=5,
                max_checkpoints=3,
            )
            # 检查是否有检查点可以恢复
            if checkpoint_manager.can_rollback():
                checkpoint = checkpoint_manager.get_latest_checkpoint()
                if checkpoint:
                    # 构建 checkpoint_data 字典
                    checkpoint_data = {
                        "iteration": checkpoint.metadata.iteration,
                        "task_plan": checkpoint.task_plan,
                        "findings": checkpoint.findings,
                        "progress": checkpoint.progress,
                    }
                    # 恢复 Agent 状态
                    restored = await agent.restore_from_checkpoint(checkpoint_data)
                    if restored:
                        logger.info(
                            "agent_restored_from_checkpoint",
                            session_id=session_id,
                            checkpoint_iteration=checkpoint.metadata.iteration,
                        )
                        yield await emit_event(SSEEventType.PROGRESS_UPDATE, {
                            "message": "Resuming from checkpoint...",
                            "iteration": checkpoint.metadata.iteration,
                            "timestamp": time.time(),
                        })
        except Exception as cp_err:
            logger.warning(f"Failed to restore from checkpoint: {cp_err}")
            # 继续正常执行，不抛异常

        # Collect assistant response
        assistant_content_parts = []
        assistant_thinking = None
        assistant_tool_calls = []
        iteration_count = 0
        has_fatal_error = False
        fatal_error_message = None

        # Run Agent and stream events
        async for event in agent.run(task):
            # P1-2: Check stop signal periodically (every 5 iterations)
            iteration_count += 1
            if iteration_count % 5 == 0:
                if await stop_service.should_stop(session_id):
                    logger.info(
                        "agent_stop_signal_received",
                        session_id=session_id,
                        iteration=iteration_count,
                    )
                    # Clear stop signal
                    await stop_service.clear_stop_signal(session_id)
                    # Set agent stopped flag
                    agent.stopped = True

                    # P2: Save artifacts before cancelling (to preserve research progress)
                    artifact_repo = ArtifactRepository(db)
                    storage = get_object_storage()
                    try:
                        findings_content = await memory.read_findings()
                        if findings_content and len(findings_content.strip()) > 100:
                            artifact_name = f"Research Report (Cancelled) - {task[:50]}" if len(task) > 50 else f"Research Report (Cancelled) - {task}"

                            if storage:
                                object_key = f"sessions/{session_id}/findings.md"
                                try:
                                    storage.ensure_bucket("tokendance-artifacts")
                                    storage.put_text("tokendance-artifacts", object_key, findings_content, "text/markdown; charset=utf-8")
                                    file_path = f"minio://tokendance-artifacts/{object_key}"
                                except Exception:
                                    file_path = f"local://{workspace_path}/findings.md"
                            else:
                                file_path = f"local://{workspace_path}/findings.md"

                            artifact = await artifact_repo.create(
                                session_id=session_id,
                                name=artifact_name,
                                artifact_type=ArtifactType.REPORT,
                                file_path=file_path,
                                file_size=len(findings_content.encode('utf-8')),
                                mime_type="text/markdown",
                                description=f"Partial research findings (cancelled): {task[:100]}",
                                extra_data={"task": task, "source": "deep_research_agent", "cancelled": True},
                            )
                            artifact.set_content_preview(findings_content, max_length=500)
                            await db.commit()

                            yield await emit_event(SSEEventType.ARTIFACT_CREATED, {
                                "artifact_id": artifact.id,
                                "name": artifact.name,
                                "type": artifact.artifact_type.value,
                                "file_path": artifact.file_path,
                                "file_size": artifact.file_size,
                                "preview": artifact.content_preview,
                                "download_url": f"/api/v1/artifacts/{artifact.id}/download",
                                "timestamp": time.time(),
                            })
                    except Exception as artifact_err:
                        logger.error(f"Failed to save artifact on cancel: {artifact_err}")

                    # Emit cancellation event
                    yield await emit_event(SSEEventType.SESSION_COMPLETED, {
                        "session_id": session_id,
                        "status": "cancelled",
                        "reason": "User requested stop",
                        "timestamp": time.time(),
                    })
                    # P1-4: Atomic update - cancel session
                    await session_service.cancel_session(session_id)
                    return

            # P1-3: Store event and emit
            event_type = event.type.value if hasattr(event.type, 'value') else str(event.type)
            yield await emit_event(event_type, event.data)

            # Collect response data for message saving
            if event_type == 'thinking':
                assistant_thinking = event.data.get('content', '')
            elif event_type == 'content':
                assistant_content_parts.append(event.data.get('content', ''))
            elif event_type == 'tool_call':
                assistant_tool_calls.append({
                    'id': event.data.get('id'),
                    'name': event.data.get('name'),
                    'args': event.data.get('args'),
                    'status': event.data.get('status'),
                })
            elif event_type == 'tool_result':
                tool_id = event.data.get('id')
                for tc in assistant_tool_calls:
                    if tc.get('id') == tool_id:
                        tc['status'] = 'success' if event.data.get('success') else 'error'
                        tc['result'] = event.data.get('result')
                        break
            elif event_type == 'done':
                total_tokens = event.data.get('tokens_used', 0)
            elif event_type == 'error':
                # Check if this is a fatal error
                if event.data.get('fatal', False):
                    has_fatal_error = True
                    fatal_error_message = event.data.get('message', 'Unknown error')
                    logger.warning(
                        "agent_fatal_error_detected",
                        session_id=session_id,
                        error=fatal_error_message,
                    )

        # P0-3: Save assistant message
        assistant_content = ''.join(assistant_content_parts)
        if assistant_content or assistant_tool_calls:
            await message_repo.create_assistant_message(
                session_id=session_id,
                content=assistant_content if assistant_content else None,
                thinking=assistant_thinking,
                tool_calls=assistant_tool_calls if assistant_tool_calls else None,
                tokens_used=total_tokens,
            )

        # P2: Save artifacts to MinIO and create artifact records
        artifact_repo = ArtifactRepository(db)
        storage = get_object_storage()

        # Read findings.md as the research report
        try:
            findings_content = await memory.read_findings()
            # WorkingMemory.read_findings() returns str, not dict

            if findings_content and len(findings_content.strip()) > 100:  # Only save if has meaningful content
                # Generate artifact name from task
                artifact_name = f"Research Report - {task[:50]}" if len(task) > 50 else f"Research Report - {task}"

                # Upload to MinIO if configured
                if storage:
                    object_key = f"sessions/{session_id}/findings.md"
                    try:
                        storage.ensure_bucket("tokendance-artifacts")
                        storage.put_text("tokendance-artifacts", object_key, findings_content, "text/markdown; charset=utf-8")
                        file_path = f"minio://tokendance-artifacts/{object_key}"
                        logger.info(f"Uploaded artifact to MinIO: {object_key}")
                    except Exception as minio_err:
                        logger.warning(f"MinIO upload failed, using local path: {minio_err}")
                        file_path = f"local://{workspace_path}/findings.md"
                else:
                    # Use local file path if MinIO not configured
                    file_path = f"local://{workspace_path}/findings.md"

                # Create artifact record in database
                artifact = await artifact_repo.create(
                    session_id=session_id,
                    name=artifact_name,
                    artifact_type=ArtifactType.REPORT,
                    file_path=file_path,
                    file_size=len(findings_content.encode('utf-8')),
                    mime_type="text/markdown",
                    description=f"Deep research findings for: {task[:100]}",
                    extra_data={
                        "task": task,
                        "tokens_used": total_tokens,
                        "source": "deep_research_agent",
                    },
                )

                # Set content preview
                artifact.set_content_preview(findings_content, max_length=500)
                await db.commit()

                # Emit artifact created event
                yield await emit_event(SSEEventType.ARTIFACT_CREATED, {
                    "artifact_id": artifact.id,
                    "name": artifact.name,
                    "type": artifact.artifact_type.value,
                    "file_path": artifact.file_path,
                    "file_size": artifact.file_size,
                    "preview": artifact.content_preview,
                    "download_url": f"/api/v1/artifacts/{artifact.id}/download",
                    "timestamp": time.time(),
                })

                logger.info(
                    "artifact_created",
                    artifact_id=artifact.id,
                    session_id=session_id,
                    type=artifact.artifact_type.value,
                )
        except Exception as artifact_err:
            logger.error(f"Failed to save artifact: {artifact_err}", exc_info=True)
            # Don't fail the session for artifact errors

        # P1-4: Atomic update - set session status based on outcome
        if has_fatal_error:
            # Mark session as FAILED if there was a fatal error
            await session_service.fail_session(
                session_id,
                error_message=fatal_error_message,
            )
            # Note: Artifact was already saved above (lines 1061-1129)
            # Even failed sessions should have their partial findings preserved
            yield await emit_event(SSEEventType.SESSION_FAILED, {
                "session_id": session_id,
                "status": "failed",
                "error": fatal_error_message,
                "timestamp": time.time(),
            })
        else:
            # Mark session as COMPLETED
            await session_service.complete_session(
                session_id,
                total_tokens_used=total_tokens,
            )
            yield await emit_event(SSEEventType.SESSION_COMPLETED, {
                "session_id": session_id,
                "status": "completed",
                "total_tokens": total_tokens,
                "timestamp": time.time(),
            })

    except Exception as e:
        logger.error(f"Agent execution error: {e}", exc_info=True)

        # P2: Try to save any partial findings before failing
        try:
            if memory:  # memory might not be initialized if error occurred early
                artifact_repo = ArtifactRepository(db)
                storage = get_object_storage()
                findings_content = await memory.read_findings()
                if findings_content and len(findings_content.strip()) > 100:
                    artifact_name = f"Research Report (Error) - {task[:50]}" if len(task) > 50 else f"Research Report (Error) - {task}"
                    if storage:
                        object_key = f"sessions/{session_id}/findings.md"
                        try:
                            storage.ensure_bucket("tokendance-artifacts")
                            storage.put_text("tokendance-artifacts", object_key, findings_content, "text/markdown; charset=utf-8")
                            file_path = f"minio://tokendance-artifacts/{object_key}"
                        except Exception:
                            file_path = f"local://{workspace_path}/findings.md"
                    else:
                        file_path = f"local://{workspace_path}/findings.md"

                    artifact = await artifact_repo.create(
                        session_id=session_id,
                        name=artifact_name,
                        artifact_type=ArtifactType.REPORT,
                        file_path=file_path,
                        file_size=len(findings_content.encode('utf-8')),
                        mime_type="text/markdown",
                        description=f"Partial research findings (error): {task[:100]}",
                        extra_data={"task": task, "source": "deep_research_agent", "error": str(e)},
                    )
                    artifact.set_content_preview(findings_content, max_length=500)
                    await db.commit()

                    yield await emit_event(SSEEventType.ARTIFACT_CREATED, {
                        "artifact_id": artifact.id,
                        "name": artifact.name,
                        "type": artifact.artifact_type.value,
                        "file_path": artifact.file_path,
                        "file_size": artifact.file_size,
                        "preview": artifact.content_preview,
                        "download_url": f"/api/v1/artifacts/{artifact.id}/download",
                        "timestamp": time.time(),
                    })
        except Exception as artifact_err:
            logger.error(f"Failed to save artifact on error: {artifact_err}")

        # P1-4: Atomic update - fail session with error
        await session_service.fail_session(
            session_id,
            error_message=str(e),
        )

        yield await emit_event(SSEEventType.SESSION_FAILED, {
            "session_id": session_id,
            "error": str(e),
            "timestamp": time.time(),
        })


@router.post("/{session_id}/events")
async def publish_event(
    session_id: str,
    event_type: SSEEventType,
    data: dict,
    db: AsyncSession = Depends(get_db),
):
    """
    Publish an event to a session's stream.

    This is used internally by the Agent Engine to emit events.
    In production, this would publish to Redis pub/sub.
    """
    # TODO: Implement Redis pub/sub publishing

    logger.info(
        "sse_event_published",
        session_id=session_id,
        event_type=event_type,
        data=data,
    )

    return {"status": "published", "event_type": event_type}
