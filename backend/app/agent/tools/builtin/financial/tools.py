# -*- coding: utf-8 -*-
"""
Financial Data Tools - BaseTool Interface

将 FinancialDataTool 包装为符合 BaseTool 接口的工具集，
供 Agent 调用。

包含：
- GetStockQuoteTool: 实时/延迟行情
- GetFinancialStatementsTool: 财务报表
- GetFinancialRatiosTool: 财务指标
- GetMarketSentimentTool: 市场情绪（新闻+舆情）
- CalculateValuationTool: 估值计算

所有工具共享同一个 FinancialDataTool 实例，避免重复初始化。
"""
import json
import logging
from typing import Any, Dict, List, Literal, Optional

from app.agent.tools.base import BaseTool, ToolResult
from app.agent.tools.risk import RiskLevel, OperationCategory
from app.agent.tools.builtin.financial.financial_data_tool import (
    FinancialDataTool,
    get_financial_tool,
)
from app.agent.tools.builtin.financial.adapters.base import FinancialDataResult

logger = logging.getLogger(__name__)


def _format_result(result: FinancialDataResult) -> str:
    """格式化金融数据结果为文本"""
    if not result.success:
        return f"Error: {result.error}"
    
    output = f"**Symbol**: {result.symbol}\n"
    output += f"**Market**: {result.market}\n"
    output += f"**Data Type**: {result.data_type}\n"
    output += f"**Source**: {result.source}\n"
    output += f"**Timestamp**: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    if result.data:
        if isinstance(result.data, list):
            output += f"**Records**: {len(result.data)}\n\n"
            # 只显示前5条
            for i, item in enumerate(result.data[:5], 1):
                output += f"### Record {i}\n"
                output += json.dumps(item, ensure_ascii=False, indent=2, default=str)[:500]
                output += "\n\n"
            if len(result.data) > 5:
                output += f"... and {len(result.data) - 5} more records\n"
        else:
            output += "**Data**:\n```json\n"
            output += json.dumps(result.data, ensure_ascii=False, indent=2, default=str)[:2000]
            output += "\n```\n"
    
    return output


class GetStockQuoteTool(BaseTool):
    """获取股票实时/延迟行情
    
    支持：
    - 美股: 输入股票代码如 "AAPL", "MSFT"
    - A股: 输入6位代码如 "600519", "000001"
    - 港股: 输入代码如 "0700.HK", "9988.HK"
    
    返回数据包括: 当前价格、涨跌幅、成交量、市盈率、市净率等
    """
    
    name = "get_stock_quote"
    description = """获取股票实时/延迟行情。

支持市场:
- 美股: AAPL, MSFT, GOOGL 等
- A股: 600519 (茅台), 000001 (平安) 等6位代码
- 港股: 0700.HK (腾讯), 9988.HK (阿里) 等

返回数据: 价格、涨跌幅、成交量、PE、PB、市值等

示例:
- 获取苹果股价: symbol="AAPL"
- 获取茅台股价: symbol="600519"
"""
    
    parameters = {
        "type": "object",
        "properties": {
            "symbol": {
                "type": "string",
                "description": "股票代码。美股用字母（AAPL），A股用6位数字（600519），港股加.HK后缀（0700.HK）"
            },
            "market": {
                "type": "string",
                "enum": ["auto", "us", "cn", "hk"],
                "default": "auto",
                "description": "市场类型。auto=自动检测, us=美股, cn=A股, hk=港股"
            }
        },
        "required": ["symbol"]
    }
    
    risk_level = RiskLevel.NONE
    operation_categories = [OperationCategory.WEB_READ]
    
    def __init__(self):
        super().__init__()
        self._tool = get_financial_tool()
    
    async def execute(self, symbol: str, market: str = "auto", **kwargs) -> str:
        """执行获取行情"""
        logger.info(f"Getting stock quote for {symbol} (market={market})")
        
        result = await self._tool.get_quote(symbol, market=market, **kwargs)
        return _format_result(result)


