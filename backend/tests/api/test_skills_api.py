"""
Skills API Tests

测试技能相关 API 端点：
- GET /api/v1/skills/skills - 列出所有 Skills
- GET /api/v1/skills/skills/{id} - 获取 Skill 详情
- GET /api/v1/skills/templates - 列出模板
- GET /api/v1/skills/templates/popular - 获取热门模板
- GET /api/v1/skills/templates/{id} - 获取模板详情
- POST /api/v1/skills/templates/{id}/render - 渲染模板
- GET /api/v1/skills/scenes - 列出场景
- GET /api/v1/skills/scenes/popular - 获取热门场景
- GET /api/v1/skills/discovery - 获取发现页数据
"""

import pytest
from unittest.mock import MagicMock, patch


# ==================== Skills Tests ====================

class TestListSkills:
    """列出 Skills 测试"""

    def test_list_skills_success(self, test_client):
        """测试成功列出 Skills"""
        with patch("app.api.v1.skills.get_skill_registry") as mock_get_registry:
            mock_registry = MagicMock()
            mock_skill = MagicMock()
            mock_skill.enabled = True
            mock_skill.to_dict.return_value = {
                "name": "test-skill",
                "display_name": "Test Skill",
                "description": "A test skill",
                "version": "1.0.0",
                "author": "test",
                "tags": ["test"],
                "allowed_tools": [],
                "max_iterations": 10,
                "timeout": 300,
                "enabled": True,
                "match_threshold": 0.5,
                "priority": 1
            }
            
            mock_registry.get_all.return_value = [mock_skill]
            mock_registry.get_by_tag.return_value = [mock_skill]
            mock_get_registry.return_value = mock_registry
            
            response = test_client.get("/api/v1/skills/skills")
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)

    def test_list_skills_with_tag_filter(self, test_client):
        """测试按标签筛选 Skills"""
        with patch("app.api.v1.skills.get_skill_registry") as mock_get_registry:
            mock_registry = MagicMock()
            mock_skill = MagicMock()
            mock_skill.enabled = True
            mock_skill.to_dict.return_value = {
                "name": "test-skill",
                "display_name": "Test Skill",
                "description": "A test skill",
                "version": "1.0.0",
                "author": "test",
                "tags": ["research"],
                "allowed_tools": [],
                "max_iterations": 10,
                "timeout": 300,
                "enabled": True,
                "match_threshold": 0.5,
                "priority": 1
            }
            
            mock_registry.get_by_tag.return_value = [mock_skill]
            mock_get_registry.return_value = mock_registry
            
            response = test_client.get("/api/v1/skills/skills?tag=research")
            
            assert response.status_code == 200


class TestGetSkill:
    """获取 Skill 详情测试"""

    def test_get_skill_success(self, test_client):
        """测试成功获取 Skill"""
        with patch("app.api.v1.skills.get_skill_registry") as mock_skill_registry, \
             patch("app.api.v1.skills.get_template_registry") as mock_template_registry:
            
            mock_skill = MagicMock()
            mock_skill.to_dict.return_value = {
                "name": "test-skill",
                "display_name": "Test Skill",
                "description": "A test skill",
                "version": "1.0.0",
                "author": "test",
                "tags": [],
                "allowed_tools": [],
                "max_iterations": 10,
                "timeout": 300,
                "enabled": True,
                "match_threshold": 0.5,
                "priority": 1
            }
            
            mock_skill_registry.return_value.get.return_value = mock_skill
            mock_template_registry.return_value.get_templates_by_skill.return_value = []
            
            response = test_client.get("/api/v1/skills/skills/test-skill")
            
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "test-skill"

    def test_get_skill_not_found(self, test_client):
        """测试 Skill 不存在"""
        with patch("app.api.v1.skills.get_skill_registry") as mock_registry:
            mock_registry.return_value.get.return_value = None
            
            response = test_client.get("/api/v1/skills/skills/nonexistent")
            
            assert response.status_code == 404


