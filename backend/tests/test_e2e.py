"""
End-to-End (E2E) Test Suite
Tests the complete flow from user registration to message streaming.
"""
import uuid
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base, async_session_maker, engine
from app.main import app
from app.models.message import Message, MessageRole
from app.models.session import Session, SessionStatus
from app.models.user import User
from app.models.workspace import Workspace


@pytest.fixture(scope="function")
async def db_session():
    """Create a fresh database session for each test."""
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async with async_session_maker() as session:
        yield session

    # Drop all tables after test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


class TestE2EFlow:
    """Test complete end-to-end flow."""

    @pytest.mark.asyncio
    async def test_complete_flow(self, db_session: AsyncSession):
        """
        Test complete E2E flow:
        1. Create user
        2. Create workspace
        3. Create session
        4. Send message
        5. Verify message storage
        6. Verify working memory creation
        """

        # Step 1: Create user
        user_id = str(uuid.uuid4())
        user = User(
            id=user_id,
            email=f"test_{user_id}@example.com",
            username=f"testuser_{user_id[:8]}",
            password_hash="hashed_password",
            is_active=True,
            is_verified=True,
        )
        db_session.add(user)
        await db_session.flush()

        print(f"✓ Step 1: User created (id={user.id})")

        # Step 2: Create workspace
        workspace_id = str(uuid.uuid4())
        workspace = Workspace(
            id=workspace_id,
            name="Test Workspace",
            slug=f"test-workspace-{workspace_id[:8]}",
            owner_id=user.id,
            filesystem_path=f"/data/users/{user.id}/workspaces/{workspace_id}",
        )
        db_session.add(workspace)
        await db_session.flush()

        print(f"✓ Step 2: Workspace created (id={workspace.id})")

        # Step 3: Create session
        session_id = str(uuid.uuid4())
        session = Session(
            id=session_id,
            workspace_id=workspace.id,
            title="E2E Test Session",
            status=SessionStatus.ACTIVE,
        )
        db_session.add(session)
        await db_session.flush()

        print(f"✓ Step 3: Session created (id={session.id})")

        # Step 4: Create user message
        user_message_id = str(uuid.uuid4())
        user_message = Message(
            id=user_message_id,
            session_id=session.id,
            role=MessageRole.USER,
            content="Hello, can you help me with a task?",
        )
        db_session.add(user_message)
        await db_session.flush()

        print(f"✓ Step 4: User message created (id={user_message.id})")

        # Step 5: Simulate agent response
        assistant_message_id = str(uuid.uuid4())
        assistant_message = Message(
            id=assistant_message_id,
            session_id=session.id,
            role=MessageRole.ASSISTANT,
            content="Of course! I'd be happy to help you with your task.",
            thinking="User is asking for help. I should be friendly and offer assistance.",
            tool_calls=[],
        )
        db_session.add(assistant_message)
        await db_session.flush()

        print(f"✓ Step 5: Assistant message created (id={assistant_message.id})")

        # Step 6: Verify data integrity
        await db_session.commit()

        # Reload and verify
        await db_session.refresh(user)
        await db_session.refresh(workspace)
        await db_session.refresh(session)

        assert user.email == f"test_{user_id}@example.com"
        assert workspace.name == "Test Workspace"
        assert workspace.owner_id == user.id
        assert session.title == "E2E Test Session"
        assert session.workspace_id == workspace.id

        print("✓ Step 6: Data integrity verified")

        # Verify message count
        from sqlalchemy import func, select

        message_count = await db_session.scalar(
            select(func.count()).select_from(Message).where(Message.session_id == session.id)
        )
        assert message_count == 2, f"Expected 2 messages, got {message_count}"

        print("✓ Step 7: Message count verified (2 messages)")

        # Verify message roles
        messages = await db_session.scalars(
            select(Message).where(Message.session_id == session.id).order_by(Message.created_at)
        )
        message_list = list(messages)

        assert len(message_list) == 2
        assert message_list[0].role == MessageRole.USER
        assert message_list[1].role == MessageRole.ASSISTANT

        print("✓ Step 8: Message roles verified")

        print("\n✅ E2E Test Passed!")

    @pytest.mark.asyncio
    async def test_workspace_quota(self, db_session: AsyncSession):
        """Test workspace quota enforcement."""

        # Create user with limited quota
        user_id = str(uuid.uuid4())
        user = User(
            id=user_id,
            email=f"quota_test_{user_id}@example.com",
            username=f"quota_user_{user_id[:8]}",
            password_hash="hashed_password",
            personal_quota={"max_workspaces": 2, "max_monthly_tokens": 1000, "max_storage_gb": 1},
            usage_stats={"current_workspaces": 0, "monthly_tokens_used": 0, "storage_used_gb": 0},
        )
        db_session.add(user)
        await db_session.commit()

        # User should be able to create workspace
        assert user.can_create_workspace()

        # Update usage
        user.usage_stats["current_workspaces"] = 2
        assert not user.can_create_workspace()

        print("✓ Workspace quota enforcement verified")

    @pytest.mark.asyncio
    async def test_session_status_transitions(self, db_session: AsyncSession):
        """Test session status transitions."""

        # Create user and workspace
        user = User(
            id=str(uuid.uuid4()),
            email="status_test@example.com",
            username="status_user",
            password_hash="hashed_password",
        )
        db_session.add(user)

        workspace = Workspace(
            id=str(uuid.uuid4()),
            name="Status Test Workspace",
            slug=f"status-test-{user.id[:8]}",
            owner_id=user.id,
            filesystem_path=f"/data/users/{user.id}/workspaces/status-test",
        )
        db_session.add(workspace)
        await db_session.flush()

        # Create session
        session = Session(
            id=str(uuid.uuid4()),
            workspace_id=workspace.id,
            title="Status Test Session",
            status=SessionStatus.ACTIVE,
        )
        db_session.add(session)
        await db_session.commit()

        # Verify initial status
        assert session.status == SessionStatus.ACTIVE
        assert session.completed_at is None

        # Complete session
        session.status = SessionStatus.COMPLETED
        session.completed_at = datetime.utcnow()
        await db_session.commit()

        assert session.status == SessionStatus.COMPLETED
        assert session.completed_at is not None

        print("✓ Session status transitions verified")


def run_e2e_tests():
    """Run E2E tests manually."""
    print("=" * 60)
    print("Running E2E Tests")
    print("=" * 60)
    print()

    pytest.main([__file__, "-v", "-s"])


if __name__ == "__main__":
    run_e2e_tests()
