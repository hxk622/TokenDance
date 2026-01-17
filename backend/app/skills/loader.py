"""
SkillLoader - Skill加载器

职责：
1. 加载L2完整指令（SKILL.md正文）
2. 按需读取L3资源（子技能、脚本、参考文档）
3. 注入到Context
4. L2缓存机制
"""

import asyncio
import logging
import re
import subprocess
from pathlib import Path
from typing import Any

from .registry import SkillRegistry
from .types import Artifact, SkillContext

logger = logging.getLogger(__name__)


class SkillLoader:
    """Skill加载器

    负责加载Skill的L2指令和L3资源。
    """

    def __init__(
        self,
        registry: SkillRegistry,
        cache_enabled: bool = True,
        cache_ttl: int = 3600,  # 缓存TTL（秒）
    ):
        """初始化加载器

        Args:
            registry: Skill注册表
            cache_enabled: 是否启用L2缓存
            cache_ttl: 缓存TTL（秒）
        """
        self.registry = registry
        self.cache_enabled = cache_enabled
        self.cache_ttl = cache_ttl

        # L2指令缓存
        self._l2_cache: dict[str, str] = {}
        self._l2_cache_time: dict[str, float] = {}

    async def load_l2(self, skill_id: str) -> str:
        """加载L2完整指令

        从SKILL.md文件中提取正文内容（YAML头之后的部分）。

        Args:
            skill_id: Skill ID

        Returns:
            L2指令内容

        Raises:
            FileNotFoundError: Skill文件不存在
            ValueError: Skill未注册
        """
        # 检查缓存
        if self.cache_enabled and skill_id in self._l2_cache:
            import time
            cache_age = time.time() - self._l2_cache_time.get(skill_id, 0)
            if cache_age < self.cache_ttl:
                logger.debug(f"L2 cache hit for {skill_id}")
                return self._l2_cache[skill_id]

        # 获取Skill元数据
        metadata = self.registry.get(skill_id)
        if not metadata:
            raise ValueError(f"Skill not found: {skill_id}")

        # 读取SKILL.md文件
        skill_file = Path(metadata.skill_path) / "SKILL.md"
        if not skill_file.exists():
            raise FileNotFoundError(f"Skill file not found: {skill_file}")

        with open(skill_file, encoding='utf-8') as f:
            content = f.read()

        # 提取正文（去除YAML头）
        # YAML头格式: ---\n...\n---\n
        pattern = r'^---\s*\n.*?\n---\s*\n'
        match = re.match(pattern, content, re.DOTALL)

        if match:
            l2_content = content[match.end():].strip()
        else:
            l2_content = content.strip()

        # 更新缓存
        if self.cache_enabled:
            import time
            self._l2_cache[skill_id] = l2_content
            self._l2_cache_time[skill_id] = time.time()

        logger.info(f"Loaded L2 instructions for {skill_id} ({len(l2_content)} chars)")
        return l2_content

    async def load_l3_resource(
        self,
        skill_id: str,
        resource_path: str,
    ) -> str:
        """加载L3资源

        从Skill的resources目录中读取资源文件。

        Args:
            skill_id: Skill ID
            resource_path: 资源相对路径（相对于resources/）

        Returns:
            资源内容

        Raises:
            FileNotFoundError: 资源文件不存在
        """
        metadata = self.registry.get(skill_id)
        if not metadata:
            raise ValueError(f"Skill not found: {skill_id}")

        full_path = Path(metadata.skill_path) / "resources" / resource_path

        if not full_path.exists():
            raise FileNotFoundError(f"Resource not found: {full_path}")

        with open(full_path, encoding='utf-8') as f:
            content = f.read()

        logger.debug(f"Loaded L3 resource: {resource_path} ({len(content)} chars)")
        return content

    async def execute_l3_script(
        self,
        skill_id: str,
        script_path: str,
        args: list[str] = None,
        timeout: int = 60,
    ) -> str:
        """执行L3脚本

        在沙箱环境中执行Python脚本，返回stdout输出。
        脚本代码不进入Context。

        Args:
            skill_id: Skill ID
            script_path: 脚本相对路径（相对于resources/）
            args: 命令行参数
            timeout: 超时时间（秒）

        Returns:
            脚本输出

        Raises:
            FileNotFoundError: 脚本文件不存在
            RuntimeError: 脚本执行失败
        """
        metadata = self.registry.get(skill_id)
        if not metadata:
            raise ValueError(f"Skill not found: {skill_id}")

        full_path = Path(metadata.skill_path) / "resources" / script_path

        if not full_path.exists():
            raise FileNotFoundError(f"Script not found: {full_path}")

        # 构建命令
        cmd = ["python", str(full_path)]
        if args:
            cmd.extend(args)

        logger.info(f"Executing L3 script: {script_path} with args {args}")

        try:
            # 在线程池中执行（避免阻塞事件循环）
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=str(full_path.parent),
                )
            )

            if result.returncode != 0:
                error_msg = result.stderr or f"Script exited with code {result.returncode}"
                logger.error(f"Script execution failed: {error_msg}")
                raise RuntimeError(f"Script execution failed: {error_msg}")

            output = result.stdout.strip()
            logger.debug(f"Script output: {output[:200]}...")
            return output

        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Script execution timed out after {timeout}s")
        except Exception as e:
            raise RuntimeError(f"Script execution error: {e}") from e

    def get_resource_path(self, skill_id: str, resource_name: str) -> Path:
        """获取资源文件路径

        Args:
            skill_id: Skill ID
            resource_name: 资源名称

        Returns:
            资源文件完整路径
        """
        metadata = self.registry.get(skill_id)
        if not metadata:
            raise ValueError(f"Skill not found: {skill_id}")

        return Path(metadata.skill_path) / "resources" / resource_name

    def list_resources(self, skill_id: str) -> list[str]:
        """列出Skill的所有资源

        Args:
            skill_id: Skill ID

        Returns:
            资源路径列表（相对路径）
        """
        metadata = self.registry.get(skill_id)
        if not metadata:
            return []

        resources_dir = Path(metadata.skill_path) / "resources"
        if not resources_dir.exists():
            return []

        resources = []
        for path in resources_dir.rglob("*"):
            if path.is_file():
                rel_path = path.relative_to(resources_dir)
                resources.append(str(rel_path))

        return resources

    async def build_skill_context(
        self,
        skill_id: str,
        session_id: str,
        workspace_id: str,
        user_id: str,
        input_artifacts: list[Artifact] = None,
    ) -> SkillContext:
        """构建Skill执行上下文

        加载L2指令，组装完整的执行上下文。

        Args:
            skill_id: Skill ID
            session_id: 会话ID
            workspace_id: 工作区ID
            user_id: 用户ID
            input_artifacts: 输入产出物列表

        Returns:
            Skill执行上下文
        """
        metadata = self.registry.get(skill_id)
        if not metadata:
            raise ValueError(f"Skill not found: {skill_id}")

        # 加载L2指令
        l2_instructions = await self.load_l2(skill_id)

        return SkillContext(
            session_id=session_id,
            workspace_id=workspace_id,
            user_id=user_id,
            skill_id=skill_id,
            skill_metadata=metadata,
            l2_instructions=l2_instructions,
            input_artifacts=input_artifacts or [],
            available_tools=metadata.allowed_tools,
            max_iterations=metadata.max_iterations,
        )

    def clear_cache(self, skill_id: str = None) -> None:
        """清除L2缓存

        Args:
            skill_id: 要清除的Skill ID，为None时清除全部
        """
        if skill_id:
            self._l2_cache.pop(skill_id, None)
            self._l2_cache_time.pop(skill_id, None)
            logger.debug(f"Cleared L2 cache for {skill_id}")
        else:
            self._l2_cache.clear()
            self._l2_cache_time.clear()
            logger.debug("Cleared all L2 cache")

    def get_cache_stats(self) -> dict[str, Any]:
        """获取缓存统计信息"""
        import time
        current_time = time.time()

        stats = {
            "total_cached": len(self._l2_cache),
            "skills": {}
        }

        for skill_id, content in self._l2_cache.items():
            cache_time = self._l2_cache_time.get(skill_id, 0)
            stats["skills"][skill_id] = {
                "size": len(content),
                "age_seconds": int(current_time - cache_time),
                "expired": (current_time - cache_time) >= self.cache_ttl,
            }

        return stats


