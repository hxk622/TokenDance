"""
Financial Data Tools for TokenDance.

This module provides tools for fetching financial data from multiple sources:
- OpenBB: Global markets (US, EU, etc.)
- AkShare: China A-Stock market
- Sentiment: Market sentiment from social media

Usage:
    from app.agent.tools.builtin.financial import FinancialDataTool
    
    tool = FinancialDataTool()
    result = await tool.execute(symbol="AAPL", data_type="quote", market="us")
"""

from app.agent.tools.builtin.financial.financial_data_tool import FinancialDataTool
from app.agent.tools.builtin.financial.adapters.openbb_adapter import OpenBBAdapter
from app.agent.tools.builtin.financial.adapters.akshare_adapter import AkShareAdapter
from app.agent.tools.builtin.financial.compliance import ComplianceChecker

__all__ = [
    "FinancialDataTool",
    "OpenBBAdapter",
    "AkShareAdapter",
    "ComplianceChecker",
]
