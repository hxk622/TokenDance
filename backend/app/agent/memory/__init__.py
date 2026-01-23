"""
Agent Memory Module - Manus 无限记忆模式实现

核心组件：
- InfiniteMemoryManager: 统一管理「文件即记忆」逻辑
- WorkingMemory: 三文件工作记忆系统（兼容性导入）
"""

import importlib.util
import os

from .infinite_memory import InfiniteMemoryManager

_parent_memory_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "memory.py")
if os.path.exists(_parent_memory_path):
    spec = importlib.util.spec_from_file_location("_memory_compat", _parent_memory_path)
    if spec and spec.loader:
        _memory_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_memory_module)
        WorkingMemory = _memory_module.WorkingMemory
        create_working_memory = _memory_module.create_working_memory
    else:
        # Fallback
        class WorkingMemory:  # type: ignore
            def __init__(self, *args, **kwargs):
                raise NotImplementedError("WorkingMemory not available")
        def create_working_memory(*args, **kwargs):  # type: ignore
            raise NotImplementedError("create_working_memory not available")
else:
    class WorkingMemory:  # type: ignore
        def __init__(self, *args, **kwargs):
            raise NotImplementedError("WorkingMemory not available")
    def create_working_memory(*args, **kwargs):  # type: ignore
        raise NotImplementedError("create_working_memory not available")

__all__ = ["InfiniteMemoryManager", "WorkingMemory", "create_working_memory"]
