"""
Session to Project Migration Script

Migrates legacy Session-centric data to Project-First architecture:
- Session → Project (QUICK_TASK type) + Conversation
- Messages → linked to Conversation instead of Session
- Artifacts → linked to Project instead of Session

Usage:
    cd backend
    uv run python scripts/migrate_session_to_project.py [--dry-run] [--batch-size 100]

Options:
    --dry-run       Preview changes without modifying database
    --batch-size N  Process N sessions at a time (default: 100)
"""
import argparse
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from contextlib import asynccontextmanager

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import async_session_maker
from app.core.datetime_utils import utc_now_naive
from app.models.artifact import Artifact
from app.models.conversation import Conversation, ConversationPurpose, ConversationStatus
from app.models.message import Message
from app.models.project import Project, ProjectStatus, ProjectType
from app.models.session import Session, SessionStatus

# Mapping from SessionStatus to ProjectStatus
STATUS_MAP = {
    SessionStatus.PENDING: ProjectStatus.DRAFT,
    SessionStatus.ACTIVE: ProjectStatus.IN_PROGRESS,
    SessionStatus.RUNNING: ProjectStatus.IN_PROGRESS,
    SessionStatus.COMPLETED: ProjectStatus.COMPLETED,
    SessionStatus.FAILED: ProjectStatus.IN_PROGRESS,  # Keep as in_progress so user can retry
    SessionStatus.CANCELLED: ProjectStatus.ARCHIVED,
    SessionStatus.ARCHIVED: ProjectStatus.ARCHIVED,
}


class MigrationStats:
    """Track migration statistics."""

    def __init__(self):
        self.total_sessions = 0
        self.migrated_sessions = 0
        self.skipped_sessions = 0
        self.failed_sessions = 0
        self.total_messages = 0
        self.total_artifacts = 0
        self.errors: list[str] = []

    def report(self) -> str:
        return f"""
Migration Statistics:
=====================
Total Sessions:    {self.total_sessions}
Migrated:          {self.migrated_sessions}
Skipped:           {self.skipped_sessions}
Failed:            {self.failed_sessions}
Messages Updated:  {self.total_messages}
Artifacts Updated: {self.total_artifacts}

Errors: {len(self.errors)}
{chr(10).join(f"  - {e}" for e in self.errors[:10])}
{"  ... and more" if len(self.errors) > 10 else ""}
"""


async def get_session_count(db: AsyncSession) -> int:
    """Count total sessions that need migration."""
    result = await db.execute(
        select(func.count(Session.id))
    )
    return result.scalar() or 0


async def get_sessions_batch(
    db: AsyncSession,
    offset: int,
    limit: int
) -> list[Session]:
    """Get a batch of sessions to migrate with eager loading."""
    result = await db.execute(
        select(Session)
        .options(
            selectinload(Session.messages),
            selectinload(Session.artifacts)
        )
        .order_by(Session.created_at)
        .offset(offset)
        .limit(limit)
    )
    return list(result.scalars().all())


async def check_already_migrated(db: AsyncSession, session_id: str) -> bool:
    """Check if a session has already been migrated to a project."""
    # Check if a project exists with the session's data
    result = await db.execute(
        select(Conversation.id).where(
            Conversation.extra_data["migrated_from_session_id"].astext == session_id
        )
    )
    return result.scalar() is not None


async def migrate_session(
    db: AsyncSession,
    session: Session,
    stats: MigrationStats,
    dry_run: bool = False
) -> str | None:
    """Migrate a single session to Project-First architecture.

    Returns the new project ID if successful, None otherwise.
    """
    try:
        # Check if already migrated
        if await check_already_migrated(db, session.id):
            stats.skipped_sessions += 1
            return None

        # Infer project type from session data
        project_type = infer_project_type(session)

        # Create Project
        project = Project(
            workspace_id=session.workspace_id,
            title=session.title or "Untitled",
            description=f"Migrated from session {session.id}",
            project_type=project_type,
            status=STATUS_MAP.get(session.status, ProjectStatus.DRAFT),
            intent=extract_intent(session),
            context={
                "decisions": [],
                "failures": extract_failures(session),
                "key_findings": [],
                "tags": ["migrated"],
            },
            settings={
                "llm_model": "claude-3-5-sonnet",
                "skill_id": session.skill_id,
            },
            total_tokens_used=session.total_tokens_used,
            conversation_count=1,
            artifact_count=len(session.artifacts) if session.artifacts else 0,
            created_at=session.created_at,
            updated_at=session.updated_at,
            last_accessed_at=session.updated_at,
        )

        if not dry_run:
            db.add(project)
            await db.flush()  # Get project.id

        # Create Conversation
        conversation = Conversation(
            project_id=project.id if not dry_run else "dry-run-id",
            title=session.title or "Initial conversation",
            purpose=ConversationPurpose.GENERAL,
            status=(ConversationStatus.COMPLETED
                    if session.status in (SessionStatus.COMPLETED, SessionStatus.ARCHIVED)
                    else ConversationStatus.ACTIVE),
            selection_context=None,
            tokens_used=session.total_tokens_used,
            # Note: message_count is a calculated @property, not stored
            created_at=session.created_at,
            updated_at=session.updated_at,
            completed_at=session.completed_at,
            extra_data={
                "migrated_from_session_id": session.id,
                "migration_timestamp": utc_now_naive().isoformat(),
            },
        )

        if not dry_run:
            db.add(conversation)
            await db.flush()  # Get conversation.id

        # Update Messages to link to Conversation
        if session.messages and not dry_run:
            message_count = len(session.messages)
            await db.execute(
                update(Message)
                .where(Message.session_id == session.id)
                .values(conversation_id=conversation.id)
            )
            stats.total_messages += message_count

        # Update Artifacts to link to Project
        if session.artifacts and not dry_run:
            artifact_count = len(session.artifacts)
            await db.execute(
                update(Artifact)
                .where(Artifact.session_id == session.id)
                .values(project_id=project.id)
            )
            stats.total_artifacts += artifact_count

        stats.migrated_sessions += 1
        return project.id if not dry_run else "dry-run-id"

    except Exception as e:
        stats.failed_sessions += 1
        stats.errors.append(f"Session {session.id}: {str(e)}")
        return None


