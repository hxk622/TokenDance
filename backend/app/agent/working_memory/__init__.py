"""
Working Memory模块 - 三文件工作法

核心文件：
1. task_plan.md - 任务路线图（Phase 1, Phase 2...）
2. findings.md - 研究发现和技术决策
3. progress.md - 执行日志和错误记录

核心规则：
- 2-Action Rule: 每进行两次搜索/浏览操作，必须将发现存入findings.md
- 3-Strike Protocol: 同类错误出现3次，必须停下来重读计划
- 强制记录所有错误到progress.md

来源：Manus核心架构，Token消耗降低60-80%，长任务成功率提升40%
"""

from .three_files import ThreeFilesManager

__all__ = [
    "ThreeFilesManager",
]
