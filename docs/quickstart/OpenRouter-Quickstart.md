# OpenRouter 集成快速入门

## ⚠️ 首先：安全处理泄露的 API Key

**你在对话中提到的 API Key 已泄露，必须立即行动！**

### 🔴 立即执行（5 分钟内）

1. **撤销泄露的 Key**
   - 访问 https://openrouter.ai/keys
   - 找到并撤销: `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`

2. **生成新 Key**
   - 点击 "Create New API Key"
   - 描述: `TokenDance Production`
   - **立即复制并保存到安全位置**

---

## 🚀 5 分钟快速开始

### Step 1: 安装安全防护（必须）

```bash
cd /path/to/TokenDance

# 安装 Git pre-commit hook（防止未来密钥泄露）
bash scripts/setup_git_hooks.sh

# 验证安装
bash scripts/test_pre_commit_hook.sh
```

**预期输出**: `🎉 所有测试通过！Pre-commit hook 工作正常。`

### Step 2: 配置环境变量

```bash
# 1. 复制配置模板
cp backend/.env.example backend/.env

# 2. 编辑 .env 文件，填入新的 API Key
vim backend/.env

# 添加以下内容（替换为你的新 Key）：
OPENROUTER_API_KEY=sk-or-v1-YOUR_NEW_KEY_HERE
OPENROUTER_MODEL=anthropic/claude-3-5-sonnet
```

**⚠️ 重要**: 
- 永远不要提交 `.env` 文件到 Git
- `.env` 已自动添加到 `.gitignore`

### Step 3: 运行示例代码

```bash
cd backend

# 测试基础功能
uv run python examples/openrouter_example.py
```

**预期输出**:
```
=== 基础对话示例 ===
模型: anthropic/claude-3-5-sonnet
回复: 你好！我是 Claude...
使用 Token: {'input_tokens': 10, 'output_tokens': 25}

=== 流式对话示例 ===
...
```

---

## 📚 核心功能

### 1. 基础对话

```python
from app.agent.llm import create_openrouter_llm, LLMMessage

# 创建客户端
llm = create_openrouter_llm()

# 发送消息
messages = [LLMMessage(role="user", content="你好")]
response = await llm.complete(messages)
print(response.content)
```

### 2. 智能路由（按任务选模型）

```python
def get_llm_for_task(task_type):
    models = {
        "deep_research": "anthropic/claude-3-opus",      # 强推理
        "code": "deepseek/deepseek-coder",               # 代码专精
        "fast_qa": "anthropic/claude-3-haiku",           # 快速低成本
    }
    return create_openrouter_llm(model=models[task_type])

# 使用
llm = get_llm_for_task("deep_research")
```

### 3. 流式响应

```python
async for chunk in llm.stream(messages):
    print(chunk, end="", flush=True)
```

### 4. Tool Calling

```python
tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "parameters": {...}
    }
}]

response = await llm.complete(messages, tools=tools)
if response.tool_calls:
    print(response.tool_calls[0]["name"])
```

---

## 🧪 测试

### 运行单元测试

```bash
cd backend
uv run pytest tests/test_openrouter_llm.py -v
```

**预期**: 12 个测试全部通过

### 测试安全 Hook

```bash
bash scripts/test_pre_commit_hook.sh
```

**预期**: 8 个测试全部通过

---

## 🔒 安全检查清单

在开始开发前，确认以下事项：

- [ ] ✅ 已撤销泄露的旧 API Key
- [ ] ✅ 已生成新的 API Key
- [ ] ✅ 新 Key 已配置到 `.env` 文件
- [ ] ✅ `.env` 已在 `.gitignore` 中
- [ ] ✅ Pre-commit hook 已安装
- [ ] ✅ Pre-commit hook 测试通过
- [ ] ✅ 示例代码运行成功

---

## 📖 完整文档

- **集成指南**: [`docs/integration/OpenRouter-Integration.md`](../integration/OpenRouter-Integration.md)
  - 架构设计
  - 进阶功能
  - 监控与成本追踪
  - 合规性建议

- **安全管理**: [`docs/security/API-Key-Management.md`](../security/API-Key-Management.md)
  - 泄露响应流程
  - 最佳实践
  - 检测工具配置

- **Hooks 使用**: [`scripts/README.md`](../../scripts/README.md)
  - 安装指南
  - 测试方法
  - 常见问题

---

## 💡 常见问题

### Q: 为什么要用 OpenRouter 而不是直连？

**A**: 
- ✅ 单一 API 访问多个模型（Claude、GPT、Gemini）
- ✅ 智能路由优化成本
- ✅ 降低供应商锁定

### Q: OpenRouter 会增加延迟吗？

**A**: 会增加 50-200ms 网络跳转，但换来的是：
- 灵活切换模型
- 透明的成本追踪
- 统一的调用接口

### Q: 如何切换回直连 Claude？

**A**: 
```python
from app.agent.llm import create_claude_llm

llm = create_claude_llm()  # 使用 Anthropic 直连
```

### Q: 测试用的假密钥会被 hook 拦截吗？

**A**: 会！这正是我们想要的。提交测试代码时使用 `--no-verify`。

### Q: 团队其他成员需要做什么？

**A**: 克隆仓库后运行:
```bash
bash scripts/setup_git_hooks.sh
```

---

## 🎯 下一步

### Phase 2: 智能路由器（推荐）

创建自动路由逻辑：

```python
# backend/app/agent/llm/router.py
class LLMRouter:
    def select_model(self, task_type, budget, latency_requirement):
        # 基于成本、延迟、能力自动选择最优模型
        pass
```

### Phase 3: 监控集成

将 LLM 调用集成到 Context Graph：

```python
# 记录到 Neo4j
await record_llm_call(
    session_id=session_id,
    provider="openrouter",
    model=llm.model,
    cost_usd=calculate_cost(response.usage)
)
```

### Phase 4: 成本优化

- 实现请求缓存
- 配置模型降级策略
- 设置预算告警

---

## 🆘 需要帮助？

- **文档问题**: 提 Issue 或 PR
- **安全问题**: 参考 [`API-Key-Management.md`](../security/API-Key-Management.md)
- **集成问题**: 查看 [`OpenRouter-Integration.md`](../integration/OpenRouter-Integration.md)

---

**记住**: 
- 🔴 立即撤销泄露的 API Key
- 🟢 使用环境变量管理密钥
- 🔵 定期测试安全 hook

**开始安全开发吧！** 🎉
