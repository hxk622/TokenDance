# TokenDance 金融场景完整设计方案 v1.0

**创建时间**: 2026-01-16  
**目标用户**: 个人投资者、行业分析师、基金经理助理  
**核心定位**: **"和 AI 一起研究"的协作工作台**，而非"等 AI 报告"的自动化工具

---

## 📊 竞品分析与定位

### 竞品对比矩阵

| 维度 | **MindSpider** | **OpenBB** | **BettaFish** | **Daily Stock Analysis** | **TokenDance (我们)** |
|-----|---------------|-----------|--------------|------------------------|-----------------------|
| **定位** | 金融数据终端 | 开源金融分析平台 | AI 投研报告生成 | 自动化选股报告 | **Vibe 投研工作台** |
| **交互模式** | 命令行 + GUI | Python 库 + Dashboard | 提问 → 等报告 | 订阅推送 | **实时协作 + 干预** |
| **数据源** | Bloomberg 级 | 多源免费数据 | 付费数据 + 爬虫 | Yahoo Finance | **多源整合 + 浏览器** |
| **核心价值** | 专业数据 | 开源生态 | 自动化报告 | 省时间 | **过程可视化 + 控制感** |
| **目标用户** | 专业交易员 | 量化开发者 | 个人投资者 | 散户 | **知识工作者** |
| **技术门槛** | 中高 | 高 | 低 | 极低 | **低（Vibe 降维）** |
| **价格** | $$$ | 免费 | $$ | $ | **Freemium** |
| **差异化** | 数据权威性 | 开源可扩展 | AI 自动化 | 简单易用 | **氛围感 + 协作感** |

### 关键洞察

#### MindSpider
- **优势**: 提供 Bloomberg 级金融数据终端，数据权威
- **局限**: 重数据轻协作，类似传统终端（Wind、东方财富）
- **启示**: 我们需要数据源集成能力，但不做数据提供商

#### OpenBB
- **优势**: 开源生态，100+ 数据源，可扩展性强
- **局限**: 面向开发者，需要编程能力
- **启示**: 可以集成 OpenBB SDK 作为底层数据层

#### BettaFish
- **优势**: AI 自动化报告生成，降低使用门槛
- **局限**: "黑盒"模式，用户无法干预过程
- **启示**: 我们要做"透明 + 可干预"的差异化

#### Daily Stock Analysis
- **优势**: 订阅推送，完全自动化
- **局限**: 无定制化，无法深度研究特定问题
- **启示**: 我们支持自定义研究主题

---

## 🎯 TokenDance 金融版核心定位

### 一句话定位
> **"TokenDance 金融版：不是替你炒股，而是让投研效率提升 10 倍的协作工作台"**

### 三大差异化优势

#### 1. Vibe Workflow - 氛围感投研
- **传统工具**: 冰冷的表格 + 静态报告
- **我们**: 三栏协作布局 + 实时数据流 + 色球动画 + 智能滚动

#### 2. 透明 + 可干预
- **BettaFish**: 提问 → 黑盒 → 等报告
- **我们**: 实时推理可视化 → 中途干预 → 修正方向 → 共同完成

#### 3. 工作流完整性
- **OpenBB**: 只有数据分析
- **我们**: 数据采集 → 深度分析 → 报告生成 → PPT 输出 → 团队协作

---

## 🏗️ 架构设计

### 数据流架构

