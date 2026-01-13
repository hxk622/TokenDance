"""
WorkingMemory 功能测试脚本
"""
import asyncio
import tempfile
from pathlib import Path
from app.agent.memory import WorkingMemory, create_working_memory


async def test_working_memory():
    """测试 WorkingMemory 基础功能"""
    print("=" * 60)
    print("WorkingMemory 功能测试")
    print("=" * 60)
    
    # 创建临时工作目录
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_path = tmpdir
        session_id = "test_session_001"
        
        print(f"\n1. 初始化 WorkingMemory")
        print(f"   Workspace: {workspace_path}")
        print(f"   Session ID: {session_id}")
        
        memory = await create_working_memory(
            workspace_path=workspace_path,
            session_id=session_id,
            initial_task="实现用户认证 API"
        )
        
        print(f"   ✅ WorkingMemory 创建成功")
        print(f"   {memory}")
        
        # 检查文件是否创建
        print(f"\n2. 检查三个文件是否创建")
        files = {
            "task_plan.md": memory.task_plan_file,
            "findings.md": memory.findings_file,
            "progress.md": memory.progress_file
        }
        
        for name, path in files.items():
            exists = "✅" if path.exists() else "❌"
            print(f"   {exists} {name}: {path}")
        
        # 测试 task_plan 读取
        print(f"\n3. 读取 task_plan.md")
        plan = await memory.read_task_plan()
        print(f"   前 200 字符: {plan[:200]}...")
        
        # 测试 2-Action Rule
        print(f"\n4. 测试 2-Action Rule")
        for i in range(3):
            should_record = memory.should_record_finding()
            print(f"   Action {i+1}: should_record_finding() = {should_record}")
        
        # 测试 append_finding
        print(f"\n5. 追加研究发现")
        await memory.append_finding(
            title="Web Search: Python async",
            content="发现 asyncio.gather() 比 asyncio.wait() 更适合并发任务",
            metadata={
                "query": "Python async best practices",
                "source": "https://docs.python.org/3/library/asyncio.html"
            }
        )
        print(f"   ✅ 发现已记录到 findings.md")
        
        # 测试 log_action
        print(f"\n6. 记录动作执行")
        await memory.log_action(
            action="运行测试",
            result="所有测试通过 (10/10)",
            status="✅"
        )
        print(f"   ✅ 动作已记录到 progress.md")
        
        # 测试 3-Strike Protocol
        print(f"\n7. 测试 3-Strike Protocol")
        for i in range(4):
            triggered = await memory.log_error(
                error_type="ImportError",
                details=f"尝试 {i+1}: cannot import 'User' from 'app.models'",
                tool_name="code_execute"
            )
            print(f"   尝试 {i+1}: 3-Strike triggered = {triggered}")
            if triggered:
                print(f"   🚨 3-Strike 已触发，应该停止并重启")
                break
        
        # 测试 log_phase_complete
        print(f"\n8. 记录 Phase 完成")
        await memory.log_phase_complete(
            phase="Phase 1",
            summary="数据库模型已创建，所有测试通过"
        )
        print(f"   ✅ Phase 完成已记录")
        
        # 显示统计信息
        print(f"\n9. 统计信息")
        stats = memory.get_statistics()
        for key, value in stats.items():
            if key == "files_exist":
                print(f"   {key}:")
                for file, exists in value.items():
                    print(f"      {file}: {exists}")
            else:
                print(f"   {key}: {value}")
        
        # 读取生成的文件内容
        print(f"\n10. 查看生成的文件内容")
        
        print(f"\n--- findings.md ---")
        findings = await memory.read_findings()
        print(findings[-300:] if len(findings) > 300 else findings)
        
        print(f"\n--- progress.md (最后 500 字符) ---")
        progress = await memory.read_progress(last_n_chars=500)
        print(progress)
        
        # 测试备份
        print(f"\n11. 测试备份功能")
        await memory.backup_files()
        backup_dir = memory.workspace_path / "backups"
        if backup_dir.exists():
            backup_files = list(backup_dir.iterdir())
            print(f"   ✅ 备份成功，文件数: {len(backup_files)}")
            for f in backup_files:
                print(f"      - {f.name}")
        
        print(f"\n" + "=" * 60)
        print("测试完成！")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_working_memory())
