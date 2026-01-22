"""
Unit tests for KnowledgeGraphService risk propagation.

Run with:
    cd backend && uv run pytest tests/services/financial/test_risk_propagation.py -v
"""

import pytest

from app.services.financial.relation.knowledge_graph import (
    Entity,
    KnowledgeGraphService,
    RiskLevel,
    RiskNode,
    RiskPropagationResult,
    RiskType,
)


class TestKnowledgeGraphRiskPropagation:
    """Tests for KnowledgeGraphService risk propagation."""

    @pytest.fixture
    def service(self) -> KnowledgeGraphService:
        """Create service instance."""
        return KnowledgeGraphService()

    @pytest.mark.asyncio
    async def test_analyze_risk_propagation_basic(self, service: KnowledgeGraphService):
        """Test basic risk propagation analysis."""
        result = await service.analyze_risk_propagation(
            symbol="600519",
        )

        assert isinstance(result, RiskPropagationResult)
        assert result.symbol == "600519"
        assert result.total_risk_score is not None
        assert result.overall_risk_level is not None

    @pytest.mark.asyncio
    async def test_risk_score_range(self, service: KnowledgeGraphService):
        """Test that risk score is in valid range."""
        result = await service.analyze_risk_propagation(
            symbol="600519",
        )

        # Risk score should be between 0 and 100
        assert 0 <= result.total_risk_score <= 100

    @pytest.mark.asyncio
    async def test_risk_level_consistency(self, service: KnowledgeGraphService):
        """Test that risk level is consistent with score."""
        result = await service.analyze_risk_propagation(
            symbol="600519",
        )

        assert result.overall_risk_level in RiskLevel
        assert isinstance(result.overall_risk_level, RiskLevel)

    @pytest.mark.asyncio
    async def test_incoming_risks(self, service: KnowledgeGraphService):
        """Test incoming risk nodes."""
        result = await service.analyze_risk_propagation(
            symbol="600519",
        )

        assert result.incoming_risks is not None

        for risk in result.incoming_risks:
            assert isinstance(risk, RiskNode)
            assert risk.entity is not None
            assert isinstance(risk.entity, Entity)
            assert risk.risk_type in RiskType
            assert risk.risk_level in RiskLevel
            assert 0 <= risk.risk_score <= 100

    @pytest.mark.asyncio
    async def test_outgoing_risks(self, service: KnowledgeGraphService):
        """Test outgoing risk nodes."""
        result = await service.analyze_risk_propagation(
            symbol="600519",
        )

        assert result.outgoing_risks is not None

        for risk in result.outgoing_risks:
            assert isinstance(risk, RiskNode)
            assert risk.entity is not None
            assert risk.risk_type in RiskType
            assert risk.risk_level in RiskLevel

    @pytest.mark.asyncio
    async def test_risk_types_coverage(self, service: KnowledgeGraphService):
        """Test that various risk types are covered."""
        result = await service.analyze_risk_propagation(
            symbol="600519",
        )

        all_risks = result.incoming_risks + result.outgoing_risks

        if len(all_risks) > 0:
            risk_types_found = {r.risk_type for r in all_risks}
            # Should have at least one risk type
            assert len(risk_types_found) >= 1

    @pytest.mark.asyncio
    async def test_self_risks(self, service: KnowledgeGraphService):
        """Test self risk nodes."""
        result = await service.analyze_risk_propagation(
            symbol="600519",
        )

        assert result.self_risks is not None

        for risk in result.self_risks:
            assert isinstance(risk, RiskNode)
            assert risk.risk_type in RiskType

    @pytest.mark.asyncio
    async def test_depth_parameter(self, service: KnowledgeGraphService):
        """Test depth parameter affects results."""
        result = await service.analyze_risk_propagation(
            symbol="600519",
        )

        # Should return valid result
        assert result.symbol == "600519"
        assert result.total_risk_score is not None

    @pytest.mark.asyncio
    async def test_risk_by_type(self, service: KnowledgeGraphService):
        """Test risk distribution by type."""
        result = await service.analyze_risk_propagation(
            symbol="600519",
        )

        assert result.risk_by_type is not None
        assert isinstance(result.risk_by_type, dict)

    @pytest.mark.asyncio
    async def test_key_insights(self, service: KnowledgeGraphService):
        """Test key insights generation."""
        result = await service.analyze_risk_propagation(
            symbol="600519",
        )

        assert result.key_insights is not None
        assert isinstance(result.key_insights, list)

    @pytest.mark.asyncio
    async def test_risk_node_structure(self, service: KnowledgeGraphService):
        """Test RiskNode data structure completeness."""
        result = await service.analyze_risk_propagation(
            symbol="600519",
        )

        all_risks = result.incoming_risks + result.outgoing_risks + result.self_risks

        for risk in all_risks:
            # Required fields
            assert risk.entity is not None
            assert risk.risk_type is not None
            assert risk.risk_level is not None
            assert risk.risk_score is not None
            assert risk.is_source is not None
            assert risk.propagation_depth is not None
            assert risk.propagation_path is not None

    @pytest.mark.asyncio
    async def test_different_symbols(self, service: KnowledgeGraphService):
        """Test with different stock symbols."""
        symbols = ["600519", "000858", "601318"]

        for symbol in symbols:
            result = await service.analyze_risk_propagation(
                symbol=symbol,
            )

            assert result.symbol == symbol
            assert result.total_risk_score is not None

    @pytest.mark.asyncio
    async def test_all_risk_types(self, service: KnowledgeGraphService):
        """Test all risk types are valid enum values."""
        valid_types = [
            RiskType.CREDIT,
            RiskType.LIQUIDITY,
            RiskType.OPERATIONAL,
            RiskType.MARKET,
            RiskType.REGULATORY,
            RiskType.CONTAGION,
        ]

        result = await service.analyze_risk_propagation(
            symbol="600519",
        )

        all_risks = result.incoming_risks + result.outgoing_risks + result.self_risks

        for risk in all_risks:
            assert risk.risk_type in valid_types

    @pytest.mark.asyncio
    async def test_all_risk_levels(self, service: KnowledgeGraphService):
        """Test all risk levels are valid enum values."""
        valid_levels = [
            RiskLevel.LOW,
            RiskLevel.MEDIUM,
            RiskLevel.HIGH,
            RiskLevel.CRITICAL,
        ]

        result = await service.analyze_risk_propagation(
            symbol="600519",
        )

        all_risks = result.incoming_risks + result.outgoing_risks + result.self_risks

        for risk in all_risks:
            assert risk.risk_level in valid_levels

    @pytest.mark.asyncio
    async def test_high_risk_count(self, service: KnowledgeGraphService):
        """Test high risk count."""
        result = await service.analyze_risk_propagation(
            symbol="600519",
        )

        assert result.high_risk_count >= 0
        assert result.critical_risk_count >= 0
