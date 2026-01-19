"""
Pre-flight Check API Tests

测试意图验证相关 API 端点：
- POST /api/v1/sessions/preflight - 验证用户意图
"""

from unittest.mock import AsyncMock, patch

import pytest


class TestPreflightCheck:
    """Pre-flight check API tests"""

    def test_preflight_complete_intent(self, test_client):
        """测试完整意图验证"""
        # Mock the IntentValidationService
        mock_response = {
            "is_complete": True,
            "confidence_score": 0.9,
            "missing_info": [],
            "suggested_questions": [],
            "reasoning": "任务清晰，包含主题和格式"
        }

        with patch(
            "app.api.v1.session.IntentValidationService"
        ) as mock_service_class:
            mock_service = AsyncMock()
            mock_service.validate_intent = AsyncMock(return_value=mock_response)
            mock_service_class.return_value = mock_service

            response = test_client.post(
                "/api/v1/sessions/preflight",
                json={"user_input": "生成一份关于AI市场的PPT"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["is_complete"] is True
            assert data["confidence_score"] == 0.9
            assert data["missing_info"] == []

    def test_preflight_incomplete_intent(self, test_client):
        """测试不完整意图验证"""
        mock_response = {
            "is_complete": False,
            "confidence_score": 0.8,
            "missing_info": ["PPT主题或内容", "目标受众"],
            "suggested_questions": ["这份PPT的主题是什么？", "PPT的目标受众是谁？"],
            "reasoning": "缺少关键的主题信息"
        }

        with patch(
            "app.api.v1.session.IntentValidationService"
        ) as mock_service_class:
            mock_service = AsyncMock()
            mock_service.validate_intent = AsyncMock(return_value=mock_response)
            mock_service_class.return_value = mock_service

            response = test_client.post(
                "/api/v1/sessions/preflight",
                json={"user_input": "生成一份PPT"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["is_complete"] is False
            assert len(data["missing_info"]) > 0
            assert len(data["suggested_questions"]) > 0

    def test_preflight_vague_intent(self, test_client):
        """测试模糊意图验证"""
        mock_response = {
            "is_complete": False,
            "confidence_score": 0.95,
            "missing_info": ["具体任务内容"],
            "suggested_questions": ["您需要什么帮助？请描述具体任务"],
            "reasoning": "意图过于模糊"
        }

        with patch(
            "app.api.v1.session.IntentValidationService"
        ) as mock_service_class:
            mock_service = AsyncMock()
            mock_service.validate_intent = AsyncMock(return_value=mock_response)
            mock_service_class.return_value = mock_service

            response = test_client.post(
                "/api/v1/sessions/preflight",
                json={"user_input": "帮我"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["is_complete"] is False
            assert "意图过于模糊" in (data.get("reasoning") or "")

    def test_preflight_with_context(self, test_client):
        """测试带上下文的意图验证"""
        mock_response = {
            "is_complete": True,
            "confidence_score": 0.85,
            "missing_info": [],
            "suggested_questions": [],
            "reasoning": "任务清晰"
        }

        with patch(
            "app.api.v1.session.IntentValidationService"
        ) as mock_service_class:
            mock_service = AsyncMock()
            mock_service.validate_intent = AsyncMock(return_value=mock_response)
            mock_service_class.return_value = mock_service

            response = test_client.post(
                "/api/v1/sessions/preflight",
                json={
                    "user_input": "继续上次的任务",
                    "context": {"workspace": "research", "last_task": "market_analysis"}
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["is_complete"] is True

    def test_preflight_empty_input(self, test_client):
        """测试空输入验证"""
        response = test_client.post(
            "/api/v1/sessions/preflight",
            json={"user_input": ""}
        )

        # Should return 422 Validation Error for empty input
        assert response.status_code == 422

    def test_preflight_missing_input(self, test_client):
        """测试缺少输入字段"""
        response = test_client.post(
            "/api/v1/sessions/preflight",
            json={}
        )

        # Should return 422 Validation Error for missing field
        assert response.status_code == 422

    def test_preflight_service_unavailable(self, test_client):
        """测试服务不可用时的处理"""
        with patch(
            "app.api.v1.session.IntentValidationService"
        ) as mock_service_class:
            mock_service_class.side_effect = ValueError(
                "No LLM API key configured"
            )

            response = test_client.post(
                "/api/v1/sessions/preflight",
                json={"user_input": "测试任务"}
            )

            # Should return 503 Service Unavailable
            assert response.status_code == 503

    def test_preflight_llm_error_fallback(self, test_client):
        """测试LLM错误时的降级处理"""
        with patch(
            "app.api.v1.session.IntentValidationService"
        ) as mock_service_class:
            mock_service = AsyncMock()
            mock_service.validate_intent = AsyncMock(
                side_effect=Exception("LLM API error")
            )
            mock_service_class.return_value = mock_service

            response = test_client.post(
                "/api/v1/sessions/preflight",
                json={"user_input": "测试任务"}
            )

            # Should return 200 with permissive response (fallback)
            assert response.status_code == 200
            data = response.json()
            assert data["is_complete"] is True
            assert data["confidence_score"] == 0.0


# ==================== Schema Validation Tests ====================

class TestIntentValidationSchema:
    """Intent validation schema tests"""

    def test_intent_validation_response_schema(self):
        """测试响应 schema 验证"""
        from app.schemas.intent import IntentValidationResponse

        response = IntentValidationResponse(
            is_complete=True,
            confidence_score=0.9,
            missing_info=[],
            suggested_questions=[],
            reasoning="测试"
        )

        assert response.is_complete is True
        assert response.confidence_score == 0.9

    def test_intent_validation_request_schema(self):
        """测试请求 schema 验证"""
        from app.schemas.intent import IntentValidationRequest

        request = IntentValidationRequest(
            user_input="测试输入",
            context={"key": "value"}
        )

        assert request.user_input == "测试输入"
        assert request.context == {"key": "value"}

    def test_intent_validation_confidence_bounds(self):
        """测试置信度边界验证"""
        from pydantic import ValidationError

        from app.schemas.intent import IntentValidationResponse

        # Valid: 0.0
        response = IntentValidationResponse(
            is_complete=False,
            confidence_score=0.0,
            missing_info=[],
            suggested_questions=[]
        )
        assert response.confidence_score == 0.0

        # Valid: 1.0
        response = IntentValidationResponse(
            is_complete=True,
            confidence_score=1.0,
            missing_info=[],
            suggested_questions=[]
        )
        assert response.confidence_score == 1.0

        # Invalid: > 1.0
        with pytest.raises(ValidationError):
            IntentValidationResponse(
                is_complete=True,
                confidence_score=1.5,
                missing_info=[],
                suggested_questions=[]
            )

        # Invalid: < 0.0
        with pytest.raises(ValidationError):
            IntentValidationResponse(
                is_complete=True,
                confidence_score=-0.1,
                missing_info=[],
                suggested_questions=[]
            )
