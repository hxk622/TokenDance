# Neo4j图数据库集成指南

## 📋 架构决策

基于MemMachine的实践和长期考虑，TokenDance采用**PostgreSQL + Neo4j混合架构**：

```
PostgreSQL (主存储):
├── 用户数据、会话、消息 (ACID保证)
├── user_memories表 (pgvector向量检索)
└── 完整历史数据

Neo4j (图查询加速):
├── Context Graph (决策轨迹图)
├── Memory Relations (记忆关联图)
├── Reflection Chains (反思链)
└── Planning Dependencies (计划依赖图)
```

## 🎯 为什么需要图数据库？

### 1. Context Graph天然是图结构
```
决策节点 → 工具调用 → 结果 → 反思 → 新决策
   ↓           ↓           ↓
 因果关系   依赖关系   时序关系
```

### 2. 未来功能需求明确
- Self-Reflection: 反思链追踪、改进效果分析
- Memory: 记忆关联查询 (2-3跳)
- Planning: 依赖图、影响分析
- Monitor: 失败模式挖掘、路径分析

### 3. MemMachine的实践验证
MemMachine用Neo4j存储Episodic Memory，证明图数据库适合Agent场景

## 🏗️ 数据同步策略

```python
class HybridStorageManager:
    """混合存储管理器"""
    
    async def record_decision(self, decision_data):
        # 1. PostgreSQL: 主存储 (ACID)
        node_id = await self.pg.insert_context_node(decision_data)
        
        # 2. Neo4j: 图关系 (异步同步)
        await self.neo4j.create_node(
            id=node_id,
            labels=["Decision"],
            properties={"summary": ...}  # 只存摘要
        )
        
        return node_id
```

**原则**: 
- PostgreSQL为数据真相源 (Source of Truth)
- Neo4j为查询加速层 (Query Accelerator)
- 异步同步，不阻塞主流程

## 📊 Neo4j图模型设计

### Context Graph
```cypher
// 节点类型
(:Decision {id, session_id, type, timestamp, summary})
(:ToolCall {id, tool_name, status})
(:ReflectionAttempt {id, iteration, score})

// 关系类型
()-[:LEADS_TO]->()      // 决策链
()-[:CALLS_TOOL]->()    // 工具调用
()-[:REFLECTED_TO]->()  // 反思链
()-[:DEPENDS_ON]->()    // 依赖关系
```

### Memory Relations
```cypher
(:Memory {id, user_id, content_summary, type})
()-[:SUPPORTS]->()      // 支持
()-[:CONTRADICTS]->()   // 矛盾
()-[:REFINES]->()       // 精炼
```

## 🔍 常用Cypher查询

### 1. 查找决策链
```cypher
MATCH path = (start:Decision {id: $node_id})-[:LEADS_TO*1..5]->(end)
RETURN path
```

### 2. 分析反思效果
```cypher
MATCH (before:ReflectionAttempt)-[:REFLECTED_TO]->(after:ReflectionAttempt)
WHERE after.score > before.score
RETURN COUNT(*) as improvements, AVG(after.score - before.score) as avg_gain
```

### 3. 查找相关记忆
```cypher
MATCH (m:Memory {id: $memory_id})-[*1..2]-(related:Memory)
RETURN DISTINCT related.id
```

## 🚀 实施路径

### Phase 1: 基础搭建 (Week 1-4)
- [x] PostgreSQL + pgvector (Memory向量检索)
- [x] Context Graph基础表结构
- [ ] Neo4j Docker部署

### Phase 2: 图数据库集成 (Week 5-6)
- [ ] 实现HybridStorageManager
- [ ] 异步同步PostgreSQL → Neo4j
- [ ] Context Graph迁移到Neo4j
- [ ] Memory Relations图查询

### Phase 3: 高级功能 (Week 7+)
- [ ] Reflection链分析Dashboard
- [ ] 失败模式自动发现
- [ ] Planning依赖可视化
- [ ] 图神经网络 (可选，未来)

## 📦 Neo4j部署配置

```yaml
# docker-compose.yml 片段

services:
  neo4j:
    image: neo4j:5.15
    container_name: tokendance_neo4j
    ports:
      - "7474:7474"  # HTTP
      - "7687:7687"  # Bolt
    environment:
      NEO4J_AUTH: neo4j/tokendance_password
      NEO4J_PLUGINS: '["apoc", "graph-data-science"]'
    volumes:
      - ./neo4j_data:/data
      - ./neo4j_logs:/logs
    restart: unless-stopped
```

## 🔗 参考资料

- **MemMachine架构**: Episodic Memory → Neo4j, Profile Memory → SQL
- **Neo4j最佳实践**: https://neo4j.com/developer/guide-data-modeling/
- **混合架构案例**: https://neo4j.com/blog/polyglot-persistence/

## ✅ 更新的设计文档

需要查看完整设计的文档：
1. `docs/architecture/LLD.md` - 数据库Schema (待更新详细Neo4j模型)
2. `docs/modules/Context-Graph.md` - Neo4j实现 (待全面改写Cypher查询)
3. `docs/modules/Memory.md` - Memory Relations图查询 (待添加示例)
4. `docs/modules/Self-Reflection.md` - 反思链图分析 (待添加Cypher)
5. `docs/modules/Monitor-Evaluation.md` - 图分析指标 (待添加)

---

**结论**: 图数据库是TokenDance长期架构的重要组成部分，从第一天就正确，为未来扩展打好基础。
