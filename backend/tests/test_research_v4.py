"""
Tests for Research v4 API endpoints.

Covers:
- Reasoning trace endpoints
- Report iteration endpoints
- Service unit tests
"""
import pytest
from unittest.mock import patch, MagicMock

from app.schemas.reasoning_trace import (
    ReasoningTrace,
    ReasoningAction,
    ResearchPhase,
)
from app.schemas.interactive_report import (
    InteractiveReport,
    ReportSection,
    RevisionRequest,
    RevisionType,
    SectionType,
)
from app.services.reasoning_trace import ReasoningTraceService
from app.services.report_iterator import ReportIterator
from app.services.saturation_detector import (
    SaturationDetector,
    AdaptiveDepthAdvisor,
    ResearchFinding,
    SaturationLevel,
)
from app.services.research_memory import (
    ResearchMemoryService,
    MemoryType,
)


class TestReasoningTraceService:
    """Tests for ReasoningTraceService."""

    def test_create_service(self):
        """Test service creation."""
        service = ReasoningTraceService("test-session-123")
        assert service.session_id == "test-session-123"
        assert len(service.get_all_traces()) == 0

    def test_record_decision(self):
        """Test recording a decision."""
        service = ReasoningTraceService("test-session")
        
        trace = service.record_decision(
            phase=ResearchPhase.SEARCHING,
            action=ReasoningAction.SELECT_SOURCE,
            reasoning="选择权威来源",
            confidence=0.85,
        )
        
        assert trace.phase == ResearchPhase.SEARCHING
        assert trace.action == ReasoningAction.SELECT_SOURCE
        assert trace.confidence == 0.85
        assert len(service.get_all_traces()) == 1

    def test_get_recent_traces(self):
        """Test getting recent traces with limit."""
        service = ReasoningTraceService("test-session")
        
        # Add multiple traces
        for i in range(10):
            service.record_decision(
                phase=ResearchPhase.SEARCHING,
                action=ReasoningAction.SELECT_SOURCE,
                reasoning=f"Reason {i}",
                confidence=0.5,
            )
        
        recent = service.get_recent_traces(5)
        assert len(recent) == 5

    def test_get_trace_by_id(self):
        """Test getting trace by ID."""
        service = ReasoningTraceService("test-session")
        
        trace = service.record_decision(
            phase=ResearchPhase.SEARCHING,
            action=ReasoningAction.SELECT_SOURCE,
            reasoning="Test",
            confidence=0.5,
        )
        
        found = service.get_trace_by_id(trace.id)
        assert found is not None
        assert found.id == trace.id
        
        # Test not found
        not_found = service.get_trace_by_id("nonexistent")
        assert not_found is None


class TestReportIterator:
    """Tests for ReportIterator service."""

    def test_create_report(self):
        """Test creating a report."""
        iterator = ReportIterator()
        
        sections = [
            ReportSection(
                id="section-1",
                type=SectionType.SUMMARY,
                title="Summary",
                content="This is the summary.",
            ),
        ]
        
        report = iterator.create_report(
            session_id="test-session",
            title="Test Report",
            query="Test query",
            sections=sections,
        )
        
        assert report.title == "Test Report"
        assert report.current_version == 1
        assert len(report.versions) == 1
        assert len(report.versions[0].sections) == 1

    def test_get_current_sections(self):
        """Test getting current sections."""
        iterator = ReportIterator()
        
        sections = [
            ReportSection(
                id="section-1",
                type=SectionType.ANALYSIS,
                title="Analysis",
                content="Content here",
            ),
        ]
        
        report = iterator.create_report(
            session_id="test",
            title="Test",
            query="Query",
            sections=sections,
        )
        
        current = iterator.get_current_sections(report.id)
        assert len(current) == 1
        assert current[0].title == "Analysis"

    def test_rollback_version(self):
        """Test rollback to previous version."""
        iterator = ReportIterator()
        
        sections = [
            ReportSection(
                id="s1",
                type=SectionType.SUMMARY,
                title="Original",
                content="Original content",
            ),
        ]
        
        report = iterator.create_report(
            session_id="test",
            title="Test",
            query="Query",
            sections=sections,
        )
        
        # Simulate applying a revision (creating v2)
        from app.schemas.interactive_report import RevisionResult
        result = RevisionResult(
            section_id="s1",
            original_content="Original content",
            revised_content="Updated content",
            revision_type=RevisionType.REWRITE,
            changes_summary="Rewritten",
        )
        
        import asyncio
        asyncio.get_event_loop().run_until_complete(
            iterator.apply_revisions(report.id, [result])
        )
        
        assert report.current_version == 2
        
        # Rollback to v1
        iterator.rollback_version(report.id, 1)
        assert report.current_version == 3  # Rollback creates new version