```
┌─────────────────────────────────────────────────────────────┐
│                      用户输入层                              │
│  "分析贵州茅台的投资价值"                                    │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│              ExecutionRouter (智能路由)                      │
│  检测: 金融关键词 → 触发 financial_research Skill           │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│           FinancialResearchAgent (金融研究 Agent)           │
│  Phase 1: 范围界定 (个股/行业/宏观)                         │
│  Phase 2: 数据采集 (多源并行)                               │
│  Phase 3: 财务分析 (指标计算 + 对比)                        │
│  Phase 4: 估值分析 (PE/PB/DCF)                             │
│  Phase 5: 市场情绪 (舆情 + 资金流)                          │
│  Phase 6: 报告生成 (结构化输出)                             │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│               数据源整合层 (Data Provider)                   │
├──────────────┬──────────────┬──────────────┬────────────────┤
│  Tavily API  │  Browser     │  OpenBB SDK  │  Public APIs   │
│  (通用搜索)  │  (深度采集)  │  (金融数据)  │  (财报/新闻)   │
└──────────────┴──────────────┴──────────────┴────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                    分析引擎层                                │
├──────────────┬──────────────┬──────────────┬────────────────┤
│ 财务分析     │ 估值模型     │ 技术分析     │ 情绪分析       │
│ (Python)     │ (DCF/相对)   │ (K线/指标)   │ (NLP)          │
└──────────────┴──────────────┴──────────────┴────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                 前端可视化层 (Vibe UI)                       │
├──────────────┬──────────────┬──────────────────────────────┤
│  左: 研究导航 │  中: 分析内容 │  右: 实时数据流              │
│  - 核心指标  │  - Markdown   │  - K 线图 (Lightweight)      │
│  - 财务分析  │  - 图表       │  - 实时价格                  │
│  - 估值对比  │  - 引用来源   │  - 最新消息                  │
│  - 市场情绪  │  - AI 助手    │  - 情绪指数                  │
│  - 风险提示  │               │                              │
└──────────────┴──────────────┴──────────────────────────────┘
```

---

## 🔧 技术栈扩展

### 新增依赖

#### 后端
```python
# 金融数据
openbb>=4.0.0           # OpenBB Platform SDK
yfinance>=0.2.0         # Yahoo Finance
pandas-ta>=0.3.0        # 技术指标计算

# 情绪分析
transformers>=4.30.0    # NLP 模型
textblob>=0.17.0        # 简单情感分析

# 财务分析
numpy-financial>=1.0.0  # 财务计算 (DCF/IRR)
```

#### 前端
```json
{
  "dependencies": {
    "lightweight-charts": "^4.0.0",  // TradingView 图表库
    "chart.js": "^4.0.0",            // 通用图表
    "d3": "^7.8.0"                   // 自定义可视化
  }
}
```

### 数据源优先级

| 数据类型 | 优先级 1 | 优先级 2 | 优先级 3 |
|---------|---------|---------|---------|
| **实时行情** | Yahoo Finance | OpenBB | Browser 爬取 |
| **财务数据** | OpenBB | Browser (东方财富) | 公告 PDF |
| **新闻资讯** | Tavily API | Browser (财联社) | RSS |
| **研报观点** | Browser (雪球) | Browser (同花顺) | - |
| **舆情数据** | Browser (微博) | Browser (雪球) | - |

---

## 🎨 前端设计规范（Vibe 金融版）

### 配色系统（专业 Fintech 风格）

```css
/* 主色调：信任蓝 + 专业灰 */
--primary: #1e40af;        /* 蓝色 - 信任、稳定 */
--primary-light: #3b82f6;  /* 浅蓝 - 强调 */
--primary-dark: #1e3a8a;   /* 深蓝 - 标题 */

/* 背景（浅色模式优先） */
--bg-main: #fafafa;        /* 浅灰 - 主背景 */
--bg-card: #ffffff;        /* 白色 - 卡片 */
--bg-elevated: #f8f9fa;    /* 略灰 - 左侧栏 */

/* 文字 */
--text-primary: #111827;   /* 几乎黑 - 标题 */
--text-body: #1f2937;      /* 深灰 - 正文 */
--text-secondary: #6b7280; /* 中灰 - 辅助 */

/* 数据状态色 */
--bull: #16a34a;           /* 绿色 - 涨 */
--bear: #dc2626;           /* 红色 - 跌 */
--neutral: #9ca3af;        /* 灰色 - 持平 */

/* 分类标签色 */
--tag-finance: #f0f9ff;    /* 浅蓝 - 财务 */
--tag-valuation: #fef3c7;  /* 浅黄 - 估值 */
--tag-risk: #fee2e2;       /* 浅红 - 风险 */
--tag-sentiment: #f3e8ff;  /* 浅紫 - 情绪 */
```

