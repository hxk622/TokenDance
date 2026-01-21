import asyncio

from app.skills.registry import get_skill_registry, SkillRegistry
from app.skills.template_registry import get_template_registry, TemplateRegistry


def test_financial_research_skill_exists():
    registry: SkillRegistry = get_skill_registry()
    registry.load_all()
    skill = registry.get("financial_research")
    assert skill is not None, "financial_research skill should be registered"
    assert "financial_data" in (skill.allowed_tools or []), "financial_data tool must be allowed"


def test_financial_research_templates_available():
    templates: TemplateRegistry = get_template_registry()
    templates.load_all()
    tpls = templates.get_templates_by_skill("financial_research")
    ids = {t.id for t in tpls}
    assert "fin_research_stock" in ids, "stock research template missing"