class SkillContextBuilder:
    """Skill上下文构建器

    提供流式API构建Skill执行上下文。
    """

    def __init__(self, loader: SkillLoader):
        self.loader = loader
        self._skill_id: str | None = None
        self._session_id: str | None = None
        self._workspace_id: str | None = None
        self._user_id: str | None = None
        self._input_artifacts: list[Artifact] = []
        self._extra_tools: list[str] = []

    def with_skill(self, skill_id: str) -> "SkillContextBuilder":
        """设置Skill ID"""
        self._skill_id = skill_id
        return self

    def with_session(
        self,
        session_id: str,
        workspace_id: str,
        user_id: str,
    ) -> "SkillContextBuilder":
        """设置会话信息"""
        self._session_id = session_id
        self._workspace_id = workspace_id
        self._user_id = user_id
        return self

    def with_input(self, artifact: Artifact) -> "SkillContextBuilder":
        """添加输入产出物"""
        self._input_artifacts.append(artifact)
        return self

    def with_inputs(self, artifacts: list[Artifact]) -> "SkillContextBuilder":
        """添加多个输入产出物"""
        self._input_artifacts.extend(artifacts)
        return self

    def with_extra_tools(self, tools: list[str]) -> "SkillContextBuilder":
        """添加额外工具（会与Skill允许的工具合并）"""
        self._extra_tools.extend(tools)
        return self

    async def build(self) -> SkillContext:
        """构建上下文"""
        if not self._skill_id:
            raise ValueError("Skill ID is required")
        if not self._session_id:
            raise ValueError("Session ID is required")

        context = await self.loader.build_skill_context(
            skill_id=self._skill_id,
            session_id=self._session_id,
            workspace_id=self._workspace_id or "",
            user_id=self._user_id or "",
            input_artifacts=self._input_artifacts,
        )

        # 合并额外工具
        if self._extra_tools:
            all_tools = set(context.available_tools)
            all_tools.update(self._extra_tools)
            context.available_tools = list(all_tools)

        return context
