"""
Messages API - 发送消息并触发 Agent 执行

集成 Agent Engine，支持 SSE 流式输出
"""

import json
import uuid
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.engine import AgentEngine
from app.agent.llm.router import TaskType, get_free_llm_for_task
from app.agent.types import ExecutionMode
from app.core.config import settings
from app.core.database import get_db
from app.core.logging import get_logger
from app.filesystem import AgentFileSystem
from app.models.message import FeedbackType
from app.repositories.message_repository import MessageRepository
from app.schemas.message import FeedbackRequest, FeedbackResponse
from app.services.session_service import SessionService

logger = get_logger(__name__)

router = APIRouter()


# ========== Schemas ==========

class MessageRequest(BaseModel):
    """发送消息请求"""
    content: str
    stream: bool = True  # 是否流式输出
    mode: str = "auto"   # 执行模式: auto/direct/planning


class MessageResponse(BaseModel):
    """消息响应"""
    message_id: str
    session_id: str
    role: str
    content: str
    reasoning: str | None = None
    token_usage: dict | None = None
    iterations: int = 0


# ========== Dependencies ==========

def get_session_service(db: AsyncSession = Depends(get_db)) -> SessionService:
    """获取 SessionService"""
    return SessionService(db)


def get_agent_engine(session_id: str, workspace_id: str, task_type: TaskType = TaskType.GENERAL) -> AgentEngine:
    """
    创建 Agent Engine 实例

    使用智能路由系统自动选择最优模型：
    - 优先使用免费模型 (DeepSeek, Gemini, Llama 等)
    - 根据任务类型选择合适的模型
    - 自动 fallback 到可用模型

    Args:
        session_id: Session ID
        workspace_id: Workspace ID
        task_type: 任务类型 (用于智能路由)

    Returns:
        AgentEngine: Agent 引擎实例
    """
    # 使用智能路由获取免费 LLM
    # 路由器会根据任务类型自动选择最优的免费模型
    # 包括 DeepSeek, Gemini, Llama, Mistral 等
    llm = get_free_llm_for_task(
        task_type=task_type,
        max_tokens=4096
    )

    # 初始化 FileSystem
    workspace_root = getattr(settings, 'WORKSPACE_ROOT_PATH', '/tmp/tokendance/workspaces')
    filesystem = AgentFileSystem(
        workspace_id=workspace_id,
        base_dir=workspace_root
    )

    # 创建 Agent Engine
    agent = AgentEngine(
        llm=llm,
        filesystem=filesystem,
        workspace_id=workspace_id,
        session_id=session_id,
        max_iterations=20
    )

    return agent


# ========== API Endpoints ==========

@router.post("/{session_id}/messages")
async def send_message(
    session_id: str,
    request: MessageRequest,
    service: SessionService = Depends(get_session_service),
):
    """
    发送消息给 Agent

    支持两种模式：
    1. stream=true: SSE 流式输出（实时显示思考过程）
    2. stream=false: 一次性返回完整结果
    """
    # 验证 session 存在
    session = await service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )

    # 获取 Agent Engine
    try:
        agent = get_agent_engine(session_id, str(session.workspace_id))
    except Exception as e:
        logger.error(f"Failed to create Agent Engine: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize Agent: {str(e)}"
        ) from e

    # 流式模式 - 使用新的统一入口 execute()
    if request.stream:
        # 解析执行模式
        mode_map = {
            "auto": ExecutionMode.AUTO,
            "direct": ExecutionMode.DIRECT,
            "planning": ExecutionMode.PLANNING,
        }
        exec_mode = mode_map.get(request.mode.lower(), ExecutionMode.AUTO)

        return StreamingResponse(
            stream_agent_execute(agent, request.content, session_id, exec_mode),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            }
        )

    # 非流式模式
    try:
        response = await agent.run(request.content)

        # 保存消息到数据库
        message_id = str(uuid.uuid4())

        # TODO: 保存到数据库
        # await service.save_message(session_id, message_id, request.content, response.answer)

        return MessageResponse(
            message_id=message_id,
            session_id=session_id,
            role="assistant",
            content=response.answer,
            reasoning=response.reasoning,
            token_usage=response.token_usage,
            iterations=response.iterations
        )

    except Exception as e:
        logger.error(f"Agent execution failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent execution failed: {str(e)}"
        ) from e