class GetFinancialStatementsTool(BaseTool):
    """获取公司财务报表
    
    获取上市公司的财务报表数据，包括：
    - 利润表 (Income Statement)
    - 资产负债表 (Balance Sheet)
    - 现金流量表 (Cash Flow Statement)
    """
    
    name = "get_financial_statements"
    description = """获取上市公司财务报表。

报表类型:
- income: 利润表（营收、利润、费用）
- balance: 资产负债表（资产、负债、股东权益）
- cashflow: 现金流量表（经营、投资、筹资现金流）
- all: 获取全部三张报表

示例:
- 获取苹果全部财报: symbol="AAPL", statement_type="all"
- 获取茅台利润表: symbol="600519", statement_type="income"
"""
    
    parameters = {
        "type": "object",
        "properties": {
            "symbol": {
                "type": "string",
                "description": "股票代码"
            },
            "statement_type": {
                "type": "string",
                "enum": ["income", "balance", "cashflow", "all"],
                "default": "all",
                "description": "报表类型"
            },
            "market": {
                "type": "string",
                "enum": ["auto", "us", "cn", "hk"],
                "default": "auto",
                "description": "市场类型"
            },
            "period": {
                "type": "string",
                "enum": ["annual", "quarterly"],
                "default": "annual",
                "description": "报告周期（年报或季报）"
            }
        },
        "required": ["symbol"]
    }
    
    risk_level = RiskLevel.NONE
    operation_categories = [OperationCategory.WEB_READ]
    
    def __init__(self):
        super().__init__()
        self._tool = get_financial_tool()
    
    async def execute(
        self,
        symbol: str,
        statement_type: str = "all",
        market: str = "auto",
        period: str = "annual",
        **kwargs
    ) -> str:
        """执行获取财务报表"""
        logger.info(f"Getting financial statements for {symbol} (type={statement_type})")
        
        result = await self._tool.get_fundamental(
            symbol,
            statement_type=statement_type,
            market=market,
            period=period,
            **kwargs
        )
        return _format_result(result)


class GetValuationMetricsTool(BaseTool):
    """获取估值指标
    
    获取股票的估值指标，包括：
    - PE (市盈率): 股价 / 每股收益
    - PB (市净率): 股价 / 每股净资产
    - PS (市销率): 市值 / 营业收入
    - PEG: PE / 盈利增速
    - EV/EBITDA 等
    """
    
    name = "get_valuation_metrics"
    description = """获取股票估值指标。

返回数据:
- PE (市盈率): 当前价格 / 每股收益，反映投资回收周期
- PB (市净率): 当前价格 / 每股净资产，反映资产溢价
- PS (市销率): 市值 / 营业收入，适用于亏损公司
- 股息率: 年度股息 / 股价
- 市值: 总市值和流通市值

用途:
- 判断股票估值高低
- 与行业/历史对比
- 筛选价值股/成长股

示例:
- 获取苹果估值: symbol="AAPL"
- 获取茅台估值: symbol="600519"
"""
    
    parameters = {
        "type": "object",
        "properties": {
            "symbol": {
                "type": "string",
                "description": "股票代码"
            },
            "market": {
                "type": "string",
                "enum": ["auto", "us", "cn", "hk"],
                "default": "auto",
                "description": "市场类型"
            }
        },
        "required": ["symbol"]
    }
    
    risk_level = RiskLevel.NONE
    operation_categories = [OperationCategory.WEB_READ]
    
    def __init__(self):
        super().__init__()
        self._tool = get_financial_tool()
    
    async def execute(self, symbol: str, market: str = "auto", **kwargs) -> str:
        """执行获取估值指标"""
        logger.info(f"Getting valuation metrics for {symbol}")
        
        result = await self._tool.get_valuation(symbol, market=market, **kwargs)
        return _format_result(result)


class GetHistoricalPriceTool(BaseTool):
    """获取历史价格数据
    
    获取股票的历史K线数据（OHLCV），用于：
    - 技术分析
    - 趋势判断
    - 历史回测
    """
    
    name = "get_historical_price"
    description = """获取股票历史价格数据（K线）。

返回数据:
- 日期 (date)
- 开盘价 (open)
- 最高价 (high)
- 最低价 (low)
- 收盘价 (close)
- 成交量 (volume)
- 涨跌幅 (change_percent)

参数:
- start_date: 开始日期 (YYYY-MM-DD)，默认1年前
- end_date: 结束日期 (YYYY-MM-DD)，默认今天
- interval: 1d=日线, 1w=周线, 1m=月线

示例:
- 获取苹果近1年日K: symbol="AAPL"
- 获取茅台近3个月日K: symbol="600519", start_date="2025-10-01"
"""
    
    parameters = {
        "type": "object",
        "properties": {
            "symbol": {
                "type": "string",
                "description": "股票代码"
            },
            "start_date": {
                "type": "string",
                "description": "开始日期 (YYYY-MM-DD)，默认1年前"
            },
            "end_date": {
                "type": "string",
                "description": "结束日期 (YYYY-MM-DD)，默认今天"
            },
            "interval": {
                "type": "string",
                "enum": ["1d", "1w", "1m"],
                "default": "1d",
                "description": "K线周期: 1d=日线, 1w=周线, 1m=月线"
            },
            "market": {
                "type": "string",
                "enum": ["auto", "us", "cn", "hk"],
                "default": "auto",
                "description": "市场类型"
            }
        },
        "required": ["symbol"]
    }
    
    risk_level = RiskLevel.NONE
    operation_categories = [OperationCategory.WEB_READ]
    
    def __init__(self):
        super().__init__()
        self._tool = get_financial_tool()
    
    async def execute(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        interval: str = "1d",
        market: str = "auto",
        **kwargs
    ) -> str:
        """执行获取历史价格"""
        logger.info(f"Getting historical price for {symbol} ({start_date} to {end_date})")
        
        result = await self._tool.get_historical(
            symbol,
            start_date=start_date,
            end_date=end_date,
            interval=interval,
            market=market,
            **kwargs
        )
        return _format_result(result)