# ==================== Templates Tests ====================

class TestListTemplates:
    """列出模板测试"""

    def test_list_templates_success(self, test_client):
        """测试成功列出模板"""
        with patch("app.api.v1.skills.get_template_registry") as mock_registry:
            mock_template = MagicMock()
            mock_template.to_dict.return_value = {
                "id": "test-template",
                "skill_id": "test-skill",
                "name": "Test Template",
                "description": "A test template",
                "prompt_template": "Hello {name}",
                "category": "general",
                "tags": [],
                "variables": [],
                "icon": "📝",
                "popularity": 0,
                "enabled": True
            }
            
            mock_registry.return_value.get_all_templates.return_value = [mock_template]
            
            response = test_client.get("/api/v1/skills/templates")
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)


class TestGetPopularTemplates:
    """获取热门模板测试"""

    def test_get_popular_templates_success(self, test_client):
        """测试成功获取热门模板"""
        with patch("app.api.v1.skills.get_template_registry") as mock_registry:
            mock_template = MagicMock()
            mock_template.to_dict.return_value = {
                "id": "popular-template",
                "skill_id": "test-skill",
                "name": "Popular Template",
                "description": "A popular template",
                "prompt_template": "Hello",
                "category": "general",
                "tags": [],
                "variables": [],
                "icon": "🔥",
                "popularity": 100,
                "enabled": True
            }
            
            mock_registry.return_value.get_popular_templates.return_value = [mock_template]
            
            response = test_client.get("/api/v1/skills/templates/popular")
            
            assert response.status_code == 200


class TestGetTemplate:
    """获取模板详情测试"""

    def test_get_template_success(self, test_client):
        """测试成功获取模板"""
        with patch("app.api.v1.skills.get_template_registry") as mock_registry:
            mock_template = MagicMock()
            mock_template.to_dict.return_value = {
                "id": "test-template",
                "skill_id": "test-skill",
                "name": "Test Template",
                "description": "A test template",
                "prompt_template": "Hello {name}",
                "category": "general",
                "tags": [],
                "variables": [],
                "icon": "📝",
                "popularity": 0,
                "enabled": True
            }
            
            mock_registry.return_value.get_template.return_value = mock_template
            
            response = test_client.get("/api/v1/skills/templates/test-template")
            
            assert response.status_code == 200

    def test_get_template_not_found(self, test_client):
        """测试模板不存在"""
        with patch("app.api.v1.skills.get_template_registry") as mock_registry:
            mock_registry.return_value.get_template.return_value = None
            
            response = test_client.get("/api/v1/skills/templates/nonexistent")
            
            assert response.status_code == 404


