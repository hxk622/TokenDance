"""
模型初始化测试 - 确保所有 ORM 模型能正确加载

这个测试会在 CI 和本地运行时提前发现:
- 关系定义错误 (如缺少外键字段)
- 循环导入问题
- 类型注解错误
"""


def test_all_models_can_be_imported():
    """测试所有模型能被正确导入"""
    # 这会触发 SQLAlchemy mapper 配置
    from app.models import (
        Artifact,
        Conversation,
        Message,
        Project,
        Session,
        Skill,
        User,
        Workspace,
    )

    # 如果能走到这里，说明所有模型配置正确
    assert User is not None
    assert Workspace is not None
    assert Session is not None
    assert Message is not None
    assert Artifact is not None
    assert Project is not None
    assert Conversation is not None
    assert Skill is not None


def test_orm_mappers_configured():
    """测试 ORM mappers 已正确配置"""
    from sqlalchemy.orm import configure_mappers

    from app.core.database import Base

    # 这会强制配置所有 mapper，暴露关系定义错误
    configure_mappers()

    # 检查所有表都已注册
    assert len(Base.metadata.tables) > 0
    print(f"Successfully configured {len(Base.metadata.tables)} tables")


def test_model_relationships_valid():
    """测试模型关系定义有效"""
    from sqlalchemy import inspect

    from app.models import Conversation, Message, Project, Session

    # 检查关键模型的关系
    session_mapper = inspect(Session)
    assert 'workspace' in session_mapper.relationships.keys()
    assert 'messages' in session_mapper.relationships.keys()

    message_mapper = inspect(Message)
    assert 'session' in message_mapper.relationships.keys()

    project_mapper = inspect(Project)
    assert 'conversations' in project_mapper.relationships.keys()

    conversation_mapper = inspect(Conversation)
    assert 'project' in conversation_mapper.relationships.keys()
    assert 'messages' in conversation_mapper.relationships.keys()
