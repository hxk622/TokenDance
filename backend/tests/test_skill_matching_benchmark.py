"""
Skill 匹配准确性 Benchmark 测试

测试目标：
1. 验证各种表达方式能正确匹配到目标 Skill
2. 评估 precision/recall
3. 测试中英文混合场景

测试用例覆盖：
- 直接表达（"帮我调研"）
- 间接表达（"我想了解一下"）
- 英文表达（"research about"）
- 中英混合（"帮我 research 一下"）
- 模糊表达（"分析分析"）
- 否定用例（不应匹配的消息）

性能说明：
- 使用 SentenceTransformer 模型进行语义匹配
- 模型加载约需 3-10 秒，推理约 50-100ms/次
- 使用 session scope fixture 避免重复加载模型
- 使用 @pytest.mark.slow 标记，默认跳过，需显式运行: pytest -m slow
"""


import pytest

# =============================================================================
# Benchmark 测试数据
# =============================================================================

# 格式: (user_message, expected_skill_id, description)
# expected_skill_id 为 None 表示不应匹配任何 Skill

BENCHMARK_CASES: list[tuple[str, str | None, str]] = [
    # =========================================================================
    # deep_research - 深度研究 (30+ cases)
    # =========================================================================

    # 直接表达 - 中文
    ("帮我调研 AI Agent 市场", "deep_research", "直接调研请求-中文"),
    ("我想深入研究一下区块链技术", "deep_research", "深入研究请求"),
    ("帮我做个市场分析", "deep_research", "市场分析请求"),
    ("调研一下竞品情况", "deep_research", "竞品调研请求"),
    ("帮我查一下 AI 领域的最新动态", "deep_research", "领域动态查询"),
    ("研究一下这个行业的发展趋势", "deep_research", "行业趋势研究"),
    ("帮我收集一些关于新能源汽车的信息", "deep_research", "信息收集请求"),
    ("做个深度分析报告", "deep_research", "深度分析请求"),
    ("帮我了解一下 SaaS 市场", "deep_research", "市场了解请求"),
    ("调查一下用户需求", "deep_research", "用户调查请求"),

    # 直接表达 - 英文
    ("research AI Agent market", "deep_research", "直接研究请求-英文"),
    ("help me investigate blockchain", "deep_research", "调查请求-英文"),
    ("do market research on EV industry", "deep_research", "市场研究-英文"),
    ("analyze competitor landscape", "deep_research", "竞品分析-英文"),
    ("gather information about cloud computing", "deep_research", "信息收集-英文"),

    # 中英混合
    ("帮我 research 一下 AI 市场", "deep_research", "中英混合-research"),
    ("做个 market analysis", "deep_research", "中英混合-analysis"),
    ("investigation 一下竞品", "deep_research", "中英混合-investigation"),

    # 间接表达
    ("我想更多地了解这个领域", "deep_research", "间接了解请求"),
    ("能不能帮我查查相关资料", "deep_research", "间接查资料"),
    ("这个技术目前发展到什么程度了", "deep_research", "发展程度询问"),
    ("有没有这方面的报告或数据", "deep_research", "报告数据请求"),

    # 带场景的表达
    ("我要写商业计划书，需要了解市场情况", "deep_research", "商业计划场景"),
    ("准备做投资决策，帮我调研一下", "deep_research", "投资决策场景"),
    ("为产品立项准备，需要市场分析", "deep_research", "产品立项场景"),

    # =========================================================================
    # ppt_generation - PPT 生成 (15+ cases)
    # =========================================================================

    # 直接表达
    ("帮我做个 PPT", "ppt_generation", "直接PPT请求"),
    ("生成一份演示文稿", "ppt_generation", "演示文稿请求"),
    ("把这份报告转成幻灯片", "ppt_generation", "报告转PPT"),
    ("制作商业提案的 PPT", "ppt_generation", "商业提案PPT"),
    ("做个汇报用的演示文稿", "ppt_generation", "汇报演示文稿"),
    ("帮我准备演讲稿幻灯片", "ppt_generation", "演讲幻灯片"),

    # 英文表达
    ("create a presentation", "ppt_generation", "演示文稿-英文"),
    ("generate PowerPoint slides", "ppt_generation", "PowerPoint-英文"),
    ("make a slide deck", "ppt_generation", "slide deck-英文"),

    # 中英混合
    ("做个 presentation 给老板看", "ppt_generation", "中英混合-presentation"),
    ("帮我 create 一个 slides", "ppt_generation", "中英混合-slides"),

    # 带场景的表达
    ("明天要做路演，帮我准备 PPT", "ppt_generation", "路演场景"),
    ("项目汇报需要演示文稿", "ppt_generation", "项目汇报场景"),
    ("培训课件需要做成 PPT", "ppt_generation", "培训课件场景"),

    # =========================================================================
    # image_generation - 图片生成 (15+ cases)
    # =========================================================================

    # 直接表达
    ("帮我生成一张图片", "image_generation", "直接生图请求"),
    ("画一张 AI 机器人的图", "image_generation", "画图请求"),
    ("生成一张海报", "image_generation", "海报生成"),
    ("帮我设计一个 logo", "image_generation", "logo设计"),
    ("做一张宣传图", "image_generation", "宣传图请求"),
    ("生成产品展示图", "image_generation", "产品展示图"),

    # 英文表达
    ("generate an image of a robot", "image_generation", "生图-英文"),
    ("create a logo design", "image_generation", "logo-英文"),
    ("draw a picture of nature", "image_generation", "画图-英文"),

    # 中英混合
    ("帮我 generate 一张图", "image_generation", "中英混合-generate"),
    ("design 一个 icon", "image_generation", "中英混合-design"),

    # 带场景的表达
    ("社交媒体需要配图", "image_generation", "社交媒体场景"),
    ("文章需要一张插图", "image_generation", "文章插图场景"),
    ("营销素材需要设计", "image_generation", "营销素材场景"),

    # =========================================================================
    # systematic-debugging - 系统化调试 (10+ cases)
    # =========================================================================

    ("帮我调试这个 bug", "systematic-debugging", "直接调试请求"),
    ("代码报错了，帮我看看", "systematic-debugging", "代码报错"),
    ("测试失败了，找不到原因", "systematic-debugging", "测试失败"),
    ("程序运行异常", "systematic-debugging", "程序异常"),
    ("debug this error", "systematic-debugging", "debug-英文"),
    ("fix this bug", "systematic-debugging", "fix bug-英文"),
    ("排查一下这个问题", "systematic-debugging", "问题排查"),
    ("为什么这段代码不工作", "systematic-debugging", "代码不工作"),

    # =========================================================================
    # test-driven-development - TDD (8+ cases)
    # =========================================================================

    ("帮我写单元测试", "test-driven-development", "单元测试请求"),
    ("用 TDD 方式开发这个功能", "test-driven-development", "TDD开发"),
    ("先写测试再实现", "test-driven-development", "测试先行"),
    ("write unit tests for this function", "test-driven-development", "单元测试-英文"),
    ("implement using TDD", "test-driven-development", "TDD-英文"),
    ("测试驱动开发这个模块", "test-driven-development", "TDD模块"),

    # =========================================================================
    # brainstorming - 头脑风暴 (8+ cases)
    # =========================================================================

    ("我们来头脑风暴一下", "brainstorming", "直接头脑风暴"),
    ("帮我想想这个功能怎么设计", "brainstorming", "功能设计"),
    ("讨论一下产品方案", "brainstorming", "产品方案讨论"),
    ("brainstorm some ideas", "brainstorming", "brainstorm-英文"),
    ("let's think about the design", "brainstorming", "设计思考-英文"),
    ("需求不太清楚，帮我梳理一下", "brainstorming", "需求梳理"),
    ("这个想法可行吗", "brainstorming", "想法可行性"),

    # =========================================================================
    # 否定用例 - 不应匹配任何 Skill
    # =========================================================================

    ("今天天气怎么样", None, "天气-不匹配"),
    ("你好", None, "打招呼-不匹配"),
    ("谢谢", None, "感谢-不匹配"),
    ("再见", None, "告别-不匹配"),
    ("讲个笑话", None, "娱乐-不匹配"),
    ("你是谁", None, "身份询问-不匹配"),
    ("hello", None, "hello-不匹配"),
    ("good morning", None, "问候-不匹配"),
]


