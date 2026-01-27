"""
Tests for Session to Project migration script.
"""
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.models.project import ProjectType
from app.models.session import Session


class TestInferProjectType:
    """Test project type inference."""

    def test_research_skill(self):
        """Research skill maps to RESEARCH type."""
        from scripts.migrate_session_to_project import infer_project_type

        session = MagicMock(spec=Session)
        session.skill_id = "deep_research_v4"
        session.title = "Test"

        result = infer_project_type(session)
        assert result == ProjectType.RESEARCH

    def test_ppt_skill(self):
        """PPT skill maps to SLIDES type."""
        from scripts.migrate_session_to_project import infer_project_type

        session = MagicMock(spec=Session)
        session.skill_id = "ppt_generator"
        session.title = "Test"

        result = infer_project_type(session)
        assert result == ProjectType.SLIDES

    def test_code_skill(self):
        """Code skill maps to CODE type."""
        from scripts.migrate_session_to_project import infer_project_type

        session = MagicMock(spec=Session)
        session.skill_id = "code_refactor"
        session.title = "Test"

        result = infer_project_type(session)
        assert result == ProjectType.CODE

    def test_title_keyword_research(self):
        """Title with research keyword maps to RESEARCH type."""
        from scripts.migrate_session_to_project import infer_project_type

        session = MagicMock(spec=Session)
        session.skill_id = None
        session.title = "竞品调研分析"

        result = infer_project_type(session)
        assert result == ProjectType.RESEARCH

    def test_title_keyword_ppt(self):
        """Title with PPT keyword maps to SLIDES type."""
        from scripts.migrate_session_to_project import infer_project_type

        session = MagicMock(spec=Session)
        session.skill_id = None
        session.title = "制作演示幻灯片"

        result = infer_project_type(session)
        assert result == ProjectType.SLIDES

    def test_default_quick_task(self):
        """Unknown types default to QUICK_TASK."""
        from scripts.migrate_session_to_project import infer_project_type

        session = MagicMock(spec=Session)
        session.skill_id = None
        session.title = "Random chat"

        result = infer_project_type(session)
        assert result == ProjectType.QUICK_TASK


class TestExtractIntent:
    """Test intent extraction."""

    def test_from_first_user_message(self):
        """Extract intent from first user message."""
        from scripts.migrate_session_to_project import extract_intent

        msg = MagicMock()
        msg.role.value = "user"
        msg.content = "Help me analyze the market"

        session = MagicMock(spec=Session)
        session.messages = [msg]
        session.title = "Test"

        result = extract_intent(session)
        assert result == "Help me analyze the market"

    def test_truncate_long_message(self):
        """Truncate long intent to 500 chars."""
        from scripts.migrate_session_to_project import extract_intent

        msg = MagicMock()
        msg.role.value = "user"
        msg.content = "x" * 1000

        session = MagicMock(spec=Session)
        session.messages = [msg]
        session.title = "Test"

        result = extract_intent(session)
        assert len(result) == 500

    def test_fallback_to_title(self):
        """Fallback to title if no user messages."""
        from scripts.migrate_session_to_project import extract_intent

        session = MagicMock(spec=Session)
        session.messages = []
        session.title = "My Task Title"

        result = extract_intent(session)
        assert result == "My Task Title"


class TestExtractFailures:
    """Test failure extraction."""

    def test_extract_tool_errors(self):
        """Extract failures from tool call errors."""
        from scripts.migrate_session_to_project import extract_failures

        msg = MagicMock()
        msg.tool_calls = [
            {"name": "web_search", "status": "error", "error": "Connection failed"},
            {"name": "file_write", "status": "success", "result": "OK"},
            {"name": "code_run", "status": "failed", "error": "Syntax error"},
        ]
        msg.created_at = datetime(2024, 1, 1, 12, 0)

        session = MagicMock(spec=Session)
        session.messages = [msg]

        result = extract_failures(session)

        assert len(result) == 2
        assert result[0]["type"] == "web_search"
        assert result[0]["message"] == "Connection failed"
        assert result[1]["type"] == "code_run"

    def test_limit_failures(self):
        """Limit to 10 failures."""
        from scripts.migrate_session_to_project import extract_failures

        msg = MagicMock()
        msg.tool_calls = [
            {"name": f"tool_{i}", "status": "error", "error": f"Error {i}"}
            for i in range(20)
        ]
        msg.created_at = datetime(2024, 1, 1, 12, 0)

        session = MagicMock(spec=Session)
        session.messages = [msg]

        result = extract_failures(session)

        assert len(result) == 10

    def test_no_failures(self):
        """Return empty list if no failures."""
        from scripts.migrate_session_to_project import extract_failures

        msg = MagicMock()
        msg.tool_calls = [
            {"name": "web_search", "status": "success", "result": "OK"},
        ]

        session = MagicMock(spec=Session)
        session.messages = [msg]

        result = extract_failures(session)

        assert result == []


class TestMigrationStats:
    """Test migration statistics."""

    def test_report_format(self):
        """Stats report includes all counts."""
        from scripts.migrate_session_to_project import MigrationStats

        stats = MigrationStats()
        stats.total_sessions = 100
        stats.migrated_sessions = 95
        stats.skipped_sessions = 3
        stats.failed_sessions = 2
        stats.total_messages = 500
        stats.total_artifacts = 50

        report = stats.report()

        assert "100" in report
        assert "95" in report
        assert "500" in report
        assert "50" in report
