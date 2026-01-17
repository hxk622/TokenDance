"""
SkillExecutor - Skill执行器

职责：
1. 根据Skill元数据执行L3脚本
2. 管理输入/输出（JSON格式）
3. 处理超时和异常
4. 支持降级策略（执行失败时返回友好错误）
"""

import asyncio
import json
import logging
import subprocess
import traceback
from pathlib import Path
from typing import Any

from .registry import SkillRegistry
from .types import SkillMetadata

logger = logging.getLogger(__name__)


class SkillExecutionError(Exception):
    """Skill执行错误"""
    pass


class SkillExecutionTimeout(SkillExecutionError):
    """Skill执行超时"""
    pass


class SkillNotFoundError(SkillExecutionError):
    """Skill不存在"""
    pass


class SkillExecutor:
    """Skill执行器

    负责执行Skill的L3脚本（自动化能力）。
    """

    def __init__(self, registry: SkillRegistry):
        """初始化执行器

        Args:
            registry: Skill注册表
        """
        self.registry = registry

    async def execute(
        self,
        skill_id: str,
        query: str,
        context: dict[str, str] | None = None,
        parameters: dict[str, Any] | None = None,
        timeout: int | None = None,
    ) -> dict[str, Any]:
        """执行Skill

        Args:
            skill_id: Skill标识符
            query: 用户原始查询
            context: 执行上下文（user_id, session_id等）
            parameters: 额外参数
            timeout: 超时时间（秒），为None则使用Skill配置的timeout

        Returns:
            执行结果（JSON）：
            {
                "status": "success" | "failed" | "timeout",
                "data": {...},
                "error": "错误信息（如果有）",
                "tokens_used": 123
            }
        """
        # 获取Skill元数据
        metadata = self.registry.get(skill_id)
        if not metadata:
            error_msg = f"Skill not found: {skill_id}"
            logger.error(error_msg)
            return self._error_response(error_msg, "failed")

        # 确定超时时间
        exec_timeout = timeout or metadata.timeout

        # 构建输入
        input_data = {
            "skill_name": skill_id,
            "query": query,
            "context": context or {},
            "parameters": parameters or {},
        }

        logger.info(
            f"Executing skill: {skill_id} "
            f"(timeout={exec_timeout}s, query_len={len(query)})"
        )

        try:
            # 在线程池中执行（避免阻塞事件循环）
            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    self._execute_script,
                    metadata,
                    input_data,
                ),
                timeout=exec_timeout,
            )

            logger.info(f"Skill {skill_id} executed successfully")
            return result

        except TimeoutError:
            error_msg = f"Skill execution timed out after {exec_timeout}s"
            logger.error(error_msg)
            return self._error_response(error_msg, "timeout")
        except SkillExecutionError as e:
            logger.error(f"Skill execution error: {e}")
            return self._error_response(str(e), "failed")
        except Exception as e:
            error_msg = f"Unexpected error during skill execution: {str(e)}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            return self._error_response(error_msg, "failed")

    def _execute_script(
        self,
        metadata: SkillMetadata,
        input_data: dict[str, Any],
    ) -> dict[str, Any]:
        """同步执行L3脚本

        Args:
            metadata: Skill元数据
            input_data: 输入数据

        Returns:
            执行结果
        """
        # 查找执行脚本
        skill_path = Path(metadata.skill_path)
        execute_script = skill_path / "resources" / "execute.py"

        if not execute_script.exists():
            # 脚本不存在，返回错误
            error_msg = (
                f"Skill entry script not found: {execute_script}\n"
                f"Required: {metadata.skill_path}/resources/execute.py"
            )
            logger.error(error_msg)
            return self._error_response(error_msg, "failed")

        try:
            # 构建命令
            cmd = ["python3", str(execute_script)]

            # 准备输入
            input_json = json.dumps(input_data, ensure_ascii=False)

            # 执行脚本
            logger.debug(f"Running: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                input=input_json,
                capture_output=True,
                text=True,
                timeout=metadata.timeout,  # subprocess级别的超时
                cwd=str(skill_path),
            )

            # 检查返回码
            if result.returncode != 0:
                error_msg = (
                    f"Script execution failed with code {result.returncode}\n"
                    f"stderr: {result.stderr}"
                )
                logger.error(error_msg)
                return self._error_response(error_msg, "failed")

            # 解析输出
            try:
                output = json.loads(result.stdout)

                # 验证输出格式
                if not isinstance(output, dict):
                    return self._error_response(
                        "Script output must be JSON object",
                        "failed"
                    )

                # 确保包含status字段
                if "status" not in output:
                    output["status"] = "success"

                logger.debug(f"Skill output: {output.get('status')}")
                return output

            except json.JSONDecodeError as e:
                error_msg = f"Script output is not valid JSON: {str(e)}\nOutput: {result.stdout}"
                logger.error(error_msg)
                return self._error_response(error_msg, "failed")

        except subprocess.TimeoutExpired:
            error_msg = "Script execution timed out"
            logger.error(error_msg)
            return self._error_response(error_msg, "timeout")
        except Exception as e:
            error_msg = f"Script execution failed: {str(e)}"
            logger.error(error_msg)
            return self._error_response(error_msg, "failed")

    def _error_response(self, error_msg: str, status: str) -> dict[str, Any]:
        """构建错误响应

        Args:
            error_msg: 错误消息
            status: 状态（failed, timeout等）

        Returns:
            错误响应
        """
        return {
            "status": status,
            "data": None,
            "error": error_msg,
            "tokens_used": 0,
        }

    def can_execute(self, skill_id: str) -> bool:
        """检查Skill是否可执行

        检查是否存在execute.py脚本

        Args:
            skill_id: Skill标识符

        Returns:
            True if Skill has execute.py, False otherwise
        """
        metadata = self.registry.get(skill_id)
        if not metadata:
            return False

        execute_script = Path(metadata.skill_path) / "resources" / "execute.py"
        return execute_script.exists()

    def get_executable_skills(self) -> list[str]:
        """获取所有可执行的Skill

        Returns:
            可执行的Skill ID列表
        """
        executable = []
        for skill in self.registry.get_all():
            if self.can_execute(skill.name):
                executable.append(skill.name)
        return executable


# ============================================================================
# 工厂函数
# ============================================================================

_global_executor: SkillExecutor | None = None


def get_skill_executor(registry: SkillRegistry | None = None) -> SkillExecutor:
    """获取全局SkillExecutor单例

    Args:
        registry: Skill注册表（首次调用时必须提供）

    Returns:
        SkillExecutor单例
    """
    global _global_executor

    if _global_executor is None:
        if registry is None:
            from .registry import get_skill_registry
            registry = get_skill_registry()
        _global_executor = SkillExecutor(registry)

    return _global_executor


def reset_skill_executor() -> None:
    """重置全局SkillExecutor单例"""
    global _global_executor
    _global_executor = None
