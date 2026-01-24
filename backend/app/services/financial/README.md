# 金融服务模块 Mock 数据说明

## 概述

金融服务模块（`backend/app/services/financial/`）目前使用 **mock 数据**进行演示。这些模块需要集成真实的金融数据源（如 Wind、东方财富、Tushare 等 API）才能提供真实数据。

## 配置

### 环境变量

```bash
# 数据模式配置
FINANCIAL_DATA_MODE=error  # 默认值，使用 mock 数据时会抛出错误
# FINANCIAL_DATA_MODE=mock   # 允许使用 mock 数据（演示模式）
# FINANCIAL_DATA_MODE=real   # 使用真实数据源（需要实现）
```

### 模式说明

- **`error`** (默认): 调用金融服务时会抛出 `FinancialServiceNotImplementedError`，明确告知功能未实现
- **`mock`**: 允许使用 mock 数据进行演示和测试
- **`real`**: 使用真实数据源（需要实现数据源集成）

## 已清理的模块

以下模块已添加 mock 数据检查和说明：

### 事件分析模块
- ✅ `event/event_calendar.py` - 事件日历服务
- ✅ `event/earnings_surprise.py` - 业绩超预期分析

### 行业分析模块
- ⚠️ `industry/industry_ranking.py` - 行业排名
- ⚠️ `industry/peer_comparison.py` - 同行对比
- ⚠️ `industry/rotation_analysis.py` - 行业轮动
- ⚠️ `industry/sector_map.py` - 板块地图

### 投资组合模块
- ⚠️ `portfolio/risk_attribution.py` - 风险归因
- ⚠️ `portfolio/var_calculator.py` - VaR 计算

### 关系分析模块
- ⚠️ `relation/customer_supplier.py` - 客户供应商关系
- ⚠️ `relation/knowledge_graph.py` - 知识图谱
- ⚠️ `relation/supply_chain_map.py` - 供应链地图

### 情绪分析模块
- ⚠️ `sentiment/sentiment_timeseries.py` - 情绪时间序列

## 使用方式

### 开发/演示环境

如果需要使用 mock 数据进行演示：

```bash
# 设置环境变量
export FINANCIAL_DATA_MODE=mock

# 或在 .env 文件中
FINANCIAL_DATA_MODE=mock
```

### 生产环境

生产环境应该：

1. **保持默认配置** (`FINANCIAL_DATA_MODE=error`)，确保不会返回假数据
2. **实现真实数据源集成**，然后设置 `FINANCIAL_DATA_MODE=real`

## 错误处理

当 `FINANCIAL_DATA_MODE=error` 时，调用金融服务会抛出：

```python
FinancialServiceNotImplementedError:
    Financial service 'EventCalendarService' feature 'get_upcoming_events' is not yet implemented.
    This requires integration with real data sources (APIs, databases).
    To use mock data for demonstration, set FINANCIAL_DATA_MODE=mock
```

前端应该捕获这个错误并显示友好的提示信息。

## 实现真实数据源

要实现真实数据源，需要：

1. **选择数据源**: Wind、东方财富、Tushare、聚宽等
2. **实现数据适配器**: 在每个服务中实现真实数据获取逻辑
3. **配置 API 密钥**: 在环境变量中配置数据源 API 密钥
4. **测试验证**: 确保数据准确性和性能
5. **更新配置**: 设置 `FINANCIAL_DATA_MODE=real`

## 示例代码

```python
from app.services.financial.config import check_data_mode_or_raise, FINANCIAL_DATA_MODE, DataMode

class MyFinancialService:
    async def get_data(self, symbol: str):
        # 检查是否允许使用 mock 数据
        if FINANCIAL_DATA_MODE == Dde.MOCK:
            return self._get_mock_data(symbol)
        elif FINANCIAL_DATA_MODE == DataMode.REAL:
            return await self._get_real_data(symbol)
        else:
            # 抛出未实现错误
            check_data_mode_or_raise("MyFinancialService", "get_data")

    def _get_mock_data(self, symbol: str):
        # Mock 数据逻辑
        return {"symbol": symbol, "data": "mock"}

    async def _get_real_data(self, symbol: str):
        # 真实数据源集成
        # 例如：调用 Wind API、Tushare API 等
        raise NotImplementedError("Real data source not implemented yet")
```

## 注意事项

1. **不要在生产环境使用 mock 数据**
2. **前端应该处理 `FinancialServiceNotImplementedError` 错误**
3. **Mock 数据仅用于演示和测试**
4. **实现真实数据源时要注意数据质量和性能**

## 相关文件

- `backend/app/services/financial/config.py` - 配置和错误定义
- `backend/app/services/financial/README.md` - 本文档
