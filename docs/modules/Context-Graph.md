# Context Graph设计文档

## 1. 核心概念

**Context Graph（上下文图谱）**：记录决策轨迹而非静态数据

- **不是**：知识图谱（实体-关系）
- **而是**：决策图谱（动作-结果-反馈）

## 2. 记录什么

```python
# 每个微小决策

class ContextGraphNode:
    id: str
    timestamp: datetime
    type: str  # reasoning/tool_call/planning/memory_access/file_op
    
    # 核心信息
    input: dict        # 输入是什么
    action: str        # 做了什么动作
    output: dict       # 输出是什么
    error: Optional[str]  # 是否失败
    
    # 上下文
    session_id: str
    parent_node_id: Optional[str]  # 因果链
    metadata: dict

# 示例：工具调用节点
{
  "type": "tool_call",
  "input": {"tool": "web_search", "query": "AI Agent架构"},
  "action": "execute_tool",
  "output": {"results": [...]},
  "error": null,
  "metadata": {
    "latency_ms": 230,
    "tokens_in_result": 1500
  }
}

# 示例：推理节点
{
  "type": "reasoning",
  "input": {"task": "生成PPT"},
  "action": "plan_generation",
  "output": {"plan": [...], "reasoning_steps": [...]},
  "error": null
}
```

## 3. 数据模型

```python
# packages/core/context_graph/models.py

class ContextGraphDB:
    """使用PostgreSQL存储图谱"""
    
    async def add_node(
        self,
        session_id: str,
        node_type: str,
        input_data: dict,
        action: str,
        output_data: dict,
        error: Optional[str] = None,
        parent_node_id: Optional[str] = None
    ) -> str:
        """添加决策节点"""
        node_id = str(uuid4())
        
        await self.db.execute("""
            INSERT INTO context_graph_nodes 
            (id, session_id, type, input, action, output, error, parent_node_id, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW())
        """, node_id, session_id, node_type, json.dumps(input_data), 
            action, json.dumps(output_data), error, parent_node_id)
        
        return node_id
    
    async def get_decision_chain(self, session_id: str) -> List[Node]:
        """获取完整决策链"""
        return await self.db.fetch("""
            SELECT * FROM context_graph_nodes
            WHERE session_id = $1
            ORDER BY created_at ASC
        """, session_id)
    
    async def get_failure_patterns(self, user_id: str) -> List[dict]:
        """分析失败模式"""
        return await self.db.fetch("""
            SELECT 
                type,
                action,
                error,
                COUNT(*) as failure_count
            FROM context_graph_nodes
            WHERE error IS NOT NULL
              AND session_id IN (
                SELECT id FROM sessions WHERE user_id = $1
              )
            GROUP BY type, action, error
            ORDER BY failure_count DESC
            LIMIT 10
        """, user_id)
```

## 4. 核心价值

### 4.1 审计追踪

```python
# 查询："Agent为什么这么做？"

async def explain_decision(session_id: str, message_id: str):
    """解释某个决策"""
    
    # 找到该消息对应的决策节点
    nodes = await context_graph.get_nodes_for_message(message_id)
    
    # 构建因果链
    explanation = []
    for node in nodes:
        explanation.append(f"""
步骤 {node.id}:
- 输入：{node.input}
- 动作：{node.action}
- 输出：{node.output}
- 原因：{node.metadata.get('reasoning', '...')}
""")
    
    return "\n".join(explanation)
```

### 4.2 失败分析

```python
# 分析："哪些操作经常失败？"

async def analyze_failures(user_id: str):
    patterns = await context_graph.get_failure_patterns(user_id)
    
    # 返回Top失败模式
    return [
        {
            "action": p["action"],
            "error": p["error"],
            "count": p["failure_count"],
            "suggestion": suggest_fix(p["action"], p["error"])
        }
        for p in patterns
    ]
```

### 4.3 模式自动涌现

```python
# 不需要预定义schema，关联性自动涌现

# 示例：发现"Deep Research"总是这个序列
# web_search → read_url → summarize → write_file

async def discover_patterns(user_id: str):
    """发现常见操作序列"""
    
    # 提取所有成功的工具调用链
    chains = await context_graph.get_successful_chains(user_id)
    
    # 使用序列挖掘算法
    frequent_patterns = find_frequent_sequences(chains, min_support=3)
    
    # 生成Skill建议
    for pattern in frequent_patterns:
        skill_name = f"auto_skill_{hash(pattern)}"
        print(f"发现模式: {' → '.join(pattern.steps)}")
        print(f"建议创建Skill: {skill_name}")
```

## 5. 与其他模块集成

```python
# 所有模块都向Context Graph记录决策

# Reasoning模块
await context_graph.add_node(
    type="reasoning",
    action="retry_after_failure",
    input={"attempt": 2},
    output={"success": True}
)

# Tool-Use模块
await context_graph.add_node(
    type="tool_call",
    action="execute_web_search",
    input={"query": "..."},
    output={"results": [...]}
)

# Memory模块
await context_graph.add_node(
    type="memory_access",
    action="retrieve_memories",
    input={"query": "..."},
    output={"memories": [...]}
)

# Planning模块
await context_graph.add_node(
    type="planning",
    action="create_plan",
    input={"goal": "..."},
    output={"plan": {...}}
)
```

## 6. UI可视化

```vue
<!-- 决策轨迹可视化 -->
<template>
  <div class="context-graph-viewer">
    <div class="timeline">
      <div v-for="node in nodes" :key="node.id" 
           :class="['node', node.type, node.error ? 'failed' : 'success']">
        <div class="node-header">
          <Icon :name="getIconForType(node.type)" />
          <span>{{ node.action }}</span>
          <span class="timestamp">{{ formatTime(node.created_at) }}</span>
        </div>
        
        <div class="node-details" v-if="expandedNodes.includes(node.id)">
          <div class="input">输入: {{ node.input }}</div>
          <div class="output">输出: {{ node.output }}</div>
          <div v-if="node.error" class="error">错误: {{ node.error }}</div>
        </div>
      </div>
    </div>
  </div>
</template>
```

## 7. 性能优化

```python
# 分区表（按时间）
CREATE TABLE context_graph_nodes (
    id UUID PRIMARY KEY,
    session_id UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    ...
) PARTITION BY RANGE (created_at);

CREATE TABLE context_graph_nodes_2026_01 PARTITION OF context_graph_nodes
FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

# 索引
CREATE INDEX idx_nodes_session ON context_graph_nodes(session_id, created_at DESC);
CREATE INDEX idx_nodes_type ON context_graph_nodes(type);
CREATE INDEX idx_nodes_error ON context_graph_nodes(error) WHERE error IS NOT NULL;
```

## 8. 总结

**核心价值**：
1. **审计追踪**：解释"发生了什么"和"为什么"
2. **失败分析**：识别常见错误模式
3. **模式涌现**：自动发现最佳实践

**与其他模块关系**：
- 所有模块都向Graph记录决策
- Memory可以从Graph提取Procedural Memory
- Reasoning从Graph学习历史失败
- Monitor从Graph统计质量指标
