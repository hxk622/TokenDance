"""
Vision Router 单元测试
"""
import pytest

from app.agent.llm.vision_router import (
    VisionRouter,
    VisionTaskType,
    get_vision_model,
)


class TestVisionRouter:
    """Vision Router 测试套件"""

    def test_select_model_ocr(self):
        """测试 OCR 任务模型选择"""
        model = VisionRouter.select_model(VisionTaskType.OCR_TEXT)
        assert model == "anthropic/claude-3-haiku"  # 默认选择最便宜的

    def test_select_model_chart_analysis(self):
        """测试图表分析任务模型选择"""
        model = VisionRouter.select_model(VisionTaskType.CHART_ANALYSIS)
        assert model == "anthropic/claude-3-5-sonnet"  # 平衡质量和成本

    def test_select_model_diagram(self):
        """测试科学示意图任务模型选择"""
        model = VisionRouter.select_model(VisionTaskType.DIAGRAM)
        assert model == "anthropic/claude-3-5-sonnet"

    def test_select_model_general(self):
        """测试通用图像理解任务模型选择"""
        model = VisionRouter.select_model(VisionTaskType.GENERAL_IMAGE)
        assert model == "google/gemini-pro-vision"  # 性价比之王

    def test_select_model_multimodal_doc(self):
        """测试多模态文档任务模型选择"""
        model = VisionRouter.select_model(VisionTaskType.MULTIMODAL_DOC)
        assert model == "anthropic/claude-3-opus"  # 最强能力

    def test_select_model_with_cost_constraint(self):
        """测试成本约束下的模型选择"""
        # 限制成本 < $1/1M tokens
        model = VisionRouter.select_model(
            VisionTaskType.CHART_ANALYSIS,
            max_cost=1.0
        )
        # Sonnet ($3) 超出预算，应该降级到 Gemini ($0.125)
        assert model in ["google/gemini-pro-vision", "anthropic/claude-3-haiku"]

    def test_select_model_with_quality_constraint(self):
        """测试质量约束下的模型选择"""
        # 要求最低质量 9 分
        model = VisionRouter.select_model(
            VisionTaskType.GENERAL_IMAGE,
            min_quality=9
        )
        # Gemini (8分) 不符合，应该升级到 Sonnet (9分) 或 Opus (10分)
        assert model in ["anthropic/claude-3-5-sonnet", "anthropic/claude-3-opus"]

    def test_select_model_prefer_speed(self):
        """测试优先速度的模型选择"""
        model = VisionRouter.select_model(
            VisionTaskType.CHART_ANALYSIS,
            prefer_speed=True
        )
        # Haiku (1200ms) 最快
        config = VisionRouter.MODELS[model]
        assert config.avg_latency_ms <= 2000

    def test_select_model_with_latency_constraint(self):
        """测试延迟约束下的模型选择"""
        model = VisionRouter.select_model(
            VisionTaskType.MULTIMODAL_DOC,
            max_latency_ms=3000
        )
        # Opus (4000ms) 超时，应该降级到 Sonnet (2500ms)
        assert model == "anthropic/claude-3-5-sonnet"

    def test_estimate_cost_single_image(self):
        """测试单张图片成本估算"""
        result = VisionRouter.estimate_cost(
            "anthropic/claude-3-haiku",
            num_images=1,
            avg_tokens_per_image=1000,
            output_tokens=500
        )

        assert result["model"] == "anthropic/claude-3-haiku"
        assert result["num_images"] == 1
        assert result["estimated_input_tokens"] == 1000
        assert result["estimated_output_tokens"] == 500

        # Haiku: $0.25/1M input, $1.25/1M output
        # Input: 1000 tokens * $0.25/1M = $0.00025
        # Output: 500 tokens * $1.25/1M = $0.000625
        # Total: $0.000875
        assert result["total_cost_usd"] == pytest.approx(0.000875, rel=1e-6)

    def test_estimate_cost_multiple_images(self):
        """测试多张图片成本估算"""
        result = VisionRouter.estimate_cost(
            "anthropic/claude-3-5-sonnet",
            num_images=10,
            avg_tokens_per_image=2000,
            output_tokens=1000
        )

        # Sonnet: $3/1M input, $15/1M output
        # Input: 20000 tokens * $3/1M = $0.06
        # Output: 1000 tokens * $15/1M = $0.015
        # Total: $0.075
        assert result["total_cost_usd"] == pytest.approx(0.075, rel=1e-4)

    def test_get_model_info(self):
        """测试获取模型信息"""
        info = VisionRouter.get_model_info("anthropic/claude-3-haiku")

        assert info is not None
        assert info["name"] == "anthropic/claude-3-haiku"
        assert info["cost_per_1m_input"] == 0.25
        assert info["cost_per_1m_output"] == 1.25
        assert info["quality_score"] == 7
        assert "ocr" in info["capabilities"]

    def test_get_model_info_unknown(self):
        """测试获取未知模型信息"""
        info = VisionRouter.get_model_info("unknown/model")
        assert info is None

    def test_list_models_by_task(self):
        """测试列出任务推荐模型"""
        models = VisionRouter.list_models_by_task(VisionTaskType.OCR_TEXT)

        assert len(models) > 0
        assert "anthropic/claude-3-haiku" in models

    def test_select_model_string_type(self):
        """测试字符串类型的任务类型"""
        model = VisionRouter.select_model("ocr_text")
        assert model == "anthropic/claude-3-haiku"

    def test_select_model_unknown_type(self):
        """测试未知任务类型（应该有默认行为）"""
        model = VisionRouter.select_model("unknown_task")
        # 应该返回默认模型
        assert model in VisionRouter.MODELS.keys()

    def test_model_registry_completeness(self):
        """测试模型注册表完整性"""
        # 确保所有任务映射的模型都在注册表中
        for task_type, models in VisionRouter.TASK_TO_MODELS.items():
            for model_name in models:
                assert model_name in VisionRouter.MODELS, \
                    f"Model {model_name} for task {task_type} not in registry"

    def test_get_vision_model_convenience_function(self):
        """测试便捷函数"""
        model = get_vision_model("chart_analysis", max_cost=5.0)
        assert model == "anthropic/claude-3-5-sonnet"

    def test_vision_model_cost_comparison(self):
        """测试不同模型的成本对比"""
        # 相同任务，不同模型的成本
        haiku_cost = VisionRouter.estimate_cost(
            "anthropic/claude-3-haiku",
            num_images=1,
            avg_tokens_per_image=1000,
            output_tokens=500
        )["total_cost_usd"]

        sonnet_cost = VisionRouter.estimate_cost(
            "anthropic/claude-3-5-sonnet",
            num_images=1,
            avg_tokens_per_image=1000,
            output_tokens=500
        )["total_cost_usd"]

        opus_cost = VisionRouter.estimate_cost(
            "anthropic/claude-3-opus",
            num_images=1,
            avg_tokens_per_image=1000,
            output_tokens=500
        )["total_cost_usd"]

        # 验证成本关系：Haiku < Sonnet < Opus
        assert haiku_cost < sonnet_cost
        assert sonnet_cost < opus_cost


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
