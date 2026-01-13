# Monitor & Evaluation设计文档

## 1. 核心目标

**持续监控Agent质量，及时发现问题，驱动系统改进**

```
监控层次：
1. 实时监控（Real-time）：当前Session的运行状态
2. 会话监控（Session-level）：单次对话的质量评估
3. 系统监控（System-level）：整体性能趋势分析
```

## 2. 监控指标体系

### 2.1 质量指标（Quality Metrics）

```python
# packages/core/monitor/quality_metrics.py

class QualityMetrics:
    """质量指标收集器"""
    
    async def collect_session_quality(self, session_id: str) -> dict:
        return {
            # 任务成功率
            "task_success_rate": await self._calc_success_rate(session_id),
            
            # Self-Reflection效果
            "reflection_improvement_rate": await self._calc_reflection_improvement(session_id),
            
            # 工具调用成功率
            "tool_success_rate": await self._calc_tool_success_rate(session_id),
            "tool_retry_rate": ...,
            
            # 规划质量
            "plan_completion_rate": ...,  # 计划完成度
            "plan_revision_count": ...,   # 计划修订次数
            
            # 输出质量
            "output_coherence_score": ...,  # 输出连贯性
            "citation_accuracy": ...,       # 引用准确性（Deep Research）
            
            # 用户满意度（间接）
            "user_intervention_count": ...,  # 用户干预次数
            "conversation_abandon_rate": ... # 对话放弃率
        }
    
    async def _calc_success_rate(self, session_id: str) -> float:
        """计算任务成功率"""
        
        # 从Context Graph获取决策节点
        nodes = await self.context_graph.get_nodes(
            session_id=session_id,
            node_types=["tool_call", "reasoning", "planning"]
        )
        
        total = len(nodes)
        if total == 0:
            return 1.0
        
        success = len([n for n in nodes if n.error is None])
        return success / total
    
    async def _calc_reflection_improvement(self, session_id: str) -> float:
        """计算反思后的改进率"""
        
        reflection_chains = await self.context_graph.get_reflection_chains(session_id)
        
        improved = 0
        total = len(reflection_chains)
        
        for chain in reflection_chains:
            # 比较反思前后的结果
            before_score = chain.initial_attempt.score
            after_score = chain.final_attempt.score
            
            if after_score > before_score:
                improved += 1
        
        return improved / total if total > 0 else 0.0
```

### 2.2 性能指标（Performance Metrics）

```python
class PerformanceMetrics:
    """性能指标收集器"""
    
    async def collect_session_performance(self, session_id: str) -> dict:
        return {
            # 延迟
            "avg_response_latency_ms": ...,
            "p50_latency_ms": ...,
            "p95_latency_ms": ...,
            "p99_latency_ms": ...,
            
            # Token使用
            "total_tokens": ...,
            "prompt_tokens": ...,
            "completion_tokens": ...,
            "context_compression_ratio": ...,  # 摘要压缩比
            
            # 成本
            "estimated_cost_usd": ...,
            "cost_per_message": ...,
            
            # 吞吐量
            "messages_per_minute": ...,
            "tools_called_per_message": ...,
            
            # 资源使用
            "avg_memory_mb": ...,
            "peak_memory_mb": ...,
            "sandbox_cpu_usage_percent": ...
        }
    
    async def _calc_latency_percentile(
        self, 
        session_id: str,
        percentile: float
    ) -> float:
        """计算延迟百分位"""
        
        latencies = await self.db.query("""
            SELECT 
                EXTRACT(EPOCH FROM (response_at - request_at)) * 1000 as latency_ms
            FROM messages
            WHERE session_id = $1 AND role = 'assistant'
            ORDER BY latency_ms
        """, session_id)
        
        if not latencies:
            return 0.0
        
        index = int(len(latencies) * percentile)
        return latencies[index]
```

### 2.3 成本指标（Cost Metrics）

```python
class CostMetrics:
    """成本指标收集器"""
    
    # LLM定价（2026年1月）
    PRICING = {
        "claude-3-5-sonnet": {
            "input": 3.0 / 1_000_000,   # $3 per 1M tokens
            "output": 15.0 / 1_000_000   # $15 per 1M tokens
        },
        "claude-3-haiku": {
            "input": 0.25 / 1_000_000,
            "output": 1.25 / 1_000_000
        },
        "gemini-1.5-flash": {
            "input": 0.075 / 1_000_000,
            "output": 0.3 / 1_000_000
        }
    }
    
    async def collect_session_cost(self, session_id: str) -> dict:
        """计算Session成本"""
        
        # 获取所有LLM调用
        llm_calls = await self.db.get_llm_calls(session_id)
        
        total_cost = 0.0
        breakdown = {}
        
        for call in llm_calls:
            model_pricing = self.PRICING[call.model]
            
            call_cost = (
                call.prompt_tokens * model_pricing["input"] +
                call.completion_tokens * model_pricing["output"]
            )
            
            total_cost += call_cost
            
            if call.model not in breakdown:
                breakdown[call.model] = 0.0
            breakdown[call.model] += call_cost
        
        return {
            "total_cost_usd": total_cost,
            "cost_breakdown": breakdown,
            "cost_per_message": total_cost / await self._get_message_count(session_id),
            
            # 成本优化效果
            "savings_from_compression_usd": await self._calc_compression_savings(session_id),
            "savings_from_skill_loading_usd": await self._calc_skill_loading_savings(session_id)
        }
```

