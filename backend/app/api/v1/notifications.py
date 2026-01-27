"""
Notifications API endpoints.

Currently returns empty data until notification storage is implemented.
"""
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field

from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/notifications", tags=["notifications"])


class NotificationItem(BaseModel):
    """Notification item (placeholder schema)."""
    id: str
    type: str
    title: str
    content: str
    link: str | None = None
    is_read: bool = Field(default=False, alias="isRead")
    created_at: str = Field(..., alias="createdAt")
    metadata: dict | None = None


class NotificationListResponse(BaseModel):
    """Response schema for notifications list."""
    notifications: list[NotificationItem]
    total: int
    unread_count: int = Field(0, alias="unreadCount")


class UnreadCountResponse(BaseModel):
    """Response schema for unread count."""
    count: int = 0


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100, alias="pageSize"),
    unread_only: bool = Query(False, alias="unreadOnly"),
    current_user: User = Depends(get_current_user),
) -> NotificationListResponse:
    """Return empty notification list (placeholder)."""
    _ = (page, page_size, unread_only, current_user)
    return NotificationListResponse(notifications=[], total=0, unreadCount=0)


@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(
    current_user: User = Depends(get_current_user),
) -> UnreadCountResponse:
    """Return unread count (placeholder)."""
    _ = current_user
    return UnreadCountResponse(count=0)


@router.post("/{notification_id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
) -> None:
    """Mark a notification as read (placeholder)."""
    _ = (notification_id, current_user)
    return None


@router.post("/read-all", status_code=status.HTTP_204_NO_CONTENT)
async def mark_all_read(
    current_user: User = Depends(get_current_user),
) -> None:
    """Mark all notifications as read (placeholder)."""
    _ = current_user
    return None


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
    notification_id: str,
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a notification (placeholder)."""
    _ = (notification_id, current_user)
    return None