def infer_project_type(session: Session) -> ProjectType:
    """Infer project type from session metadata."""
    skill_id = session.skill_id or ""
    title = (session.title or "").lower()

    # Check skill ID
    if "research" in skill_id or "deep_research" in skill_id:
        return ProjectType.RESEARCH
    if "ppt" in skill_id or "slides" in skill_id:
        return ProjectType.SLIDES
    if "code" in skill_id:
        return ProjectType.CODE
    if "data" in skill_id or "analysis" in skill_id:
        return ProjectType.DATA_ANALYSIS
    if "doc" in skill_id or "document" in skill_id:
        return ProjectType.DOCUMENT

    # Check title keywords
    if any(kw in title for kw in ["research", "调研", "分析"]):
        return ProjectType.RESEARCH
    if any(kw in title for kw in ["ppt", "slides", "演示", "幻灯片"]):
        return ProjectType.SLIDES
    if any(kw in title for kw in ["code", "代码", "编程"]):
        return ProjectType.CODE

    # Default to quick task
    return ProjectType.QUICK_TASK


def extract_intent(session: Session) -> str:
    """Extract intent from session's first user message or title."""
    # Try to get from first user message
    if session.messages:
        for msg in session.messages:
            if msg.role.value == "user" and msg.content:
                # Use first user message as intent
                return msg.content[:500]  # Truncate if too long

    # Fallback to title
    return session.title or "No intent recorded"


def extract_failures(session: Session) -> list[dict]:
    """Extract failures from session messages (tool call errors)."""
    failures = []

    if not session.messages:
        return failures

    for msg in session.messages:
        if msg.tool_calls:
            for tc in msg.tool_calls:
                if tc.get("status") in ("error", "failed"):
                    failures.append({
                        "type": tc.get("name", "unknown_tool"),
                        "message": str(tc.get("error", tc.get("result", "Unknown error"))),
                        "learning": None,
                        "timestamp": msg.created_at.isoformat() if msg.created_at else utc_now_naive().isoformat(),
                    })

    return failures[:10]  # Limit to 10 most recent failures


@asynccontextmanager
async def get_session():
    """Context manager for database sessions."""
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def run_migration(
    dry_run: bool = False,
    batch_size: int = 100
) -> MigrationStats:
    """Run the full migration process."""
    stats = MigrationStats()

    async with get_session() as db:
        # Get total count
        stats.total_sessions = await get_session_count(db)
        print(f"Found {stats.total_sessions} sessions to migrate")

        if stats.total_sessions == 0:
            print("No sessions to migrate.")
            return stats

        # Process in batches
        offset = 0
        while offset < stats.total_sessions:
            print(f"Processing batch {offset // batch_size + 1} "
                  f"(sessions {offset + 1} to {min(offset + batch_size, stats.total_sessions)})")

            sessions = await get_sessions_batch(db, offset, batch_size)

            for session in sessions:
                await migrate_session(db, session, stats, dry_run)

            if not dry_run:
                await db.commit()

            offset += batch_size

    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Migrate Sessions to Project-First architecture"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying database"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Number of sessions to process at a time"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("Session to Project Migration")
    print("=" * 60)
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE MIGRATION'}")
    print(f"Batch size: {args.batch_size}")
    print()

    if not args.dry_run:
        confirm = input("This will modify the database. Continue? [y/N] ")
        if confirm.lower() != "y":
            print("Aborted.")
            return

    stats = asyncio.run(run_migration(
        dry_run=args.dry_run,
        batch_size=args.batch_size
    ))

    print(stats.report())

    if args.dry_run:
        print("\nThis was a DRY RUN. No changes were made.")
    else:
        print("\nMigration complete!")


if __name__ == "__main__":
    main()
