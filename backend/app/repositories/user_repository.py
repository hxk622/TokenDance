"""User repository - data access for User model."""
from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import AuthProvider, User


class UserRepository:
    """Repository for User data access operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        email: str,
        username: str,
        password_hash: str | None = None,
        auth_provider: str = AuthProvider.EMAIL_PASSWORD.value,
        display_name: str | None = None,
        avatar_url: str | None = None,
    ) -> User:
        """Create a new user.

        Args:
            email: User email (unique)
            username: Username (unique)
            password_hash: Hashed password (optional for OAuth users)
            auth_provider: Authentication provider
            display_name: Display name
            avatar_url: Avatar URL

        Returns:
            Created User instance
        """
        user = User(
            email=email,
            username=username,
            password_hash=password_hash,
            auth_provider=auth_provider,
            display_name=display_name,
            avatar_url=avatar_url,
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_by_id(self, user_id: UUID) -> User | None:
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

    async def get_by_email(self, email: str) -> User | None:
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

    async def get_by_username(self, username: str) -> User | None:
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

    async def get_by_wechat_openid(self, openid: str) -> User | None:
        """Get user by WeChat OpenID.

        Args:
            openid: WeChat OpenID

        Returns:
            User instance or None if not found
        """
        result = await self.session.execute(
            select(User).where(User.wechat_openid == openid)
        )
        return result.scalar_one_or_none()

    async def get_by_gmail_sub(self, sub: str) -> User | None:
        """Get user by Gmail subject (sub).

        Args:
            sub: Gmail subject identifier

        Returns:
            User instance or None if not found
        """
        result = await self.session.execute(
            select(User).where(User.gmail_sub == sub)
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

    async def update_wechat_info(
        self,
        user_id: UUID,
        openid: str,
        unionid: str | None = None,
        nickname: str | None = None,
        headimgurl: str | None = None,
    ) -> User | None:
        """Update user's WeChat OAuth information.

        Args:
            user_id: User UUID
            openid: WeChat OpenID
            unionid: WeChat UnionID (optional)
            nickname: WeChat nickname (optional)
            headimgurl: WeChat avatar URL (optional)

        Returns:
            Updated User instance or None if not found
        """
        result = await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(
                wechat_openid=openid,
                wechat_unionid=unionid,
                wechat_nickname=nickname,
                wechat_headimgurl=headimgurl,
                auth_provider=AuthProvider.WECHAT.value,
            )
        )
        await self.session.commit()

        if result.rowcount > 0:
            return await self.get_by_id(user_id)
        return None

    async def update_gmail_info(
        self,
        user_id: UUID,
        sub: str,
        email: str,
        name: str | None = None,
        picture: str | None = None,
        access_token: str | None = None,
        refresh_token: str | None = None,
        expires_at: datetime | None = None,
    ) -> User | None:
        """Update user's Gmail OAuth information.

        Args:
            user_id: User UUID
            sub: Gmail subject identifier
            email: Gmail email
            name: Gmail name (optional)
            picture: Gmail picture URL (optional)
            access_token: Gmail access token (optional)
            refresh_token: Gmail refresh token (optional)
            expires_at: Token expiration time (optional)

        Returns:
            Updated User instance or None if not found
        """
        result = await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(
                gmail_sub=sub,
                gmail_email=email,
                gmail_name=name,
                gmail_picture=picture,
                gmail_access_token=access_token,
                gmail_refresh_token=refresh_token,
                gmail_token_expires_at=expires_at,
                auth_provider=AuthProvider.GMAIL.value,
                email_verified=True,
            )
        )
        await self.session.commit()

        if result.rowcount > 0:
            return await self.get_by_id(user_id)
        return None

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
            .values(is_verified=True, email_verified=True)
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
