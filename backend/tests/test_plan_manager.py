"""
Plan Manager测试脚本
"""
from app.filesystem import AgentFileSystem
from app.agent.working_memory import ThreeFilesManager
from app.agent.planning import PlanManager, Task, TaskStatus


def test_plan_manager():
    """测试PlanManager基本功能"""
    
    # 创建依赖
    fs = AgentFileSystem(
        workspace_root="./test_workspace",
        org_id="test_org",
        team_id="test_team",
        workspace_id="test_ws"
    )
    three_files = ThreeFilesManager(fs, session_id="test_session_002")
    plan_manager = PlanManager(three_files)
    
    print("=" * 60)
    print("测试1: 创建任务计划")
    print("=" * 60)
    
    tasks = [
        Task(
            id="task1",
            title="需求分析",
            description="分析用户需求，确定功能范围",
            tools_needed=["web_search", "read_url"],
            estimated_time=30
        ),
        Task(
            id="task2",
            title="技术选型",
            description="选择合适的技术栈",
            depends_on=["task1"],
            tools_needed=["web_search"],
            estimated_time=20
        ),
        Task(
            id="task3",
            title="实现核心功能",
            description="实现主要功能模块",
            depends_on=["task2"],
            tools_needed=["file_ops", "shell"],
            estimated_time=120
        ),
        Task(
            id="task4",
            title="测试验证",
            description="单元测试和集成测试",
            depends_on=["task3"],
            tools_needed=["shell"],
            estimated_time=60
        ),
    ]
    
    plan = plan_manager.create_plan(
        goal="构建一个Web应用",
        tasks=tasks
    )
    
    print(f"Plan ID: {plan.id}")
    print(f"Goal: {plan.goal}")
    print(f"Total tasks: {len(plan.tasks)}")
    
    print("\n" + "=" * 60)
    print("测试2: 获取下一个任务")
    print("=" * 60)
    next_task = plan_manager.get_next_task()
    print(f"Next task: {next_task.title if next_task else 'None'}")
    print(f"Description: {next_task.description if next_task else 'N/A'}")
    
    print("\n" + "=" * 60)
    print("测试3: 执行任务流程")
    print("=" * 60)
    
    # 开始第一个任务
    plan_manager.update_task_status("task1", TaskStatus.IN_PROGRESS)
    print("task1: 开始执行")
    
    # 完成第一个任务
    plan_manager.update_task_status("task1", TaskStatus.COMPLETED)
    print("task1: 已完成")
    
    # 获取下一个任务
    next_task = plan_manager.get_next_task()
    print(f"下一个任务: {next_task.title if next_task else 'None'}")
    
    # 开始并失败第二个任务
    plan_manager.update_task_status("task2", TaskStatus.IN_PROGRESS)
    plan_manager.update_task_status("task2", TaskStatus.FAILED, error="网络连接失败")
    print("task2: 失败（网络连接失败）")
    
    print("\n" + "=" * 60)
    print("测试4: 查看进度")
    print("=" * 60)
    progress = plan.get_progress()
    for key, value in progress.items():
        print(f"{key}: {value}")
    
    print("\n" + "=" * 60)
    print("测试5: Plan Recitation（计划摘要）")
    print("=" * 60)
    summary = plan_manager.get_plan_summary()
    print(summary)
    
    print("\n" + "=" * 60)
    print("测试6: Markdown输出")
    print("=" * 60)
    markdown = plan.to_markdown()
    print(markdown[:500] + "...")
    
    print("\n" + "=" * 60)
    print("测试7: 重试失败任务")
    print("=" * 60)
    task2 = plan.get_task("task2")
    print(f"task2 can retry: {task2.can_retry()}")
    plan_manager.retry_failed_task("task2")
    print("task2: 已重置为待处理")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    test_plan_manager()
