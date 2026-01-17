"""
ShellTool测试脚本
"""
import asyncio

from app.agent.tools.builtin.shell import ShellTool


async def test_shell_tool():
    """测试ShellTool基本功能"""

    # 创建工具实例
    shell = ShellTool(workspace_path=".")

    print("=" * 60)
    print("测试1: ls命令")
    print("=" * 60)
    result = await shell.execute("ls -la")
    print(f"Success: {result.success}")
    print(f"Stdout:\n{result.data.get('stdout', '')[:500]}")

    print("\n" + "=" * 60)
    print("测试2: grep搜索")
    print("=" * 60)
    result = await shell.execute("grep -r 'ShellTool' app/agent/tools/")
    print(f"Success: {result.success}")
    print(f"Stdout:\n{result.data.get('stdout', '')[:500]}")

    print("\n" + "=" * 60)
    print("测试3: git status")
    print("=" * 60)
    result = await shell.execute("git status")
    print(f"Success: {result.success}")
    print(f"Stdout:\n{result.data.get('stdout', '')[:500]}")

    print("\n" + "=" * 60)
    print("测试4: 危险命令（应被拒绝）")
    print("=" * 60)
    result = await shell.execute("rm -rf /")
    print(f"Success: {result.success}")
    print(f"Error: {result.error}")

    print("\n" + "=" * 60)
    print("测试5: 白名单外命令（应被拒绝）")
    print("=" * 60)
    result = await shell.execute("python --version")
    print(f"Success: {result.success}")
    print(f"Error: {result.error}")


if __name__ == "__main__":
    asyncio.run(test_shell_tool())