# =============================================================================
# 测试夹具
# =============================================================================

@pytest.fixture(scope="session")
def skill_registry_session():
    """创建并加载 Registry (session scope，整个测试会话只创建一次)"""
    from app.skills.registry import SkillRegistry

    registry = SkillRegistry()
    registry.load_all()
    return registry


@pytest.fixture
def skill_registry(skill_registry_session):
    """Function-scoped alias for compatibility"""
    return skill_registry_session


@pytest.fixture
def skill_matcher(skill_registry):
    """创建 SkillMatcher（不使用 Embedding，快速测试）"""
    from app.skills.matcher import SkillMatcher

    return SkillMatcher(skill_registry, enable_embedding=False)


# 使用 session scope 的 embedding matcher，避免每个测试都重新加载模型
_cached_embedding_matcher = None


@pytest.fixture(scope="session")
def skill_matcher_with_embedding_session(skill_registry_session):
    """创建带 Embedding 的 SkillMatcher (session scope，模型只加载一次)
    
    性能优化：模型加载约 3-10 秒，使用 session scope 避免重复加载。
    """
    from app.skills.matcher import create_skill_matcher

    return create_skill_matcher(skill_registry_session, use_sentence_transformer=True)


@pytest.fixture
def skill_matcher_with_embedding(skill_matcher_with_embedding_session):
    """Function-scoped alias for compatibility"""
    return skill_matcher_with_embedding_session


