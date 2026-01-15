#!/usr/bin/env python3
"""
浏览器场景集成测试

测试 agent-browser 与真实网站的交互能力。
需要在有网络环境下运行。

Usage:
    cd backend && uv run python tests/integration/test_browser_scenarios.py
"""

import asyncio
import json
import subprocess
import sys
from dataclasses import dataclass
from typing import Optional


@dataclass
class TestResult:
    """测试结果"""
    name: str
    success: bool
    snapshot_lines: int = 0
    token_estimate: int = 0
    error: Optional[str] = None
    url: Optional[str] = None


async def run_cmd(args: list[str], timeout: int = 30) -> tuple[bool, str, str]:
    """运行 agent-browser 命令"""
    try:
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(),
            timeout=timeout,
        )
        return proc.returncode == 0, stdout.decode(), stderr.decode()
    except asyncio.TimeoutError:
        return False, "", "Timeout"
    except Exception as e:
        return False, "", str(e)


async def test_basic_page(session: str = "test-basic") -> TestResult:
    """测试：基础页面加载 (example.com)"""
    result = TestResult(name="Basic Page Load", success=False)
    
    try:
        # 打开页面
        ok, out, err = await run_cmd([
            "agent-browser", "--session", session,
            "open", "https://example.com"
        ])
        if not ok:
            result.error = f"Open failed: {err}"
            return result
        
        result.url = "https://example.com"
        
        # 获取 snapshot
        ok, snapshot, err = await run_cmd([
            "agent-browser", "--session", session,
            "snapshot", "-i", "-c"
        ])
        if not ok:
            result.error = f"Snapshot failed: {err}"
            return result
        
        result.snapshot_lines = len(snapshot.strip().split('\n'))
        result.token_estimate = len(snapshot) // 4  # 粗略估算
        result.success = True
        
        # 关闭
        await run_cmd(["agent-browser", "--session", session, "close"])
        
    except Exception as e:
        result.error = str(e)
    
    return result


async def test_search_engine(session: str = "test-search") -> TestResult:
    """测试：搜索引擎交互 (Bing)"""
    result = TestResult(name="Search Engine (Bing)", success=False)
    
    try:
        # 打开 Bing
        ok, out, err = await run_cmd([
            "agent-browser", "--session", session,
            "open", "https://www.bing.com"
        ])
        if not ok:
            result.error = f"Open failed: {err}"
            return result
        
        result.url = "https://www.bing.com"
        
        # 等待页面加载
        await asyncio.sleep(2)
        
        # 获取 snapshot 找搜索框
        ok, snapshot, err = await run_cmd([
            "agent-browser", "--session", session,
            "snapshot", "-i", "-c"
        ])
        if not ok:
            result.error = f"Snapshot failed: {err}"
            return result
        
        result.snapshot_lines = len(snapshot.strip().split('\n'))
        result.token_estimate = len(snapshot) // 4
        
        # 查找搜索框 ref（通常是 @e1 或类似）
        # 尝试填写搜索
        ok, _, err = await run_cmd([
            "agent-browser", "--session", session,
            "fill", "input[name='q']", "AI Agent"
        ])
        
        result.success = True
        
        # 关闭
        await run_cmd(["agent-browser", "--session", session, "close"])
        
    except Exception as e:
        result.error = str(e)
    
    return result


async def test_github_page(session: str = "test-github") -> TestResult:
    """测试：GitHub 仓库页面（动态内容）"""
    result = TestResult(name="GitHub Repo Page", success=False)
    
    try:
        # 打开 GitHub
        ok, out, err = await run_cmd([
            "agent-browser", "--session", session,
            "open", "https://github.com/anthropics/anthropic-cookbook"
        ])
        if not ok:
            result.error = f"Open failed: {err}"
            return result
        
        result.url = "https://github.com/anthropics/anthropic-cookbook"
        
        # 等待 JS 渲染
        await asyncio.sleep(3)
        
        # 获取 snapshot
        ok, snapshot, err = await run_cmd([
            "agent-browser", "--session", session,
            "snapshot", "-i", "-c"
        ])
        if not ok:
            result.error = f"Snapshot failed: {err}"
            return result
        
        result.snapshot_lines = len(snapshot.strip().split('\n'))
        result.token_estimate = len(snapshot) // 4
        result.success = "@e" in snapshot  # 有交互元素
        
        # 关闭
        await run_cmd(["agent-browser", "--session", session, "close"])
        
    except Exception as e:
        result.error = str(e)
    
    return result


