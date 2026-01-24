"""
自适应 LLM 路由器

基于历史数据和 Context Graph 动态优化模型选择
支持 A/B 测试和自动学习
"""
import json
import logging
import random
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from .advanced_router import AdvancedRouter, RoutingConstraints
from .router import MODEL_REGISTRY, TaskType

logger = logging.getLogger(__name__)


@dataclass
class ModelPerformance:
    """模型历史表现数据"""
    model_name: str
    task_type: str
    total_calls: int = 0
    success_count: int = 0
    failure_count: int = 0
    total_cost: float = 0.0
    total_latency_ms: float = 0.0
    avg_quality_score: float = 0.0  # 用户反馈的质量评分
    last_used: datetime = None

    @property
    def success_rate(self) -> float:
        if self.total_calls == 0:
            return 0.0
        return self.success_count / self.total_calls

    @property
    def avg_cost(self) -> float:
        if self.total_calls == 0:
            return 0.0
        return self.total_cost / self.total_calls

    @property
    def avg_latency(self) -> float:
        if self.total_calls == 0:
            return 0.0
        return self.total_latency_ms / self.total_calls

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_name": self.model_name,
            "task_type": self.task_type,
            "total_calls": self.total_calls,
            "success_rate": self.success_rate,
            "avg_cost": self.avg_cost,
            "avg_latency": self.avg_latency,
            "avg_quality_score": self.avg_quality_score,
            "last_used": self.last_used.isoformat() if self.last_used else None
        }


@dataclass
class ABTestConfig:
    """A/B 测试配置"""
    experiment_name: str
    control_model: str
    treatment_model: str
    traffic_split: float = 0.5  # treatment 组的流量比例
    start_time: datetime = None
    end_time: datetime = None
    task_types: list[str] = field(default_factory=list)  # 空列表表示所有任务类型
    is_active: bool = True

    def is_running(self) -> bool:
        if not self.is_active:
            return False
        now = datetime.now()
        if self.start_time and now < self.start_time:
            return False
        if self.end_time and now > self.end_time:
            return False
        return True


