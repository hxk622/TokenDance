"""
SSE (Server-Sent Events) Stream API

Provides real-time streaming of Agent execution events.
"""
import asyncio
import json
import time
from typing import AsyncGenerator, Optional
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import get_logger
from app.services.session_service import SessionService

logger = get_logger(__name__)
router = APIRouter()


class SSEEventType(str, Enum):
    """SSE Event Types"""
    # Agent events
    AGENT_THINKING = "agent_thinking"
    AGENT_TOOL_CALL = "agent_tool_call"
    AGENT_TOOL_RESULT = "agent_tool_result"
    AGENT_MESSAGE = "agent_message"
    AGENT_ERROR = "agent_error"
    
    # Session events
    SESSION_STARTED = "session_started"
    SESSION_COMPLETED = "session_completed"
    SESSION_FAILED = "session_failed"
    
    # Workflow events
    NODE_STARTED = "node_started"
    NODE_COMPLETED = "node_completed"
    NODE_FAILED = "node_failed"
    
    # File events
    FILE_CREATED = "file_created"
    FILE_MODIFIED = "file_modified"
    FILE_DELETED = "file_deleted"
    
    # Keepalive
    PING = "ping"


def format_sse(event: str, data: dict) -> str:
    """Format data as SSE message"""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


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
                "arguments": {"query": f"AI Agent market analysis"} if node["id"] == "1" else {"data_source": "search_results"},
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


@router.get("/{session_id}/stream")
async def stream_session_events(
    session_id: str,
    request: Request,
    token: Optional[str] = Query(None, description="Auth token"),
    db: AsyncSession = Depends(get_db),
):
    """
    Stream SSE events for a session.
    
    Events include:
    - agent_thinking: Agent's reasoning process
    - agent_tool_call: Tool invocation
    - agent_tool_result: Tool execution result
    - agent_message: Final message
    - node_started/completed/failed: Workflow node status
    - file_created/modified/deleted: Coworker file operations
    - session_started/completed/failed: Session lifecycle
    - ping: Keepalive
    
    Usage:
        const eventSource = new EventSource(`/api/v1/sessions/${sessionId}/stream?token=${token}`);
        eventSource.addEventListener('agent_thinking', (e) => console.log(JSON.parse(e.data)));
    """
    # TODO: Verify token authentication
    
    # Verify session exists
    session_service = SessionService(db)
    session = await session_service.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    logger.info(
        "sse_stream_started",
        session_id=session_id,
        client_ip=request.client.host if request.client else "unknown",
    )
    
    async def event_generator():
        try:
            # Use mock stream for now
            # In production, this would subscribe to Redis pub/sub
            stream = mock_agent_execution_stream(session_id)
            
            async for event in keepalive_generator(stream):
                # Check if client disconnected
                if await request.is_disconnected():
                    logger.info("sse_client_disconnected", session_id=session_id)
                    break
                    
                yield event
                
        except asyncio.CancelledError:
            logger.info("sse_stream_cancelled", session_id=session_id)
        except Exception as e:
            logger.error("sse_stream_error", session_id=session_id, error=str(e))
            yield format_sse("error", {"message": str(e)})
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


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
