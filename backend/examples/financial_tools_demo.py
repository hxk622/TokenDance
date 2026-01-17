"""
Financial Tools Demo - 金融数据工具使用示例

演示如何使用 FinancialDataTool 和 SentimentTool。
"""

import asyncio
from datetime import datetime, timedelta

# Phase 1: 结构化数据工具
from app.agent.tools.builtin.financial import FinancialDataTool

# Phase 2: 舆情分析工具
from app.agent.tools.builtin.financial.sentiment import (
    get_sentiment_tool,
)


async def demo_financial_data():
    """演示结构化金融数据查询"""
    print("=" * 60)
    print("Phase 1: 结构化金融数据")
    print("=" * 60)

    tool = FinancialDataTool()

    # 1. 获取股票基本信息
    print("\n1. 获取茅台基本信息:")
    info = await tool.get_stock_info("600519")
    if info.get("success"):
        data = info.get("data", {})
        print(f"  股票名称: {data.get('name', 'N/A')}")
        print(f"  市场: {data.get('market', 'N/A')}")
        print(f"  最新价: {data.get('price', 'N/A')}")
        print(f"  市值: {data.get('market_cap', 'N/A')}")
    else:
        print(f"  错误: {info.get('error')}")

    # 2. 获取历史数据（最近30天）
    print("\n2. 获取茅台最近30天数据:")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    hist = await tool.get_historical(
        "600519",
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
    )

    if hist.get("success"):
        data = hist.get("data", {})
        records = data.get("records", [])
        print(f"  获取到 {len(records)} 条数据")
        if records:
            latest = records[-1]
            print(f"  最新记录 ({latest.get('date')}):")
            print(f"    开盘: {latest.get('open')}, 收盘: {latest.get('close')}")
            print(f"    最高: {latest.get('high')}, 最低: {latest.get('low')}")
            print(f"    成交量: {latest.get('volume')}")
    else:
        print(f"  错误: {hist.get('error')}")

    # 3. 获取实时行情
    print("\n3. 获取茅台实时行情:")
    quote = await tool.get_quote("600519")
    if quote.get("success"):
        data = quote.get("data", {})
        print(f"  当前价: {data.get('current_price', 'N/A')}")
        print(f"  涨跌幅: {data.get('change_percent', 'N/A')}%")
        print(f"  今日开盘: {data.get('open', 'N/A')}")
        print(f"  今日最高: {data.get('high', 'N/A')}")
        print(f"  今日最低: {data.get('low', 'N/A')}")
    else:
        print(f"  错误: {quote.get('error')}")


async def demo_sentiment_analysis():
    """演示舆情分析"""
    print("\n" + "=" * 60)
    print("Phase 2: 舆情分析")
    print("=" * 60)

    # 使用全局单例
    tool = get_sentiment_tool()

    # 1. 分析茅台舆情（从雪球和股吧）
    print("\n1. 分析茅台舆情 (雪球 + 股吧):")
    result = await tool.analyze(
        "600519",
        sources=["xueqiu", "guba"],
        limit_per_source=10,
    )

    if result.success:
        print(f"  ✓ 成功采集 {len(result.posts)} 条帖子")
        print(f"  数据源: {', '.join(result.sources_used)}")

        if result.analysis:
            analysis = result.analysis
            print("\n  【整体情绪】")
            print(f"    结论: {analysis.overall_label}")
            print(f"    评分: {analysis.overall_score:.2f} (-1看空 ~ +1看多)")
            print(f"    置信度: {analysis.confidence:.2f}")

            print("\n  【情绪分布】")
            print(f"    看多: {analysis.bullish_count} 条")
            print(f"    看空: {analysis.bearish_count} 条")
            print(f"    中性: {analysis.neutral_count} 条")

            if analysis.key_bullish_points:
                print("\n  【看多观点】")
                for point in analysis.key_bullish_points[:3]:
                    print(f"    - {point}")

            if analysis.key_bearish_points:
                print("\n  【看空观点】")
                for point in analysis.key_bearish_points[:3]:
                    print(f"    - {point}")

            if analysis.trending_topics:
                print("\n  【热门话题】")
                for topic in analysis.trending_topics[:3]:
                    print(f"    - {topic}")

        # 显示部分帖子
        print("\n  【示例帖子】")
        for i, post in enumerate(result.posts[:3]):
            print(f"    {i+1}. [{post.source}] {post.content[:50]}...")
            if post.sentiment_label:
                print(f"       情绪: {post.sentiment_label} ({post.sentiment_score:.2f})")
    else:
        print("  ✗ 失败")
        for error in result.errors:
            print(f"    - {error}")

    # 2. 仅爬取数据（不分析）
    print("\n2. 仅爬取雪球数据 (不分析):")
    result = await tool.crawl_only(
        "600519",
        sources=["xueqiu"],
        limit_per_source=5,
    )

    if result.success:
        print(f"  ✓ 爬取 {len(result.posts)} 条帖子")
        for post in result.posts[:2]:
            print(f"    - {post.content[:60]}...")
            print(f"      作者: {post.author}, 点赞: {post.likes}")

    # 3. 搜索特定话题
    print("\n3. 搜索 '白酒' 相关讨论:")
    result = await tool.search(
        "白酒",
        sources=["xueqiu"],
        limit=5,
    )

    if result.success:
        print(f"  ✓ 搜索到 {len(result.posts)} 条帖子")
        if result.analysis:
            print(f"  整体情绪: {result.analysis.overall_label}")

    # 关闭连接
    await tool.close()


async def demo_combined_analysis():
    """演示组合分析：结构化数据 + 舆情"""
    print("\n" + "=" * 60)
    print("组合分析：数据 + 舆情")
    print("=" * 60)

    symbol = "600519"

    # 1. 获取基本面数据
    data_tool = FinancialDataTool()
    info = await data_tool.get_stock_info(symbol)
    quote = await data_tool.get_quote(symbol)

    # 2. 获取舆情
    sentiment_tool = get_sentiment_tool()
    sentiment = await sentiment_tool.analyze(symbol, limit_per_source=20)

    # 3. 综合报告
    print(f"\n【{info.get('data', {}).get('name', symbol)} 综合分析】")

    if quote.get("success"):
        data = quote.get("data", {})
        print("\n技术面:")
        print(f"  当前价: {data.get('current_price')}")
        print(f"  涨跌幅: {data.get('change_percent')}%")

    if sentiment.success and sentiment.analysis:
        a = sentiment.analysis
        print("\n舆情面:")
        print(f"  市场情绪: {a.overall_label}")
        print(f"  情绪评分: {a.overall_score:.2f}")
        print(f"  样本数量: {a.analyzed_count} 条帖子")
        print(f"  多空比: {a.bullish_count}:{a.bearish_count}")

    print("\n合规声明:")
    print(f"  {sentiment.disclaimer}")

    await sentiment_tool.close()


async def main():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print("TokenDance 金融工具 Demo")
    print("=" * 60)

    try:
        # Phase 1: 结构化数据
        await demo_financial_data()

        # Phase 2: 舆情分析
        await demo_sentiment_analysis()

        # 组合分析
        await demo_combined_analysis()

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("Demo 完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
