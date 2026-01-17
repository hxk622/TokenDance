"""
三文件工作法测试脚本
"""
from app.agent.working_memory import ThreeFilesManager
from app.filesystem import AgentFileSystem


def test_three_files():
    """测试ThreeFilesManager基本功能"""

    # 创建文件系统和三文件管理器
    fs = AgentFileSystem(
        workspace_root="./test_workspace",
        org_id="test_org",
        team_id="test_team",
        workspace_id="test_ws"
    )
    manager = ThreeFilesManager(fs, session_id="test_session_001")

    print("=" * 60)
    print("测试1: 读取三个文件")
    print("=" * 60)
    data = manager.read_all()
    print(f"Task Plan: {data['task_plan']['content'][:100]}...")
    print(f"Findings: {data['findings']['content'][:100]}...")
    print(f"Progress: {data['progress']['content'][:100]}...")

    print("\n" + "=" * 60)
    print("测试2: 更新task_plan.md")
    print("=" * 60)
    manager.update_task_plan("## 新增目标\n- [ ] 完成测试", append=True)
    updated = manager.read_task_plan()
    print(f"Updated content:\n{updated['content']}")

    print("\n" + "=" * 60)
    print("测试3: 添加研究发现")
    print("=" * 60)
    manager.update_findings("发现了一个重要的技术点：三文件工作法可以节省60-80% Token")
    findings = manager.read_findings()
    print(f"Findings:\n{findings['content']}")

    print("\n" + "=" * 60)
    print("测试4: 记录执行日志")
    print("=" * 60)
    manager.update_progress("成功执行了test操作")
    manager.update_progress("遇到了一个错误：连接超时", is_error=True)
    progress = manager.read_progress()
    print(f"Progress:\n{progress['content']}")

    print("\n" + "=" * 60)
    print("测试5: 2-Action Rule")
    print("=" * 60)
    should_write = manager.record_action("web_search", {})
    print(f"第1次搜索后should_write: {should_write}")
    should_write = manager.record_action("read_url", {})
    print(f"第2次操作后should_write: {should_write}")

    print("\n" + "=" * 60)
    print("测试6: 3-Strike Protocol")
    print("=" * 60)
    result = manager.record_error("connection_timeout", "连接超时错误1")
    print(f"第1次错误: {result}")
    result = manager.record_error("connection_timeout", "连接超时错误2")
    print(f"第2次错误: {result}")
    result = manager.record_error("connection_timeout", "连接超时错误3")
    print(f"第3次错误（触发Protocol）: {result}")

    print("\n" + "=" * 60)
    print("测试7: 获取Context摘要")
    print("=" * 60)
    summary = manager.get_context_summary()
    print(f"Context Summary:\n{summary}")

    print("\n" + "=" * 60)
    print("测试8: 获取文件路径")
    print("=" * 60)
    paths = manager.get_file_paths()
    for name, path in paths.items():
        print(f"{name}: {path}")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    test_three_files()
