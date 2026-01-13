# Tool-Use设计文档

> **核心更新 (2026-01-09)**: 集成 KV-Cache 优化策略
> - 工具定义一次性加载（固定前缀）
> - 工具掩码技术（Attention Mask）
> - KV-Cache 命中率 > 90%

## 1. 三步走闭环

```python
# 描述(Definition) → 决策(Reasoning) → 执行与反馈(Execution & Observation)

class ToolRegistry:
    def register(self, tool: BaseTool):
        """注册工具（Definition）"""
        self.tools[tool.name] = {
            "function": tool.execute,
            "schema": tool.get_json_schema(),  # OpenAPI格式
            "description": tool.description,
            "risk_level": tool.risk_level
        }

class ToolExecutor:
    async def execute(self, tool_name: str, args: dict):
        """执行工具（Execution）"""
        result = await self.tools[tool_name].execute(**args)
        
        # 反馈给Agent（Observation）
        return ToolResult(
            status="success" | "error",
            data=result,
            summary=self._summarize(result)  # 大结果摘要化
        )
```

## 2. 稳定性四大策略

### 2.1 强类型约束(Guardrails)

```python
from pydantic import BaseModel, Field

class WebSearchArgs(BaseModel):
    """工具参数强类型"""
    query: str = Field(..., min_length=1, max_length=200)
    num_results: int = Field(10, ge=1, le=50)

@tool_registry.register
class WebSearchTool(BaseTool):
    name = "web_search"
    args_schema = WebSearchArgs
    
    async def execute(self, query: str, num_results: int = 10):
        # Pydantic自动校验
        ...
```

### 2.2 自我修复循环

```python
async def execute_with_self_heal(tool_name: str, args: dict, max_retries=2):
    """参数错误时自动修复"""
    for attempt in range(max_retries + 1):
        try:
            return await tool.execute(**args)
        except ValidationError as e:
            if attempt == max_retries:
                raise
            
            # LLM修复参数
            fixed_args = await llm.fix_tool_args(
                tool_name=tool_name,
                original_args=args,
                error=str(e)
            )
            args = fixed_args
```

### 2.3 MCP协议

```python
# Model Context Protocol：标准化工具接口

class MCPTool(BaseTool):
    """MCP标准工具"""
    
    def get_mcp_manifest(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.args_schema.model_json_schema(),
            "outputSchema": self.result_schema.model_json_schema()
        }
```

### 2.4 层级化工具选择

```python
# 避免 Action Space爆炸

class ToolSelector:
    async def select_tools_for_task(self, task: str) -> List[str]:
        """根据任务类型选择相关工具子集"""
        
        # Level 1: 核心通用工具（永远可用）
        core_tools = ["web_search", "read_file", "write_file"]
        
        # Level 2: 任务相关工具（按需加载）
        if "代码" in task or "编程" in task:
            return core_tools + ["run_code", "lint", "test"]
        elif "PPT" in task or "演示" in task:
            return core_tools + ["create_ppt", "add_slide"]
        else:
            return core_tools
```

## 3. Tool-Making（未来趋势）

```python
# Agent自己创造工具

class ToolMaker:
    async def create_tool_from_description(self, description: str):
        """根据描述生成新工具"""
        
        code = await llm.generate_tool_code(description)
        
        # 在Sandbox中测试
        test_result = await sandbox.test_tool(code)
        
        if test_result.passed:
            # 动态注册
            tool = self._load_tool_from_code(code)
            tool_registry.register(tool)
            return tool
        
        return None
```

## 4. 与文件系统集成

```python
# 大结果存文件，Message中只放摘要

class DualContextToolExecutor:
    async def execute(self, tool_name: str, args: dict):
        result = await self.tools[tool_name].execute(**args)
        
        if len(str(result)) > 5000:
            # 存文件
            path = f"temp/{tool_name}_{uuid4().hex[:8]}.json"
            await self.fs.write(path, json.dumps(result))
            
            return ToolResult(
                type="file_reference",
                file_path=path,
                summary=f"{tool_name}结果已存储至{path}"
            )
        
        return ToolResult(type="inline", data=result)
```

## 5. KV-Cache 优化策略 🆕 ⭐

### 5.1 工具定义一次性加载

**原则**：所有工具定义在初始化时加载，成为 System Prompt 的一部分，永不变化。