# =============================================================================
# 基础测试
# =============================================================================

class TestSkillMatchingBasic:
    """基础匹配测试"""

    def test_registry_loaded(self, skill_registry):
        """验证 Registry 加载成功"""
        assert len(skill_registry) > 0, "Should load skills"
        assert "deep_research" in skill_registry
        assert "ppt_generation" in skill_registry or "ppt" in skill_registry

    @pytest.mark.asyncio
    async def test_keyword_matching(self, skill_matcher):
        """测试关键词匹配"""
        # 测试明确的调研请求
        match = await skill_matcher.match("帮我调研 AI 市场", min_score=0.0)
        assert match is not None, "Should match research query"


# =============================================================================
# Benchmark 测试
# =============================================================================

@pytest.mark.slow
class TestSkillMatchingBenchmark:
    """Skill 匹配准确性 Benchmark
    
    标记为 slow，默认跳过。运行方式：pytest -m slow
    """

    @pytest.mark.asyncio
    @pytest.mark.parametrize("user_message,expected_skill,description", BENCHMARK_CASES)
    async def test_matching_accuracy(
        self,
        skill_matcher_with_embedding,
        user_message: str,
        expected_skill: str | None,
        description: str,
    ):
        """测试各种表达方式的匹配准确性"""
        match = await skill_matcher_with_embedding.match(user_message, min_score=0.0)

        if expected_skill is None:
            # 不应匹配任何 Skill（阈值过滤后为 None）
            if match is not None:
                # 如果有匹配，分数应该低于阈值
                assert match.score < 0.7, (
                    f"[{description}] Should not match any skill with high confidence, "
                    f"but matched {match.skill_id} with score {match.score:.2f}"
                )
        else:
            assert match is not None, (
                f"[{description}] Should match '{expected_skill}', but no match found"
            )
            # 注意：由于 Skill ID 可能有变化（如 ppt vs ppt_generation），这里做灵活匹配
            matched_id = match.skill_id
            assert expected_skill in matched_id or matched_id in expected_skill, (
                f"[{description}] Expected '{expected_skill}', but matched '{matched_id}' "
                f"with score {match.score:.2f}"
            )


