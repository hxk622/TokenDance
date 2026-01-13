-- TokenDance 多租户数据库Schema
-- 三层模型: Organization -> Team -> Workspace
-- 支持PostgreSQL Row Level Security (RLS)

-- ============================================
-- 1. 组织表 (Organizations)
-- ============================================
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,  -- URL友好标识
    
    -- 配置
    settings JSONB DEFAULT '{}',
    
    -- 资源配额
    max_teams INT DEFAULT 10,
    max_workspaces INT DEFAULT 100,
    max_sessions INT DEFAULT 1000,
    storage_quota_gb INT DEFAULT 100,
    
    -- 状态
    status VARCHAR(20) DEFAULT 'active',  -- active/suspended/deleted
    
    -- 时间戳
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,
    
    -- 索引
    INDEX idx_orgs_slug (slug),
    INDEX idx_orgs_status (status)
);

-- ============================================
-- 2. 用户表 (Users)
-- ============================================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(100),
    avatar_url TEXT,
    
    -- 认证
    password_hash VARCHAR(255),  -- bcrypt hash
    
    -- 偏好设置
    preferences JSONB DEFAULT '{}',
    
    -- 状态
    is_active BOOLEAN DEFAULT TRUE,
    email_verified BOOLEAN DEFAULT FALSE,
    
    -- 时间戳
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_login_at TIMESTAMPTZ,
    
    -- 索引
    INDEX idx_users_email (email),
    INDEX idx_users_active (is_active)
);

-- ============================================
-- 3. 组织成员表 (Organization Members)
-- ============================================
CREATE TABLE organization_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- 角色
    role VARCHAR(20) NOT NULL,  -- owner/admin/member
    
    -- 权限
    permissions JSONB DEFAULT '[]',
    
    -- 时间戳
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- 唯一约束
    UNIQUE(org_id, user_id),
    
    -- 索引
    INDEX idx_org_members_org (org_id),
    INDEX idx_org_members_user (user_id)
);

-- ============================================
-- 4. 团队表 (Teams)
-- ============================================
CREATE TABLE teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) NOT NULL,
    description TEXT,
    
    -- 配置
    settings JSONB DEFAULT '{}',
    
    -- 状态
    is_active BOOLEAN DEFAULT TRUE,
    
    -- 时间戳
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- 唯一约束（组织内团队名唯一）
    UNIQUE(org_id, slug),
    
    -- 索引
    INDEX idx_teams_org (org_id),
    INDEX idx_teams_slug (org_id, slug)
);

-- ============================================
-- 5. 团队成员表 (Team Members)
-- ============================================
CREATE TABLE team_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- 角色
    role VARCHAR(20) NOT NULL,  -- admin/member
    
    -- 时间戳
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- 唯一约束
    UNIQUE(team_id, user_id),
    
    -- 索引
    INDEX idx_team_members_team (team_id),
    INDEX idx_team_members_user (user_id)
);

-- ============================================
-- 6. 工作空间表 (Workspaces)
-- ============================================
CREATE TABLE workspaces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),  -- 创建者
    
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- 配置
    settings JSONB DEFAULT '{}',
    
    -- 状态
    is_active BOOLEAN DEFAULT TRUE,
    
    -- 时间戳
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- 索引
    INDEX idx_workspaces_org (org_id),
    INDEX idx_workspaces_team (team_id),
    INDEX idx_workspaces_user (user_id)
);

-- ============================================
-- 7. 会话表 (Sessions)
-- ============================================
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),
    
    title VARCHAR(500),
    
    -- 状态
    status VARCHAR(20) DEFAULT 'active',  -- active/completed/failed
    
    -- Skill
    skill_id VARCHAR(100),
    
    -- 上下文摘要
    context_summary TEXT,
    
    -- 时间戳
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    
    -- 索引
    INDEX idx_sessions_workspace (workspace_id, created_at DESC),
    INDEX idx_sessions_user (user_id, created_at DESC),
    INDEX idx_sessions_status (status)
);

