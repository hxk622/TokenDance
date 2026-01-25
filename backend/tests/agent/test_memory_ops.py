"""
Memory Operations Tools (MemAct) 测试

测试内容：
1. register_block: 注册内容块
2. MemRetainTool: 标记内容块为重要
3. MemDeleteTool: 删除内容块
4. MemSummarizeTool: 压缩内容块
5. MemPinTool: 固定到长期记忆
6. MemListBlocksTool: 列出所有内容块
"""

import pytest

from app.agent.tools.builtin.memory_ops import (
    MemDeleteTool,
    MemListBlocksTool,
    MemPinTool,
    MemRetainTool,
    MemSummarizeTool,
    clear_block_store,
    get_block_store,
    register_block,
)


@pytest.fixture(autouse=True)
def setup_and_teardown():
    """每个测试前后清理 block store"""
    clear_block_store()
    yield
    clear_block_store()


class TestRegisterBlock:
    """测试 register_block 函数"""

    def test_register_single_block(self):
        """测试注册单个 block"""
        block_id = register_block("Hello World", "user_message")

        assert block_id == "b_0001"
        store = get_block_store()
        assert block_id in store
        assert store[block_id]["content"] == "Hello World"
        assert store[block_id]["block_type"] == "user_message"
        assert store[block_id]["status"] == "active"

    def test_register_multiple_blocks(self):
        """测试注册多个 blocks"""
        id1 = register_block("Message 1", "user_message")
        id2 = register_block("Message 2", "assistant_message")
        id3 = register_block("Tool output", "tool_result")

        assert id1 == "b_0001"
        assert id2 == "b_0002"
        assert id3 == "b_0003"

        store = get_block_store()
        assert len(store) == 3

    def test_register_with_metadata(self):
        """测试带 metadata 注册"""
        block_id = register_block(
            "Content",
            "tool_result",
            metadata={"tool_name": "web_search", "query": "AI"}
        )

        store = get_block_store()
        assert store[block_id]["metadata"]["tool_name"] == "web_search"

    def test_token_count_estimation(self):
        """测试 token 数估算"""
        content = "这是一段中文内容" * 10  # ~80 字符
        block_id = register_block(content, "user_message")

        store = get_block_store()
        # 估算: len(content) // 3
        assert store[block_id]["token_count"] == len(content) // 3


class TestMemRetainTool:
    """测试 MemRetainTool"""

    @pytest.fixture
    def tool(self):
        return MemRetainTool()

    @pytest.mark.asyncio
    async def test_retain_existing_block(self, tool):
        """测试保留已存在的 block"""
        block_id = register_block("Important data", "tool_result")

        result = await tool.execute(block_id=block_id, reason="Contains key metrics")

        assert result["success"] is True
        assert result["retained"] == block_id

        store = get_block_store()
        assert store[block_id]["status"] == "retained"
        assert store[block_id]["importance"] == 0.8  # 0.5 + 0.3
        assert store[block_id]["metadata"]["retain_reason"] == "Contains key metrics"

    @pytest.mark.asyncio
    async def test_retain_nonexistent_block(self, tool):
        """测试保留不存在的 block"""
        result = await tool.execute(block_id="nonexistent", reason="Test")

        assert result["success"] is False
        assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_retain_deleted_block(self, tool):
        """测试保留已删除的 block"""
        block_id = register_block("Data", "tool_result")
        store = get_block_store()
        store[block_id]["status"] = "deleted"

        result = await tool.execute(block_id=block_id, reason="Test")

        assert result["success"] is False
        assert "deleted" in result["error"]

    @pytest.mark.asyncio
    async def test_retain_missing_block_id(self, tool):
        """测试缺少 block_id"""
        result = await tool.execute(reason="Test")

        assert result["success"] is False
        assert "required" in result["error"]


class TestMemDeleteTool:
    """测试 MemDeleteTool"""

    @pytest.fixture
    def tool(self):
        return MemDeleteTool()

    @pytest.mark.asyncio
    async def test_delete_existing_block(self, tool):
        """测试删除已存在的 block"""
        block_id = register_block("Temporary data", "tool_result")

        result = await tool.execute(block_id=block_id, reason="No longer needed")

        assert result["success"] is True
        assert result["deleted"] == block_id
        assert result["tokens_freed"] > 0

        store = get_block_store()
        assert store[block_id]["status"] == "deleted"
        assert store[block_id]["deleted_at"] is not None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_block(self, tool):
        """测试删除不存在的 block"""
        result = await tool.execute(block_id="nonexistent", reason="Test")

        assert result["success"] is False
        assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_delete_retained_block(self, tool):
        """测试删除已保留的 block（应该失败）"""
        block_id = register_block("Important data", "tool_result")
        store = get_block_store()
        store[block_id]["status"] = "retained"

        result = await tool.execute(block_id=block_id, reason="Test")

        assert result["success"] is False
        assert "retained" in result["error"]

    @pytest.mark.asyncio
    async def test_delete_already_deleted_block(self, tool):
        """测试删除已删除的 block"""
        block_id = register_block("Data", "tool_result")
        store = get_block_store()
        store[block_id]["status"] = "deleted"

        result = await tool.execute(block_id=block_id, reason="Test")

        assert result["success"] is False
        assert "already deleted" in result["error"]


