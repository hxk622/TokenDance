"""
Agent Worker Startup Script

Starts the Agent Worker process that listens for conversation turn execution tasks.

Usage:
    cd backend
    uv run python scripts/start_agent_worker.py

The worker will:
1. Connect to Redis and listen on "agent:execute" channel
2. Load conversation context for each turn
3. Execute Agent and stream events to SSE
4. Update shared_memory after execution
5. Save results to database
"""
import asyncio
import logging
import signal
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.agent.worker import start_agent_worker
from app.core.config import settings
from app.core.database import async_session_maker, init_db
from app.core.logging import setup_logging
from app.core.redis import get_redis_client, init_redis
from app.services.sse_event_store import SSEEventStore

logger = logging.getLogger(__name__)


async def main():
    """Main entry point for Agent Worker."""
    # Setup logging
    setup_logging()

    logger.info("agent_worker_starting", environment=settings.ENVIRONMENT)

    # Initialize database
    await init_db()
    logger.info("database_initialized")

    # Initialize Redis
    await init_redis()
    redis = await get_redis_client()
    logger.info("redis_initialized")

    # Create SSEEventStore
    event_store = SSEEventStore(redis)

    # Create database session
    async with async_session_maker() as db:
        # Start worker (this will run indefinitely)
        try:
            await start_agent_worker(
                redis=redis,
                db=db,
                settings=settings,
                event_store=event_store,
            )
        except KeyboardInterrupt:
            logger.info("agent_worker_interrupted")
        except Exception as e:
            logger.error(f"agent_worker_error: {e}", exc_info=True)
            raise
        finally:
            logger.info("agent_worker_shutdown")


def handle_signal(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"received_signal_{signum}")
    sys.exit(0)


if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    # Run worker
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("agent_worker_stopped")
    except Exception as e:
        logger.error(f"agent_worker_failed: {e}", exc_info=True)
        sys.exit(1)
