"""
Skill API 端点

提供 Skill 发现、模板查询、场景预设等功能。
"""


from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.skills.registry import get_skill_registry
from app.skills.template_registry import get_template_registry
from app.skills.types import TemplateCategory

router = APIRouter()


# ==================== 响应模型 ====================

class TemplateVariableResponse(BaseModel):
    """模板变量响应"""
    name: str
    label: str
    type: str
    required: bool = False
    placeholder: str | None = None
    options: list[dict] | None = None
    default: str | None = None


class TemplateResponse(BaseModel):
    """模板响应"""
    id: str
    skill_id: str
    name: str
    description: str
    prompt_template: str
    category: str
    tags: list[str]
    variables: list[dict]
    example_input: str | None = None
    example_output: str | None = None
    icon: str
    popularity: int
    enabled: bool


class SceneResponse(BaseModel):
    """场景预设响应"""
    id: str
    name: str
    description: str
    template_ids: list[str]
    recommended_skills: list[str]
    category: str
    tags: list[str]
    icon: str
    cover_image: str | None = None
    color: str
    popularity: int
    enabled: bool


class SkillResponse(BaseModel):
    """Skill 响应"""
    name: str
    display_name: str
    description: str
    version: str
    author: str
    tags: list[str]
    allowed_tools: list[str]
    max_iterations: int
    timeout: int
    enabled: bool
    match_threshold: float
    priority: int


class SkillWithTemplatesResponse(BaseModel):
    """带模板的 Skill 响应"""
    name: str
    display_name: str
    description: str
    version: str
    author: str
    tags: list[str]
    allowed_tools: list[str]
    max_iterations: int
    timeout: int
    enabled: bool
    match_threshold: float
    priority: int
    templates: list[TemplateResponse]


class CategoryResponse(BaseModel):
    """分类响应"""
    id: str
    name: str
    template_count: int
    scene_count: int


class DiscoveryResponse(BaseModel):
    """发现页面响应"""
    popular_templates: list[TemplateResponse]
    popular_scenes: list[SceneResponse]
    categories: list[CategoryResponse]
    total_templates: int
    total_scenes: int


class RenderTemplateRequest(BaseModel):
    """渲染模板请求"""
    variables: dict[str, str]


class RenderTemplateResponse(BaseModel):
    """渲染模板响应"""
    rendered_prompt: str
    skill_id: str
    template_id: str


# ==================== Skill 端点 ====================

@router.get("/skills", response_model=list[SkillResponse])
async def list_skills(
    tag: str | None = Query(None, description="按标签筛选"),
    enabled_only: bool = Query(True, description="只返回启用的 Skill"),
):
    """获取所有 Skill 列表"""
    registry = get_skill_registry()

    if tag:
        skills = registry.get_by_tag(tag)
    else:
        skills = registry.get_all()

    if enabled_only:
        skills = [s for s in skills if s.enabled]

    return [s.to_dict() for s in skills]