class TestMemSummarizeTool:
    """测试 MemSummarizeTool"""

    @pytest.fixture
    def tool(self):
        return MemSummarizeTool()

    @pytest.mark.asyncio
    async def test_summarize_multiple_blocks(self, tool):
        """测试压缩多个 blocks"""
        id1 = register_block("Search result 1: Market size is $50B" * 10, "tool_result")
        id2 = register_block("Search result 2: Growth rate is 15%" * 10, "tool_result")

        result = await tool.execute(
            block_ids=[id1, id2],
            summary="Key findings: Market size $50B, growth rate 15%"
        )

        assert result["success"] is True
        assert result["summary_id"].startswith("b_")
        assert result["original_tokens"] > result["compressed_tokens"]
        assert result["compression_ratio"] < 1.0
        assert result["summarized_blocks"] == [id1, id2]

        # 验证原始 blocks 状态
        store = get_block_store()
        assert store[id1]["status"] == "summarized"
        assert store[id2]["status"] == "summarized"
        assert store[result["summary_id"]]["status"] == "active"
        assert store[result["summary_id"]]["block_type"] == "summary"

    @pytest.mark.asyncio
    async def test_summarize_with_missing_blocks(self, tool):
        """测试压缩包含不存在的 block"""
        id1 = register_block("Data", "tool_result")

        result = await tool.execute(
            block_ids=[id1, "nonexistent"],
            summary="Summary"
        )

        assert result["success"] is False
        assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_summarize_empty_block_ids(self, tool):
        """测试空 block_ids"""
        result = await tool.execute(block_ids=[], summary="Summary")

        assert result["success"] is False
        assert "required" in result["error"]

    @pytest.mark.asyncio
    async def test_summarize_empty_summary(self, tool):
        """测试空 summary"""
        id1 = register_block("Data", "tool_result")

        result = await tool.execute(block_ids=[id1], summary="")

        assert result["success"] is False
        assert "required" in result["error"]

    @pytest.mark.asyncio
    async def test_summarize_preserves_source_block_ids(self, tool):
        """测试摘要保留源 block IDs"""
        id1 = register_block("Data 1", "tool_result")
        id2 = register_block("Data 2", "tool_result")

        result = await tool.execute(
            block_ids=[id1, id2],
            summary="Combined summary"
        )

        store = get_block_store()
        summary_block = store[result["summary_id"]]
        assert summary_block["source_block_ids"] == [id1, id2]


class TestMemPinTool:
    """测试 MemPinTool"""

    @pytest.fixture
    def tool(self):
        return MemPinTool()

    @pytest.mark.asyncio
    async def test_pin_preference(self, tool):
        """测试固定用户偏好"""
        result = await tool.execute(
            content="用户偏好蓝色配色方案",
            memory_type="preference",
            importance=0.9
        )

        assert result["success"] is True
        assert result["memory_id"].startswith("b_")
        assert result["memory_type"] == "preference"
        assert result["importance"] == 0.9

        store = get_block_store()
        block = store[result["memory_id"]]
        assert block["status"] == "pinned"
        assert block["block_type"] == "memory_preference"

    @pytest.mark.asyncio
    async def test_pin_fact(self, tool):
        """测试固定事实"""
        result = await tool.execute(
            content="用户公司名称: TechCorp",
            memory_type="fact"
        )

        assert result["success"] is True
        assert result["memory_type"] == "fact"
        assert result["importance"] == 0.7  # default

    @pytest.mark.asyncio
    async def test_pin_pattern(self, tool):
        """测试固定行为模式"""
        result = await tool.execute(
            content="用户通常在周一上午做周报",
            memory_type="pattern"
        )

        assert result["success"] is True
        assert result["memory_type"] == "pattern"

    @pytest.mark.asyncio
    async def test_pin_skill(self, tool):
        """测试固定技能模式"""
        result = await tool.execute(
            content="深度研究流程: web_search -> read_url -> summarize",
            memory_type="skill"
        )

        assert result["success"] is True
        assert result["memory_type"] == "skill"

    @pytest.mark.asyncio
    async def test_pin_invalid_type(self, tool):
        """测试无效的 memory_type"""
        result = await tool.execute(
            content="Content",
            memory_type="invalid_type"
        )

        assert result["success"] is False
        assert "Invalid memory_type" in result["error"]

    @pytest.mark.asyncio
    async def test_pin_empty_content(self, tool):
        """测试空内容"""
        result = await tool.execute(content="", memory_type="preference")

        assert result["success"] is False
        assert "required" in result["error"]


