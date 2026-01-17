# SSE Events Specification

TokenDance 前后端 Server-Sent Events (SSE) 事件规范。

## 事件分类

### 1. Session 事件
| Event | 描述 | 数据字段 |
|-------|------|---------|
| `session_started` | 会话开始 | `session_id`, `timestamp` |
| `session_completed` | 会话完成 | `session_id`, `status`, `duration_ms`, `timestamp` |
| `session_failed` | 会话失败 | `session_id`, `error`, `timestamp` |

### 2. Skill 事件
| Event | 描述 | 数据字段 |
|-------|------|---------|
| `skill_matched` | Skill 匹配成功 | `skill_id`, `skill_name`, `display_name`, `description`, `icon`, `color`, `confidence`, `timestamp` |
| `skill_completed` | Skill 执行完成 | `skill_id`, `status`, `duration_ms`, `timestamp` |

### 3. Agent 思考/决策事件
| Event | 描述 | 数据字段 |
|-------|------|---------|
| `agent_thinking` | Agent 思考过程 | `content`, `node_id`, `timestamp` |
| `agent_tool_call` | 工具调用开始 | `tool_name`, `tool_id`, `arguments`, `node_id`, `timestamp` |
| `agent_tool_result` | 工具执行结果 | `tool_name`, `tool_id`, `success`, `result`, `error`, `duration_ms`, `node_id`, `timestamp` |
| `agent_message` | Agent 消息输出 | `content`, `role`, `citations`, `timestamp` |
| `agent_error` | Agent 错误 | `message`, `type`, `details`, `timestamp` |

### 4. Workflow 节点事件
| Event | 描述 | 数据字段 |
|-------|------|---------|
| `node_started` | 节点开始执行 | `node_id`, `node_type`, `label`, `timestamp` |
| `node_completed` | 节点执行完成 | `node_id`, `node_type`, `label`, `status`, `duration_ms`, `output`, `timestamp` |
| `node_failed` | 节点执行失败 | `node_id`, `node_type`, `label`, `error`, `timestamp` |

### 5. File 操作事件
| Event | 描述 | 数据字段 |
|-------|------|---------|
| `file_created` | 文件创建 | `path`, `size`, `timestamp` |
| `file_modified` | 文件修改 | `path`, `changes`, `timestamp` |
| `file_deleted` | 文件删除 | `path`, `timestamp` |
| `file_read` | 文件读取 | `path`, `lines`, `timestamp` |

### 6. Browser 操作事件
| Event | 描述 | 数据字段 |
|-------|------|---------|
| `browser_opened` | 浏览器打开 | `browser_id`, `url`, `timestamp` |
| `browser_navigated` | 导航到 URL | `browser_id`, `url`, `title`, `timestamp` |
| `browser_action` | 浏览器操作 | `browser_id`, `action`, `target`, `value`, `timestamp` |
| `browser_screenshot` | 截图 | `browser_id`, `path`, `timestamp` |
| `browser_closed` | 浏览器关闭 | `browser_id`, `timestamp` |

### 7. HITL (Human-in-the-Loop) 事件
| Event | 描述 | 数据字段 |
|-------|------|---------|
| `hitl_request` | 需要人类确认 | `request_id`, `tool`, `args`, `risk_level`, `description`, `timeout`, `timestamp` |
| `hitl_timeout` | 确认超时 | `request_id`, `timestamp` |

### 8. Artifact 事件
| Event | 描述 | 数据字段 |
|-------|------|---------|
| `artifact_created` | 产物创建 | `artifact_id`, `type`, `name`, `path`, `timestamp` |
| `artifact_updated` | 产物更新 | `artifact_id`, `changes`, `timestamp` |

### 9. Progress 事件
| Event | 描述 | 数据字段 |
|-------|------|---------|
| `progress_update` | 进度更新 | `current`, `total`, `message`, `percentage`, `timestamp` |
| `iteration_start` | 迭代开始 | `iteration`, `max_iterations`, `timestamp` |

### 10. Token/Cost 事件
| Event | 描述 | 数据字段 |
|-------|------|---------|
| `token_usage` | Token 使用统计 | `input_tokens`, `output_tokens`, `total_tokens`, `model`, `timestamp` |

### 11. System 事件
| Event | 描述 | 数据字段 |
|-------|------|---------|
| `ping` | 心跳保活 | `timestamp` |
| `error` | 系统错误 | `message`, `code`, `timestamp` |

## 事件数据示例

```json
// skill_matched
{
  "event": "skill_matched",
  "data": {
    "skill_id": "deep_research",
    "skill_name": "deep_research",
    "display_name": "Deep Research",
    "description": "深度研究技能",
    "icon": "search",
    "color": "blue",
    "confidence": 0.92,
    "timestamp": 1737115234.567
  }
}

// agent_tool_call
{
  "event": "agent_tool_call",
  "data": {
    "tool_name": "web_search",
    "tool_id": "tc_123",
    "arguments": {"query": "AI market analysis"},
    "node_id": "node_1",
    "timestamp": 1737115235.123
  }
}

// browser_action
{
  "event": "browser_action",
  "data": {
    "browser_id": "br_456",
    "action": "click",
    "target": "button.submit",
    "value": null,
    "timestamp": 1737115236.789
  }
}

// hitl_request
{
  "event": "hitl_request",
  "data": {
    "request_id": "hitl_789",
    "tool": "file_delete",
    "args": {"path": "/important/file.txt"},
    "risk_level": "high",
    "description": "删除重要文件",
    "timeout": 60,
    "timestamp": 1737115237.456
  }
}

// progress_update
{
  "event": "progress_update",
  "data": {
    "current": 3,
    "total": 10,
    "message": "正在分析第 3 个数据源...",
    "percentage": 30,
    "timestamp": 1737115238.123
  }
}
```

## Icon 映射

SkillIndicator 支持的 icon 值：
- `brain` / `sparkles` - AI/智能
- `code` - 代码/编程
- `search` - 搜索/研究
- `file` - 文件/文档
- `tool` / `wrench` - 工具
- `globe` - 网络/浏览器
- `database` - 数据
- `default` / `bolt` - 默认

## Color 映射

SkillIndicator 支持的 color 值：
- `blue` - 蓝色 (默认)
- `green` - 绿色
- `purple` - 紫色
- `orange` - 橙色
- `cyan` - 青色
