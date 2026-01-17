"""
FileOpsTool测试脚本
"""
import asyncio

from app.agent.tools.builtin.file_ops import create_file_ops_tool
from app.filesystem import AgentFileSystem


async def test_file_ops_tool():
    """测试FileOpsTool基本功能"""

    # 创建文件系统和工具
    fs = AgentFileSystem(
        workspace_root="./test_workspace",
        org_id="test_org",
        team_id="test_team",
        workspace_id="test_ws"
    )
    tool = create_file_ops_tool(fs)

    print("=" * 60)
    print("测试1: 写入文件")
    print("=" * 60)
    result = await tool.execute(
        "write",
        path="test_file.txt",
        content="Hello from FileOpsTool!"
    )
    print(f"Success: {result.success}")
    print(f"Data: {result.data}")

    print("\n" + "=" * 60)
    print("测试2: 读取文件")
    print("=" * 60)
    result = await tool.execute(
        "read",
        path="test_file.txt"
    )
    print(f"Success: {result.success}")
    print(f"Content: {result.data.get('content')}")

    print("\n" + "=" * 60)
    print("测试3: 写入带Frontmatter的文件")
    print("=" * 60)
    result = await tool.execute(
        "write",
        path="test_with_meta.md",
        content="# 测试文档\n\n这是内容。",
        metadata={"title": "测试", "tags": ["test"]}
    )
    print(f"Success: {result.success}")
    print(f"Has frontmatter: {result.data.get('has_frontmatter')}")

    print("\n" + "=" * 60)
    print("测试4: 读取Frontmatter")
    print("=" * 60)
    result = await tool.execute(
        "read",
        path="test_with_meta.md",
        parse_frontmatter=True
    )
    print(f"Success: {result.success}")
    print(f"Metadata: {result.data.get('metadata')}")
    print(f"Content: {result.data.get('content')[:50]}...")

    print("\n" + "=" * 60)
    print("测试5: 列出文件")
    print("=" * 60)
    result = await tool.execute(
        "list",
        directory="",
        pattern="*.md"
    )
    print(f"Success: {result.success}")
    print(f"Files: {result.data.get('files')}")
    print(f"Count: {result.data.get('count')}")

    print("\n" + "=" * 60)
    print("测试6: 检查文件存在")
    print("=" * 60)
    result = await tool.execute(
        "exists",
        path="test_file.txt"
    )
    print(f"Success: {result.success}")
    print(f"Exists: {result.data.get('exists')}")

    result = await tool.execute(
        "exists",
        path="not_exist.txt"
    )
    print(f"not_exist.txt Exists: {result.data.get('exists')}")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_file_ops_tool())
