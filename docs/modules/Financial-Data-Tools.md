# 金融数据工具设计文档

> 集成结构化金融数据 + 非结构化舆情数据

## 设计原则

1. **数据全面性** - 结构化（财报/行情）+ 非结构化（舆情/情绪）
2. **合规可控** - 爬取开关 + 白名单/黑名单机制
3. **数据源可插拔** - 支持多数据源切换
4. **统一接口** - 对上层 Agent 暴露一致的 API

## 架构设计

```
┌─────────────────────────────────────────────────────────┐
│                TokenDance Financial Tools               │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │           FinancialDataRouter                    │   │
│  │  (根据查询类型路由到不同数据源)                   │   │
│  └──────────────────────┬──────────────────────────┘   │
│                         │                               │
│         ┌───────────────┼───────────────┐              │
│         ▼               ▼               ▼              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐      │
│  │ OpenBB      │ │ Sentiment   │ │ A-Stock     │      │
│  │ Adapter     │ │ Crawler     │ │ Adapter     │      │
│  │ ─────────── │ │ ─────────── │ │ ─────────── │      │
│  │ 美股/全球   │ │ 舆情采集    │ │ A股数据     │      │
│  │ 财报/行情   │ │ 情绪分析    │ │ 东方财富等  │      │
│  └─────────────┘ └─────────────┘ └─────────────┘      │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │           Compliance Control Layer               │   │
│  │  - 爬取开关 (enable_crawling: bool)             │   │
│  │  - 白名单 (allowed_domains: list)               │   │
│  │  - 黑名单 (blocked_domains: list)               │   │
│  │  - 频率限制 (rate_limit: int)                   │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## 数据源集成

### 1. 结构化金融数据 (OpenBB)

**数据类型**:
- 股票行情 (实时/历史)
- 财务报表 (资产负债表/利润表/现金流)
- 估值指标 (PE/PB/PS/EV)
- 机构持仓
- 分析师评级
- 宏观经济指标

**示例 API**:
```python
from openbb import obb

# 股票历史价格
obb.equity.price.historical("AAPL", provider="yfinance")

# 财务报表
obb.equity.fundamental.income("AAPL", provider="fmp")

# 估值指标
obb.equity.fundamental.metrics("AAPL")
```

**数据源**:
| Provider | 免费 | 需 API Key | 数据类型 |
|----------|------|------------|----------|
| Yahoo Finance | ✅ | ❌ | 行情/基本面 |
| FMP | 部分 | ✅ | 全面财务数据 |
| Polygon | 部分 | ✅ | 实时行情 |
| FRED | ✅ | ✅ | 宏观经济 |
| Alpha Vantage | 部分 | ✅ | 行情/技术指标 |

### 2. A 股数据 (补充)

OpenBB 对 A 股支持有限，需要补充数据源：

**候选方案**:
| 方案 | 优点 | 缺点 |
|------|------|------|
| AkShare | 免费、数据全 | 非官方 API |
| Tushare | 数据质量高 | 需积分/付费 |
| 东方财富 API | 官方接口 | 需要申请 |
| 同花顺 iFind | 专业级 | 企业付费 |

**推荐**: AkShare (开源) + Tushare (补充)

### 3. 非结构化舆情数据

**数据类型**:
- 财经新闻
- 社交媒体讨论 (雪球、微博财经)
- 股吧论坛
- 研报摘要
- 公告解读

**采集策略**:
```yaml
# 舆情采集配置
sentiment_crawler:
  enabled: true  # 总开关
  
  # 白名单模式 (只爬这些)
  whitelist_mode: true
  allowed_domains:
    - xueqiu.com       # 雪球 (投资社区)
    - guba.eastmoney.com  # 东方财富股吧
    - finance.sina.com.cn  # 新浪财经
    - cls.cn           # 财联社
    
  # 黑名单 (明确禁止)
  blocked_domains:
    - weibo.com        # 微博 (ToS 严格)
    - xiaohongshu.com  # 小红书 (非金融)
    - douyin.com       # 抖音 (反爬强)
    
  # 合规控制
  rate_limit: 10       # 每分钟请求数
  user_agent_rotate: true
  respect_robots_txt: true
  delay_between_requests: 3  # 秒
```

## 工具接口设计

### FinancialDataTool

```python
class FinancialDataTool(BaseTool):
    """金融数据获取工具"""
    
    name = "financial_data"
    description = "获取金融市场数据，包括行情、财报、估值、舆情等"
    
    async def execute(
        self,
        symbol: str,
        data_type: Literal["quote", "fundamental", "valuation", "sentiment", "news"],
        market: Literal["us", "cn", "hk"] = "us",
        **kwargs
    ) -> FinancialDataResult:
        """
        Args:
            symbol: 股票代码 (如 AAPL, 600519.SH)
            data_type: 数据类型
            market: 市场 (美股/A股/港股)
        """
        pass
```

### SentimentAnalysisTool

```python
class SentimentAnalysisTool(BaseTool):
    """舆情分析工具"""
    
    name = "sentiment_analysis"
    description = "分析特定股票/话题的市场情绪"
    
    async def execute(
        self,
        query: str,
        sources: list[str] = ["xueqiu", "guba"],
        time_range: str = "7d",
        limit: int = 50
    ) -> SentimentResult:
        """
        Args:
            query: 搜索关键词 (股票名称/代码/话题)
            sources: 数据源列表
            time_range: 时间范围
            limit: 结果数量限制
        
        Returns:
            SentimentResult:
                - overall_sentiment: float (-1 到 1)
                - sentiment_distribution: dict
                - key_opinions: list
                - trending_keywords: list
        """
        pass