class TestSaturationDetector:
    """Tests for SaturationDetector service."""

    def test_low_saturation(self):
        """Test detection with few findings."""
        detector = SaturationDetector()
        
        # Add just 2 findings (below threshold)
        for i in range(2):
            detector.add_finding(ResearchFinding(
                id=f"finding-{i}",
                content=f"Finding {i}",
                source_url=f"https://example{i}.com",
                key_points=[f"Point {i}"],
            ))
        
        metrics = detector.detect_saturation()
        assert metrics.saturation_level == SaturationLevel.LOW
        assert metrics.confidence < 0.5

    def test_add_finding_tracks_domains(self):
        """Test that findings track source domains."""
        detector = SaturationDetector()
        
        detector.add_finding(ResearchFinding(
            id="f1",
            content="Test",
            source_url="https://example.com/page1",
            key_points=["Point 1"],
        ))
        
        detector.add_finding(ResearchFinding(
            id="f2",
            content="Test 2",
            source_url="https://another.com/page",
            key_points=["Point 2"],
        ))
        
        assert len(detector._source_domains) == 2

    def test_reset(self):
        """Test detector reset."""
        detector = SaturationDetector()
        
        detector.add_finding(ResearchFinding(
            id="f1",
            content="Test",
            source_url="https://example.com",
            key_points=["Point"],
        ))
        
        detector.reset()
        
        assert len(detector._findings) == 0
        assert len(detector._source_domains) == 0


class TestAdaptiveDepthAdvisor:
    """Tests for AdaptiveDepthAdvisor."""

    def test_advice_with_low_saturation(self):
        """Test advice when saturation is low."""
        detector = SaturationDetector()
        advisor = AdaptiveDepthAdvisor(detector)
        advisor.set_current_depth(10)
        
        advice = advisor.get_advice("test query")
        
        # Low saturation should suggest continuing
        assert advice.action.value in ["continue", "continue_focused"]

    def test_should_auto_stop_false_when_low(self):
        """Test auto-stop is false when saturation is low."""
        detector = SaturationDetector()
        advisor = AdaptiveDepthAdvisor(detector)
        
        assert advisor.should_auto_stop() is False


class TestResearchMemoryService:
    """Tests for ResearchMemoryService."""

    def test_add_and_get_memory(self):
        """Test adding and retrieving memories."""
        service = ResearchMemoryService()
        
        memory = service.add_memory(
            user_id="user-123",
            memory_type=MemoryType.FINDING,
            content="Important finding about AI",
            tags=["ai", "research"],
        )
        
        assert memory.user_id == "user-123"
        assert memory.memory_type == MemoryType.FINDING
        
        memories = service.get_memories("user-123")
        assert len(memories) == 1
        assert memories[0].id == memory.id

    def test_find_related_memories(self):
        """Test finding related memories by query."""
        service = ResearchMemoryService()
        
        service.add_memory(
            user_id="user-1",
            memory_type=MemoryType.FINDING,
            content="Machine learning is a subset of AI",
            tags=["ai", "ml"],
        )
        
        service.add_memory(
            user_id="user-1",
            memory_type=MemoryType.FINDING,
            content="Python is a programming language",
            tags=["python"],
        )
        
        related = service.find_related_memories("user-1", "AI machine learning")
        assert len(related) >= 1
        assert "machine learning" in related[0].content.lower()

    def test_delete_memory(self):
        """Test deleting a memory."""
        service = ResearchMemoryService()
        
        memory = service.add_memory(
            user_id="user-1",
            memory_type=MemoryType.NOTE,
            content="Test note",
        )
        
        result = service.delete_memory("user-1", memory.id)
        assert result is True
        
        memories = service.get_memories("user-1")
        assert len(memories) == 0

    def test_save_and_get_context(self):
        """Test saving and retrieving research context."""
        service = ResearchMemoryService()
        
        context = service.save_context(
            session_id="session-1",
            query="AI research trends",
            user_id="user-1",
            findings=["Finding 1", "Finding 2"],
            questions=["Question 1"],
        )
        
        assert context.query == "AI research trends"
        assert len(context.key_findings) == 2
        
        retrieved = service.get_context("session-1")
        assert retrieved is not None
        assert retrieved.session_id == "session-1"