class TestRenderTemplate:
    """渲染模板测试"""

    def test_render_template_success(self, test_client):
        """测试成功渲染模板"""
        with patch("app.api.v1.skills.get_template_registry") as mock_registry:
            mock_template = MagicMock()
            mock_template.skill_id = "test-skill"
            mock_template.get_required_variables.return_value = ["name"]
            mock_template.render.return_value = "Hello World"
            
            mock_registry.return_value.get_template.return_value = mock_template
            
            response = test_client.post(
                "/api/v1/skills/templates/test-template/render",
                json={"variables": {"name": "World"}}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["rendered_prompt"] == "Hello World"

    def test_render_template_missing_variables(self, test_client):
        """测试缺少必填变量"""
        with patch("app.api.v1.skills.get_template_registry") as mock_registry:
            mock_template = MagicMock()
            mock_template.get_required_variables.return_value = ["name", "topic"]
            
            mock_registry.return_value.get_template.return_value = mock_template
            
            response = test_client.post(
                "/api/v1/skills/templates/test-template/render",
                json={"variables": {"name": "World"}}
            )
            
            assert response.status_code == 400


# ==================== Scenes Tests ====================

class TestListScenes:
    """列出场景测试"""

    def test_list_scenes_success(self, test_client):
        """测试成功列出场景"""
        with patch("app.api.v1.skills.get_template_registry") as mock_registry:
            mock_scene = MagicMock()
            mock_scene.to_dict.return_value = {
                "id": "test-scene",
                "name": "Test Scene",
                "description": "A test scene",
                "template_ids": [],
                "recommended_skills": [],
                "category": "general",
                "tags": [],
                "icon": "🎬",
                "color": "#000000",
                "popularity": 0,
                "enabled": True
            }
            
            mock_registry.return_value.get_all_scenes.return_value = [mock_scene]
            
            response = test_client.get("/api/v1/skills/scenes")
            
            assert response.status_code == 200


class TestGetPopularScenes:
    """获取热门场景测试"""

    def test_get_popular_scenes_success(self, test_client):
        """测试成功获取热门场景"""
        with patch("app.api.v1.skills.get_template_registry") as mock_registry:
            mock_scene = MagicMock()
            mock_scene.to_dict.return_value = {
                "id": "popular-scene",
                "name": "Popular Scene",
                "description": "A popular scene",
                "template_ids": [],
                "recommended_skills": [],
                "category": "general",
                "tags": [],
                "icon": "🔥",
                "color": "#FF0000",
                "popularity": 100,
                "enabled": True
            }
            
            mock_registry.return_value.get_popular_scenes.return_value = [mock_scene]
            
            response = test_client.get("/api/v1/skills/scenes/popular")
            
            assert response.status_code == 200


class TestGetScene:
    """获取场景详情测试"""

    def test_get_scene_success(self, test_client):
        """测试成功获取场景"""
        with patch("app.api.v1.skills.get_template_registry") as mock_registry:
            mock_scene = MagicMock()
            mock_scene.to_dict.return_value = {
                "id": "test-scene",
                "name": "Test Scene",
                "description": "A test scene",
                "template_ids": [],
                "recommended_skills": [],
                "category": "general",
                "tags": [],
                "icon": "🎬",
                "color": "#000000",
                "popularity": 0,
                "enabled": True
            }
            
            mock_registry.return_value.get_scene.return_value = mock_scene
            
            response = test_client.get("/api/v1/skills/scenes/test-scene")
            
            assert response.status_code == 200

    def test_get_scene_not_found(self, test_client):
        """测试场景不存在"""
        with patch("app.api.v1.skills.get_template_registry") as mock_registry:
            mock_registry.return_value.get_scene.return_value = None
            
            response = test_client.get("/api/v1/skills/scenes/nonexistent")
            
            assert response.status_code == 404


# ==================== Discovery Tests ====================

class TestGetDiscovery:
    """获取发现页数据测试"""

    def test_get_discovery_success(self, test_client):
        """测试成功获取发现页数据"""
        with patch("app.api.v1.skills.get_template_registry") as mock_registry:
            mock_registry.return_value.get_discovery_data.return_value = {
                "popular_templates": [],
                "popular_scenes": [],
                "categories": [],
                "total_templates": 0,
                "total_scenes": 0
            }
            
            response = test_client.get("/api/v1/skills/discovery")
            
            assert response.status_code == 200
            data = response.json()
            assert "popular_templates" in data
            assert "popular_scenes" in data


class TestListCategories:
    """列出分类测试"""

    def test_list_categories_success(self, test_client):
        """测试成功列出分类"""
        with patch("app.api.v1.skills.get_template_registry") as mock_registry:
            mock_registry.return_value.get_discovery_data.return_value = {
                "categories": [
                    {"id": "general", "name": "General", "template_count": 5, "scene_count": 2}
                ],
                "popular_templates": [],
                "popular_scenes": [],
                "total_templates": 5,
                "total_scenes": 2
            }
            
            response = test_client.get("/api/v1/skills/categories")
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)


# ==================== Main ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
