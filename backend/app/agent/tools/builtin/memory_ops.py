"""
Memory Operations Tools (MemAct Memory-as-Action)

借鉴 MemAct 框架理念，将记忆管理暴露为 Agent 可主动调用的工具。
让 Agent 可以根据当前任务状态决定保留/删除/压缩哪些信息。

工具列表：
- mem_retain: 标记内容块为重要，优先保留
- mem_delete: 删除不再需要的内容块
- mem_summarize: 压缩多个内容块为摘要
- mem_pin: 将内容固定到长期记忆
"""

from datetime import datetime
from typing import Any

from app.agent.tools.base import BaseTool
from app.agent.tools.risk import OperationCategory, RiskLevel
from app.core.logging import get_logger

logger = get_logger(__name__)


# ============================================================================
# 全局 Block 存储（运行时）
# 实际生产环境应该集成到 ContextManager 或数据库
# ============================================================================

_block_store: dict[str, dict[str, Any]] = {}
_block_counter: int = 0


def _generate_block_id() -> str:
    """生成唯一的 block_id"""
    global _block_counter
    _block_counter += 1
    return f"b_{_block_counter:04d}"


def get_block_store() -> dict[str, dict[str, Any]]:
    """获取 block 存储（供外部访问）"""
    return _block_store


def register_block(content: str, block_type: str, metadata: dict | None = None) -> str:
    """注册一个新的 block（供 ContextManager 调用）

    Args:
        content: 内容
        block_type: 类型 (user_message, assistant_message, tool_result, summary)
        metadata: 额外元数据

    Returns:
        block_id: 新创建的 block ID
    """
    block_id = _generate_block_id()
    _block_store[block_id] = {
        "block_id": block_id,
        "content": content,
        "block_type": block_type,
        "token_count": len(content) // 3,  # 粗略估算
        "importance": 0.5,
        "status": "active",
        "source_block_ids": [],
        "metadata": metadata or {},
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "deleted_at": None,
    }
    logger.debug(f"Registered block: {block_id} ({block_type}, {len(content)} chars)")
    return block_id


def clear_block_store() -> None:
    """清空 block 存储（用于测试）"""
    global _block_store, _block_counter
    _block_store = {}
    _block_counter = 0


# ============================================================================
# Memory Tools
# ============================================================================


class MemRetainTool(BaseTool):
    """标记内容块为重要，优先保留

    当 Agent 认为某个内容块包含重要信息时，可以调用此工具将其标记为"保留"。
    被标记的内容块在自动压缩时会被优先保留。
    """

    name = "mem_retain"
    description = (
        "标记一个 Context 内容块为重要，优先保留不被压缩。"
        "当你认为某个搜索结果、工具输出或对话内容很重要时使用。"
        "参数: block_id (内容块ID), reason (保留原因)"
    )
    parameters = {
        "type": "object",
        "properties": {
            "block_id": {
                "type": "string",
                "description": "要保留的内容块 ID (如 b_001, b_002)"
            },
            "reason": {
                "type": "string",
                "description": "保留原因，解释为什么这个内容块很重要"
            }
        },
        "required": ["block_id", "reason"]
    }

    risk_level = RiskLevel.LOW
    operation_categories: list[OperationCategory] = []  # Memory operation, no external effects

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        block_id = kwargs.get("block_id", "")
        reason = kwargs.get("reason", "")

        if not block_id:
            return {"success": False, "error": "block_id is required"}

        if block_id not in _block_store:
            return {
                "success": False,
                "error": f"Block {block_id} not found. Available: {list(_block_store.keys())[:5]}"
            }

        block = _block_store[block_id]

        # 检查状态
        if block["status"] == "deleted":
            return {"success": False, "error": f"Block {block_id} has been deleted"}

        # 更新状态和重要性
        block["status"] = "retained"
        block["importance"] = min(1.0, block["importance"] + 0.3)  # 提升重要性
        block["updated_at"] = datetime.now().isoformat()
        block["metadata"]["retain_reason"] = reason

        logger.info(f"Block {block_id} marked as retained: {reason}")

        return {
            "success": True,
            "retained": block_id,
            "new_importance": block["importance"],
            "message": f"已将内容块 {block_id} 标记为重要，优先保留"
        }


