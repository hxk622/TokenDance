"""
模板注册服务

负责加载、管理和查询 Skill 模板和场景预设。
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from .types import (
    ScenePreset,
    SkillMetadata,
    SkillTemplate,
    SkillWithTemplates,
    TemplateCategory,
)

logger = logging.getLogger(__name__)


class TemplateRegistry:
    """模板注册表

    管理所有 Skill 模板和场景预设的加载、缓存和查询。
    """

    def __init__(self, skills_dir: str, presets_dir: Optional[str] = None):
        """初始化模板注册表

        Args:
            skills_dir: Skill 目录路径
            presets_dir: 场景预设目录路径（可选，默认为 skills_dir/presets）
        """
        self.skills_dir = Path(skills_dir)
        self.presets_dir = Path(presets_dir) if presets_dir else self.skills_dir / "presets"

        # 缓存
        self._templates: Dict[str, SkillTemplate] = {}  # template_id -> template
        self._skill_templates: Dict[str, List[str]] = {}  # skill_id -> [template_ids]
        self._scenes: Dict[str, ScenePreset] = {}  # scene_id -> scene

        self._loaded = False

    def load_all(self) -> None:
        """加载所有模板和场景预设"""
        if self._loaded:
            return

        logger.info(f"Loading templates from {self.skills_dir}")

        # 加载 Skill 模板
        self._load_skill_templates()

        # 加载场景预设
        self._load_scene_presets()

        self._loaded = True
        logger.info(
            f"Loaded {len(self._templates)} templates, "
            f"{len(self._scenes)} scenes"
        )

    def _load_skill_templates(self) -> None:
        """加载所有 Skill 的模板"""
        # 递归查找所有 templates.yaml 文件
        for templates_file in self.skills_dir.rglob("templates.yaml"):
            try:
                self._load_templates_file(templates_file)
            except Exception as e:
                logger.error(f"Failed to load templates from {templates_file}: {e}")

    def _load_templates_file(self, file_path: Path) -> None:
        """加载单个模板文件"""
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data or "templates" not in data:
            return

        # 从路径推断 skill_id
        skill_dir = file_path.parent
        skill_md = skill_dir / "SKILL.md"
        skill_id = None

        if skill_md.exists():
            # 从 SKILL.md 读取 skill name
            with open(skill_md, "r", encoding="utf-8") as f:
                content = f.read()
                # 解析 YAML frontmatter
                if content.startswith("---"):
                    end_idx = content.find("---", 3)
                    if end_idx > 0:
                        frontmatter = content[3:end_idx]
                        meta = yaml.safe_load(frontmatter)
                        skill_id = meta.get("name")

        if not skill_id:
            skill_id = skill_dir.name

        # 解析模板
        for tpl_data in data["templates"]:
            template = self._parse_template(tpl_data, skill_id)
            if template:
                self._templates[template.id] = template

                # 建立 skill -> templates 映射
                if skill_id not in self._skill_templates:
                    self._skill_templates[skill_id] = []
                self._skill_templates[skill_id].append(template.id)

    def _parse_template(
        self, data: Dict, default_skill_id: str
    ) -> Optional[SkillTemplate]:
        """解析模板数据"""
        try:
            # 解析分类
            category_str = data.get("category", "other")
            try:
                category = TemplateCategory(category_str)
            except ValueError:
                category = TemplateCategory.OTHER

            return SkillTemplate(
                id=data["id"],
                skill_id=data.get("skill_id", default_skill_id),
                name=data["name"],
                description=data.get("description", ""),
                prompt_template=data.get("prompt_template", ""),
                category=category,
                tags=data.get("tags", []),
                variables=data.get("variables", []),
                example_input=data.get("example_input"),
                example_output=data.get("example_output"),
                icon=data.get("icon", "📝"),
                popularity=data.get("popularity", 0),
                enabled=data.get("enabled", True),
            )
        except KeyError as e:
            logger.error(f"Missing required field in template: {e}")
            return None

    def _load_scene_presets(self) -> None:
        """加载场景预设"""
        scenes_file = self.presets_dir / "scenes.yaml"
        if not scenes_file.exists():
            logger.warning(f"Scenes file not found: {scenes_file}")
            return

        try:
            with open(scenes_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data or "scenes" not in data:
                return

            for scene_data in data["scenes"]:
                scene = self._parse_scene(scene_data)
                if scene:
                    self._scenes[scene.id] = scene

        except Exception as e:
            logger.error(f"Failed to load scenes: {e}")

    def _parse_scene(self, data: Dict) -> Optional[ScenePreset]:
        """解析场景预设数据"""
        try:
            # 解析分类
            category_str = data.get("category", "other")
            try:
                category = TemplateCategory(category_str)
            except ValueError:
                category = TemplateCategory.OTHER

            return ScenePreset(
                id=data["id"],
                name=data["name"],
                description=data.get("description", ""),
                template_ids=data.get("template_ids", []),
                recommended_skills=data.get("recommended_skills", []),
                category=category,
                tags=data.get("tags", []),
                icon=data.get("icon", "🎯"),
                cover_image=data.get("cover_image"),
                color=data.get("color", "#6366f1"),
                popularity=data.get("popularity", 0),
                enabled=data.get("enabled", True),
            )
        except KeyError as e:
            logger.error(f"Missing required field in scene: {e}")
            return None

    # ==================== 查询接口 ====================

    def get_template(self, template_id: str) -> Optional[SkillTemplate]:
        """获取单个模板"""
        self.load_all()
        return self._templates.get(template_id)

    def get_templates_by_skill(self, skill_id: str) -> List[SkillTemplate]:
        """获取某个 Skill 的所有模板"""
        self.load_all()
        template_ids = self._skill_templates.get(skill_id, [])
        return [
            self._templates[tid]
            for tid in template_ids
            if tid in self._templates and self._templates[tid].enabled
        ]

    def get_all_templates(self) -> List[SkillTemplate]:
        """获取所有启用的模板"""
        self.load_all()
        return [t for t in self._templates.values() if t.enabled]

    def get_templates_by_category(
        self, category: TemplateCategory
    ) -> List[SkillTemplate]:
        """按分类获取模板"""
        self.load_all()
        return [
            t for t in self._templates.values()
            if t.enabled and t.category == category
        ]

    def search_templates(self, query: str) -> List[SkillTemplate]:
        """搜索模板（按名称、描述、标签）"""
        self.load_all()
        query_lower = query.lower()
        results = []

        for template in self._templates.values():
            if not template.enabled:
                continue

            # 匹配名称
            if query_lower in template.name.lower():
                results.append(template)
                continue

            # 匹配描述
            if query_lower in template.description.lower():
                results.append(template)
                continue

            # 匹配标签
            if any(query_lower in tag.lower() for tag in template.tags):
                results.append(template)
                continue

        return results

    def get_scene(self, scene_id: str) -> Optional[ScenePreset]:
        """获取单个场景预设"""
        self.load_all()
        return self._scenes.get(scene_id)

    def get_all_scenes(self) -> List[ScenePreset]:
        """获取所有启用的场景预设"""
        self.load_all()
        return [s for s in self._scenes.values() if s.enabled]

    def get_scenes_by_category(self, category: TemplateCategory) -> List[ScenePreset]:
        """按分类获取场景预设"""
        self.load_all()
        return [
            s for s in self._scenes.values()
            if s.enabled and s.category == category
        ]

    def get_scene_templates(self, scene_id: str) -> List[SkillTemplate]:
        """获取场景预设包含的所有模板"""
        self.load_all()
        scene = self._scenes.get(scene_id)
        if not scene:
            return []

        return [
            self._templates[tid]
            for tid in scene.template_ids
            if tid in self._templates and self._templates[tid].enabled
        ]

    def get_popular_templates(self, limit: int = 10) -> List[SkillTemplate]:
        """获取热门模板"""
        self.load_all()
        templates = [t for t in self._templates.values() if t.enabled]
        templates.sort(key=lambda t: t.popularity, reverse=True)
        return templates[:limit]

    def get_popular_scenes(self, limit: int = 5) -> List[ScenePreset]:
        """获取热门场景"""
        self.load_all()
        scenes = [s for s in self._scenes.values() if s.enabled]
        scenes.sort(key=lambda s: s.popularity, reverse=True)
        return scenes[:limit]

    def increment_template_popularity(self, template_id: str) -> None:
        """增加模板使用次数"""
        if template_id in self._templates:
            self._templates[template_id].popularity += 1

    def increment_scene_popularity(self, scene_id: str) -> None:
        """增加场景使用次数"""
        if scene_id in self._scenes:
            self._scenes[scene_id].popularity += 1

    # ==================== 组合查询 ====================

    def get_skill_with_templates(
        self, skill_metadata: SkillMetadata
    ) -> SkillWithTemplates:
        """获取带模板的 Skill 信息"""
        templates = self.get_templates_by_skill(skill_metadata.name)
        return SkillWithTemplates(metadata=skill_metadata, templates=templates)

    def get_discovery_data(self) -> Dict:
        """获取发现页面所需的所有数据"""
        self.load_all()

        return {
            "popular_templates": [t.to_dict() for t in self.get_popular_templates()],
            "popular_scenes": [s.to_dict() for s in self.get_popular_scenes()],
            "categories": [
                {
                    "id": cat.value,
                    "name": self._get_category_display_name(cat),
                    "template_count": len(self.get_templates_by_category(cat)),
                    "scene_count": len(self.get_scenes_by_category(cat)),
                }
                for cat in TemplateCategory
            ],
            "total_templates": len([t for t in self._templates.values() if t.enabled]),
            "total_scenes": len([s for s in self._scenes.values() if s.enabled]),
        }

    def _get_category_display_name(self, category: TemplateCategory) -> str:
        """获取分类显示名称"""
        names = {
            TemplateCategory.RESEARCH: "研究分析",
            TemplateCategory.WRITING: "写作创作",
            TemplateCategory.DATA: "数据处理",
            TemplateCategory.VISUALIZATION: "可视化",
            TemplateCategory.CODING: "编程开发",
            TemplateCategory.DOCUMENT: "文档生成",
            TemplateCategory.OTHER: "其他",
        }
        return names.get(category, category.value)

    def reload(self) -> None:
        """重新加载所有模板和场景"""
        self._templates.clear()
        self._skill_templates.clear()
        self._scenes.clear()
        self._loaded = False
        self.load_all()


# ==================== 全局单例 ====================

_template_registry: Optional[TemplateRegistry] = None


def get_template_registry() -> TemplateRegistry:
    """获取模板注册表单例"""
    global _template_registry
    if _template_registry is None:
        # 默认路径
        skills_dir = os.path.join(
            os.path.dirname(__file__),
            "builtin"
        )
        _template_registry = TemplateRegistry(skills_dir)
    return _template_registry


def init_template_registry(
    skills_dir: str,
    presets_dir: Optional[str] = None
) -> TemplateRegistry:
    """初始化模板注册表"""
    global _template_registry
    _template_registry = TemplateRegistry(skills_dir, presets_dir)
    _template_registry.load_all()
    return _template_registry


def reset_template_registry() -> None:
    """重置模板注册表（用于测试）"""
    global _template_registry
    _template_registry = None
