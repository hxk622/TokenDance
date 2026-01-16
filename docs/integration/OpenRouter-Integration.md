# OpenRouter 集成指南

## 概述

OpenRouter 是一个统一的 LLM 网关服务，通过单一 API 接口访问多家 LLM 提供商（Claude、GPT、Gemini 等），支持智能路由和成本优化。

**集成优势**：
- **模型聚合** - 单一 API Key 访问 10+ 主流 LLM
- **成本优化** - 根据任务类型选择性价比最优模型
- **降低供应商锁定** - 无缝切换不同提供商
- **透明定价** - 实时显示各模型成本

## 架构设计

### LLM Provider 抽象层

```
TokenDance Agent Runtime
├── BaseLLM (抽象基类)
│   ├── ClaudeLLM (Anthropic 直连)
│   ├── QwenLLM (通义千问)
│   └── OpenRouterLLM (多模型网关) ⭐ 新增
```

### 集成位置

```
backend/app/agent/llm/
├── base.py           # BaseLLM 抽象基类
├── anthropic.py      # Claude 直连实现
├── qwen.py           # 通义千问实现
├── openrouter.py     # OpenRouter 实现 ⭐
└── __init__.py       # 模块导出
```

## 快速开始

### 1. 环境变量配置

```bash
# .env
OPENROUTER_API_KEY=sk-or-v1-xxxxx
OPENROUTER_MODEL=anthropic/claude-3-5-sonnet
OPENROUTER_SITE_URL=https://tokendance.ai
OPENROUTER_APP_NAME=TokenDance
```

⚠️ **安全提醒**：
- 永远不要在代码中硬编码 API Key
- 使用环境变量或密钥管理服务
- 定期轮换密钥

### 2. 基础使用

```python
from app.agent.llm import OpenRouterLLM, LLMMessage

# 初始化客户端
llm = OpenRouterLLM(
    api_key="sk-or-v1-xxxxx",
    model="anthropic/claude-3-5-sonnet"
)

# 完整调用
messages = [
    LLMMessage(role="user", content="你好")
]
response = await llm.complete(messages)
print(response.content)

# 流式调用
async for chunk in llm.stream(messages):
    print(chunk, end="", flush=True)
```

### 3. 使用工厂函数（推荐）

```python
from app.agent.llm import create_openrouter_llm

# 从环境变量自动加载配置
llm = create_openrouter_llm()

# 或者覆盖特定参数
llm = create_openrouter_llm(
    model="gpt-4",
    temperature=0.7
)
```

## 进阶功能

### 智能路由策略

根据任务类型动态选择最优模型：

```python
from app.agent.llm import create_openrouter_llm

def get_llm_for_task(task_type: str):
    """根据任务类型选择 LLM"""
    model_map = {
        "deep_research": "anthropic/claude-3-opus",      # 推理能力强
        "code_generation": "deepseek/deepseek-coder",    # 代码专精
        "fast_qa": "anthropic/claude-3-haiku",           # 速度快、成本低
        "multimodal": "google/gemini-pro-vision",        # 图像理解
    }
    
    model = model_map.get(task_type, "anthropic/claude-3-5-sonnet")
    return create_openrouter_llm(model=model)

# 使用示例
llm = get_llm_for_task("deep_research")
```

### 温度参数调整

```python
# 创意任务（高温度）
creative_llm = create_openrouter_llm(
    model="anthropic/claude-3-opus",
    temperature=1.0
)

# 精确任务（低温度）
precise_llm = create_openrouter_llm(
    model="anthropic/claude-3-5-sonnet",
    temperature=0.2
)
```

### Tool Calling 支持

```python
from app.agent.llm import OpenRouterLLM, LLMMessage

llm = OpenRouterLLM(api_key="sk-or-v1-xxxxx")

tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "获取天气信息",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string"}
            },
            "required": ["location"]
        }
    }
}]

messages = [LLMMessage(role="user", content="北京天气怎么样？")]
response = await llm.complete(messages, tools=tools)

if response.tool_calls:
    tool_call = response.tool_calls[0]
    print(f"调用工具: {tool_call['name']}")
    print(f"参数: {tool_call['input']}")
```

## 监控与成本追踪

### 集成到 Context Graph