### 核心组件库

| 组件 | 技术选型 | 用途 |
|-----|---------|-----|
| **MetricCard** | Vue 3 + Tailwind | 核心指标卡片 (PE/PB/ROE) |
| **ValuationTable** | Tanstack Table | 估值对比表格 |
| **SentimentRadar** | Chart.js Radar | 市场情绪雷达图 |
| **KLineChart** | Lightweight Charts | 实时 K 线图 |
| **TrendChart** | Chart.js Line | 财务趋势图 |
| **AIAssistant** | Custom Vue Component | AI 研究助手对话框 |

### 禁止事项（遵守 UI-UX-Pro-Max）

- ❌ Emoji 图标（🚀📈💰）→ 使用 Heroicons
- ❌ 彩虹渐变背景 → 单色或细微渐变
- ❌ `scale` hover 效果 → 使用 `border-color` + `shadow`
- ❌ 功能导向描述 → 用户任务导向描述

---

## 📋 开发任务拆解

### Phase 1: 基础架构（Week 1-2）

#### 任务 1.1: FinancialResearchAgent 核心
**文件**: `backend/app/agent/agents/financial_research.py`

**功能**:
- 继承 DeepResearchAgent
- 金融场景专属状态机：`scoping → collecting → analyzing → valuating → sentiment → reporting`
- 集成 financial_research_template.md
- 数据源路由：自动选择 Yahoo/OpenBB/Browser

**工作量**: 3-4 天  
**优先级**: P0

---

#### 任务 1.2: 金融数据工具集
**文件**: `backend/app/agent/tools/financial/`

**工具清单**:
```python
# 1. get_stock_quote.py - 实时行情
class GetStockQuoteTool(BaseTool):
    """获取股票实时行情（价格、涨跌幅、成交量）"""
    risk_level = RiskLevel.NONE
    operation_categories = [OperationCategory.WEB_READ]

# 2. get_financial_statements.py - 财务报表
class GetFinancialStatementsTool(BaseTool):
    """获取财务报表（资产负债表、利润表、现金流量表）"""

# 3. get_financial_ratios.py - 财务指标
class GetFinancialRatiosTool(BaseTool):
    """计算财务指标（ROE、毛利率、资产负债率等）"""

# 4. get_analyst_ratings.py - 分析师评级
class GetAnalystRatingsTool(BaseTool):
    """获取机构评级和目标价"""

# 5. get_market_sentiment.py - 市场情绪
class GetMarketSentimentTool(BaseTool):
    """分析社交媒体、新闻的市场情绪"""

# 6. calculate_valuation.py - 估值计算
class CalculateValuationTool(BaseTool):
    """计算 PE/PB/PS/DCF 估值"""
```

**工作量**: 5-6 天  
**优先级**: P0

---

#### 任务 1.3: OpenBB SDK 集成
**文件**: `backend/app/services/openbb_provider.py`

**功能**:
- OpenBB Platform 初始化
- 数据源管理（equity/economy/crypto/etf）
- 错误处理与降级（OpenBB 失败 → Yahoo Finance → Browser）

**示例**:
```python
from openbb import obb

class OpenBBProvider:
    async def get_stock_data(self, symbol: str) -> dict:
        """获取股票数据"""
        try:
            # OpenBB 优先
            data = obb.equity.price.historical(symbol)
            return data.to_dict()
        except Exception as e:
            # 降级到 Yahoo Finance
            return await self._fallback_yahoo(symbol)
```

**工作量**: 2-3 天  
**优先级**: P1

---

### Phase 2: 分析引擎（Week 3-4）

#### 任务 2.1: 财务分析模块
**文件**: `backend/app/services/financial_analyzer.py`