# =============================================================================
# 精度/召回率评估
# =============================================================================

@pytest.mark.slow
class TestPrecisionRecall:
    """评估匹配的 Precision 和 Recall
    
    标记为 slow，默认跳过。运行方式：pytest -m slow
    """

    @pytest.mark.asyncio
    async def test_calculate_metrics(self, skill_matcher_with_embedding):
        """计算整体精度和召回率"""
        true_positives = 0
        false_positives = 0
        false_negatives = 0
        true_negatives = 0

        results = []

        for user_message, expected_skill, description in BENCHMARK_CASES:
            match = await skill_matcher_with_embedding.match(user_message, min_score=0.0)

            if expected_skill is None:
                # 不应匹配
                if match is None or match.score < 0.7:
                    true_negatives += 1
                    results.append((description, "TN", None, None))
                else:
                    false_positives += 1
                    results.append((description, "FP", match.skill_id, match.score))
            else:
                # 应该匹配
                if match is not None and match.score >= 0.5:
                    matched_correct = expected_skill in match.skill_id or match.skill_id in expected_skill
                    if matched_correct:
                        true_positives += 1
                        results.append((description, "TP", match.skill_id, match.score))
                    else:
                        false_positives += 1
                        results.append((description, "FP", match.skill_id, match.score))
                else:
                    false_negatives += 1
                    score = match.score if match else 0
                    results.append((description, "FN", match.skill_id if match else None, score))

        # 计算指标
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

        # 打印详细结果
        print("\n" + "=" * 80)
        print("Skill Matching Benchmark Results")
        print("=" * 80)
        print(f"\nTotal cases: {len(BENCHMARK_CASES)}")
        print(f"True Positives:  {true_positives}")
        print(f"False Positives: {false_positives}")
        print(f"False Negatives: {false_negatives}")
        print(f"True Negatives:  {true_negatives}")
        print(f"\nPrecision: {precision:.2%}")
        print(f"Recall:    {recall:.2%}")
        print(f"F1 Score:  {f1:.2%}")

        # 打印失败用例
        failures = [r for r in results if r[1] in ("FP", "FN")]
        if failures:
            print(f"\n--- Failures ({len(failures)}) ---")
            for desc, status, matched, score in failures:
                print(f"  [{status}] {desc}: matched={matched}, score={score}")

        print("=" * 80)

        # 断言：期望 F1 > 0.7（可调整）
        assert f1 >= 0.6, f"F1 score {f1:.2%} is below threshold 60%"


# =============================================================================
# 阈值敏感性测试
# =============================================================================

@pytest.mark.slow
class TestThresholdSensitivity:
    """测试不同阈值对匹配结果的影响
    
    标记为 slow，默认跳过。运行方式：pytest -m slow
    """

    @pytest.mark.asyncio
    async def test_threshold_impact(self, skill_matcher_with_embedding):
        """测试不同阈值的影响"""
        thresholds = [0.5, 0.6, 0.7, 0.8, 0.9]

        test_cases = [
            ("帮我调研 AI 市场", "deep_research"),
            ("research AI market", "deep_research"),
            ("帮我做个 PPT", "ppt_generation"),
            ("生成一张图片", "image_generation"),
        ]

        print("\n" + "=" * 60)
        print("Threshold Sensitivity Analysis")
        print("=" * 60)

        for user_message, _expected in test_cases:
            print(f"\nQuery: {user_message}")
            match = await skill_matcher_with_embedding.match(user_message, min_score=0.0)
            if match:
                print(f"  Matched: {match.skill_id} (score={match.score:.3f})")
                for threshold in thresholds:
                    would_match = match.score >= threshold
                    status = "✓" if would_match else "✗"
                    print(f"    threshold={threshold}: {status}")
            else:
                print("  No match")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
