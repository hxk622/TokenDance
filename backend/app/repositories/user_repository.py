"""User repository - data access for User model."""
from typing import Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    """Repository for User data access operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        email: str,
        username: str,
        password_hash: str,
    ) -> User:
        """Create a new user.
        
        Args:
            email: User email (unique)
            username: Username (unique)
            password_hash: Hashed password
            
        Returns:
            Created User instance
        """
        user = User(
            email=email,
            username=username,
            password_hash=password_hash,
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID.
        
        Args:
            user_id: User UUID
            
        Returns:
            User instance or None if not found
        """
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email.
        
        Args:
            email: User email
            
        Returns:
            User instance or None if not found
        """
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username.
        
        Args:
            username: Username
            
        Returns:
            User instance or None if not found
        """
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def update(self, user: User) -> User:
        """Update user.
        
        Args:
            user: User instance with updated fields
            
        Returns:
            Updated User instance
        """
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def increment_workspace_count(self, user_id: UUID) -> None:
        """Increment user's workspace count.
        
        Args:
            user_id: User UUID
        """
        user = await self.get_by_id(user_id)
        if user:
            if not user.usage_stats:
                user.usage_stats = {}
            user.usage_stats["workspace_count"] = (
                user.usage_stats.get("workspace_count", 0) + 1
            )
            await self.update(user)

    async def verify_email(self, user_id: UUID) -> bool:
        """Mark user's email as verified.
        
        Args:
            user_id: User UUID
            
        Returns:
            True if successful, False otherwise
        """
        result = await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(is_verified=True)
        )
        await self.session.commit()
        return result.rowcount > 0

    async def deactivate(self, user_id: UUID) -> bool:
        """Deactivate user account.
        
        Args:
            user_id: User UUID
            
        Returns:
            True if successful, False otherwise
        """
        result = await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(is_active=False)
        )
        await self.session.commit()
        return result.rowcount > 0