**功能**:
- 盈利能力分析（ROE/ROA/毛利率/净利率）
- 成长能力分析（营收增速/利润增速）
- 偿债能力分析（资产负债率/流动比率）
- 现金流分析（经营现金流/自由现金流）
- 财务健康度评分（0-100 分）

**工作量**: 3-4 天  
**优先级**: P0

---

#### 任务 2.2: 估值分析模块
**文件**: `backend/app/services/valuation_analyzer.py`

**功能**:
- 相对估值（PE/PB/PS/EV/EBITDA）
- 行业对比（与同行业平均对比）
- 历史估值（过去 5 年估值区间）
- DCF 简化模型（参考值，非精确计算）
- 合理估值区间建议

**工作量**: 3-4 天  
**优先级**: P1

---

#### 任务 2.3: 情绪分析模块
**文件**: `backend/app/services/sentiment_analyzer.py`

**功能**:
- 社交媒体抓取（微博、雪球、Twitter）
- 情感分类（积极/中性/消极）
- 关键词提取（利好/利空关键词）
- 情绪指数计算（0-100 分）
- 情绪趋势图（过去 30 天）

**依赖**:
```python
from transformers import AutoModelForSequenceClassification, AutoTokenizer
# 或使用 textblob（简单但不够准确）
```

**工作量**: 4-5 天  
**优先级**: P2（可延后）

---

### Phase 3: 前端 Vibe UI（Week 5-6）

#### 任务 3.1: 股票分析报告页面
**文件**: `frontend/src/views/FinancialReportView.vue`

**布局**: 三栏结构（参考前文设计）
- **左栏**: 研究导航（核心指标/财务/估值/情绪/风险）
- **中栏**: Markdown 报告 + 图表
- **右栏**: 实时数据流（K 线 + 价格 + 消息）

**组件清单**:
- `MetricCard.vue` - 指标卡片
- `ValuationTable.vue` - 估值对比表
- `SentimentRadar.vue` - 情绪雷达图
- `KLineChart.vue` - K 线图（Lightweight Charts）
- `FinancialTrendChart.vue` - 财务趋势图
- `AIAssistantBox.vue` - AI 助手对话框

**工作量**: 5-6 天  
**优先级**: P0

---

#### 任务 3.2: 实时数据流右侧栏
**文件**: `frontend/src/components/financial/RealtimePanel.vue`

**功能**:
- K 线图实时更新（WebSocket 或轮询）
- 价格跳动动画（数字跳动效果）
- 最新消息流（自动滚动）
- 情绪指数仪表盘

**技术选型**:
- Lightweight Charts (TradingView 开源)
- Chart.js (通用图表)
- Framer Motion (动画)

**工作量**: 3-4 天  
**优先级**: P1

---

#### 任务 3.3: AI 研究助手交互
**文件**: `frontend/src/components/financial/AIAssistant.vue`

**功能**:
- 卡片式对话框（浅蓝底 #f0f9ff）
- 预设问题（"这家公司的护城河在哪？"）
- 追问功能（"继续研究估值"）
- 历史对话记录

**设计要点**:
- 协作感 > 命令感
- 图标用 Heroicons 的 `BotIcon`
- 提问样式而非命令式按钮

**工作量**: 2-3 天  
**优先级**: P1

---

### Phase 4: 测试与优化（Week 7-8）

#### 任务 4.1: E2E 测试
**文件**: `backend/tests/e2e/test_financial_research.py`

**测试用例**:
- 完整研究流程（输入股票代码 → 生成报告）
- 数据源降级（OpenBB 失败 → Yahoo Finance）
- 估值计算准确性
- 情绪分析准确率

**工作量**: 3-4 天  
**优先级**: P1

---

#### 任务 4.2: 性能优化
**目标**:
- 报告生成时间 < 60s
- 前端首屏加载 < 2s
- 实时数据更新延迟 < 1s

**优化策略**:
- 数据缓存（Redis，TTL 5 分钟）
- 并行数据采集（asyncio.gather）
- 前端虚拟滚动（大量数据时）