async def stream_agent_response(
    agent: AgentEngine,
    user_message: str,
    session_id: str
) -> AsyncGenerator[str, None]:
    """
    流式输出 Agent 响应

    SSE 事件类型：
    - reasoning: 推理过程
    - tool_call: 工具调用
    - tool_result: 工具结果
    - answer: 最终答案
    - error: 错误
    - done: 完成
    """
    try:
        # 发送开始事件
        yield format_sse("start", {
            "session_id": session_id,
            "message": "Agent started processing..."
        })

        # 添加用户消息
        agent.context_manager.add_user_message(user_message)

        # Agent 主循环
        iteration = 0
        max_iterations = agent.max_iterations

        while iteration < max_iterations:
            iteration += 1

            # 发送迭代事件
            yield format_sse("iteration", {
                "iteration": iteration,
                "max_iterations": max_iterations
            })

            # 调用 LLM
            llm_response = await agent._call_llm()

            # 添加到 context
            agent.context_manager.add_assistant_message(
                content=llm_response.content,
                metadata={"usage": llm_response.usage}
            )

            # 更新 token 使用
            if llm_response.usage:
                agent.context_manager.update_token_usage(
                    input_tokens=llm_response.usage.get("input_tokens", 0),
                    output_tokens=llm_response.usage.get("output_tokens", 0)
                )

            # 提取推理过程
            reasoning = agent.executor.extract_reasoning(llm_response.content)
            if reasoning:
                yield format_sse("reasoning", {
                    "content": reasoning,
                    "iteration": iteration
                })

            # 检查是否有最终答案
            if agent.executor.has_final_answer(llm_response.content):
                answer = agent.executor.extract_answer(llm_response.content)

                yield format_sse("answer", {
                    "content": answer or llm_response.content,
                    "iteration": iteration,
                    "token_usage": agent.context_manager.get_token_usage()
                })

                yield format_sse("done", {
                    "iterations": iteration,
                    "token_usage": agent.context_manager.get_token_usage()
                })

                break

            # 检查是否有工具调用
            if agent.executor.has_tool_calls(llm_response.content):
                # 解析工具调用
                tool_calls = agent.executor.parse_tool_calls(llm_response.content)

                for tool_call in tool_calls:
                    # 发送工具调用事件
                    yield format_sse("tool_call", {
                        "tool_name": tool_call.tool_name,
                        "parameters": tool_call.parameters,
                        "iteration": iteration
                    })

                # 执行工具
                tool_results = await agent.executor.execute_all(tool_calls)

                # 处理工具结果
                await agent._handle_tool_results(tool_calls, tool_results)

                # 发送工具结果
                for tool_result in tool_results:
                    yield format_sse("tool_result", {
                        "tool_name": tool_result.tool_name,
                        "success": tool_result.success,
                        "result": tool_result.result if tool_result.success else None,
                        "error": tool_result.error if not tool_result.success else None,
                        "iteration": iteration
                    })

                # 添加工具结果到 context
                tool_results_text = agent.executor.format_tool_results(tool_results)
                agent.context_manager.add_tool_result_message(tool_results_text)

                # 继续下一轮
                continue

            # 如果既没有答案也没有工具调用
            yield format_sse("answer", {
                "content": llm_response.content,
                "iteration": iteration,
                "token_usage": agent.context_manager.get_token_usage()
            })

            yield format_sse("done", {
                "iterations": iteration,
                "token_usage": agent.context_manager.get_token_usage()
            })

            break

        # 达到最大迭代次数
        if iteration >= max_iterations:
            yield format_sse("error", {
                "message": f"Reached maximum iterations ({max_iterations})",
                "type": "MaxIterationsError"
            })

            yield format_sse("done", {
                "iterations": iteration,
                "token_usage": agent.context_manager.get_token_usage()
            })

    except Exception as e:
        logger.error(f"Error in Agent streaming: {e}", exc_info=True)
        yield format_sse("error", {
            "message": str(e),
            "type": type(e).__name__
        })

        yield format_sse("done", {
            "error": True
        })


