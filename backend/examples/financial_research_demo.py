"""Minimal demo: fetch Kweichow Moutai (600519) data using FinancialDataTool.

Run:
    uv run python backend/examples/financial_research_demo.py
"""
import asyncio

from app.agent.tools.builtin.financial import FinancialDataTool


async def main():
    tool = FinancialDataTool()

    symbol = "600519"  # Kweichow Moutai

    print("== Quote ==")
    q = await tool.get_quote(symbol, market="cn")
    print(q.success, q.error or q.data)

    print("\n== Fundamentals ==")
    f = await tool.get_fundamental(symbol, statement_type="all", market="cn")
    print(f.success, f.error or (list(f.data.keys()) if isinstance(f.data, dict) else type(f.data)))

    print("\n== Valuation ==")
    v = await tool.get_valuation(symbol, market="cn")
    print(v.success, v.error or v.data)

    print("\n== Disclaimer ==")
    print(tool.get_disclaimer())


if __name__ == "__main__":
    asyncio.run(main())