class MemDeleteTool(BaseTool):
    """删除不再需要的内容块

    当 Agent 确定某个内容块不再需要时，可以调用此工具删除它以释放 Context 空间。
    删除是软删除，24小时内可恢复。
    """

    name = "mem_delete"
    description = (
        "删除一个不再需要的 Context 内容块，释放 Context 空间。"
        "删除是软删除，24小时内可恢复。"
        "参数: block_id (内容块ID), reason (删除原因)"
    )
    parameters = {
        "type": "object",
        "properties": {
            "block_id": {
                "type": "string",
                "description": "要删除的内容块 ID"
            },
            "reason": {
                "type": "string",
                "description": "删除原因，解释为什么不再需要这个内容块"
            }
        },
        "required": ["block_id", "reason"]
    }

    risk_level = RiskLevel.MEDIUM  # 中等风险，因为会删除数据
    operation_categories: list[OperationCategory] = []  # Memory operation, no external effects

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        block_id = kwargs.get("block_id", "")
        reason = kwargs.get("reason", "")

        if not block_id:
            return {"success": False, "error": "block_id is required"}

        if block_id not in _block_store:
            return {
                "success": False,
                "error": f"Block {block_id} not found"
            }

        block = _block_store[block_id]

        # 检查是否已删除
        if block["status"] == "deleted":
            return {"success": False, "error": f"Block {block_id} is already deleted"}

        # 检查是否被标记为保留
        if block["status"] == "retained":
            return {
                "success": False,
                "error": f"Block {block_id} is marked as retained. Use mem_retain to unmark first."
            }

        # 软删除
        tokens_freed = block["token_count"]
        block["status"] = "deleted"
        block["deleted_at"] = datetime.now().isoformat()
        block["updated_at"] = datetime.now().isoformat()
        block["metadata"]["delete_reason"] = reason

        logger.info(f"Block {block_id} soft-deleted: {reason}")

        return {
            "success": True,
            "deleted": block_id,
            "tokens_freed": tokens_freed,
            "message": f"已删除内容块 {block_id}，释放约 {tokens_freed} tokens（24h 内可恢复）"
        }


class MemSummarizeTool(BaseTool):
    """压缩多个内容块为摘要

    当 Context 过长时，Agent 可以调用此工具将多个内容块压缩为一个摘要。
    原始内容块会被标记为"已压缩"，但保留以供需要时恢复。
    """

    name = "mem_summarize"
    description = (
        "将多个 Context 内容块压缩为一个摘要，减少 Context 长度。"
        "适合压缩已经提取关键信息的搜索结果、工具输出等。"
        "参数: block_ids (要压缩的内容块ID列表), summary (摘要内容), target_tokens (目标token数)"
    )
    parameters = {
        "type": "object",
        "properties": {
            "block_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "要压缩的内容块 ID 列表"
            },
            "summary": {
                "type": "string",
                "description": "压缩后的摘要内容，需包含原始内容的关键信息"
            },
            "target_tokens": {
                "type": "integer",
                "description": "目标 token 数（可选，默认自动计算）",
                "default": 200
            }
        },
        "required": ["block_ids", "summary"]
    }

    risk_level = RiskLevel.MEDIUM
    operation_categories: list[OperationCategory] = []  # Memory operation, no external effects

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        block_ids = kwargs.get("block_ids", [])
        summary = kwargs.get("summary", "")
        # target_tokens is available for future use but not enforced currently
        _ = kwargs.get("target_tokens", 200)

        if not block_ids:
            return {"success": False, "error": "block_ids is required"}

        if not summary:
            return {"success": False, "error": "summary is required"}

        # 验证所有 block_ids 存在
        missing_ids = [bid for bid in block_ids if bid not in _block_store]
        if missing_ids:
            return {
                "success": False,
                "error": f"Blocks not found: {missing_ids}"
            }

        # 计算原始 token 数
        original_tokens = 0
        for bid in block_ids:
            block = _block_store[bid]
            if block["status"] not in ("deleted", "summarized"):
                original_tokens += block["token_count"]

        # 创建摘要 block
        summary_block_id = _generate_block_id()
        summary_tokens = len(summary) // 3

        _block_store[summary_block_id] = {
            "block_id": summary_block_id,
            "content": summary,
            "block_type": "summary",
            "token_count": summary_tokens,
            "importance": 0.7,  # 摘要默认较高重要性
            "status": "active",
            "source_block_ids": block_ids,
            "metadata": {
                "original_tokens": original_tokens,
                "compression_ratio": summary_tokens / original_tokens if original_tokens > 0 else 1.0
            },
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "deleted_at": None,
        }

        # 标记原始 blocks 为已压缩
        for bid in block_ids:
            block = _block_store[bid]
            if block["status"] not in ("deleted", "summarized"):
                block["status"] = "summarized"
                block["updated_at"] = datetime.now().isoformat()
                block["metadata"]["summarized_to"] = summary_block_id

        compression_ratio = summary_tokens / original_tokens if original_tokens > 0 else 1.0

        logger.info(
            f"Summarized {len(block_ids)} blocks into {summary_block_id}: "
            f"{original_tokens} -> {summary_tokens} tokens ({compression_ratio:.1%})"
        )

        return {
            "success": True,
            "summary_id": summary_block_id,
            "original_tokens": original_tokens,
            "compressed_tokens": summary_tokens,
            "compression_ratio": round(compression_ratio, 2),
            "summarized_blocks": block_ids,
            "message": f"已将 {len(block_ids)} 个内容块压缩为摘要 {summary_block_id}，"
                      f"节省约 {original_tokens - summary_tokens} tokens"
        }