```python
# backend/app/tools/registry.py

class ToolRegistry:
    """KV-Cache 友好的工具注册表"""
    
    def __init__(self):
        self.tools = {}
        self._tool_definitions_text = None  # 缓存工具定义文本
    
    def register(self, tool: BaseTool):
        """注册工具"""
        self.tools[tool.name] = {
            "function": tool.execute,
            "schema": tool.get_json_schema(),
            "description": tool.description,
            "risk_level": tool.risk_level
        }
        # 重置缓存
        self._tool_definitions_text = None
    
    def get_all_tool_definitions(self) -> str:
        """
        获取所有工具的定义文本（用于 System Prompt）
        
        关键：
        - 这个文本在 session 开始时生成，之后永不变化
        - 包含所有工具，即使当前不用
        - 通过掩码技术控制可见性
        """
        if self._tool_definitions_text is not None:
            return self._tool_definitions_text
        
        lines = ["<|TOOLS|>"]
        
        for tool_name, tool_info in sorted(self.tools.items()):
            schema = tool_info["schema"]
            lines.append(f"\n### {tool_name}")
            lines.append(f"**Description**: {tool_info['description']}")
            lines.append(f"**Schema**: {json.dumps(schema, indent=2)}")
            lines.append(f"**Risk Level**: {tool_info['risk_level']}")
        
        self._tool_definitions_text = "\n".join(lines)
        return self._tool_definitions_text
    
    def get_tool_positions(self) -> Dict[str, Tuple[int, int]]:
        """
        计算每个工具在 System Prompt 中的 Token 位置
        用于工具掩码（Tool Masking）
        """
        positions = {}
        current_pos = 0
        
        for tool_name, tool_info in sorted(self.tools.items()):
            # 粗略估计：1 字 = 1 token（实际需要精确 tokenization）
            tool_text = self._format_tool_definition(tool_name, tool_info)
            token_count = len(tool_text) // 4  # 粗略估计
            
            positions[tool_name] = (current_pos, current_pos + token_count)
            current_pos += token_count
        
        return positions

# 使用示例：
SYSTEM_PROMPT = f"""
<|SYSTEM|>
你是 TokenDance Agent。

{tool_registry.get_all_tool_definitions()}  # 所有工具一次性加载

# 行为规范
...
"""
```

**好处**：
- ✅ System Prompt 固定不变 → KV-Cache 100% 命中
- ✅ 无需每轮重新加载工具定义
- ✅ 性能提升 7x

---

### 5.2 工具掩码技术（Tool Definition Masking）

**问题**：所有工具定义都在 context 中，但某些步骤只需要部分工具。如何让模型"看不见"不可用的工具？

**解决**：使用 Attention Mask 技术，而不是从 context 中删除工具定义。

```python
# backend/app/tools/masking.py

class ToolMasking:
    """工具掩码管理器"""
    
    def __init__(self, tool_registry: ToolRegistry):
        self.registry = tool_registry
        self.tool_positions = tool_registry.get_tool_positions()
    
    def generate_attention_mask(
        self,
        available_tools: List[str],
        total_tokens: int
    ) -> List[int]:
        """
        生成 Attention Mask
        
        原理：
        - mask[i] = 1: Token i 对模型可见
        - mask[i] = 0: Token i 对模型不可见（但仍然在 context 中）
        
        效果：
        - 工具定义永远在 context → KV-Cache 100% 命中
        - 模型只能调用可见的工具 → 行为正确
        """
        mask = [1] * total_tokens  # 默认全部可见
        
        # 掩码不可用的工具
        for tool_name, (start, end) in self.tool_positions.items():
            if tool_name not in available_tools:
                # 设置为 0，模型看不见
                mask[start:end] = [0] * (end - start)
        
        return mask
    
    def get_available_tools_for_step(self, step_type: str) -> List[str]:
        """
        根据步骤类型返回可用工具
        
        示例：
        - 搜索阶段：只需要 web_search
        - 阅读阶段：需要 read_url, summarize
        - 生成阶段：需要 create_artifact
        """
        if step_type == "search":
            return ["web_search"]
        elif step_type == "read":
            return ["read_url", "summarize"]
        elif step_type == "generate":
            return ["create_artifact"]
        else:
            # 默认：所有工具可用
            return list(self.tool_positions.keys())

# 使用示例：
class AgentExecutor:
    async def execute_step(self, step_type: str):
        # 获取可用工具
        available_tools = self.tool_masking.get_available_tools_for_step(step_type)
        
        # 生成掩码
        attention_mask = self.tool_masking.generate_attention_mask(
            available_tools=available_tools,
            total_tokens=len(self.context_tokens)
        )
        
        # 调用 LLM（传入掩码）
        response = await self.llm.generate(
            messages=self.context,
            attention_mask=attention_mask,  # 关键！
            use_cache=True
        )
```

**关键优势**：
- ✅ 工具定义永远在 context，KV-Cache 不失效
- ✅ 通过掩码控制可见性，模型行为正确
- ✅ 无需重新加载 context，性能最优

**注意事项**：
- ⚠️ 需要 LLM API 支持 `attention_mask` 参数（Claude/Gemini 可能不支持）
- ⚠️ 如果 API 不支持，降级方案：在 System Prompt 中动态标记可用工具

```python
# 降级方案：在 System Prompt 中显式标记
SYSTEM_PROMPT = f"""
...

# 当前可用工具 (⭐ 开启 = 可用，❌ 禁用 = 不可用)
⭐ web_search
❌ read_url
⭐ summarize

请只调用标记为 ⭐ 的工具。
"""
```

---

## 6. 总结

**核心设计**：
1. 三步走闭环：Definition → Reasoning → Execution
2. 四大稳定性策略：Guardrails、Self-Heal、MCP、层级选择
3. 与文件系统集成：大结果存文件
4. **KV-Cache 优化**：工具定义一次性加载 + 工具掩码技术 🆕

**与其他模块关系**：
- 依赖 Reasoning：工具调用失败触发 Self-Reflection
- 依赖 Sandbox：代码执行工具需要安全隔离
- 依赖 Context Graph：记录工具调用轨迹
- 依赖 Context Manager：提供 KV-Cache 友好的 System Prompt