```python
from app.agent.llm import OpenRouterLLM
from datetime import datetime

async def tracked_llm_call(llm: OpenRouterLLM, messages, session_id: str):
    """带监控的 LLM 调用"""
    start_time = datetime.now()
    response = await llm.complete(messages)
    latency_ms = (datetime.now() - start_time).total_seconds() * 1000
    
    # 记录到 Neo4j Context Graph
    await record_llm_call(
        session_id=session_id,
        provider="openrouter",
        model=llm.model,
        input_tokens=response.usage["input_tokens"],
        output_tokens=response.usage["output_tokens"],
        latency_ms=latency_ms,
        cost_usd=calculate_cost(response.usage)
    )
    
    return response
```

### 成本计算

```python
def calculate_cost(usage: dict, model: str) -> float:
    """计算 LLM 调用成本"""
    # OpenRouter 定价（示例）
    pricing = {
        "anthropic/claude-3-opus": {
            "input": 15.0 / 1_000_000,   # $15 / 1M tokens
            "output": 75.0 / 1_000_000   # $75 / 1M tokens
        },
        "anthropic/claude-3-5-sonnet": {
            "input": 3.0 / 1_000_000,
            "output": 15.0 / 1_000_000
        },
        "anthropic/claude-3-haiku": {
            "input": 0.25 / 1_000_000,
            "output": 1.25 / 1_000_000
        }
    }
    
    rates = pricing.get(model, pricing["anthropic/claude-3-5-sonnet"])
    cost = (
        usage["input_tokens"] * rates["input"] +
        usage["output_tokens"] * rates["output"]
    )
    return round(cost, 6)
```

## 支持的模型

### Anthropic Claude
- `anthropic/claude-3-opus` - 最强推理能力
- `anthropic/claude-3-5-sonnet` - 平衡性能与成本
- `anthropic/claude-3-haiku` - 快速响应

### OpenAI
- `openai/gpt-4-turbo` - GPT-4 最新版
- `openai/gpt-3.5-turbo` - 经济型选择

### Google
- `google/gemini-pro` - Gemini 主力模型
- `google/gemini-pro-vision` - 支持图像

### 开源模型
- `deepseek/deepseek-coder` - 代码专精
- `meta-llama/llama-3-70b` - 开源大模型

完整列表见：https://openrouter.ai/models

## 合规性与安全

### 金融投研场景注意事项

1. **数据隐私**
   - ✅ OpenRouter 声明不存储请求数据
   - ✅ 支持企业级合规审计
   - ⚠️ 敏感数据需脱敏处理

2. **脱敏示例**
```python
def sanitize_financial_data(text: str) -> str:
    """脱敏处理金融数据"""
    import re
    # 隐藏账户号码
    text = re.sub(r'\d{16,19}', '****', text)
    # 隐藏身份证号
    text = re.sub(r'\d{17}[\dXx]', '****', text)
    return text

messages = [
    LLMMessage(role="user", content=sanitize_financial_data(user_input))
]
```

3. **审计日志**
```python
async def audit_log(session_id, request, response):
    """记录 LLM 调用审计日志"""
    await db.execute(
        """
        INSERT INTO llm_audit_log (session_id, timestamp, model, prompt_hash, response_hash)
        VALUES (?, ?, ?, ?, ?)
        """,
        session_id, datetime.now(), model, hash(request), hash(response)
    )
```

## 故障排查

### 常见问题

**Q: API 调用超时**
```python
# 增加超时时间
llm = OpenRouterLLM(api_key="...", timeout=180.0)
```

**Q: 模型不支持 Tool Calling**
- 检查模型是否支持 function calling
- 使用 Claude 3.5 Sonnet 或 GPT-4

**Q: 成本过高**
```python
# 策略 1: 使用更小的模型
llm = create_openrouter_llm(model="anthropic/claude-3-haiku")

# 策略 2: 降低 max_tokens
response = await llm.complete(messages, max_tokens=1024)

# 策略 3: 缓存常见查询
from functools import lru_cache

@lru_cache(maxsize=100)
async def cached_llm_call(prompt: str):
    return await llm.complete([LLMMessage(role="user", content=prompt)])
```

## 测试

运行单元测试：

```bash
cd backend
uv run pytest tests/test_openrouter_llm.py -v
```

## 下一步

- [ ] 实现智能路由器（基于成本和延迟自动选择模型）
- [ ] 集成 Prometheus 监控指标
- [ ] 添加请求重试和降级策略
- [ ] 构建 LLM Provider 切换 UI

## 参考资料

- [OpenRouter 官方文档](https://openrouter.ai/docs)
- [TokenDance Agent Runtime 设计](../architecture/Agent-Runtime-Design.md)
- [Context Graph 决策轨迹](../modules/Context-Graph.md)
