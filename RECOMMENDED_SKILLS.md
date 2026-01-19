# TokenDance项目推荐的Claude Code技能

## 项目架构
- **前端**: Vue3 + Vite + TypeScript + Tailwind CSS
- **后端**: Python FastAPI + PostgreSQL + Redis
- **核心**: AI Agent系统 + MCP工具集成

---

## 🎯 推荐安装的技能

### 1. ✅ webapp-testing（已安装）
**用途**: 自动化测试前后端
```bash
# 测试前后端集成
python scripts/with_server.py \
  --server "cd backend && uvicorn app.main:app --reload" --port 8000 \
  --server "cd frontend && pnpm dev" --port 5173 \
  -- python test_integration.py
```

**适用场景**:
- 测试Agent交互流程
- 验证前端UI功能
- 端到端测试

---

### 2. 🎨 frontend-design
**用途**: 创建高质量Vue3组件和页面

**适用场景**:
- 优化Agent对话界面
- 创建新的Dashboard组件
- 设计工作流可视化界面

**示例**:
> "帮我设计一个Agent执行状态的可视化组件，使用Vue3和Tailwind CSS"

---

### 3. 🔧 mcp-builder
**用途**: 构建和扩展MCP服务器

**适用场景**:
- 添加新的Agent工具
- 集成外部API服务
- 扩展MCP工具能力

**示例**:
> "帮我创建一个MCP服务器，用于集成GitHub API"

---

### 4. 🌐 web-artifacts-builder
**用途**: 创建复杂的多组件Web应用

**适用场景**:
- 构建Agent配置界面
- 创建交互式报告
- 开发复杂的数据可视化

---

### 5. 📊 xlsx
**用途**: Excel文件处理和数据分析

**适用场景**:
- Agent生成数据报告
- 导出会话统计
- 批量数据处理

**示例**:
> "将所有session数据导出为Excel，包含统计图表"

---

### 6. 📝 docx
**用途**: Word文档生成和编辑

**适用场景**:
- Agent生成研究报告
- 创建项目文档
- 导出会话记录

---

### 7. 📄 pdf
**用途**: PDF文档处理

**适用场景**:
- 生成Agent执行报告
- 导出分析结果
- 文档归档

---

### 8. 🎨 theme-factory
**用途**: 统一平台主题风格

**适用场景**:
- 应用品牌色彩
- 统一UI风格
- 快速切换主题

---

## 🚀 使用方法

### 自动调用
在对话中直接描述任务，Claude会自动识别并使用相应技能：

```
✅ "帮我测试前端的登录功能" → webapp-testing
✅ "创建一个Agent状态卡片组件" → frontend-design
✅ "构建一个天气查询MCP工具" → mcp-builder
✅ "导出用户数据到Excel" → xlsx
```

### 手动指定
如果需要明确使用某个技能：

```
"使用frontend-design技能，帮我创建一个..."
```

---

## 📊 技能与项目功能映射

| 项目功能 | 推荐技能 | 优先级 |
|---------|---------|--------|
| Agent对话界面优化 | frontend-design | ⭐⭐⭐ |
| 工作流可视化 | web-artifacts-builder | ⭐⭐⭐ |
| 自动化测试 | webapp-testing | ⭐⭐⭐ |
| MCP工具扩展 | mcp-builder | ⭐⭐⭐ |
| 数据报告导出 | xlsx, docx, pdf | ⭐⭐ |
| UI主题定制 | theme-factory | ⭐⭐ |

---

## 🔧 技能配置示例

### webapp-testing配置
```python
# test_integration.py
from playwright.sync_api import sync_playwright

def test_agent_chat():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("http://localhost:5173")

        # 测试Agent对话
        page.fill('[data-testid="chat-input"]', "Hello Agent")
        page.click('[data-testid="send-button"]')

        # 验证响应
        response = page.wait_for_selector('[data-testid="agent-response"]')
        assert response.text_content()

        browser.close()
```

### mcp-builder配置
```python
# custom_mcp_server.py
from fastmcp import FastMCP

mcp = FastMCP("TokenDance Custom Tools")

@mcp.tool()
def analyze_session(session_id: str) -> dict:
    """分析Agent会话数据"""
    # 实现逻辑
    return {"status": "success"}
```

---

## 📚 相关文档

- **技能详情**: `~/.claude/plugins/marketplaces/anthropic-agent-skills/skills/`
- **项目架构**: `FIXES_SUMMARY.md`
- **API文档**: `backend/app/api/v1/`

---

## 💡 最佳实践

1. **测试驱动开发**: 使用webapp-testing在开发新功能前编写测试
2. **组件复用**: 使用frontend-design创建可复用的Vue组件库
3. **工具扩展**: 使用mcp-builder为Agent添加新能力
4. **数据导出**: 使用xlsx/docx/pdf为用户提供多格式报告

---

## 🎓 学习资源

### webapp-testing
```bash
# 查看帮助
python ~/.claude/plugins/marketplaces/anthropic-agent-skills/skills/webapp-testing/scripts/with_server.py --help
```

### mcp-builder
```bash
# 查看MCP示例
cat ~/.claude/plugins/marketplaces/anthropic-agent-skills/skills/mcp-builder/reference/python_mcp_server.md
```

---

## 📦 技能状态

| 技能名称 | 状态 | 位置 |
|---------|------|------|
| webapp-testing | ✅ 已安装 | anthropic-agent-skills |
| frontend-design | ✅ 可用 | anthropic-agent-skills |
| mcp-builder | ✅ 可用 | anthropic-agent-skills |
| web-artifacts-builder | ✅ 可用 | anthropic-agent-skills |
| xlsx | ✅ 可用 | anthropic-agent-skills |
| docx | ✅ 可用 | anthropic-agent-skills |
| pdf | ✅ 可用 | anthropic-agent-skills |
| theme-factory | ✅ 可用 | anthropic-agent-skills |

**注意**: 所有技能都已在 `anthropic-agent-skills` marketplace中可用，Claude会自动识别和使用。

---

## 🔄 更新日志

- **2026-01-19**: 创建技能推荐文档，识别8个核心技能
- 下次更新: 根据项目需求添加更多技能

---

## 📞 获取帮助

如需使用某个技能，直接在对话中说：
> "我想使用[技能名]来[做什么]"

Claude会自动加载相应技能并提供帮助！