class GetFinancialNewsTool(BaseTool):
    """获取财经新闻
    
    获取与特定股票相关的财经新闻和公告。
    """
    
    name = "get_financial_news"
    description = """获取股票相关财经新闻和公告。

返回数据:
- 新闻标题
- 发布时间
- 新闻来源
- 摘要/内容

数据来源:
- 美股: Yahoo Finance, Bloomberg, Reuters
- A股: 东方财富, 同花顺, 公司公告
- 港股: HKEX 公告, 财经媒体

示例:
- 获取苹果最新新闻: symbol="AAPL", limit=10
- 获取茅台公告: symbol="600519", limit=5
"""
    
    parameters = {
        "type": "object",
        "properties": {
            "symbol": {
                "type": "string",
                "description": "股票代码"
            },
            "limit": {
                "type": "integer",
                "default": 10,
                "description": "返回新闻数量上限"
            },
            "market": {
                "type": "string",
                "enum": ["auto", "us", "cn", "hk"],
                "default": "auto",
                "description": "市场类型"
            }
        },
        "required": ["symbol"]
    }
    
    risk_level = RiskLevel.NONE
    operation_categories = [OperationCategory.WEB_READ]
    
    def __init__(self):
        super().__init__()
        self._tool = get_financial_tool()
    
    async def execute(
        self,
        symbol: str,
        limit: int = 10,
        market: str = "auto",
        **kwargs
    ) -> str:
        """执行获取财经新闻"""
        logger.info(f"Getting financial news for {symbol} (limit={limit})")
        
        result = await self._tool.get_news(symbol, limit=limit, market=market, **kwargs)
        return _format_result(result)


class GetNorthFlowTool(BaseTool):
    """获取北向资金流向（A股专用）
    
    获取沪深港通北向资金的净流入/流出数据。
    北向资金是外资通过沪港通/深港通投资A股的资金，
    被认为是"聪明钱"的风向标。
    """
    
    name = "get_north_flow"
    description = """获取A股北向资金流向数据。

什么是北向资金:
- 外资通过沪港通/深港通买入A股的资金
- 被视为机构/外资动向的重要指标
- 持续流入通常被视为看好信号

返回数据:
- 日期
- 沪股通净流入
- 深股通净流入
- 北向资金总净流入

注意: 此工具仅适用于A股市场。

示例:
- 获取今日北向资金: get_north_flow
"""
    
    parameters = {
        "type": "object",
        "properties": {}
    }
    
    risk_level = RiskLevel.NONE
    operation_categories = [OperationCategory.WEB_READ]
    
    def __init__(self):
        super().__init__()
        self._tool = get_financial_tool()
    
    async def execute(self, **kwargs) -> str:
        """执行获取北向资金"""
        logger.info("Getting north capital flow data")
        
        result = await self._tool.get_north_flow()
        return _format_result(result)


