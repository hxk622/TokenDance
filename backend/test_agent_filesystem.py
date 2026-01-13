"""
AgentFileSystem测试脚本
"""
from app.filesystem import AgentFileSystem


def test_agent_filesystem():
    """测试AgentFileSystem基本功能"""
    
    # 创建文件系统实例
    fs = AgentFileSystem(
        workspace_root="./test_workspace",
        org_id="test_org",
        team_id="test_team",
        workspace_id="test_ws"
    )
    
    print("=" * 60)
    print("测试1: 工作空间信息")
    print("=" * 60)
    info = fs.get_workspace_info()
    for key, value in info.items():
        print(f"{key}: {value}")
    
    print("\n" + "=" * 60)
    print("测试2: 写入普通文件")
    print("=" * 60)
    path = fs.write("test.txt", "Hello, TokenDance!")
    print(f"文件已写入: {path}")
    content = fs.read("test.txt")
    print(f"读取内容: {content}")
    
    print("\n" + "=" * 60)
    print("测试3: 写入带Frontmatter的Markdown")
    print("=" * 60)
    metadata = {
        "title": "测试文档",
        "author": "TokenDance Agent",
        "tags": ["test", "markdown"],
    }
    path = fs.write_with_frontmatter(
        "test.md",
        "# 标题\n\n这是正文内容。",
        metadata=metadata
    )
    print(f"Markdown已写入: {path}")
    
    data = fs.read_with_frontmatter("test.md")
    print(f"元数据: {data['metadata']}")
    print(f"内容: {data['content'][:50]}...")
    
    print("\n" + "=" * 60)
    print("测试4: Session目录")
    print("=" * 60)
    session_dir = fs.get_session_dir("session_123")
    print(f"Session目录: {session_dir}")
    
    # 写入三文件
    fs.write("sessions/session_123/task_plan.md", "# Task Plan\n\nTODO列表...")
    fs.write("sessions/session_123/findings.md", "# Findings\n\n研究发现...")
    fs.write("sessions/session_123/progress.md", "# Progress\n\n执行日志...")
    print("三文件已创建")
    
    print("\n" + "=" * 60)
    print("测试5: 列出文件")
    print("=" * 60)
    files = fs.list_files("sessions/session_123", "*.md")
    print(f"Markdown文件: {files}")
    
    print("\n" + "=" * 60)
    print("测试6: 检查文件存在")
    print("=" * 60)
    print(f"test.txt存在: {fs.exists('test.txt')}")
    print(f"not_exist.txt存在: {fs.exists('not_exist.txt')}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    test_agent_filesystem()