@router.get("/skills/{skill_id}", response_model=SkillWithTemplatesResponse)
async def get_skill(skill_id: str):
    """获取单个 Skill 详情（包含模板）"""
    registry = get_skill_registry()
    template_registry = get_template_registry()

    skill = registry.get(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill not found: {skill_id}")

    templates = template_registry.get_templates_by_skill(skill_id)

    return {
        **skill.to_dict(),
        "templates": [t.to_dict() for t in templates],
    }


@router.get("/skills/{skill_id}/templates", response_model=list[TemplateResponse])
async def get_skill_templates(skill_id: str):
    """获取某个 Skill 的所有模板"""
    template_registry = get_template_registry()
    templates = template_registry.get_templates_by_skill(skill_id)
    return [t.to_dict() for t in templates]


# ==================== 模板端点 ====================

@router.get("/templates", response_model=list[TemplateResponse])
async def list_templates(
    category: str | None = Query(None, description="按分类筛选"),
    skill_id: str | None = Query(None, description="按 Skill 筛选"),
    search: str | None = Query(None, description="搜索关键词"),
    limit: int = Query(50, ge=1, le=100, description="返回数量限制"),
):
    """获取模板列表"""
    template_registry = get_template_registry()

    if search:
        templates = template_registry.search_templates(search)
    elif skill_id:
        templates = template_registry.get_templates_by_skill(skill_id)
    elif category:
        try:
            cat = TemplateCategory(category)
            templates = template_registry.get_templates_by_category(cat)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid category: {category}") from e
    else:
        templates = template_registry.get_all_templates()

    return [t.to_dict() for t in templates[:limit]]


@router.get("/templates/popular", response_model=list[TemplateResponse])
async def get_popular_templates(
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
):
    """获取热门模板"""
    template_registry = get_template_registry()
    templates = template_registry.get_popular_templates(limit)
    return [t.to_dict() for t in templates]


@router.get("/templates/{template_id}", response_model=TemplateResponse)
async def get_template(template_id: str):
    """获取单个模板详情"""
    template_registry = get_template_registry()
    template = template_registry.get_template(template_id)

    if not template:
        raise HTTPException(status_code=404, detail=f"Template not found: {template_id}")

    return template.to_dict()


@router.post("/templates/{template_id}/render", response_model=RenderTemplateResponse)
async def render_template(template_id: str, request: RenderTemplateRequest):
    """渲染模板，替换变量生成最终提示词"""
    template_registry = get_template_registry()
    template = template_registry.get_template(template_id)

    if not template:
        raise HTTPException(status_code=404, detail=f"Template not found: {template_id}")

    # 检查必填变量
    required_vars = template.get_required_variables()
    missing_vars = [v for v in required_vars if v not in request.variables]
    if missing_vars:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required variables: {', '.join(missing_vars)}"
        )

    # 渲染模板
    rendered = template.render(request.variables)

    # 增加使用次数
    template_registry.increment_template_popularity(template_id)

    return {
        "rendered_prompt": rendered,
        "skill_id": template.skill_id,
        "template_id": template_id,
    }


# ==================== 场景预设端点 ====================

@router.get("/scenes", response_model=list[SceneResponse])
async def list_scenes(
    category: str | None = Query(None, description="按分类筛选"),
    limit: int = Query(20, ge=1, le=50, description="返回数量限制"),
):
    """获取场景预设列表"""
    template_registry = get_template_registry()

    if category:
        try:
            cat = TemplateCategory(category)
            scenes = template_registry.get_scenes_by_category(cat)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid category: {category}") from e
    else:
        scenes = template_registry.get_all_scenes()

    return [s.to_dict() for s in scenes[:limit]]


@router.get("/scenes/popular", response_model=list[SceneResponse])
async def get_popular_scenes(
    limit: int = Query(5, ge=1, le=20, description="返回数量"),
):
    """获取热门场景预设"""
    template_registry = get_template_registry()
    scenes = template_registry.get_popular_scenes(limit)
    return [s.to_dict() for s in scenes]


@router.get("/scenes/{scene_id}", response_model=SceneResponse)
async def get_scene(scene_id: str):
    """获取单个场景预设详情"""
    template_registry = get_template_registry()
    scene = template_registry.get_scene(scene_id)

    if not scene:
        raise HTTPException(status_code=404, detail=f"Scene not found: {scene_id}")

    return scene.to_dict()


@router.get("/scenes/{scene_id}/templates", response_model=list[TemplateResponse])
async def get_scene_templates(scene_id: str):
    """获取场景预设包含的所有模板"""
    template_registry = get_template_registry()

    scene = template_registry.get_scene(scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail=f"Scene not found: {scene_id}")

    templates = template_registry.get_scene_templates(scene_id)

    # 增加使用次数
    template_registry.increment_scene_popularity(scene_id)

    return [t.to_dict() for t in templates]


# ==================== 发现页面端点 ====================

@router.get("/discovery", response_model=DiscoveryResponse)
async def get_discovery_data():
    """获取发现页面所需的所有数据"""
    template_registry = get_template_registry()
    return template_registry.get_discovery_data()


@router.get("/categories", response_model=list[CategoryResponse])
async def list_categories():
    """获取所有分类及其统计信息"""
    template_registry = get_template_registry()
    data = template_registry.get_discovery_data()
    return data["categories"]
