"""
Conversation API - 多轮对话 API

提供完整的多轮对话功能:
1. 创建对话
2. 发送消息 (核心)
3. 获取对话详情
4. 流式获取 Turn 事件
5. 列出对话
6. 归档对话
"""
import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.redis import get_redis
from app.models.conversation import ConversationPurpose, ConversationStatus
from app.models.turn import TurnStatus
from app.models.user import User
from app.services.conversation_service import ConversationService
from app.services.sse_event_store import SSEEventStore

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/conversations", tags=["conversations"])


# ==================== Request/Response Models ====================

class CreateConversationRequest(BaseModel):
    """创建对话请求"""
    project_id: str = Field(..., description="项目 ID")
    title: str | None = Field(None, description="对话标题 (可选,不提供则使用默认值)")
    purpose: ConversationPurpose = Field(ConversationPurpose.GENERAL, description="对话目的")
    initial_message: str | None = Field(None, description="初始消息 (可选)")


class SendMessageRequest(BaseModel):
    """发送消息请求"""
    content: str = Field(..., min_length=1, max_length=10000, description="消息内容")
    parent_message_id: str | None = Field(None, description="父消息 ID (用于分支对话)")


class ConversationResponse(BaseModel):
    """对话响应"""
    id: str
    project_id: str
    title: str
    status: str
    purpose: str
    turn_count: int
    message_count: int
    created_at: str
    last_message_at: str | None


class TurnResponse(BaseModel):
    """Turn 响应"""
    turn_id: str
    session_id: str | None
    turn_number: int
    status: str
    stream_url: str


class TurnDetail(BaseModel):
    """Turn 详情"""
    id: str
    conversation_id: str
    turn_number: int
    status: str
    user_input: str
    assistant_response: str | None
    tokens_used: int
    duration_ms: int | None
    created_at: str
    completed_at: str | None


class ConversationDetail(BaseModel):
    """对话详情"""
    id: str
    project_id: str
    title: str
    status: str
    purpose: str
    turn_count: int
    message_count: int
    total_tokens_used: int
    turns: list[TurnDetail]
    shared_memory: dict | None
    context_summary: str | None
    created_at: str
    last_message_at: str | None


# ==================== API Endpoints ====================