-- ============================================
-- 8. 消息表 (Messages)
-- ============================================
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    
    -- 消息类型
    role VARCHAR(20) NOT NULL,  -- user/assistant/system/tool
    content TEXT,
    
    -- 推理过程
    thinking TEXT,  -- Agent的思考过程
    
    -- 工具调用
    tool_calls JSONB,  -- [{tool_name, args, result}]
    
    -- 引用
    citations JSONB,  -- 引用来源
    
    -- Token统计
    token_count INT,
    
    -- 时间戳
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- 索引
    INDEX idx_messages_session (session_id, created_at ASC)
);

-- ============================================
-- 9. 产物表 (Artifacts)
-- ============================================
CREATE TABLE artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    
    type VARCHAR(50) NOT NULL,  -- document/ppt/code/data
    name VARCHAR(500) NOT NULL,
    file_path TEXT NOT NULL,  -- 文件系统路径
    
    -- 元数据
    metadata JSONB DEFAULT '{}',
    
    -- 大小
    size_bytes BIGINT,
    
    -- 时间戳
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- 索引
    INDEX idx_artifacts_session (session_id, created_at DESC),
    INDEX idx_artifacts_type (type)
);

-- ============================================
-- 10. Row Level Security (RLS) 策略
-- ============================================

-- 启用RLS
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE workspaces ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE artifacts ENABLE ROW LEVEL SECURITY;

-- 创建RLS策略函数
CREATE OR REPLACE FUNCTION current_user_id() RETURNS UUID AS $$
    SELECT current_setting('app.current_user_id', TRUE)::UUID;
$$ LANGUAGE SQL STABLE;

CREATE OR REPLACE FUNCTION current_org_id() RETURNS UUID AS $$
    SELECT current_setting('app.current_org_id', TRUE)::UUID;
$$ LANGUAGE SQL STABLE;

-- Organizations: 用户只能看到自己所属的组织
CREATE POLICY org_policy ON organizations
    FOR ALL
    USING (
        id IN (
            SELECT org_id FROM organization_members
            WHERE user_id = current_user_id()
        )
    );

-- Teams: 用户只能看到自己所属组织的团队
CREATE POLICY team_policy ON teams
    FOR ALL
    USING (
        org_id = current_org_id()
        OR id IN (
            SELECT team_id FROM team_members
            WHERE user_id = current_user_id()
        )
    );

-- Workspaces: 用户只能看到自己团队的工作空间
CREATE POLICY workspace_policy ON workspaces
    FOR ALL
    USING (
        org_id = current_org_id()
        AND team_id IN (
            SELECT team_id FROM team_members
            WHERE user_id = current_user_id()
        )
    );

-- Sessions: 用户只能看到自己工作空间的会话
CREATE POLICY session_policy ON sessions
    FOR ALL
    USING (
        workspace_id IN (
            SELECT id FROM workspaces
            WHERE org_id = current_org_id()
            AND team_id IN (
                SELECT team_id FROM team_members
                WHERE user_id = current_user_id()
            )
        )
    );

-- Messages: 用户只能看到自己会话的消息
CREATE POLICY message_policy ON messages
    FOR ALL
    USING (
        session_id IN (
            SELECT id FROM sessions
            WHERE workspace_id IN (
                SELECT id FROM workspaces
                WHERE org_id = current_org_id()
            )
        )
    );

-- Artifacts: 用户只能看到自己会话的产物
CREATE POLICY artifact_policy ON artifacts
    FOR ALL
    USING (
        session_id IN (
            SELECT id FROM sessions
            WHERE workspace_id IN (
                SELECT id FROM workspaces
                WHERE org_id = current_org_id()
            )
        )
    );

-- ============================================
-- 11. 触发器：自动更新updated_at
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_organizations_updated_at BEFORE UPDATE ON organizations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_teams_updated_at BEFORE UPDATE ON teams
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_workspaces_updated_at BEFORE UPDATE ON workspaces
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sessions_updated_at BEFORE UPDATE ON sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