```

## 合规控制层

### 配置文件

`config/financial_compliance.yaml`:

```yaml
# 金融数据采集合规配置
compliance:
  # 全局开关
  enable_web_crawling: true
  
  # 结构化数据 (API)
  structured_data:
    openbb:
      enabled: true
      providers: [yfinance, fmp, fred]
    akshare:
      enabled: true
    tushare:
      enabled: false  # 需要配置 token
      
  # 非结构化数据 (爬取)
  unstructured_data:
    mode: whitelist  # whitelist | blacklist | disabled
    
    # 白名单 - 允许采集的域名
    whitelist:
      - domain: xueqiu.com
        enabled: true
        rate_limit: 5/min
        description: "雪球 - 投资者社区"
        
      - domain: guba.eastmoney.com
        enabled: true
        rate_limit: 10/min
        description: "东方财富股吧"
        
      - domain: finance.sina.com.cn
        enabled: true
        rate_limit: 20/min
        description: "新浪财经新闻"
        
      - domain: cls.cn
        enabled: true
        rate_limit: 10/min
        description: "财联社快讯"
        
    # 黑名单 - 明确禁止的域名
    blacklist:
      - weibo.com
      - xiaohongshu.com
      - douyin.com
      - zhihu.com
      
  # 通用爬取规则
  crawling_rules:
    respect_robots_txt: true
    max_concurrent_requests: 3
    default_delay: 2  # 秒
    user_agent: "TokenDance/1.0 (Financial Research Bot)"
    timeout: 30
    
  # 数据保留策略
  data_retention:
    raw_data_ttl: 7d      # 原始数据保留 7 天
    processed_data_ttl: 30d  # 处理后数据保留 30 天
    
  # 免责声明
  disclaimer: |
    本工具仅用于投资研究辅助，采集的舆情数据仅供参考。
    用户应自行遵守相关法律法规和平台服务条款。
    TokenDance 不对数据的准确性和合规性承担责任。
```

### 运行时检查

```python
class ComplianceChecker:
    """合规检查器"""
    
    def __init__(self, config_path: str):
        self.config = load_config(config_path)
        
    def can_crawl(self, domain: str) -> tuple[bool, str]:
        """检查是否允许爬取指定域名"""
        
        if not self.config.enable_web_crawling:
            return False, "Web crawling is globally disabled"
            
        if self.config.mode == "disabled":
            return False, "Unstructured data crawling is disabled"
            
        if domain in self.config.blacklist:
            return False, f"{domain} is in blacklist"
            
        if self.config.mode == "whitelist":
            if domain not in [w.domain for w in self.config.whitelist]:
                return False, f"{domain} is not in whitelist"
                
        return True, "OK"
        
    def get_rate_limit(self, domain: str) -> int:
        """获取指定域名的频率限制"""
        for w in self.config.whitelist:
            if w.domain == domain:
                return w.rate_limit
        return self.config.crawling_rules.default_rate_limit
```

## 数据流程

```
用户请求: "分析贵州茅台的投资价值"
        │
        ▼
┌───────────────────────────────────────┐
│       Intent Parser                    │
│  识别: symbol=600519, market=cn       │
│  需要: 基本面 + 估值 + 舆情           │
└───────────────────────────────────────┘
        │
        ├──────────────────┬──────────────────┐
        ▼                  ▼                  ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ 结构化数据   │    │ A股数据     │    │ 舆情数据    │
│ (OpenBB)    │    │ (AkShare)   │    │ (Crawler)   │
│             │    │             │    │             │
│ - 财务报表  │    │ - 实时行情  │    │ - 雪球讨论  │
│ - 估值指标  │    │ - 北向资金  │    │ - 股吧热帖  │
│ - 机构持仓  │    │ - 龙虎榜    │    │ - 财经新闻  │
└─────────────┘    └─────────────┘    └─────────────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           ▼
              ┌─────────────────────────┐
              │    Data Aggregator      │
              │  数据聚合 + 标准化       │
              └─────────────────────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │    Analysis Engine      │
              │  财务分析 + 情绪分析     │
              └─────────────────────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │    Report Generator     │
              │  生成投研报告            │
              └─────────────────────────┘
```

## 实现优先级

### Phase 1: 基础数据能力 (1-2 周)
- [ ] OpenBB SDK 集成
- [ ] A 股数据适配器 (AkShare)
- [ ] 合规配置文件

### Phase 2: 舆情采集 (2-3 周)
- [ ] 舆情爬虫框架
- [ ] 白名单域名适配 (雪球、股吧)
- [ ] 情绪分析模块

### Phase 3: 数据融合 (1-2 周)
- [ ] 数据聚合器
- [ ] 投研报告生成
- [ ] 与 Deep Research 集成

## 技术选型

| 组件 | 选型 | 理由 |
|------|------|------|
| 结构化数据 | OpenBB | 成熟、数据源丰富 |
| A 股数据 | AkShare | 开源、免费、数据全 |
| 舆情爬取 | Playwright | 已有基础设施 |
| 情绪分析 | Claude API | 高质量中文理解 |
| 数据存储 | PostgreSQL + Redis | 持久化 + 缓存 |

## 参考资源

- OpenBB 文档: https://docs.openbb.co
- AkShare 文档: https://akshare.akfamily.xyz
- BettaFish 架构: https://github.com/666ghj/BettaFish
- MindSpider 参考: https://github.com/666ghj/MindSpider