class GetDragonTigerTool(BaseTool):
    """获取龙虎榜数据（A股专用）
    
    获取A股龙虎榜数据，显示当日异动股票的主力买卖情况。
    龙虎榜是判断主力资金动向的重要参考。
    """
    
    name = "get_dragon_tiger"
    description = """获取A股龙虎榜数据。

什么是龙虎榜:
- 显示当日异动股票（涨跌幅大、换手率高等）
- 披露买入/卖出前5名的席位和金额
- 可以看到机构、游资的操作方向

返回数据:
- 股票代码和名称
- 上榜原因
- 买入金额前5席位
- 卖出金额前5席位

参数:
- date: 日期 (YYYYMMDD)，默认最新交易日

注意: 此工具仅适用于A股市场。

示例:
- 获取今日龙虎榜: get_dragon_tiger
- 获取指定日期: date="20260115"
"""
    
    parameters = {
        "type": "object",
        "properties": {
            "date": {
                "type": "string",
                "description": "日期 (YYYYMMDD格式)，默认最新交易日"
            }
        }
    }
    
    risk_level = RiskLevel.NONE
    operation_categories = [OperationCategory.WEB_READ]
    
    def __init__(self):
        super().__init__()
        self._tool = get_financial_tool()
    
    async def execute(self, date: Optional[str] = None, **kwargs) -> str:
        """执行获取龙虎榜"""
        logger.info(f"Getting dragon tiger list (date={date})")
        
        result = await self._tool.get_dragon_tiger(date=date)
        return _format_result(result)


class FinancialDataToolWrapper(BaseTool):
    """统一金融数据工具（包装器）
    
    将所有金融数据类型整合到一个工具中，
    通过 data_type 参数选择不同的数据类型。
    
    适用于需要更灵活的金融数据获取场景。
    """
    
    name = "financial_data"
    description = """统一金融数据获取工具。

数据类型 (data_type):
- quote: 实时行情（价格、涨跌、成交量）
- fundamental: 财务报表（利润表、资产负债表、现金流）
- valuation: 估值指标（PE、PB、PS、市值）
- historical: 历史价格（K线数据）
- news: 财经新闻和公告

市场 (market):
- auto: 自动检测（推荐）
- us: 美股
- cn: A股
- hk: 港股

代码格式:
- 美股: AAPL, MSFT, GOOGL
- A股: 600519, 000001 (6位数字)
- 港股: 0700.HK, 9988.HK

示例:
- 获取苹果行情: symbol="AAPL", data_type="quote"
- 获取茅台财报: symbol="600519", data_type="fundamental"
- 获取腾讯估值: symbol="0700.HK", data_type="valuation"
"""
    
    parameters = {
        "type": "object",
        "properties": {
            "symbol": {
                "type": "string",
                "description": "股票代码"
            },
            "data_type": {
                "type": "string",
                "enum": ["quote", "fundamental", "valuation", "historical", "news"],
                "default": "quote",
                "description": "数据类型"
            },
            "market": {
                "type": "string",
                "enum": ["auto", "us", "cn", "hk"],
                "default": "auto",
                "description": "市场类型"
            }
        },
        "required": ["symbol"]
    }
    
    risk_level = RiskLevel.NONE
    operation_categories = [OperationCategory.WEB_READ]
    
    def __init__(self):
        super().__init__()
        self._tool = get_financial_tool()
    
    async def execute(
        self,
        symbol: str,
        data_type: str = "quote",
        market: str = "auto",
        **kwargs
    ) -> str:
        """执行金融数据获取"""
        logger.info(f"Financial data request: {symbol}, type={data_type}, market={market}")
        
        result = await self._tool.execute(
            symbol=symbol,
            data_type=data_type,
            market=market,
            **kwargs
        )
        
        # 添加免责声明
        output = _format_result(result)
        output += "\n\n---\n*数据仅供参考，不构成投资建议*"
        
        return output


# ==================== 工具集合 ====================

def get_financial_tools() -> List[BaseTool]:
    """获取所有金融工具实例"""
    return [
        GetStockQuoteTool(),
        GetFinancialStatementsTool(),
        GetValuationMetricsTool(),
        GetHistoricalPriceTool(),
        GetFinancialNewsTool(),
        GetNorthFlowTool(),
        GetDragonTigerTool(),
        FinancialDataToolWrapper(),  # 统一入口
    ]


def get_primary_financial_tool() -> BaseTool:
    """获取主要金融工具（推荐使用）
    
    返回 FinancialDataToolWrapper，它整合了所有金融数据类型。
    """
    return FinancialDataToolWrapper()


__all__ = [
    "GetStockQuoteTool",
    "GetFinancialStatementsTool",
    "GetValuationMetricsTool",
    "GetHistoricalPriceTool",
    "GetFinancialNewsTool",
    "GetNorthFlowTool",
    "GetDragonTigerTool",
    "FinancialDataToolWrapper",
    "get_financial_tools",
    "get_primary_financial_tool",
]
