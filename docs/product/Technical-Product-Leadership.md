# TokenDance 技术与产品领先性

**版本**: v1.0  
**日期**: 2026-01-17

---

## 🎯 核心定位

> **TokenDance: Vibe-Agentic Workflow Platform - 人机共生的智能工作台**

不同于传统的 AI 工具，TokenDance 追求的是 **"和 AI 一起工作"** 的协作体验，而非简单的自动化替代。

---

## 🏆 技术领先性

### 1. Agent Runtime 架构

TokenDance 是 **Agent Runtime**，而非通用智能体。

**核心五律** (详见 `docs/architecture/Agent-Runtime-Design.md`):
1. **工具先于推理** - 有结构化工具优先调用
2. **透明先于效率** - 实时推理可视化
3. **控制先于自主** - 用户可中途干预
4. **沉淀先于遗忘** - Context Graph 记录决策
5. **协作先于替代** - 增强人类而非替代

### 2. 三路执行混合架构

```
用户请求
    ↓
ExecutionRouter (路由决策)
    ├─ 80%+ 置信度 → SKILL PATH (⚡ <100ms)
    ├─ 结构化任务 → MCP CODE PATH (🔧 <5s)  
    └─ 其他 → LLM REASONING PATH (🧠 adaptive)
```

- **Skill Path**: 预构建能力，毫秒级响应
- **MCP Code Path**: LLM 生成代码，沙箱执行
- **LLM Path**: 推理生成，灵活应对

### 3. 三文件工作法 (Working Memory)

借鉴 Manus 架构，实现 **Token 节省 60-80%**：

| 文件 | 作用 |
|------|------|
| `task_plan.md` | 任务路线图 + 阶段目标 |
| `findings.md` | 研究发现 + 技术决策 |
| `progress.md` | 执行日志 + 错误记录 |

**核心规则**:
- **2-Action Rule**: 每 2 次重大操作写入 findings
- **3-Strike Protocol**: 同类错误 3 次触发恢复
- **Plan Recitation**: 每次开始前重读计划

### 4. Append-Only Context 模式

- **KV-Cache 100% 命中率**: 只追加不修改
- **7x 性能提升**: 相比每轮重构 context
- **简化状态管理**: 所有消息永久保留

### 5. 金融分析引擎 (11,000+ 行)

**财务分析 (FinancialAnalyzer)**:
- 五维分析: 盈利/成长/偿债/效率/现金流
- 多权重评分: 30%+25%+20%+15%+10%
- HealthLevel 分级: EXCELLENT → CRITICAL

**估值分析 (ValuationAnalyzer)**:
- 相对估值: PE/PB/PS/EV-EBITDA/PEG
- 历史估值: 5年区间 + 百分位
- 行业对比: 溢价/折价 + 排名
- DCF 模型: 简化折现 + 敏感性分析

**技术指标 (TechnicalIndicators)**:
- 趋势: MACD, SMA/EMA, ADX
- 动量: RSI, KDJ, Williams %R, CCI, ROC
- 波动: 布林带, ATR
- 成交量: OBV, 量比

### 6. 多源数据降级策略

```
美股: OpenBB (yfinance) → OpenBB (fmp) → Mock
A股:  AkShare → Mock
港股: OpenBB (yfinance) → Mock
```

- 市场自动检测: US/CN/HK
- Provider 健康检查: 连续失败自动切换
- 差异化 TTL: 行情 5min, 财报 1h, 估值 30min

---

## 💡 产品领先性

### 1. Vibe Workflow 设计理念

**核心主张**: 以情绪价值和认知流为核心的设计范式

| 维度 | 传统工具 | Vibe Workflow |
|------|----------|---------------|
| 目标 | 完成任务 | 享受过程 |
| 反馈 | 二元反馈 | 情感激励 |
| 用户状态 | 被动疲劳 | 主动沉浸 |
| 产品门槛 | 学习手册 | 直觉探索 |

### 2. 透明 + 可干预

- **实时推理可视化**: Chain-of-Thought 展示
- **中途干预**: 用户可调整方向
- **Working Memory UI**: 三文件面板可视化
- **HITL 确认**: 高风险操作人工确认

### 3. 信任等级机制

**风险等级**: NONE → LOW → MEDIUM → HIGH → CRITICAL

- **动态风险评估**: 工具可根据参数动态计算
- **会话级授权**: "记住此选择" 减少重复确认
- **审计日志**: 所有授权决策可追溯

### 4. Skill 冷启动优化

- **场景预设**: 8 个预配置工作场景
- **模板系统**: 10+ 研究/PPT 模板
- **智能发现**: /discover 页面引导探索

---

## 📊 竞品差异化

| 维度 | Claude Cowork | MindSpider | BettaFish | **TokenDance** |
|------|---------------|------------|-----------|----------------|
| 定位 | 通用 Agent | 数据终端 | 自动报告 | **协作工作台** |
| 透明度 | 中 | 低 | 低 | **高** |
| 可干预 | 低 | 中 | 无 | **高** |
| Vibe | ❌ | ❌ | ❌ | **✅** |
| 金融专业 | ❌ | ✅ | ✅ | **✅** |
| 开源 | ❌ | ❌ | ❌ | **✅** |

---

## 🚀 核心价值主张

1. **Vibe Workflow**: 氛围感工作体验，而非冰冷的数据堆砌
2. **透明 + 可干预**: 实时可视化 + 中途调整 + HITL 确认
3. **专业级分析**: 五维财务分析 + 智能估值 + 技术指标
4. **工作流完整性**: 数据采集 → 分析 → 报告 → PPT → 协作

---

## 📚 参考文档

| 文档 | 内容 |
|------|------|
| `docs/architecture/Agent-Runtime-Design.md` | Agent Runtime 五律 |
| `docs/product/VisionAndMission.md` | 产品愿景 |
| `docs/product/Financial-Product-Plan.md` | 金融场景设计 |
| `docs/product/Financial-Achievement-Summary.md` | 金融技术成就 |
| `docs/ux/DESIGN-PRINCIPLES.md` | UI 设计原则 |

---

**文档维护**: TokenDance Core Team  
**最后更新**: 2026-01-17
