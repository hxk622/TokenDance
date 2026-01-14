"""
Demo SSE Stream API

Provides a demo streaming endpoint that doesn't require database session.
Used for frontend-backend integration testing.
"""
import asyncio
import json
import time
import random
from typing import AsyncGenerator

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


def format_sse(event: str, data: dict) -> str:
    """Format data as SSE message"""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


async def demo_execution_stream() -> AsyncGenerator[str, None]:
    """
    Demo agent execution stream with realistic workflow.
    
    Simulates a research task with multiple agents.
    """
    
    # Session started
    yield format_sse("session_started", {
        "session_id": "demo-session-001",
        "timestamp": time.time(),
    })
    await asyncio.sleep(0.3)
    
    # Define demo workflow
    workflow = [
        {
            "id": "1",
            "type": "manus",
            "label": "搜索市场数据",
            "thoughts": [
                "用户需要AI Agent市场分析报告...",
                "我需要先搜索最新的市场数据和趋势...",
                "让我调用web_search工具来获取信息。",
            ],
            "tool": {
                "name": "web_search",
                "args": {"query": "AI Agent market 2025 trends analysis"},
                "result": {
                    "found": 15,
                    "sources": [
                        "Gartner AI Report 2025",
                        "McKinsey AI Agents Analysis",
                        "TechCrunch AI Startups",
                    ],
                },
            },
        },
        {
            "id": "2", 
            "type": "manus",
            "label": "分析竞品",
            "thoughts": [
                "根据搜索结果，我需要分析主要竞品...",
                "主要玩家包括：OpenAI、Anthropic、Google...",
                "让我分析他们的产品特点和市场定位。",
            ],
            "tool": {
                "name": "analyze_data",
                "args": {"data_source": "search_results", "focus": "competitors"},
                "result": {
                    "competitors": [
                        {"name": "OpenAI Agents", "strength": "生态系统", "weakness": "成本"},
                        {"name": "Claude", "strength": "安全性", "weakness": "工具集成"},
                        {"name": "Gemini", "strength": "多模态", "weakness": "企业功能"},
                    ],
                    "insights": ["市场CAGR 35%", "企业采用率上升", "安全性成关键"],
                },
            },
        },
        {
            "id": "3",
            "type": "coworker", 
            "label": "生成分析摘要",
            "thoughts": [
                "现在我需要整理分析结果...",
                "先创建一个findings文件保存关键发现...",
            ],
            "files": [
                {"path": "findings.md", "action": "created", "preview": "# Key Findings\n\n1. Market growing at 35% CAGR..."},
            ],
        },
        {
            "id": "4",
            "type": "coworker",
            "label": "生成最终报告",
            "thoughts": [
                "让我把所有内容整合成最终报告...",
                "报告需要包含执行摘要、市场分析、竞品对比...",
            ],
            "files": [
                {"path": "report.md", "action": "created", "preview": "# AI Agent Market Analysis Report\n\n## Executive Summary..."},
                {"path": "charts/market_share.png", "action": "created", "preview": "[Chart: Market Share Distribution]"},
            ],
        },
    ]
    
    for node in workflow:
        # Node started
        yield format_sse("node_started", {
            "node_id": node["id"],
            "node_type": node["type"],
            "label": node["label"],
            "status": "active",
            "timestamp": time.time(),
        })
        await asyncio.sleep(0.4)
        
        # Agent thinking (stream thoughts)
        for thought in node["thoughts"]:
            yield format_sse("agent_thinking", {
                "content": thought,
                "node_id": node["id"],
                "timestamp": time.time(),
            })
            await asyncio.sleep(random.uniform(0.3, 0.6))
        
        # Tool call (for manus type)
        if "tool" in node:
            tool = node["tool"]
            yield format_sse("agent_tool_call", {
                "tool_name": tool["name"],
                "arguments": tool["args"],
                "node_id": node["id"],
                "timestamp": time.time(),
            })
            await asyncio.sleep(random.uniform(0.5, 1.0))
            
            yield format_sse("agent_tool_result", {
                "tool_name": tool["name"],
                "success": True,
                "result": tool["result"],
                "node_id": node["id"],
                "timestamp": time.time(),
            })
            await asyncio.sleep(0.3)
        
        # File operations (for coworker type)
        if "files" in node:
            for file_op in node["files"]:
                event_type = f"file_{file_op['action']}"
                yield format_sse(event_type, {
                    "path": file_op["path"],
                    "action": file_op["action"],
                    "preview": file_op.get("preview", ""),
                    "timestamp": time.time(),
                })
                await asyncio.sleep(0.3)
        
        # Node completed
        yield format_sse("node_completed", {
            "node_id": node["id"],
            "node_type": node["type"],
            "label": node["label"],
            "status": "success",
            "duration_ms": random.randint(1000, 3000),
            "timestamp": time.time(),
        })
        await asyncio.sleep(0.4)
    
    # Final agent message
    yield format_sse("agent_message", {
        "content": "✅ 任务执行完成！我已经完成了AI Agent市场分析，生成了以下文件：\n\n"
                   "1. **findings.md** - 关键发现摘要\n"
                   "2. **report.md** - 完整分析报告\n"
                   "3. **charts/market_share.png** - 市场份额图表\n\n"
                   "报告显示AI Agent市场正以35%的年复合增长率快速发展，企业采用率持续上升。",
        "role": "assistant",
        "timestamp": time.time(),
    })
    await asyncio.sleep(0.3)
    
    # Session completed
    yield format_sse("session_completed", {
        "session_id": "demo-session-001",
        "status": "completed",
        "total_duration_ms": 12500,
        "timestamp": time.time(),
    })


@router.get("/demo/stream")
async def demo_stream(request: Request):
    """
    Demo SSE stream endpoint.
    
    No authentication or database required.
    Perfect for frontend integration testing.
    
    Usage:
        const es = new EventSource('/api/v1/demo/stream');
        es.onmessage = (e) => console.log(e);
        es.addEventListener('agent_thinking', (e) => console.log(JSON.parse(e.data)));
    """
    logger.info(
        "demo_stream_started",
        client_ip=request.client.host if request.client else "unknown",
    )
    
    async def event_generator():
        try:
            async for event in demo_execution_stream():
                if await request.is_disconnected():
                    logger.info("demo_stream_client_disconnected")
                    break
                yield event
        except asyncio.CancelledError:
            logger.info("demo_stream_cancelled")
        except Exception as e:
            logger.error("demo_stream_error", error=str(e))
            yield format_sse("error", {"message": str(e)})
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/demo/ping")
async def demo_ping():
    """Health check endpoint for demo API"""
    return {"status": "ok", "timestamp": time.time()}
