"""
Financial Data Tools for TokenDance.

This module provides tools for fetching financial data from multiple sources:
- OpenBB: Global markets (US, EU, etc.)
- AkShare: China A-Stock market
- Sentiment: Market sentiment from social media

Usage:
    # BaseTool interface (recommended for Agent):
    from app.agent.tools.builtin.financial import get_financial_tools
    
    tools = get_financial_tools()  # Returns list of BaseTool instances
    
    # Or use individual tools:
    from app.agent.tools.builtin.financial import GetStockQuoteTool
    tool = GetStockQuoteTool()
    result = await tool.execute(symbol="AAPL")
    
    # Direct FinancialDataTool (lower level):
    from app.agent.tools.builtin.financial import FinancialDataTool
    tool = FinancialDataTool()
    result = await tool.execute(symbol="AAPL", data_type="quote", market="us")
"""

from app.agent.tools.builtin.financial.financial_data_tool import (
    FinancialDataTool,
    get_financial_tool,
)
from app.agent.tools.builtin.financial.adapters.openbb_adapter import OpenBBAdapter
from app.agent.tools.builtin.financial.adapters.akshare_adapter import AkShareAdapter
from app.agent.tools.builtin.financial.compliance import ComplianceChecker

# BaseTool interface wrappers
from app.agent.tools.builtin.financial.tools import (
    GetStockQuoteTool,
    GetFinancialStatementsTool,
    GetValuationMetricsTool,
    GetHistoricalPriceTool,
    GetFinancialNewsTool,
    GetNorthFlowTool,
    GetDragonTigerTool,
    FinancialDataToolWrapper,
    get_financial_tools,
    get_primary_financial_tool,
)

# Multi-source fallback provider
from app.agent.tools.builtin.financial.provider import (
    FinancialDataProvider,
    get_financial_provider,
)

__all__ = [
    # Core
    "FinancialDataTool",
    "get_financial_tool",
    "OpenBBAdapter",
    "AkShareAdapter",
    "ComplianceChecker",
    # BaseTool wrappers
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
    # Provider (multi-source fallback)
    "FinancialDataProvider",
    "get_financial_provider",
]