**工作量**: 2-3 天  
**优先级**: P2

---

## 🚀 MVP 发布路线图

### Week 1-2: 基础架构
- [x] FinancialResearchAgent 核心（已有模板）
- [ ] 金融数据工具集
- [ ] OpenBB SDK 集成

### Week 3-4: 分析引擎
- [ ] 财务分析模块
- [ ] 估值分析模块
- [ ] 情绪分析模块（可延后）

### Week 5-6: Vibe UI
- [ ] 三栏布局报告页面
- [ ] 实时数据流右侧栏
- [ ] AI 研究助手交互

### Week 7-8: 测试优化
- [ ] E2E 测试
- [ ] 性能优化
- [ ] 合规审查（免责声明/风险提示）

---

## 📊 成功标准

### 功能完整性
- [ ] 输入股票代码/公司名，自动生成研究报告
- [ ] 报告包含：核心指标/财务/估值/情绪/风险 5 个章节
- [ ] 实时数据流：K 线图 + 价格 + 最新消息
- [ ] AI 助手支持追问和深度研究

### 用户体验（Vibe）
- [ ] 三栏布局响应式（1280px+）
- [ ] 滚动联动流畅（Scroll-Sync）
- [ ] 数据更新有动画反馈
- [ ] 整体氛围感评分 > 4.5/5

### 性能指标
- [ ] 报告生成时间 < 60s（中等复杂度）
- [ ] 前端首屏加载 < 2s
- [ ] 实时数据延迟 < 1s

### 合规要求
- [ ] 所有报告包含免责声明
- [ ] 不提供买卖建议
- [ ] 不预测股价
- [ ] 数据来源清晰标注

---

## ⚠️ 风险与挑战

### 技术风险
1. **数据源稳定性** - 爬虫可能被反爬/数据格式变化
   - **缓解**: 多源备份 + 降级策略
2. **估值模型准确性** - 简化 DCF 模型可能不够准确
   - **缓解**: 标注为"参考值"，不作为投资依据
3. **情绪分析准确率** - NLP 模型可能误判
   - **缓解**: 人工抽样验证 + 持续优化

### 合规风险
1. **法律边界** - 投研工具 vs 投资顾问
   - **缓解**: 清晰免责声明 + 只做信息整合
2. **数据版权** - 部分数据源可能有版权限制
   - **缓解**: 优先使用公开/免费数据源
3. **用户误用** - 用户将参考信息当作投资建议
   - **缓解**: 强化风险提示 + 用户教育

### 产品风险
1. **与 BettaFish 竞争** - 对方先发优势
   - **缓解**: 强化"协作导向"差异化
2. **用户留存** - 金融工具粘性依赖准确性
   - **缓解**: 定期更新模型 + 用户反馈闭环
3. **变现路径** - Freemium 转化率不确定
   - **缓解**: MVP 先验证价值，后优化商业模式

---

## 💰 商业化路径（初步）

### Freemium 模型

#### 免费版
- 每天 3 次研究额度
- 基础指标 + 财务分析
- 报告不可导出

#### Pro 版（$19.99/月）
- 无限研究次数
- 完整估值 + 情绪分析
- 报告导出（PDF/Markdown）
- AI 助手无限追问

#### Team 版（$99/月，5 人）
- Pro 版所有功能
- 团队协作（共享报告）
- 自定义模板
- API 接口

---

## 📚 参考资料

- **竞品**: MindSpider, OpenBB, BettaFish, Daily Stock Analysis
- **数据源**: Yahoo Finance, OpenBB, 东方财富, 雪球, 财联社
- **设计规范**: `docs/ux/UI-UX-Pro-Max-Integration.md`
- **模板**: `backend/app/skills/builtin/deep_research/resources/financial_research_template.md`

---

**文档维护者**: TokenDance 核心团队  
**最后更新**: 2026-01-16  
**版本历史**:
- v1.0 (2026-01-16): 初始版本，完整设计方案与任务拆解