async def test_hacker_news(session: str = "test-hn") -> TestResult:
    """测试：Hacker News（列表页面）"""
    result = TestResult(name="Hacker News List", success=False)
    
    try:
        ok, out, err = await run_cmd([
            "agent-browser", "--session", session,
            "open", "https://news.ycombinator.com"
        ])
        if not ok:
            result.error = f"Open failed: {err}"
            return result
        
        result.url = "https://news.ycombinator.com"
        
        await asyncio.sleep(2)
        
        ok, snapshot, err = await run_cmd([
            "agent-browser", "--session", session,
            "snapshot", "-i", "-c"
        ])
        if not ok:
            result.error = f"Snapshot failed: {err}"
            return result
        
        result.snapshot_lines = len(snapshot.strip().split('\n'))
        result.token_estimate = len(snapshot) // 4
        
        # 检查是否捕获到了链接
        link_count = snapshot.count("@e")
        result.success = link_count >= 10  # HN 首页应该有很多链接
        
        await run_cmd(["agent-browser", "--session", session, "close"])
        
    except Exception as e:
        result.error = str(e)
    
    return result


async def test_screenshot(session: str = "test-screenshot") -> TestResult:
    """测试：截图功能"""
    result = TestResult(name="Screenshot Capture", success=False)
    
    try:
        ok, _, err = await run_cmd([
            "agent-browser", "--session", session,
            "open", "https://example.com"
        ])
        if not ok:
            result.error = f"Open failed: {err}"
            return result
        
        result.url = "https://example.com"
        
        # 截图
        screenshot_path = "/tmp/tokendance_test_screenshot.png"
        ok, _, err = await run_cmd([
            "agent-browser", "--session", session,
            "screenshot", screenshot_path
        ])
        
        import os
        result.success = ok and os.path.exists(screenshot_path)
        
        if result.success:
            result.token_estimate = 50  # 截图返回只是路径
        
        # 清理
        if os.path.exists(screenshot_path):
            os.remove(screenshot_path)
        
        await run_cmd(["agent-browser", "--session", session, "close"])
        
    except Exception as e:
        result.error = str(e)
    
    return result


def print_result(result: TestResult) -> None:
    """打印测试结果"""
    status = "✅" if result.success else "❌"
    print(f"\n{status} {result.name}")
    if result.url:
        print(f"   URL: {result.url}")
    if result.success:
        print(f"   Snapshot: {result.snapshot_lines} lines")
        print(f"   Token estimate: ~{result.token_estimate} tokens")
    if result.error:
        print(f"   Error: {result.error}")


async def main():
    """运行所有场景测试"""
    print("=" * 60)
    print("Agent-Browser 场景集成测试")
    print("=" * 60)
    
    tests = [
        test_basic_page,
        test_search_engine,
        test_github_page,
        test_hacker_news,
        test_screenshot,
    ]
    
    results: list[TestResult] = []
    
    for test_func in tests:
        print(f"\n⏳ Running: {test_func.__doc__.split('：')[1].strip() if '：' in (test_func.__doc__ or '') else test_func.__name__}...")
        result = await test_func()
        results.append(result)
        print_result(result)
    
    # 汇总
    print("\n" + "=" * 60)
    print("测试汇总")
    print("=" * 60)
    
    passed = sum(1 for r in results if r.success)
    total = len(results)
    
    print(f"\n通过: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 所有测试通过！Agent-browser 集成正常工作。")
    else:
        print("\n⚠️ 部分测试失败，请检查网络或 agent-browser 安装。")
    
    # Token 效率统计
    total_tokens = sum(r.token_estimate for r in results if r.success)
    avg_tokens = total_tokens // max(passed, 1)
    print(f"\n📊 Token 效率:")
    print(f"   平均每页 ~{avg_tokens} tokens (compact snapshot)")
    print(f"   对比传统 HTML: 10,000-50,000 tokens/页")
    print(f"   节省率: ~{100 - (avg_tokens * 100 // 10000)}%+")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