class TestMemListBlocksTool:
    """测试 MemListBlocksTool"""

    @pytest.fixture
    def tool(self):
        return MemListBlocksTool()

    @pytest.mark.asyncio
    async def test_list_empty_store(self, tool):
        """测试列出空存储"""
        result = await tool.execute()

        assert result["success"] is True
        assert result["total_blocks"] == 0
        assert result["blocks"] == []

    @pytest.mark.asyncio
    async def test_list_all_blocks(self, tool):
        """测试列出所有 blocks"""
        register_block("Message 1", "user_message")
        register_block("Message 2", "assistant_message")
        register_block("Tool output", "tool_result")

        result = await tool.execute()

        assert result["success"] is True
        assert result["total_blocks"] == 3
        assert len(result["blocks"]) == 3

    @pytest.mark.asyncio
    async def test_list_excludes_deleted_by_default(self, tool):
        """测试默认不包含已删除的 blocks"""
        id1 = register_block("Active", "user_message")
        id2 = register_block("Deleted", "user_message")

        store = get_block_store()
        store[id2]["status"] = "deleted"

        result = await tool.execute()

        assert result["total_blocks"] == 1
        assert result["blocks"][0]["block_id"] == id1

    @pytest.mark.asyncio
    async def test_list_includes_deleted(self, tool):
        """测试包含已删除的 blocks"""
        register_block("Active", "user_message")
        id2 = register_block("Deleted", "user_message")

        store = get_block_store()
        store[id2]["status"] = "deleted"

        result = await tool.execute(include_deleted=True)

        assert result["total_blocks"] == 2

    @pytest.mark.asyncio
    async def test_list_filter_by_status(self, tool):
        """测试按状态过滤"""
        id1 = register_block("Active", "user_message")
        id2 = register_block("Retained", "user_message")

        store = get_block_store()
        store[id2]["status"] = "retained"

        result = await tool.execute(status_filter="retained")

        assert result["total_blocks"] == 1
        assert result["blocks"][0]["block_id"] == id2

    @pytest.mark.asyncio
    async def test_list_calculates_tokens(self, tool):
        """测试 token 统计"""
        register_block("A" * 300, "user_message")  # ~100 tokens
        register_block("B" * 300, "assistant_message")  # ~100 tokens

        result = await tool.execute()

        assert result["total_tokens"] > 0
        assert result["active_tokens"] > 0

    @pytest.mark.asyncio
    async def test_list_preview_truncation(self, tool):
        """测试内容预览截断"""
        long_content = "X" * 200
        register_block(long_content, "user_message")

        result = await tool.execute()

        preview = result["blocks"][0]["preview"]
        assert len(preview) <= 103  # 100 + "..."
        assert preview.endswith("...")


class TestMemActWorkflow:
    """测试完整的 MemAct 工作流"""

    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """测试完整工作流：注册 -> 保留 -> 压缩 -> 固定"""
        retain_tool = MemRetainTool()
        summarize_tool = MemSummarizeTool()
        pin_tool = MemPinTool()
        list_tool = MemListBlocksTool()

        # 1. 模拟搜索结果注册
        id1 = register_block("市场规模: 全球 AI 市场预计 2025 年达 $500B", "tool_result")
        id2 = register_block("增长率: 年复合增长率 25%", "tool_result")
        id3 = register_block("主要玩家: OpenAI, Anthropic, Google", "tool_result")

        # 2. 标记重要内容
        await retain_tool.execute(block_id=id1, reason="核心数据点")

        # 3. 压缩非关键内容
        result = await summarize_tool.execute(
            block_ids=[id2, id3],
            summary="AI市场增长25%，主要玩家包括OpenAI等"
        )
        summary_id = result["summary_id"]

        # 4. 固定关键发现到长期记忆
        await pin_tool.execute(
            content="AI市场规模$500B，增长率25%",
            memory_type="fact",
            importance=0.8
        )

        # 5. 查看最终状态
        list_result = await list_tool.execute()

        # 验证
        store = get_block_store()

        # id1 被保留
        assert store[id1]["status"] == "retained"

        # id2, id3 被压缩
        assert store[id2]["status"] == "summarized"
        assert store[id3]["status"] == "summarized"

        # 摘要是活跃的
        assert store[summary_id]["status"] == "active"

        # 有一个 pinned 的长期记忆
        pinned_blocks = [b for b in store.values() if b["status"] == "pinned"]
        assert len(pinned_blocks) == 1