@router.post("/", response_model=ConversationResponse)
async def create_conversation(
    request: CreateConversationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """
    创建新对话

    如果提供了 initial_message,会自动创建首个 Turn 并启动 Agent 执行。

    Returns:
        ConversationResponse: 对话基本信息
    """
    try:
        service = ConversationService(db)

        # 创建对话
        conversation, turn = await service.create_conversation(
            project_id=request.project_id,
            title=request.title,
            purpose=request.purpose,
            initial_message=request.initial_message,
        )

        # 如果有初始消息,通知 Agent Worker 开始执行
        if turn:
            await _notify_agent_worker(redis, conversation.id, turn.id, request.initial_message)

        return ConversationResponse(
            id=conversation.id,
            project_id=conversation.project_id,
            title=conversation.title,
            status=conversation.status.value,
            purpose=conversation.purpose.value,
            turn_count=conversation.turn_count,
            message_count=conversation.message_count_db,
            created_at=conversation.created_at.isoformat(),
            last_message_at=conversation.last_message_at.isoformat() if conversation.last_message_at else None,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Failed to create conversation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create conversation") from e


@router.post("/{conversation_id}/messages", response_model=TurnResponse)
async def send_message(
    conversation_id: str,
    request: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """
    向对话发送新消息 (核心 API)

    这是多轮对话的核心接口:
    1. 创建新的 Turn
    2. 保存 User Message
    3. 通知 Agent Worker 开始执行
    4. 返回 Turn 信息和 SSE stream URL

    Returns:
        TurnResponse: Turn 信息和流式 URL
    """
    try:
        service = ConversationService(db)

        # 发送消息,创建 Turn
        turn = await service.send_message(
            conversation_id=conversation_id,
            content=request.content,
            parent_message_id=request.parent_message_id,
        )

        # 通知 Agent Worker 开始执行
        await _notify_agent_worker(redis, conversation_id, turn.id, request.content)

        # 构造 stream URL
        stream_url = f"/api/v1/conversations/{conversation_id}/turns/{turn.id}/stream"

        return TurnResponse(
            turn_id=turn.id,
            session_id=turn.primary_session_id,
            turn_number=turn.turn_number,
            status=turn.status.value,
            stream_url=stream_url,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Failed to send message: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to send message") from e


@router.get("/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取对话详情

    包括:
    - 对话基本信息
    - 所有 Turns
    - shared_memory
    - context_summary

    Returns:
        ConversationDetail: 完整的对话信息
    """
    try:
        service = ConversationService(db)

        # 获取对话 (包含 turns)
        conversation = await service.get_conversation(
            conversation_id=conversation_id,
            include_turns=True,
        )

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # 构造 turns 详情
        turns = [
            TurnDetail(
                id=turn.id,
                conversation_id=turn.conversation_id,
                turn_number=turn.turn_number,
                status=turn.status.value,
                user_input=turn.user_input,
                assistant_response=turn.assistant_response,
                tokens_used=turn.tokens_used,
                duration_ms=turn.duration_ms,
                created_at=turn.created_at.isoformat(),
                completed_at=turn.completed_at.isoformat() if turn.completed_at else None,
            )
            for turn in conversation.turns
        ]

        return ConversationDetail(
            id=conversation.id,
            project_id=conversation.project_id,
            title=conversation.title,
            status=conversation.status.value,
            purpose=conversation.purpose.value,
            turn_count=conversation.turn_count,
            message_count=conversation.message_count_db,
            total_tokens_used=conversation.tokens_used,
            turns=turns,
            shared_memory=conversation.shared_memory,
            context_summary=conversation.context_summary,
            created_at=conversation.created_at.isoformat(),
            last_message_at=conversation.last_message_at.isoformat() if conversation.last_message_at else None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conversation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get conversation") from e


@router.get("/", response_model=list[ConversationResponse])
async def list_conversations(
    project_id: str = Query(..., description="项目 ID"),
    status: ConversationStatus | None = Query(None, description="状态筛选"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    列出对话列表

    支持:
    - 按项目筛选
    - 按状态筛选
    - 分页

    Returns:
        List[ConversationResponse]: 对话列表
    """
    try:
        service = ConversationService(db)

        conversations = await service.list_conversations(
            project_id=project_id,
            status=status,
            limit=limit,
            offset=offset,
        )

        return [
            ConversationResponse(
                id=conv.id,
                project_id=conv.project_id,
                title=conv.title,
                status=conv.status.value,
                purpose=conv.purpose.value,
                turn_count=conv.turn_count,
                message_count=conv.message_count_db,
                created_at=conv.created_at.isoformat(),
                last_message_at=conv.last_message_at.isoformat() if conv.last_message_at else None,
            )
            for conv in conversations
        ]

    except Exception as e:
        logger.error(f"Failed to list conversations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list conversations") from e


@router.post("/{conversation_id}/archive")
async def archive_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    归档对话

    归档后的对话变为只读,不能再发送新消息。

    Returns:
        dict: 操作结果
    """
    try:
        service = ConversationService(db)
        await service.archive_conversation(conversation_id)

        return {"status": "archived", "conversation_id": conversation_id}

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Failed to archive conversation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to archive conversation") from e


@router.get("/{conversation_id}/turns/{turn_id}/stream")
async def stream_turn_events(
    conversation_id: str,
    turn_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """
    流式获取 Turn 执行事件 (SSE)

    这是多轮对话的核心流式接口:
    1. 验证 Turn 存在且属于该 Conversation
    2. 从 SSEEventStore 读取事件流
    3. 实时推送 Agent 执行事件

    Event Types:
    - thinking: Agent 思考过程
    - tool_call: 工具调用
    - tool_result: 工具结果
    - content: 响应内容
    - done: 执行完成
    - error: 执行错误

    Returns:
        StreamingResponse: SSE 事件流
    """
    try:
        # 验证 Turn 存在
        from app.models.turn import Turn
        turn = await db.get(Turn, turn_id)

        if not turn:
            raise HTTPException(status_code=404, detail="Turn not found")

        if turn.conversation_id != conversation_id:
            raise HTTPException(status_code=400, detail="Turn does not belong to this conversation")

        # 获取 SSEEventStore
        event_store = SSEEventStore(redis)

        # 创建 SSE 流
        async def event_generator():
            """生成 SSE 事件流"""
            try:
                # 发送初始连接事件
                yield f"event: connected\ndata: {json.dumps({'turn_id': turn_id, 'status': turn.status.value})}\n\n"

                # 如果 Turn 已完成,先发送历史事件
                if turn.status in (TurnStatus.COMPLETED, TurnStatus.FAILED, TurnStatus.CANCELLED):
                    events = await event_store.get_events(turn_id)
                    for event in events:
                        yield f"event: {event['type']}\ndata: {json.dumps(event['data'])}\n\n"

                    # 发送完成事件
                    yield f"event: done\ndata: {json.dumps({'status': turn.status.value})}\n\n"
                    return

                # 实时流式推送事件
                async for event in event_store.stream_events(turn_id, timeout=300):
                    yield f"event: {event['type']}\ndata: {json.dumps(event['data'])}\n\n"

                    # 如果收到 done 或 error 事件,结束流
                    if event['type'] in ('done', 'error'):
                        break

            except Exception as e:
                logger.error(f"Error streaming turn events: {e}", exc_info=True)
                error_data = {"error": str(e), "turn_id": turn_id}
                yield f"event: error\ndata: {json.dumps(error_data)}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Disable nginx buffering
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to stream turn events: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to stream turn events") from e


# ==================== Helper Functions ====================

async def _notify_agent_worker(
    redis: Redis,
    conversation_id: str,
    turn_id: str,
    user_input: str,
):
    """
    通知 Agent Worker 开始执行

    通过 Redis pub/sub 发送执行任务
    """
    message = {
        "conversation_id": conversation_id,
        "turn_id": turn_id,
        "user_input": user_input,
    }

    await redis.publish("agent:execute", json.dumps(message))

    logger.info(
        "agent_worker_notified",
        conversation_id=conversation_id,
        turn_id=turn_id,
    )
