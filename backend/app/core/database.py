"""
Database configuration and session management.
Uses SQLAlchemy 2.0 with async support.
"""
from collections.abc import AsyncGenerator
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Create async engine
use_null_pool = "pytest" in sys.modules
engine_kwargs: dict[str, object] = {
    "echo": settings.DEBUG,
    "pool_pre_ping": True,  # Verify connections before using
    "pool_recycle": 3600,   # Recycle connections after 1 hour
}

if use_null_pool:
    engine_kwargs["poolclass"] = NullPool
else:
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20

engine = create_async_engine(
    settings.DATABASE_URL,
    **engine_kwargs,
)

# Create async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Alias for compatibility
AsyncSessionLocal = async_session_maker

# Declarative base for models
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database sessions.

    Usage:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database - create all tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("database_initialized")


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()
    logger.info("database_connections_closed")


async def check_db_health() -> bool:
    """Check database connection health."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error("database_health_check_failed", error=str(e))
        return False


async def check_tables_exist() -> tuple[bool, list[str]]:
    """
    Check if critical database tables exist.

    Returns:
        Tuple of (all_exist: bool, missing_tables: list[str])
    """
    critical_tables = ['users', 'workspaces', 'sessions', 'messages']
    missing_tables = []

    try:
        async with engine.connect() as conn:
            for table in critical_tables:
                result = await conn.execute(
                    text(
                        "SELECT EXISTS ("
                        "SELECT FROM information_schema.tables "
                        "WHERE table_schema = 'public' "
                        "AND table_name = :table_name"
                        ")"
                    ),
                    {"table_name": table}
                )
                exists = result.scalar()
                if not exists:
                    missing_tables.append(table)

        return len(missing_tables) == 0, missing_tables
    except Exception as e:
        logger.error("table_check_failed", error=str(e))
        return False, critical_tables


async def run_migrations() -> bool:
    """
    Run database migrations using Alembic.

    Returns:
        True if migrations succeeded, False otherwise
    """
    import os
    import subprocess

    try:
        # Get the backend directory path
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        logger.info("running_database_migrations", backend_dir=backend_dir)

        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=backend_dir,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            logger.info("database_migrations_completed", output=result.stdout)
            return True
        else:
            logger.error("database_migrations_failed",
                        stderr=result.stderr,
                        stdout=result.stdout,
                        returncode=result.returncode)
            return False
    except subprocess.TimeoutExpired:
        logger.error("database_migrations_timeout")
        return False
    except Exception as e:
        logger.error("database_migrations_error", error=str(e))
        return False
