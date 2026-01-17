"""
SkillRegistry - Skill注册表

职责：
1. 启动时扫描skills/目录
2. 解析所有SKILL.md的YAML头
3. 构建L1元数据索引
4. 生成System Prompt中的Skill列表
"""

import logging
import re
from pathlib import Path

import yaml

from .types import SkillMetadata

logger = logging.getLogger(__name__)


class SkillRegistry:
    """Skill注册表

    管理所有Skill的L1元数据，提供快速查询能力。
    支持多目录扫描：builtin（内置）和 scientific（科学计算）。
    """

    def __init__(
        self,
        skills_dirs: list[Path] | None = None,
        include_scientific: bool = True,
    ):
        """初始化注册表

        Args:
            skills_dirs: Skill目录路径列表，默认为 builtin/（包含所有子目录）
            include_scientific: 是否包含科学计算技能（现在在 builtin/scientific/ 下，默认True）
        """
        if skills_dirs is None:
            base_dir = Path(__file__).parent
            # 所有 Skill 都在 builtin/ 下，包括 builtin/scientific/
            skills_dirs = [base_dir / "builtin"]

        self.skills_dirs = [Path(d) for d in skills_dirs]
        self.skills: dict[str, SkillMetadata] = {}
        self._loaded = False

    def load_all(self) -> None:
        """扫描并加载所有Skill元数据"""
        if self._loaded:
            logger.warning("SkillRegistry already loaded, skipping reload")
            return

        total_loaded = 0

        for skills_dir in self.skills_dirs:
            if not skills_dir.exists():
                logger.warning(f"Skills directory not found: {skills_dir}")
                continue

            logger.info(f"Loading skills from: {skills_dir}")
            loaded_count = self._load_from_directory(skills_dir)
            total_loaded += loaded_count

        self._loaded = True
        logger.info(f"Total loaded: {total_loaded} skills from {len(self.skills_dirs)} directories")

    def _load_from_directory(self, skills_dir: Path, recursive: bool = True) -> int:
        """从单个目录加载skills

        Args:
            skills_dir: Skill目录路径
            recursive: 是否递归扫描子目录（用于按类别分组的scientific skills）

        Returns:
            加载的skill数量
        """
        loaded_count = 0

        for item in skills_dir.iterdir():
            if not item.is_dir():
                continue

            # 跳过特殊目录
            if item.name.startswith("_") or item.name.startswith("."):
                continue

            skill_file = item / "SKILL.md"

            if skill_file.exists():
                # 这是一个skill目录
                try:
                    metadata = self._parse_skill_file(skill_file)
                    if metadata and metadata.enabled:
                        self.skills[metadata.name] = metadata
                        logger.debug(f"Loaded skill: {metadata.name}")
                        loaded_count += 1
                    elif metadata:
                        logger.debug(f"Skill disabled: {metadata.name}")
                except Exception as e:
                    logger.error(f"Failed to parse skill file {skill_file}: {e}")
            elif recursive:
                # 这可能是一个分类目录（如 scientific/bioinformatics/）
                sub_count = self._load_from_directory(item, recursive=False)
                loaded_count += sub_count

        return loaded_count

    def _parse_skill_file(self, skill_file: Path) -> SkillMetadata | None:
        """解析SKILL.md的YAML头

        SKILL.md格式：
        ---
        name: skill_name
        display_name: 技能名称
        description: 技能描述
        ...
        ---

        ## 正文内容
        """
        with open(skill_file, encoding='utf-8') as f:
            content = f.read()

        # 使用正则提取YAML frontmatter
        pattern = r'^---\s*\n(.*?)\n---\s*\n'
        match = re.match(pattern, content, re.DOTALL)

        if not match:
            logger.warning(f"No YAML frontmatter found in {skill_file}")
            return None

        yaml_content = match.group(1)

        try:
            data = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in {skill_file}: {e}")
            return None

        if not data:
            return None

        # 验证必填字段
        required_fields = ['name', 'display_name', 'description', 'version']
        for field in required_fields:
            if field not in data:
                logger.error(f"Missing required field '{field}' in {skill_file}")
                return None

        # 构建SkillMetadata
        return SkillMetadata(
            name=data['name'],
            display_name=data.get('display_name', data['name']),
            description=data['description'],
            version=data['version'],
            author=data.get('author', 'system'),
            tags=data.get('tags', []),
            allowed_tools=data.get('allowed_tools', []),
            max_iterations=data.get('max_iterations', 30),
            timeout=data.get('timeout', 300),
            enabled=data.get('enabled', True),
            match_threshold=data.get('match_threshold', 0.7),
            priority=data.get('priority', 0),
            conflicts_with=data.get('conflicts_with', []),
            requires=data.get('requires', []),
            skill_path=str(skill_file.parent),
        )

    def get(self, skill_id: str) -> SkillMetadata | None:
        """获取Skill元数据

        Args:
            skill_id: Skill唯一标识

        Returns:
            SkillMetadata或None
        """
        return self.skills.get(skill_id)

    def get_all(self) -> list[SkillMetadata]:
        """获取所有启用的Skill元数据"""
        return list(self.skills.values())

    def get_by_tag(self, tag: str) -> list[SkillMetadata]:
        """根据标签获取Skill列表"""
        return [
            skill for skill in self.skills.values()
            if tag in skill.tags
        ]

    def get_skill_ids(self) -> list[str]:
        """获取所有Skill ID"""
        return list(self.skills.keys())

    def get_skill_list(self) -> str:
        """获取Skill列表（用于LLM提示）"""
        return ", ".join([
            f"{s.name}({s.display_name})"
            for s in sorted(self.skills.values(), key=lambda x: -x.priority)
        ])

    def generate_system_prompt_fragment(self) -> str:
        """生成System Prompt中的Skill列表片段

        格式:
        [Available Skills]
        - **深度研究**: 深度研究能力，支持多源搜索、信息聚合...
        - **PPT生成**: 智能演示文稿生成...
        """
        if not self.skills:
            return ""

        lines = ["[Available Skills]"]

        # 按优先级排序
        sorted_skills = sorted(
            self.skills.values(),
            key=lambda x: -x.priority
        )

        for skill in sorted_skills:
            lines.append(skill.to_system_prompt())

        return "\n".join(lines)

    def check_conflicts(self, skill_ids: list[str]) -> list[tuple]:
        """检查Skill之间的冲突

        Args:
            skill_ids: 要检查的Skill ID列表

        Returns:
            冲突的Skill对列表 [(skill1, skill2), ...]
        """
        conflicts = []
        skill_set = set(skill_ids)

        for skill_id in skill_ids:
            skill = self.get(skill_id)
            if not skill:
                continue

            for conflict_id in skill.conflicts_with:
                if conflict_id in skill_set:
                    # 避免重复添加
                    pair = tuple(sorted([skill_id, conflict_id]))
                    if pair not in conflicts:
                        conflicts.append(pair)

        return conflicts

    def resolve_dependencies(self, skill_ids: list[str]) -> list[str]:
        """解析Skill依赖，返回正确的执行顺序

        使用拓扑排序确保依赖的Skill先执行。

        Args:
            skill_ids: 原始Skill ID列表

        Returns:
            排序后的Skill ID列表
        """
        # 收集所有需要的Skill（包括依赖）
        all_skills = set(skill_ids)
        to_process = list(skill_ids)

        while to_process:
            skill_id = to_process.pop(0)
            skill = self.get(skill_id)
            if not skill:
                continue

            for dep_id in skill.requires:
                if dep_id not in all_skills:
                    all_skills.add(dep_id)
                    to_process.append(dep_id)

        # 构建依赖图
        graph: dict[str, list[str]] = {sid: [] for sid in all_skills}
        in_degree: dict[str, int] = dict.fromkeys(all_skills, 0)

        for skill_id in all_skills:
            skill = self.get(skill_id)
            if not skill:
                continue

            for dep_id in skill.requires:
                if dep_id in all_skills:
                    graph[dep_id].append(skill_id)
                    in_degree[skill_id] += 1

        # 拓扑排序
        result = []
        queue = [sid for sid, degree in in_degree.items() if degree == 0]

        while queue:
            # 按优先级选择
            queue.sort(key=lambda x: -(self.get(x).priority if self.get(x) else 0))
            skill_id = queue.pop(0)
            result.append(skill_id)

            for next_id in graph[skill_id]:
                in_degree[next_id] -= 1
                if in_degree[next_id] == 0:
                    queue.append(next_id)

        # 检查是否有循环依赖
        if len(result) != len(all_skills):
            logger.error("Circular dependency detected in skills")
            # 返回原始顺序
            return skill_ids

        return result

    def reload(self) -> None:
        """重新加载所有Skill"""
        self.skills.clear()
        self._loaded = False
        self.load_all()

    def is_loaded(self) -> bool:
        """检查是否已加载"""
        return self._loaded

    def __len__(self) -> int:
        return len(self.skills)

    def __contains__(self, skill_id: str) -> bool:
        return skill_id in self.skills


# 全局单例
_registry: SkillRegistry | None = None


def get_skill_registry() -> SkillRegistry:
    """获取全局SkillRegistry单例"""
    global _registry
    if _registry is None:
        _registry = SkillRegistry()
        _registry.load_all()
    return _registry


def init_skill_registry(
    skills_dirs: list[Path] | None = None,
    include_scientific: bool = True,
) -> SkillRegistry:
    """初始化全局SkillRegistry

    Args:
        skills_dirs: Skill目录路径列表
        include_scientific: 是否包含科学计算技能

    Returns:
        初始化后的SkillRegistry
    """
    global _registry
    _registry = SkillRegistry(skills_dirs, include_scientific)
    _registry.load_all()
    return _registry