class MemPinTool(BaseTool):
    """将内容固定到长期记忆

    当 Agent 发现值得长期记住的信息（用户偏好、重要事实、成功模式等），
    可以调用此工具将其保存到长期记忆系统。
    """

    name = "mem_pin"
    description = (
        "将重要内容固定到长期记忆，跨 Session 持久化。"
        "适合保存：用户偏好、重要事实、成功的工作流模式等。"
        "参数: content (要保存的内容), memory_type (记忆类型), importance (重要性0-1)"
    )
    parameters = {
        "type": "object",
        "properties": {
            "content": {
                "type": "string",
                "description": "要保存到长期记忆的内容"
            },
            "memory_type": {
                "type": "string",
                "enum": ["preference", "fact", "pattern", "skill"],
                "description": "记忆类型: preference(用户偏好), fact(事实), pattern(行为模式), skill(技能)"
            },
            "importance": {
                "type": "number",
                "minimum": 0,
                "maximum": 1,
                "description": "重要性 (0-1)，影响记忆保留优先级",
                "default": 0.7
            }
        },
        "required": ["content", "memory_type"]
    }

    risk_level = RiskLevel.LOW
    operation_categories: list[OperationCategory] = []  # Memory operation, no external effects

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        content = kwargs.get("content", "")
        memory_type = kwargs.get("memory_type", "")
        importance = kwargs.get("importance", 0.7)

        if not content:
            return {"success": False, "error": "content is required"}

        if not memory_type:
            return {"success": False, "error": "memory_type is required"}

        valid_types = ["preference", "fact", "pattern", "skill"]
        if memory_type not in valid_types:
            return {
                "success": False,
                "error": f"Invalid memory_type. Must be one of: {valid_types}"
            }

        # 创建一个 pinned block（实际应该写入 Memory 系统）
        memory_block_id = _generate_block_id()

        _block_store[memory_block_id] = {
            "block_id": memory_block_id,
            "content": content,
            "block_type": f"memory_{memory_type}",
            "token_count": len(content) // 3,
            "importance": importance,
            "status": "pinned",
            "source_block_ids": [],
            "metadata": {
                "memory_type": memory_type,
                "pinned": True,
                "pin_time": datetime.now().isoformat()
            },
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "deleted_at": None,
        }

        logger.info(f"Pinned to long-term memory: {memory_block_id} ({memory_type})")

        # TODO: 实际应该写入 MemoryManager
        # await memory_manager.save_memory(Memory(
        #     user_id=user_id,
        #     memory_type=memory_type,
        #     content=content,
        #     importance_score=importance
        # ))

        return {
            "success": True,
            "memory_id": memory_block_id,
            "memory_type": memory_type,
            "importance": importance,
            "message": f"已将内容保存到长期记忆 ({memory_type})，ID: {memory_block_id}"
        }


# ============================================================================
# 辅助工具
# ============================================================================


class MemListBlocksTool(BaseTool):
    """列出当前 Context 中的所有内容块

    帮助 Agent 了解当前 Context 状态，以便做出记忆管理决策。
    """

    name = "mem_list_blocks"
    description = (
        "列出当前 Context 中的所有内容块及其状态。"
        "用于了解 Context 状态，以便决定保留、删除或压缩哪些内容。"
    )
    parameters = {
        "type": "object",
        "properties": {
            "include_deleted": {
                "type": "boolean",
                "description": "是否包含已删除的块",
                "default": False
            },
            "status_filter": {
                "type": "string",
                "enum": ["all", "active", "retained", "summarized", "pinned"],
                "description": "按状态过滤",
                "default": "all"
            }
        },
        "required": []
    }

    risk_level = RiskLevel.LOW
    operation_categories = []

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        include_deleted = kwargs.get("include_deleted", False)
        status_filter = kwargs.get("status_filter", "all")

        blocks = []
        total_tokens = 0
        active_tokens = 0

        for block_id, block in _block_store.items():
            # 过滤已删除
            if not include_deleted and block["status"] == "deleted":
                continue

            # 按状态过滤
            if status_filter != "all" and block["status"] != status_filter:
                continue

            blocks.append({
                "block_id": block_id,
                "type": block["block_type"],
                "tokens": block["token_count"],
                "importance": block["importance"],
                "status": block["status"],
                "preview": block["content"][:100] + "..." if len(block["content"]) > 100 else block["content"]
            })

            total_tokens += block["token_count"]
            if block["status"] in ("active", "retained"):
                active_tokens += block["token_count"]

        return {
            "success": True,
            "blocks": blocks,
            "total_blocks": len(blocks),
            "total_tokens": total_tokens,
            "active_tokens": active_tokens,
            "message": f"共 {len(blocks)} 个内容块，{total_tokens} tokens (活跃: {active_tokens})"
        }


# ============================================================================
# 工具创建函数
# ============================================================================


def create_memory_tools() -> list[BaseTool]:
    """创建所有 Memory Tools"""
    return [
        MemRetainTool(),
        MemDeleteTool(),
        MemSummarizeTool(),
        MemPinTool(),
        MemListBlocksTool(),
    ]


def get_memory_tool_names() -> list[str]:
    """获取所有 Memory Tool 名称"""
    return [
        "mem_retain",
        "mem_delete",
        "mem_summarize",
        "mem_pin",
        "mem_list_blocks",
    ]