## 3. 实时监控

### 3.1 监控Dashboard

```python
# packages/core/monitor/dashboard.py

class MonitorDashboard:
    """实时监控Dashboard"""
    
    async def get_realtime_status(self) -> dict:
        """获取实时状态"""
        
        return {
            # 系统状态
            "system": {
                "status": "healthy" | "degraded" | "down",
                "active_sessions": await self._count_active_sessions(),
                "requests_per_minute": await self._calc_rpm(),
                "avg_latency_ms": await self._calc_recent_latency()
            },
            
            # 异常告警
            "alerts": await self._get_active_alerts(),
            
            # 热点问题
            "top_errors": await self._get_top_errors(limit=10),
            
            # 资源使用
            "resources": {
                "postgres_connections": ...,
                "redis_memory_mb": ...,
                "minio_storage_gb": ...,
                "sandbox_containers": ...
            }
        }
    
    async def _get_active_alerts(self) -> List[Alert]:
        """获取活跃告警"""
        
        alerts = []
        
        # 检查延迟告警
        avg_latency = await self._calc_recent_latency()
        if avg_latency > 5000:  # 超过5秒
            alerts.append(Alert(
                level="warning",
                message=f"High latency detected: {avg_latency}ms",
                timestamp=now()
            ))
        
        # 检查错误率告警
        error_rate = await self._calc_error_rate()
        if error_rate > 0.1:  # 超过10%
            alerts.append(Alert(
                level="critical",
                message=f"High error rate: {error_rate * 100:.1f}%",
                timestamp=now()
            ))
        
        # 检查成本告警
        daily_cost = await self._calc_daily_cost()
        if daily_cost > 100:  # 超过$100/天
            alerts.append(Alert(
                level="warning",
                message=f"High daily cost: ${daily_cost:.2f}",
                timestamp=now()
            ))
        
        return alerts
```

### 3.2 异常检测

```python
class AnomalyDetector:
    """异常检测器"""
    
    async def detect_anomalies(self, session_id: str) -> List[Anomaly]:
        """检测异常"""
        
        anomalies = []
        
        # 异常1：Token突然暴增
        token_spike = await self._detect_token_spike(session_id)
        if token_spike:
            anomalies.append(Anomaly(
                type="token_spike",
                message=f"Token使用突增 {token_spike.ratio}x",
                details=token_spike
            ))
        
        # 异常2：反思循环过长
        long_reflection = await self._detect_long_reflection(session_id)
        if long_reflection:
            anomalies.append(Anomaly(
                type="long_reflection",
                message=f"反思循环 {long_reflection.iterations} 次未收敛",
                details=long_reflection
            ))
        
        # 异常3：工具调用失败率过高
        tool_failures = await self._detect_tool_failures(session_id)
        if tool_failures.rate > 0.5:
            anomalies.append(Anomaly(
                type="tool_failures",
                message=f"工具调用失败率 {tool_failures.rate * 100:.1f}%",
                details=tool_failures
            ))
        
        return anomalies
    
    async def _detect_token_spike(self, session_id: str):
        """检测Token突增"""
        
        recent_tokens = await self.db.get_recent_token_usage(session_id, limit=5)
        
        if len(recent_tokens) < 5:
            return None
        
        avg_baseline = sum(recent_tokens[:-1]) / (len(recent_tokens) - 1)
        latest = recent_tokens[-1]
        
        if latest > avg_baseline * 3:  # 3倍突增
            return TokenSpike(
                baseline=avg_baseline,
                actual=latest,
                ratio=latest / avg_baseline
            )
        
        return None
```

## 4. 质量评估

### 4.1 输出质量评估

```python
class OutputQualityEvaluator:
    """输出质量评估器"""
    
    async def evaluate_response(
        self, 
        user_query: str,
        agent_response: str
    ) -> QualityScore:
        """评估Agent响应质量"""
        
        # 使用小模型评估，降低成本
        evaluation = await self.small_llm.generate(
            prompt=f"""
Evaluate the quality of this AI agent response.

User Query: {user_query}
Agent Response: {agent_response}

Evaluate on 0-100 scale:
1. Relevance: Does it answer the query?
2. Completeness: Is the answer complete?
3. Coherence: Is it well-structured?
4. Accuracy: Are the facts correct?

Return JSON:
{{
  "relevance": 0-100,
  "completeness": 0-100,
  "coherence": 0-100,
  "accuracy": 0-100,
  "overall": 0-100,
  "issues": ["issue1", ...],
  "suggestions": ["suggestion1", ...]
}}
""",
            temperature=0.3,
            response_format="json"
        )
        
        return QualityScore(**json.loads(evaluation.content))
```

### 4.2 Deep Research质量评估