class AdaptiveRouter(AdvancedRouter):
    """自适应路由器

    基于历史数据动态优化模型选择，支持：
    - 历史成功率学习
    - A/B 测试框架
    - Context Graph 集成（Neo4j）
    - 自动降级和探索
    """

    # 探索率（选择非最优模型以收集数据）
    EXPLORATION_RATE = 0.1

    # 最小样本数（达到此数量前使用探索策略）
    MIN_SAMPLES = 10

    def __init__(
        self,
        context_graph_client = None,
        enable_exploration: bool = True
    ):
        super().__init__()

        # Context Graph 客户端（Neo4j）
        self.context_graph = context_graph_client

        # 本地性能缓存（当 Context Graph 不可用时使用）
        self._performance_cache: dict[str, ModelPerformance] = {}

        # A/B 测试配置
        self._ab_tests: dict[str, ABTestConfig] = {}

        # 是否启用探索
        self.enable_exploration = enable_exploration

        logger.info(f"AdaptiveRouter initialized (exploration={enable_exploration})")

    async def select_model_async(
        self,
        task_type: TaskType | str,
        constraints: RoutingConstraints | None = None,
        session_id: str | None = None,
        **kwargs
    ) -> str:
        """异步智能选择模型（支持 Context Graph 查询）

        Args:
            task_type: 任务类型
            constraints: 路由约束
            session_id: 会话 ID（用于 A/B 测试分组）

        Returns:
            str: 最优模型名称
        """
        # 转换任务类型
        if isinstance(task_type, str):
            try:
                task_type = TaskType(task_type)
            except ValueError:
                task_type = TaskType.GENERAL

        # 1. 检查 A/B 测试
        ab_model = self._check_ab_test(task_type, session_id)
        if ab_model:
            logger.info(f"A/B test assigned model: {ab_model}")
            return ab_model

        # 2. 尝试从 Context Graph 获取历史数据
        history_data = await self._fetch_performance_from_graph(task_type)

        # 3. 如果有足够的历史数据，使用自适应选择
        if history_data and self._has_sufficient_data(history_data, task_type):
            model = self._select_by_history(history_data, task_type, constraints)
            if model:
                logger.info(f"Adaptive selection: {model} (based on historical performance)")
                return model

        # 4. 探索策略（收集新数据）
        if self.enable_exploration and random.random() < self.EXPLORATION_RATE:
            explore_model = self._select_for_exploration(task_type)
            if explore_model:
                logger.info(f"Exploration selection: {explore_model}")
                return explore_model

        # 5. 回退到高级路由
        return super().select_model(task_type, constraints)

    def select_model(
        self,
        task_type: TaskType | str,
        constraints: RoutingConstraints | None = None,
        **kwargs
    ) -> str:
        """同步版本（使用本地缓存）"""
        # 转换任务类型
        if isinstance(task_type, str):
            try:
                task_type = TaskType(task_type)
            except ValueError:
                task_type = TaskType.GENERAL

        # 使用本地缓存的历史数据
        if self._has_sufficient_local_data(task_type):
            model = self._select_by_local_history(task_type, constraints)
            if model:
                return model

        # 回退到高级路由
        return super().select_model(task_type, constraints)

    async def _fetch_performance_from_graph(
        self,
        task_type: TaskType
    ) -> list[dict] | None:
        """从 Context Graph 获取模型历史表现"""
        if not self.context_graph:
            return None

        try:
            # Neo4j Cypher 查询
            query = """
            MATCH (call:LLMCall)-[:FOR_TASK]->(task:Task {type: $task_type})
            WHERE call.timestamp > datetime() - duration('P30D')
            RETURN
                call.model as model,
                COUNT(*) as total_calls,
                SUM(CASE WHEN call.success THEN 1 ELSE 0 END) as success_count,
                AVG(call.cost_usd) as avg_cost,
                AVG(call.latency_ms) as avg_latency,
                AVG(COALESCE(call.quality_score, 0)) as avg_quality
            ORDER BY success_count DESC
            """

            result = await self.context_graph.run_async(
                query,
                task_type=task_type.value
            )

            return result
        except Exception as e:
            logger.warning(f"Failed to fetch from Context Graph: {e}")
            return None

    def _has_sufficient_data(
        self,
        history_data: list[dict],
        task_type: TaskType
    ) -> bool:
        """检查是否有足够的历史数据"""
        total_samples = sum(d.get("total_calls", 0) for d in history_data)
        return total_samples >= self.MIN_SAMPLES

    def _has_sufficient_local_data(self, task_type: TaskType) -> bool:
        """检查本地缓存是否有足够数据"""
        key_prefix = f"{task_type.value}:"
        relevant = [
            v for k, v in self._performance_cache.items()
            if k.startswith(key_prefix)
        ]
        total_samples = sum(p.total_calls for p in relevant)
        return total_samples >= self.MIN_SAMPLES

    def _select_by_history(
        self,
        history_data: list[dict],
        task_type: TaskType,
        constraints: RoutingConstraints | None
    ) -> str | None:
        """基于历史数据选择模型"""
        if not history_data:
            return None

        # 计算综合分数
        scored_models = []
        for data in history_data:
            model = data.get("model")
            if not model:
                continue

            # 检查约束
            if constraints and not self._model_meets_constraints(model, constraints):
                continue

            # 计算自适应分数
            score = self._calculate_adaptive_score(data)
            scored_models.append((model, score))

        if not scored_models:
            return None

        # 选择最高分
        scored_models.sort(key=lambda x: x[1], reverse=True)
        return scored_models[0][0]

    def _select_by_local_history(
        self,
        task_type: TaskType,
        constraints: RoutingConstraints | None
    ) -> str | None:
        """基于本地缓存历史选择"""
        key_prefix = f"{task_type.value}:"
        relevant = [
            (k.split(":")[1], v) for k, v in self._performance_cache.items()
            if k.startswith(key_prefix) and v.total_calls >= 3
        ]

        if not relevant:
            return None

        # 按成功率排序
        scored = []
        for model, perf in relevant:
            # 检查约束
            if constraints and not self._model_meets_constraints(model, constraints):
                continue

            # 计算分数：成功率 * 0.5 + 质量 * 0.3 + 成本效益 * 0.2
            score = (
                perf.success_rate * 50 +
                perf.avg_quality_score * 30 +
                max(0, 20 - perf.avg_cost * 10)
            )
            scored.append((model, score))

        if not scored:
            return None

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[0][0]

    def _model_meets_constraints(
        self,
        model: str,
        constraints: RoutingConstraints
    ) -> bool:
        """检查模型是否满足约束"""
        config = MODEL_REGISTRY.get(model)
        if not config:
            return False

        if constraints.max_latency_ms and config.avg_latency_ms > constraints.max_latency_ms:
            return False

        if model in constraints.excluded_models:
            return False

        return True

    def _calculate_adaptive_score(self, data: dict) -> float:
        """计算自适应分数

        综合考虑：
        - 成功率 (40%)
        - 平均质量 (30%)
        - 成本效益 (20%)
        - 样本量置信度 (10%)
        """
        success_rate = data.get("success_count", 0) / max(data.get("total_calls", 1), 1)
        avg_quality = data.get("avg_quality", 0) or 0
        avg_cost = data.get("avg_cost", 0) or 0
        total_calls = data.get("total_calls", 0)

        # 成功率分数
        success_score = success_rate * 40

        # 质量分数（假设 0-10 分）
        quality_score = (avg_quality / 10) * 30

        # 成本效益分数（成本越低越好）
        cost_score = max(0, 20 - avg_cost * 10)

        # 置信度分数（样本越多越有信心）
        confidence = min(total_calls / 100, 1.0)  # 100 样本达到满置信
        confidence_score = confidence * 10

        return success_score + quality_score + cost_score + confidence_score

    def _select_for_exploration(self, task_type: TaskType) -> str | None:
        """选择用于探索的模型（随机选择一个较少使用的）"""
        key_prefix = f"{task_type.value}:"

        # 统计每个模型的使用次数
        usage = defaultdict(int)
        for k, v in self._performance_cache.items():
            if k.startswith(key_prefix):
                model = k.split(":")[1]
                usage[model] = v.total_calls

        # 找出使用次数最少的模型
        all_models = list(MODEL_REGISTRY.keys())
        least_used = [m for m in all_models if usage.get(m, 0) < self.MIN_SAMPLES]

        if least_used:
            return random.choice(least_used)

        return None

    def _check_ab_test(
        self,
        task_type: TaskType,
        session_id: str | None
    ) -> str | None:
        """检查 A/B 测试分配"""
        for test in self._ab_tests.values():
            if not test.is_running():
                continue

            # 检查任务类型是否匹配
            if test.task_types and task_type.value not in test.task_types:
                continue

            # 基于 session_id 确定分组（确保同一用户始终在同一组）
            if session_id:
                # 使用 hash 确保一致性
                hash_value = hash(f"{test.experiment_name}:{session_id}") % 100
                is_treatment = hash_value < (test.traffic_split * 100)
            else:
                # 随机分配
                is_treatment = random.random() < test.traffic_split

            return test.treatment_model if is_treatment else test.control_model

        return None

    # ========== 数据记录接口 ==========

    async def record_call_result(
        self,
        model: str,
        task_type: TaskType | str,
        success: bool,
        cost_usd: float = 0.0,
        latency_ms: float = 0.0,
        quality_score: float | None = None,
        session_id: str | None = None
    ):
        """记录调用结果（用于学习）

        Args:
            model: 使用的模型
            task_type: 任务类型
            success: 是否成功
            cost_usd: 成本
            latency_ms: 延迟
            quality_score: 质量评分（用户反馈）
            session_id: 会话 ID
        """
        if isinstance(task_type, str):
            try:
                task_type = TaskType(task_type)
            except ValueError:
                task_type = TaskType.GENERAL

        # 1. 更新本地缓存
        cache_key = f"{task_type.value}:{model}"
        if cache_key not in self._performance_cache:
            self._performance_cache[cache_key] = ModelPerformance(
                model_name=model,
                task_type=task_type.value
            )

        perf = self._performance_cache[cache_key]
        perf.total_calls += 1
        if success:
            perf.success_count += 1
        else:
            perf.failure_count += 1
        perf.total_cost += cost_usd
        perf.total_latency_ms += latency_ms
        if quality_score is not None:
            # 滑动平均更新质量分数
            perf.avg_quality_score = (
                perf.avg_quality_score * 0.9 + quality_score * 0.1
            ) if perf.avg_quality_score > 0 else quality_score
        perf.last_used = datetime.now()

        # 2. 写入 Context Graph（异步）
        if self.context_graph:
            try:
                await self._write_to_context_graph(
                    model, task_type, success, cost_usd, latency_ms,
                    quality_score, session_id
                )
            except Exception as e:
                logger.warning(f"Failed to write to Context Graph: {e}")

    async def _write_to_context_graph(
        self,
        model: str,
        task_type: TaskType,
        success: bool,
        cost_usd: float,
        latency_ms: float,
        quality_score: float | None,
        session_id: str | None
    ):
        """写入 Context Graph"""
        query = """
        CREATE (call:LLMCall {
            model: $model,
            task_type: $task_type,
            success: $success,
            cost_usd: $cost_usd,
            latency_ms: $latency_ms,
            quality_score: $quality_score,
            session_id: $session_id,
            timestamp: datetime()
        })
        """

        await self.context_graph.run_async(
            query,
            model=model,
            task_type=task_type.value,
            success=success,
            cost_usd=cost_usd,
            latency_ms=latency_ms,
            quality_score=quality_score,
            session_id=session_id
        )

    # ========== A/B 测试管理 ==========

    def create_ab_test(
        self,
        name: str,
        control_model: str,
        treatment_model: str,
        traffic_split: float = 0.5,
        duration_days: int = 7,
        task_types: list[str] = None
    ) -> ABTestConfig:
        """创建 A/B 测试

        Args:
            name: 实验名称
            control_model: 对照组模型
            treatment_model: 实验组模型
            traffic_split: 实验组流量比例
            duration_days: 实验持续天数
            task_types: 限定的任务类型（None 表示所有）

        Returns:
            ABTestConfig: 测试配置
        """
        config = ABTestConfig(
            experiment_name=name,
            control_model=control_model,
            treatment_model=treatment_model,
            traffic_split=traffic_split,
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(days=duration_days),
            task_types=task_types or [],
            is_active=True
        )

        self._ab_tests[name] = config
        logger.info(f"A/B test created: {name} ({control_model} vs {treatment_model})")
        return config

    def stop_ab_test(self, name: str):
        """停止 A/B 测试"""
        if name in self._ab_tests:
            self._ab_tests[name].is_active = False
            logger.info(f"A/B test stopped: {name}")

    def get_ab_test_results(self, name: str) -> dict[str, Any] | None:
        """获取 A/B 测试结果"""
        if name not in self._ab_tests:
            return None

        test = self._ab_tests[name]

        # 从缓存获取两组的表现数据
        control_perf = {}
        treatment_perf = {}

        for task_type in (test.task_types or [t.value for t in TaskType]):
            control_key = f"{task_type}:{test.control_model}"
            treatment_key = f"{task_type}:{test.treatment_model}"

            if control_key in self._performance_cache:
                control_perf[task_type] = self._performance_cache[control_key].to_dict()
            if treatment_key in self._performance_cache:
                treatment_perf[task_type] = self._performance_cache[treatment_key].to_dict()

        return {
            "experiment_name": name,
            "control_model": test.control_model,
            "treatment_model": test.treatment_model,
            "traffic_split": test.traffic_split,
            "is_running": test.is_running(),
            "control_performance": control_perf,
            "treatment_performance": treatment_perf
        }

    # ========== 状态导出 ==========

    def get_performance_summary(self) -> dict[str, Any]:
        """获取性能摘要"""
        summary = {}
        for key, perf in self._performance_cache.items():
            summary[key] = perf.to_dict()
        return summary

    def export_state(self) -> str:
        """导出路由器状态（用于持久化）"""
        state = {
            "performance_cache": self.get_performance_summary(),
            "ab_tests": {
                name: {
                    "experiment_name": test.experiment_name,
                    "control_model": test.control_model,
                    "treatment_model": test.treatment_model,
                    "traffic_split": test.traffic_split,
                    "is_active": test.is_active
                }
                for name, test in self._ab_tests.items()
            },
            "routing_history": self.get_routing_history()
        }
        return json.dumps(state, indent=2, default=str)

    def import_state(self, state_json: str):
        """导入路由器状态"""
        state = json.loads(state_json)

        # 恢复性能缓存
        for key, data in state.get("performance_cache", {}).items():
            self._performance_cache[key] = ModelPerformance(
                model_name=data["model_name"],
                task_type=data["task_type"],
                total_calls=data["total_calls"],
                success_count=int(data["success_rate"] * data["total_calls"]),
                total_cost=data["avg_cost"] * data["total_calls"],
                total_latency_ms=data["avg_latency"] * data["total_calls"],
                avg_quality_score=data["avg_quality_score"]
            )

        logger.info(f"Imported router state: {len(self._performance_cache)} models")
