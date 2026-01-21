"""
Project API Tests - Project-First Architecture

测试 Project API 路由是否正确注册
"""
import pytest
from fastapi.testclient import TestClient


# ========== Basic Route Tests ==========


class TestProjectRoutes:
    """测试 Project API 路由是否正确注册"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        from app.main import app
        return TestClient(app)

    def test_project_routes_registered(self, client):
        """测试 project 路由已注册"""
        # Test that routes exist (will return 422 for missing params, not 404)
        response = client.get("/api/v1/projects")
        # Should be 422 (missing workspace_id) not 404 (not found)
        assert response.status_code == 422, "Project list route not registered"

    def test_project_detail_route_registered(self, client):
        """测试 project detail 路由已注册"""
        response = client.get("/api/v1/projects/test-id")
        # Should be 404 (project not found) not 404 (route not found)
        assert response.status_code == 404
        assert response.json()["detail"] == "Project not found"

    def test_project_create_route_registered(self, client):
        """测试 project create 路由已注册"""
        response = client.post("/api/v1/projects", json={})
        # Should be 422 (validation error) not 404
        assert response.status_code == 422

    def test_conversation_routes_registered(self, client):
        """测试 conversation 路由已注册"""
        response = client.get("/api/v1/projects/test-id/conversations")
        # Should be 404 (project not found) not 404 (route not found)
        assert response.status_code == 404

    def test_chat_route_registered(self, client):
        """测试 chat 路由已注册"""
        response = client.post(
            "/api/v1/projects/test-id/chat",
            json={"message": "test"}
        )
        # Should be 404 (project not found) not 404 (route not found)
        assert response.status_code == 404

    def test_context_routes_registered(self, client):
        """测试 context 路由已注册"""
        # Decision route
        response = client.post(
            "/api/v1/projects/test-id/context/decision",
            params={"decision": "test"}
        )
        assert response.status_code == 404

        # Failure route
        response = client.post(
            "/api/v1/projects/test-id/context/failure",
            params={"failure_type": "test", "message": "test"}
        )
        assert response.status_code == 404

        # Finding route
        response = client.post(
            "/api/v1/projects/test-id/context/finding",
            params={"finding": "test"}
        )
        assert response.status_code == 404

        # Get context route
        response = client.get("/api/v1/projects/test-id/context")
        assert response.status_code == 404


# ========== Project CRUD Tests ==========


class TestProjectCRUD:
    """测试 Project CRUD 操作"""

    def test_create_project(self, test_client, test_workspace_id):
        """测试创建 Project"""
        response = test_client.post(
            "/api/v1/projects",
            json={
                "workspace_id": test_workspace_id,
                "intent": "研究人工智能的最新进展",
                "title": "AI Research",
                "description": "A test project",
                "project_type": "research"
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert "id" in data
        assert data["workspace_id"] == test_workspace_id
        assert data["title"] == "AI Research"
        assert data["intent"] == "研究人工智能的最新进展"
        assert data["project_type"] == "research"
        assert data["status"] == "draft"

        # 清理
        test_client.delete(f"/api/v1/projects/{data['id']}?hard_delete=true")

    def test_create_project_auto_title(self, test_client, test_workspace_id):
        """测试自动生成标题"""
        response = test_client.post(
            "/api/v1/projects",
            json={
                "workspace_id": test_workspace_id,
                "intent": "帮我写一篇关于量子计算的文章",
            }
        )

        assert response.status_code == 200
        data = response.json()

        # 标题应该从 intent 自动生成
        assert data["title"] is not None
        assert len(data["title"]) > 0

        # 清理
        test_client.delete(f"/api/v1/projects/{data['id']}?hard_delete=true")

    def test_list_projects(self, test_client, test_workspace_id, test_project):
        """测试列出 Projects"""
        response = test_client.get(
            f"/api/v1/projects?workspace_id={test_workspace_id}"
        )

        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert "total" in data
        assert data["total"] >= 1

        # 应该包含测试 project
        project_ids = [p["id"] for p in data["items"]]
        assert test_project["id"] in project_ids

    def test_list_projects_filter_by_type(self, test_client, test_workspace_id, test_project):
        """测试按类型筛选 Projects"""
        response = test_client.get(
            f"/api/v1/projects?workspace_id={test_workspace_id}&project_type=quick_task"
        )

        assert response.status_code == 200
        data = response.json()

        # 所有返回的 project 应该都是 quick_task 类型
        for project in data["items"]:
            assert project["project_type"] == "quick_task"

    def test_get_project(self, test_client, test_project):
        """测试获取 Project 详情"""
        project_id = test_project["id"]

        response = test_client.get(f"/api/v1/projects/{project_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == project_id
        assert "context" in data
        assert "settings" in data

    def test_get_project_not_found(self, test_client):
        """测试获取不存在的 Project"""
        response = test_client.get("/api/v1/projects/nonexistent-id")
        assert response.status_code == 404

    def test_update_project(self, test_client, test_project):
        """测试更新 Project"""
        project_id = test_project["id"]

        response = test_client.patch(
            f"/api/v1/projects/{project_id}",
            json={
                "title": "Updated Title",
                "description": "Updated description"
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["title"] == "Updated Title"

    def test_archive_project(self, test_client, test_workspace_id):
        """测试归档 Project (软删除)"""
        # 创建一个新 project 用于归档
        create_response = test_client.post(
            "/api/v1/projects",
            json={
                "workspace_id": test_workspace_id,
                "intent": "To be archived",
            }
        )
        project_id = create_response.json()["id"]

        # 归档
        response = test_client.delete(f"/api/v1/projects/{project_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "archived"

        # 验证状态已更新
        get_response = test_client.get(f"/api/v1/projects/{project_id}")
        assert get_response.json()["status"] == "archived"

        # 清理 (hard delete)
        test_client.delete(f"/api/v1/projects/{project_id}?hard_delete=true")


# ========== Conversation Tests ==========


class TestConversation:
    """测试 Conversation 相关操作"""

    def test_create_conversation(self, test_client, test_project):
        """测试创建 Conversation"""
        project_id = test_project["id"]

        response = test_client.post(
            f"/api/v1/projects/{project_id}/conversations",
            json={
                "title": "First Conversation",
                "purpose": "general"
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert "id" in data
        assert data["project_id"] == project_id
        assert data["title"] == "First Conversation"
        assert data["purpose"] == "general"
        assert data["status"] == "active"

    def test_create_conversation_default(self, test_client, test_project):
        """测试创建默认 Conversation"""
        project_id = test_project["id"]

        response = test_client.post(
            f"/api/v1/projects/{project_id}/conversations"
        )

        assert response.status_code == 200
        data = response.json()

        assert data["purpose"] == "general"
        assert data["title"] == "New Conversation"

    def test_list_conversations(self, test_client, test_project):
        """测试列出 Conversations"""
        project_id = test_project["id"]

        # 先创建一个 conversation
        test_client.post(
            f"/api/v1/projects/{project_id}/conversations",
            json={"title": "Test Conv"}
        )

        response = test_client.get(
            f"/api/v1/projects/{project_id}/conversations"
        )

        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert data["total"] >= 1


# ========== Context Management Tests ==========


class TestContextManagement:
    """测试 Context 管理功能"""

    def test_add_decision(self, test_client, test_project):
        """测试添加决策到 Context"""
        project_id = test_project["id"]

        response = test_client.post(
            f"/api/v1/projects/{project_id}/context/decision",
            params={
                "decision": "Use Python for backend",
                "reason": "Team familiarity"
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "added"
        assert data["decision"] == "Use Python for backend"
        assert data["total_decisions"] >= 1

    def test_add_failure(self, test_client, test_project):
        """测试添加失败记录到 Context (Keep the Failures)"""
        project_id = test_project["id"]

        response = test_client.post(
            f"/api/v1/projects/{project_id}/context/failure",
            params={
                "failure_type": "api_error",
                "message": "Rate limit exceeded",
                "learning": "Add retry logic with exponential backoff"
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "added"
        assert data["failure_type"] == "api_error"
        assert data["total_failures"] >= 1

    def test_add_finding(self, test_client, test_project):
        """测试添加发现到 Context"""
        project_id = test_project["id"]

        response = test_client.post(
            f"/api/v1/projects/{project_id}/context/finding",
            params={
                "finding": "GPT-4 has 128K context window",
                "source": "OpenAI documentation"
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "added"
        assert data["finding"] == "GPT-4 has 128K context window"
        assert data["total_findings"] >= 1

    def test_get_context(self, test_client, test_project):
        """测试获取完整 Context"""
        project_id = test_project["id"]

        # 先添加一些数据
        test_client.post(
            f"/api/v1/projects/{project_id}/context/decision",
            params={"decision": "Test decision"}
        )

        response = test_client.get(
            f"/api/v1/projects/{project_id}/context"
        )

        assert response.status_code == 200
        data = response.json()

        assert "intent" in data
        assert "decisions" in data
        assert "failures" in data
        assert "key_findings" in data


# ========== Chat Tests ==========


class TestChat:
    """测试 Chat 功能（目前是 placeholder）"""

    def test_chat_placeholder(self, test_client, test_project):
        """测试 Chat endpoint (placeholder)"""
        project_id = test_project["id"]

        response = test_client.post(
            f"/api/v1/projects/{project_id}/chat",
            json={
                "message": "Hello, world!"
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "received"
        assert data["project_id"] == project_id
        assert "conversation_id" in data
        assert data["message"] == "Hello, world!"
        assert "context_available" in data

    def test_chat_with_selection(self, test_client, test_project):
        """测试带 selection 的 Chat"""
        project_id = test_project["id"]

        response = test_client.post(
            f"/api/v1/projects/{project_id}/chat",
            json={
                "message": "改进这段文字",
                "selection": {
                    "artifact_id": "test-artifact-id",
                    "selected_text": "This is selected text",
                    "selection_range": {
                        "start": 0,
                        "end": 21
                    }
                }
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["selection"] is not None
        assert data["selection"]["artifact_id"] == "test-artifact-id"
