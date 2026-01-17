"""
Parallel Exploration - 多线程策略探索

当任务不确定时，同时尝试多条路径，选择最优者继续深入。
"""
from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class StrategyType(str, Enum):
    SKILL_FIRST = "skill_first"       # 优先 Skill 执行
    MCP_FIRST = "mcp_first"           # 优先 MCP 代码生成
    LLM_ONLY = "llm_only"             # 仅使用 LLM 推理
    CHUNK_PARALLEL = "chunk_parallel" # 分块并行
    SEQUENTIAL = "sequential"          # 顺序执行


@dataclass
class StrategyCandidate:
    """单个探索策略候选项"""
    strategy_type: StrategyType
    description: str
    estimated_cost: float  # 预估 token 成本 (0-1 归一化)
    estimated_quality: float  # 预估质量 (0-1 归一化)
    parameters: dict = field(default_factory=dict)


@dataclass
class ExplorationResult:
    """单个策略探索结果"""
    strategy: StrategyCandidate
    success: bool
    output: Any
    confidence: float  # 结果置信度 (0-1)
    elapsed_seconds: float
    error: str | None = None


class ParallelExploration:
    """
    多策略并行探索器

    当任务具有不确定性时，同时尝试多个候选策略：
    - 快速测试每个策略的可行性 (timeout 限制)
    - 选择置信度最高的策略继续
    """

    def __init__(
        self,
        max_parallel: int = 3,
        test_timeout_seconds: float = 5.0,
    ):
        self.max_parallel = max_parallel
        self.test_timeout = test_timeout_seconds

    def generate_candidate_strategies(
        self,
        task_description: str,
        available_skills: list[str],
    ) -> list[StrategyCandidate]:
        """
        根据任务描述生成候选策略列表

        Args:
            task_description: 用户任务描述
            available_skills: 当前可用的 Skill 列表

        Returns:
            按预估质量降序的候选策略列表
        """
        candidates: list[StrategyCandidate] = []

        # 关键词匹配生成候选
        lower_task = task_description.lower()

        # Skill-first: 若有匹配的内置 Skill
        if available_skills:
            candidates.append(
                StrategyCandidate(
                    strategy_type=StrategyType.SKILL_FIRST,
                    description="使用匹配的内置 Skill 优先执行",
                    estimated_cost=0.2,
                    estimated_quality=0.9,
                    parameters={"skills": available_skills[:3]},
                )
            )

        # MCP-first: 若任务涉及代码生成
        if any(kw in lower_task for kw in ["代码", "code", "实现", "脚本", "程序"]):
            candidates.append(
                StrategyCandidate(
                    strategy_type=StrategyType.MCP_FIRST,
                    description="MCP 代码生成优先",
                    estimated_cost=0.5,
                    estimated_quality=0.75,
                )
            )

        # Chunk-parallel: 若任务涉及大量数据处理
        if any(kw in lower_task for kw in ["批量", "所有", "全部", "多个", "列表"]):
            candidates.append(
                StrategyCandidate(
                    strategy_type=StrategyType.CHUNK_PARALLEL,
                    description="数据分块并行处理",
                    estimated_cost=0.7,
                    estimated_quality=0.85,
                )
            )

        # LLM-only: 纯推理任务
        if any(kw in lower_task for kw in ["解释", "分析", "为什么", "总结", "概述"]):
            candidates.append(
                StrategyCandidate(
                    strategy_type=StrategyType.LLM_ONLY,
                    description="LLM 推理优先",
                    estimated_cost=0.4,
                    estimated_quality=0.8,
                )
            )

        # Sequential fallback
        candidates.append(
            StrategyCandidate(
                strategy_type=StrategyType.SEQUENTIAL,
                description="顺序执行 (保守策略)",
                estimated_cost=0.3,
                estimated_quality=0.7,
            )
        )

        # 按预估质量降序
        candidates.sort(key=lambda c: c.estimated_quality, reverse=True)
        return candidates[: self.max_parallel]

    async def explore_multiple_strategies(
        self,
        task: str,
        candidates: list[StrategyCandidate],
        test_executor: Callable[[StrategyCandidate], Any],
    ) -> ExplorationResult:
        """
        并行测试多个候选策略，选择最优

        Args:
            task: 任务描述 (日志用)
            candidates: 候选策略列表
            test_executor: 实际执行测试的函数，接收 StrategyCandidate，返回测试产物

        Returns:
            最优策略的探索结果
        """
        logger.info(f"Parallel exploration: testing {len(candidates)} strategies")

        async def run_test(candidate: StrategyCandidate) -> ExplorationResult:
            start = time.perf_counter()
            try:
                result = await asyncio.wait_for(
                    asyncio.to_thread(test_executor, candidate),
                    timeout=self.test_timeout,
                )
                elapsed = time.perf_counter() - start
                # 简易置信度：成功 + 预估质量 + 速度奖励
                speed_bonus = max(0, (self.test_timeout - elapsed) / self.test_timeout * 0.1)
                confidence = candidate.estimated_quality + speed_bonus
                return ExplorationResult(
                    strategy=candidate,
                    success=True,
                    output=result,
                    confidence=confidence,
                    elapsed_seconds=elapsed,
                )
            except TimeoutError:
                elapsed = time.perf_counter() - start
                return ExplorationResult(
                    strategy=candidate,
                    success=False,
                    output=None,
                    confidence=0.0,
                    elapsed_seconds=elapsed,
                    error="Timeout",
                )
            except Exception as e:
                elapsed = time.perf_counter() - start
                return ExplorationResult(
                    strategy=candidate,
                    success=False,
                    output=None,
                    confidence=0.0,
                    elapsed_seconds=elapsed,
                    error=str(e),
                )

        results = await asyncio.gather(*[run_test(c) for c in candidates])
        successes = [r for r in results if r.success]
        if successes:
            best = max(successes, key=lambda r: r.confidence)
            logger.info(
                f"Exploration done: best strategy={best.strategy.strategy_type.value}, "
                f"confidence={best.confidence:.2f}"
            )
            return best

        # 全部失败时返回第一个失败结果
        logger.warning("All exploration strategies failed")
        return results[0]
