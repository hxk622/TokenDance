"""API v1 router - aggregates all v1 endpoints."""
from fastapi import APIRouter

from app.api.v1 import auth, session, chat

api_router = APIRouter()

# Include all route modules
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(session.router, prefix="/sessions", tags=["sessions"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
