"""Quick test for financial data tools."""

import asyncio
import sys

sys.path.insert(0, '/Users/xingkaihan/Documents/Code/TokenDance/backend')

from app.agent.tools.builtin.financial import FinancialDataTool


async def test_us_stock():
    """Test US stock data via OpenBB."""
    tool = FinancialDataTool()

    print("=" * 60)
    print("Testing US Stock: AAPL")
    print("=" * 60)

    # Test quote
    print("\n1. Getting quote...")
    result = await tool.get_quote("AAPL")
    if result.success:
        print("   ✅ Quote success!")
        print(f"   Source: {result.source}")
        data = result.data
        if isinstance(data, dict):
            # Print key fields
            for key in ['symbol', 'name', 'price', 'open', 'high', 'low', 'volume']:
                if key in data:
                    print(f"   {key}: {data[key]}")
    else:
        print(f"   ❌ Quote failed: {result.error}")

    # Test historical
    print("\n2. Getting historical data (last 5 days)...")
    result = await tool.get_historical("AAPL", start_date="2025-01-10", end_date="2025-01-15")
    if result.success:
        print("   ✅ Historical success!")
        print(f"   Records: {result.metadata.get('records', 'N/A')}")
        if isinstance(result.data, list) and len(result.data) > 0:
            print(f"   Latest: {result.data[-1]}")
    else:
        print(f"   ❌ Historical failed: {result.error}")

    print("\n" + "=" * 60)


async def test_cn_stock():
    """Test A-Stock data via AkShare."""
    tool = FinancialDataTool()

    print("Testing A-Stock: 600519 (贵州茅台)")
    print("=" * 60)

    # Test quote
    print("\n1. Getting quote...")
    result = await tool.get_quote("600519")
    if result.success:
        print("   ✅ Quote success!")
        print(f"   Source: {result.source}")
        data = result.data
        if isinstance(data, dict):
            for key in ['code', 'name', 'price', 'change_percent', 'volume', 'pe_ttm', 'pb']:
                if key in data:
                    print(f"   {key}: {data[key]}")
    else:
        print(f"   ❌ Quote failed: {result.error}")
        print("   (AkShare may not be installed)")

    print("\n" + "=" * 60)


async def test_compliance():
    """Test compliance checker."""
    from app.agent.tools.builtin.financial.compliance import get_compliance_checker

    print("Testing Compliance Checker")
    print("=" * 60)

    checker = get_compliance_checker()

    # Test whitelist
    test_urls = [
        "https://xueqiu.com/S/SH600519",
        "https://guba.eastmoney.com/list,600519.html",
        "https://weibo.com/finance",
        "https://zhihu.com/question/123",
    ]

    for url in test_urls:
        can_crawl, reason = checker.can_crawl(url)
        status = "✅ Allowed" if can_crawl else "❌ Blocked"
        print(f"   {status}: {url}")
        print(f"      Reason: {reason}")

    print("\n" + "=" * 60)


async def main():
    """Run all tests."""
    print("\n🔬 TokenDance Financial Data Tool Test\n")

    await test_us_stock()
    await test_cn_stock()
    await test_compliance()

    print("\n✅ Test completed!\n")


if __name__ == "__main__":
    asyncio.run(main())
