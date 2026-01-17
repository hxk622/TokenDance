"""API v1 router - aggregates all v1 endpoints."""
from fastapi import APIRouter

from app.api.v1 import (
    agent_config,
    auth,
    browser,
    chat,
    demo_stream,
    files,
    financial,
    hitl,
    mcp,
    messages,
    ppt,
    research,
    session,
    skills,
    stream,
    timeline,
    tools,
    trust,
    working_memory,
    workspace,
)

api_router = APIRouter()

# Include all route modules
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(workspace.router, prefix="/workspaces", tags=["workspaces"])
api_router.include_router(session.router, prefix="/sessions", tags=["sessions"])
api_router.include_router(messages.router, prefix="/sessions", tags=["messages"])  # New Agent Engine integration
api_router.include_router(stream.router, prefix="/sessions", tags=["stream"])  # SSE streaming
api_router.include_router(mcp.router, prefix="/mcp", tags=["mcp"])  # MCP tools management
api_router.include_router(demo_stream.router, tags=["demo"])  # Demo endpoints (no auth)
api_router.include_router(hitl.router, tags=["hitl"])  # Human-in-the-Loop
api_router.include_router(trust.router, prefix="/trust", tags=["trust"])  # Trust configuration
api_router.include_router(skills.router, prefix="/skills", tags=["skills"])  # Skill discovery and templates
api_router.include_router(timeline.router, tags=["timeline"])  # Research Timeline
api_router.include_router(research.router, tags=["research"])  # Deep Research API
api_router.include_router(files.router, tags=["files"])  # File indexing & search
api_router.include_router(browser.router, tags=["browser"])  # Browser automation
api_router.include_router(ppt.router, tags=["ppt"])  # PPT Generation (Phase 1 & 2)
api_router.include_router(financial.router, prefix="/financial", tags=["financial"])  # Financial Analysis
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])  # Legacy
api_router.include_router(agent_config.router, tags=["agent-configs"])  # Agent Configuration
api_router.include_router(tools.router, tags=["tools"])  # Tools
api_router.include_router(working_memory.router, tags=["working-memory"])  # Working Memory