```python
class ResearchQualityEvaluator:
    """Deep Research质量评估器"""
    
    async def evaluate_research(
        self,
        query: str,
        research_result: dict
    ) -> ResearchQuality:
        """评估Deep Research质量"""
        
        return ResearchQuality(
            # 引用质量
            citation_count=len(research_result["citations"]),
            citation_diversity=await self._calc_citation_diversity(
                research_result["citations"]
            ),
            citation_freshness=await self._calc_citation_freshness(
                research_result["citations"]
            ),
            
            # 内容质量
            content_depth_score=await self._evaluate_depth(
                research_result["content"]
            ),
            source_quality_score=await self._evaluate_sources(
                research_result["citations"]
            ),
            
            # 完整性
            topic_coverage=await self._calc_topic_coverage(
                query,
                research_result["content"]
            )
        )
    
    async def _calc_citation_diversity(self, citations: List[dict]) -> float:
        """计算引用多样性"""
        
        # 域名去重
        domains = set(
            urlparse(c["url"]).netloc 
            for c in citations
        )
        
        # 多样性 = 不同域名数 / 总引用数
        return len(domains) / len(citations) if citations else 0.0
```

## 5. A/B测试框架

```python
# packages/core/monitor/ab_test.py

class ABTestManager:
    """A/B测试管理器"""
    
    async def assign_variant(self, user_id: str, experiment: str) -> str:
        """分配实验变体"""
        
        # 基于user_id哈希分桶
        bucket = hash(f"{user_id}:{experiment}") % 100
        
        experiments = {
            "reflection_mode": {
                "control": (0, 50),      # 50% 用Reflexion
                "external_loop": (50, 100)  # 50% 用External-Loop
            },
            "context_compression": {
                "control": (0, 50),      # 50% 不压缩
                "compressed": (50, 100)   # 50% 压缩
            }
        }
        
        config = experiments.get(experiment)
        if not config:
            return "control"
        
        for variant, (start, end) in config.items():
            if start <= bucket < end:
                return variant
        
        return "control"
    
    async def record_experiment_result(
        self,
        experiment: str,
        variant: str,
        user_id: str,
        metrics: dict
    ):
        """记录实验结果"""
        
        await self.db.insert_experiment_result(
            experiment=experiment,
            variant=variant,
            user_id=user_id,
            metrics=metrics,
            timestamp=now()
        )
    
    async def analyze_experiment(self, experiment: str) -> dict:
        """分析实验结果"""
        
        results = await self.db.get_experiment_results(experiment)
        
        # 按变体分组
        by_variant = {}
        for r in results:
            if r.variant not in by_variant:
                by_variant[r.variant] = []
            by_variant[r.variant].append(r.metrics)
        
        # 计算统计显著性
        analysis = {}
        for variant, metrics_list in by_variant.items():
            analysis[variant] = {
                "sample_size": len(metrics_list),
                "avg_success_rate": np.mean([m["success_rate"] for m in metrics_list]),
                "avg_latency_ms": np.mean([m["latency_ms"] for m in metrics_list]),
                "avg_cost_usd": np.mean([m["cost_usd"] for m in metrics_list])
            }
        
        # 比较control vs treatment
        if "control" in analysis and "external_loop" in analysis:
            improvement = {
                "success_rate_lift": (
                    analysis["external_loop"]["avg_success_rate"] -
                    analysis["control"]["avg_success_rate"]
                ),
                "latency_reduction": (
                    analysis["control"]["avg_latency_ms"] -
                    analysis["external_loop"]["avg_latency_ms"]
                )
            }
            analysis["improvement"] = improvement
        
        return analysis
```

## 6. 日志与追踪

```python
# packages/core/monitor/logging.py

import structlog

# 结构化日志
logger = structlog.get_logger()

class AgentLogger:
    """Agent结构化日志"""
    
    def log_tool_call(
        self,
        session_id: str,
        tool_name: str,
        args: dict,
        result: dict,
        latency_ms: float
    ):
        logger.info(
            "tool_call",
            session_id=session_id,
            tool_name=tool_name,
            args=args,
            result_status=result.get("status"),
            latency_ms=latency_ms
        )
    
    def log_reflection(
        self,
        session_id: str,
        mode: str,
        iteration: int,
        improved: bool
    ):
        logger.info(
            "reflection",
            session_id=session_id,
            mode=mode,
            iteration=iteration,
            improved=improved
        )
    
    def log_error(
        self,
        session_id: str,
        error_type: str,
        error_message: str,
        stacktrace: str
    ):
        logger.error(
            "agent_error",
            session_id=session_id,
            error_type=error_type,
            error_message=error_message,
            stacktrace=stacktrace
        )
```

## 7. 总结

**TokenDance监控体系**：
1. **质量优先**：成功率、反思效果、引用准确性
2. **成本可控**：实时成本监控、异常告警
3. **持续改进**：A/B测试框架、数据驱动决策

**监控覆盖**：
- 实时监控：Dashboard + 异常检测
- 会话监控：质量评分 + 性能分析
- 系统监控：趋势分析 + A/B测试

**与其他模块集成**：
- Context Graph提供决策轨迹数据
- Memory存储历史质量模式
- Self-Reflection根据监控结果触发
- Planning根据成功率调整策略