async def stream_agent_execute(
    agent: AgentEngine,
    user_message: str,
    session_id: str,
    mode: ExecutionMode = ExecutionMode.AUTO,
) -> AsyncGenerator[str, None]:
    """
    使用统一入口 execute() 流式输出 Agent 响应

    这是新的推荐方式，支持:
    - 自动模式选择 (AUTO)
    - 直接执行 (DIRECT)
    - 计划执行 (PLANNING)

    Args:
        agent: Agent 引擎实例
        user_message: 用户消息
        session_id: Session ID
        mode: 执行模式

    Yields:
        str: SSE 格式的事件流
    """
    try:
        # 发送开始事件
        yield format_sse("start", {
            "session_id": session_id,
            "mode": mode.value,
            "message": "Agent started processing..."
        })

        # 使用统一入口执行
        async for event in agent.execute(user_message, mode=mode):
            # 转换 SSEEvent 为 SSE 字符串
            event_type = event.type.value
            event_data = event.data or {}

            # 添加 session_id 到数据中
            event_data["session_id"] = session_id

            yield format_sse(event_type, event_data)

            # 如果是完成事件，结束
            if event.type.value == "done":
                break

    except Exception as e:
        logger.error(f"Error in Agent execute streaming: {e}", exc_info=True)
        yield format_sse("error", {
            "message": str(e),
            "type": type(e).__name__
        })
        yield format_sse("done", {
            "error": True
        })


def format_sse(event_type: str, data: dict) -> str:
    """
    格式化 SSE 事件

    Args:
        event_type: 事件类型
        data: 事件数据

    Returns:
        str: SSE 格式字符串
    """
    return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.get("/{session_id}/messages")
async def get_messages(
    session_id: str,
    limit: int = 50,
    service: SessionService = Depends(get_session_service),
):
    """
    获取 Session 的消息历史
    """
    # 验证 session 存在
    session = await service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )

    # 获取消息
    messages = await service.get_session_messages(session_id, limit=limit)

    return messages


@router.post("/feedback/{message_id}")
async def submit_feedback(
    message_id: str,
    request: FeedbackRequest,
    db: AsyncSession = Depends(get_db),
) -> FeedbackResponse:
    """
    Submit feedback (like/dislike) for a message.
    
    Used for collecting SFT training data.
    
    Args:
        message_id: The message ID to provide feedback for
        request: Feedback request with 'like', 'dislike', or null to clear
    
    Returns:
        FeedbackResponse with updated feedback state
    """
    from datetime import datetime
    
    repo = MessageRepository(db)
    message = await repo.get_by_id(message_id)
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Message {message_id} not found"
        )
    
    # Only allow feedback on assistant messages
    if message.role.value != "assistant":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Feedback can only be provided for assistant messages"
        )
    
    # Convert feedback string to enum or None
    feedback_value = None
    if request.feedback:
        if request.feedback not in ("like", "dislike"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Feedback must be 'like', 'dislike', or null"
            )
        feedback_value = FeedbackType(request.feedback)
    
    # Update the message
    feedback_at = datetime.utcnow() if feedback_value else None
    updated_message = await repo.update(
        message_id,
        feedback=feedback_value,
        feedback_at=feedback_at
    )
    
    return FeedbackResponse(
        message_id=message_id,
        feedback=updated_message.feedback.value if updated_message.feedback else None,
        feedback_at=updated_message.feedback_at
    )


@router.get("/{session_id}/working-memory")
async def get_working_memory(
    session_id: str,
    service: SessionService = Depends(get_session_service),
):
    """
    获取 Working Memory (三文件) 内容

    返回：
    - task_plan.md: 任务计划
    - findings.md: 研究发现
    - progress.md: 执行日志
    """
    # 验证 session 存在
    session = await service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )

    try:
        # 初始化 FileSystem
        workspace_root = getattr(settings, 'WORKSPACE_ROOT_PATH', '/tmp/tokendance/workspaces')
        filesystem = AgentFileSystem(
            workspace_id=str(session.workspace_id),
            base_dir=workspace_root
        )

        # 获取 Three Files Manager
        from app.agent.working_memory.three_files import ThreeFilesManager
        three_files = ThreeFilesManager(filesystem=filesystem, session_id=session_id)

        # 读取所有文件
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
            }
        }

    except Exception as e:
        logger.error(f"Error reading working memory: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read working memory: {str(e)}"
        ) from e
