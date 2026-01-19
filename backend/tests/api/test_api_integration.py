"""
API Integration Tests

测试 API 端点与 Agent Engine 的集成
"""

import os

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

# 跳过如果没有配置 API KEY
pytestmark = pytest.mark.skipif(
    not os.getenv("OPENROUTER_API_KEY"),
    reason="OPENROUTER_API_KEY not set"
)


# ========== Fixtures ==========

@pytest.fixture
def test_client():
    """创建测试客户端"""
    from app.main import app
    return TestClient(app)


@pytest.fixture
async def async_client():
    """创建异步测试客户端"""
    from app.main import app
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def test_workspace_id():
    """测试用的 workspace ID"""
    return "test_workspace_api"


@pytest.fixture
async def test_session(test_client, test_workspace_id):
    """创建测试 session"""
    response = test_client.post(
        "/api/v1/sessions",
        json={
            "workspace_id": test_workspace_id,
            "user_id": "test_user",
            "title": "API Integration Test"
        }
    )

    assert response.status_code == 201
    session = response.json()

    yield session

    # 清理: 删除 session
    test_client.delete(f"/api/v1/sessions/{session['id']}")


# ========== Session API Tests ==========

def test_create_session(test_client, test_workspace_id):
    """测试创建 Session"""
    response = test_client.post(
        "/api/v1/sessions",
        json={
            "workspace_id": test_workspace_id,
            "user_id": "test_user",
            "title": "Test Session"
        }
    )

    assert response.status_code == 201
    data = response.json()

    assert "id" in data
    assert data["workspace_id"] == test_workspace_id
    assert data["title"] == "Test Session"


def test_list_sessions(test_client, test_workspace_id, test_session):
    """测试列出 Sessions"""
    response = test_client.get(
        f"/api/v1/sessions?workspace_id={test_workspace_id}"
    )

    assert response.status_code == 200
    data = response.json()

    assert "items" in data
    assert len(data["items"]) > 0


def test_get_session(test_client, test_session):
    """测试获取 Session 详情"""
    session_id = test_session["id"]

    response = test_client.get(f"/api/v1/sessions/{session_id}")

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == session_id


# ========== Messages API Tests ==========

def test_send_message_no_stream(test_client, test_session):
    """测试发送消息（非流式）"""
    session_id = test_session["id"]

    response = test_client.post(
        f"/api/v1/sessions/{session_id}/messages",
        json={
            "content": "2 + 2 等于几？",
            "stream": False
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert "content" in data
    assert "4" in data["content"]
    assert data["role"] == "assistant"
    assert "token_usage" in data


@pytest.mark.asyncio
async def test_send_message_stream(async_client, test_session):
    """测试发送消息（流式）"""
    session_id = test_session["id"]

    async with async_client.stream(
        "POST",
        f"/api/v1/sessions/{session_id}/messages",
        json={
            "content": "简单说一下 FastAPI 是什么",
            "stream": True
        }
    ) as response:
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

        events = []
        async for line in response.aiter_lines():
            if line.startswith("event:"):
                event_type = line.split(":", 1)[1].strip()
            elif line.startswith("data:"):
                import json
                event_data = json.loads(line.split(":", 1)[1])
                events.append((event_type, event_data))

        # 验证事件序列
        event_types = [e[0] for e in events]

        assert "start" in event_types
        assert "answer" in event_types or "reasoning" in event_types
        assert "done" in event_types


def test_get_messages(test_client, test_session):
    """测试获取消息历史"""
    session_id = test_session["id"]

    # 先发送一条消息
    test_client.post(
        f"/api/v1/sessions/{session_id}/messages",
        json={
            "content": "Hello",
            "stream": False
        }
    )

    # 获取消息历史
    response = test_client.get(f"/api/v1/sessions/{session_id}/messages")

    assert response.status_code == 200
    data = response.json()

    assert "items" in data
    # 应该至少有2条消息（用户+助手）
    assert len(data["items"]) >= 2


def test_get_working_memory(test_client, test_session):
    """测试获取 Working Memory"""
    session_id = test_session["id"]

    # 先发送一条消息触发 Agent
    test_client.post(
        f"/api/v1/sessions/{session_id}/messages",
        json={
            "content": "创建一个简单的任务计划",
            "stream": False
        }
    )

    # 获取 Working Memory
    response = test_client.get(
        f"/api/v1/sessions/{session_id}/working-memory"
    )

    assert response.status_code == 200
    data = response.json()

    assert "task_plan" in data
    assert "findings" in data
    assert "progress" in data

    # 验证三个文件都有内容
    assert "content" in data["task_plan"]
    assert "content" in data["findings"]
    assert "content" in data["progress"]


# ========== Error Handling Tests ==========

def test_session_not_found(test_client):
    """测试 Session 不存在的情况"""
    response = test_client.get("/api/v1/sessions/nonexistent_id")

    assert response.status_code == 404
    data = response.json()

    assert "error" in data


def test_send_message_to_nonexistent_session(test_client):
    """测试向不存在的 Session 发送消息"""
    response = test_client.post(
        "/api/v1/sessions/nonexistent_id/messages",
        json={
            "content": "Hello",
            "stream": False
        }
    )

    assert response.status_code == 404


def test_invalid_request_body(test_client, test_session):
    """测试无效的请求体"""
    session_id = test_session["id"]

    response = test_client.post(
        f"/api/v1/sessions/{session_id}/messages",
        json={
            # 缺少必需的 content 字段
            "stream": True
        }
    )

    assert response.status_code == 422
    data = response.json()

    assert "error" in data
    assert data["error"]["type"] == "ValidationError"


# ========== Performance Tests ==========

@pytest.mark.slow
def test_concurrent_messages(test_client, test_session):
    """测试并发发送消息"""
    session_id = test_session["id"]

    import concurrent.futures

    def send_message(n):
        response = test_client.post(
            f"/api/v1/sessions/{session_id}/messages",
            json={
                "content": f"什么是 {n}？",
                "stream": False
            }
        )
        return response.status_code

    # 并发发送3条消息
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        results = list(executor.map(send_message, ["Python", "FastAPI", "Vue"]))

    # 所有请求都应该成功
    assert all(status == 200 for status in results)


# ========== Main (用于单独运行) ==========

if __name__ == "__main__":
    """
    运行方式：

    pytest backend/test_api_integration.py -v
    pytest backend/test_api_integration.py::test_send_message_stream -v -s
    """
    pytest.main([__file__, "-v", "-s"])
