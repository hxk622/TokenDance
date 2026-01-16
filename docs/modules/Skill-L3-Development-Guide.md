# Skill L3 执行脚本开发指南

## 概述

Skill 的 L3 层是**自动化能力**的核心。通过编写 `execute.py` 脚本，你可以使 Skill 不仅仅是指令包，而是真正的自动执行工具。

## 架构回顾

```
Skill = L1 + L2 + L3
├── L1 (元数据)    → SKILL.md YAML 头 - 一直在 System Prompt 中
├── L2 (指令)      → SKILL.md 正文 - 按需加载，缓存
└── L3 (脚本)      → resources/execute.py - 自动执行，产出结果
```

## 标准规范

### 1. 入口脚本位置

```
backend/app/skills/builtin/{skill_name}/
├── SKILL.md              # L1 + L2
└── resources/
    └── execute.py        # L3 主入口
```

### 2. 脚本输入规范

脚本通过 **stdin** 接收 JSON 格式的输入：

```json
{
  "skill_name": "deep_research",
  "query": "用户原始查询",
  "context": {
    "user_id": "user123",
    "session_id": "sess456",
    "workspace_id": "ws789"
  },
  "parameters": {
    "param1": "value1",
    "param2": ["value2", "value3"]
  }
}
```

### 3. 脚本输出规范

脚本通过 **stdout** 输出 JSON 格式的结果：

```json
{
  "status": "success|failed|timeout",
  "data": {
    "result_key": "result_value",
    "items": ["item1", "item2"]
  },
  "error": "错误信息（如果有）",
  "tokens_used": 1500
}
```

**字段说明**:
- `status`: 执行状态 (必填)
  - `success` - 执行成功，data 字段包含结果
  - `failed` - 执行失败，error 字段包含错误信息
  - `timeout` - 执行超时
- `data`: 执行结果 (status=success 时必填)
  - 可以是任何类型（dict、list、string 等）
- `error`: 错误描述 (status=failed 时必填)
- `tokens_used`: LLM Token 消耗数量 (可选，默认0)

## 示例 1: 简单脚本 (deep_research)

```python
#!/usr/bin/env python3
"""
深度研究 Skill 的 L3 执行脚本

负责执行实际的研究逻辑（网络搜索、信息聚合等）
"""

import json
import sys
from typing import Dict, Any, Optional


def execute_research(query: str, context: Dict[str, str]) -> Dict[str, Any]:
    """执行深度研究
    
    Args:
        query: 用户查询
        context: 执行上下文
        
    Returns:
        研究结果
    """
    # TODO: 实现实际的研究逻辑
    # 这里可以调用：
    # 1. Web 搜索 API
    # 2. 学术数据库 API
    # 3. 信息聚合和总结
    
    # 示例结果
    return {
        "query": query,
        "sources": ["web_result_1", "academic_result_1"],
        "summary": "基于多源搜索的研究结果总结...",
        "key_findings": [
            "发现 1",
            "发现 2",
            "发现 3"
        ],
        "references": [
            {"title": "参考资料 1", "url": "https://example.com"},
            {"title": "参考资料 2", "url": "https://example.com"}
        ]
    }


def main(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """主函数
    
    Args:
        input_data: 从 stdin 接收的 JSON 数据
        
    Returns:
        执行结果 JSON
    """
    try:
        skill_name = input_data.get("skill_name", "unknown")
        query = input_data.get("query", "")
        context = input_data.get("context", {})
        parameters = input_data.get("parameters", {})
        
        if not query:
            return {
                "status": "failed",
                "error": "Query is required",
                "tokens_used": 0
            }
        
        # 执行研究
        result = execute_research(query, context)
        
        return {
            "status": "success",
            "data": result,
            "tokens_used": 1500  # 预估 Token 消耗
        }
    
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e),
            "tokens_used": 0
        }


if __name__ == "__main__":
    # 从 stdin 读取输入
    input_json = sys.stdin.read()
    input_data = json.loads(input_json)
    
    # 执行
    result = main(input_data)
    
    # 输出结果到 stdout
    print(json.dumps(result, ensure_ascii=False, indent=2))
```

## 示例 2: 复杂脚本 (PPT 生成)

```python
#!/usr/bin/env python3
"""
PPT 生成 Skill 的 L3 执行脚本

负责：
1. 解析输入内容
2. 生成大纲
3. 填充内容
4. 渲染和导出
"""

import json
import sys
import tempfile
from pathlib import Path
from typing import Dict, Any, List


class PPTGenerator:
    """PPT 生成器"""
    
    def __init__(self, query: str, context: Dict[str, str]):
        self.query = query
        self.context = context
        self.slides = []
    
    def generate_outline(self) -> List[Dict[str, Any]]:
        """生成 PPT 大纲"""
        # TODO: 根据 query 生成大纲
        return [
            {
                "type": "title",
                "title": "标题页",
                "subtitle": "副标题"
            },
            {
                "type": "content",
                "title": "内容页 1",
                "points": ["要点 1", "要点 2"]
            },
            {
                "type": "conclusion",
                "title": "结论",
                "points": ["结论 1"]
            }
        ]
    
    def fill_content(self) -> List[Dict[str, Any]]:
        """填充内容"""
        # TODO: 扩展每一页的内容
        return self.slides
    
    def render(self) -> str:
        """渲染为 Markdown"""
        # TODO: 将 Slides 渲染为 Marp Markdown
        markdown = "# My Presentation\n\n---\n\n## Slide 1\n\nContent here"
        return markdown
    
    def generate(self) -> Dict[str, Any]:
        """完整生成流程"""
        try:
            # 生成大纲
            self.slides = self.generate_outline()
            
            # 填充内容
            self.fill_content()
            
            # 渲染
            markdown = self.render()
            
            # 保存到临时文件
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.md',
                delete=False
            ) as f:
                f.write(markdown)
                temp_file = f.name
            
            return {
                "outline_id": "outline_123",
                "slides_count": len(self.slides),
                "markdown_file": temp_file,
                "preview_url": f"/preview/ppt/outline_123.html"
            }
        
        except Exception as e:
            raise RuntimeError(f"PPT generation failed: {e}")


def main(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """主函数"""
    try:
        query = input_data.get("query", "")
        context = input_data.get("context", {})
        parameters = input_data.get("parameters", {})
        
        if not query:
            return {
                "status": "failed",
                "error": "Query (content) is required",
                "tokens_used": 0
            }
        
        # 生成 PPT
        generator = PPTGenerator(query, context)
        result = generator.generate()
        
        return {
            "status": "success",
            "data": result,
            "tokens_used": 2000  # 预估 Token 消耗
        }
    
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e),
            "tokens_used": 0
        }


if __name__ == "__main__":
    input_json = sys.stdin.read()
    input_data = json.loads(input_json)
    result = main(input_data)
    print(json.dumps(result, ensure_ascii=False, indent=2))
```

## 最佳实践

### 1. 错误处理

始终捕获异常并返回结构化的错误信息：

```python
try:
    # 执行逻辑
    result = do_something()
except TimeoutError as e:
    return {
        "status": "timeout",
        "error": "Operation timed out after 30s",
        "tokens_used": 0
    }
except ValueError as e:
    return {
        "status": "failed",
        "error": f"Invalid input: {e}",
        "tokens_used": 0
    }
except Exception as e:
    return {
        "status": "failed",
        "error": f"Unexpected error: {e}",
        "tokens_used": 0
    }
```

### 2. 日志记录

使用 Python 的 logging 模块，输出到 stderr（不要污染 stdout）：

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info("Starting skill execution")
logger.debug(f"Query: {query}")
logger.warning("This operation may take a while")
logger.error("Critical error occurred")
```

### 3. 依赖检查

在脚本开头检查所需的依赖：

```python
def check_dependencies():
    """检查脚本依赖"""
    try:
        import requests
        import numpy
        import pandas
    except ImportError as e:
        return False, f"Missing dependency: {e}"
    return True, None

def main(input_data):
    ok, error = check_dependencies()
    if not ok:
        return {
            "status": "failed",
            "error": error,
            "tokens_used": 0
        }
    # ... 继续执行
```

### 4. Token 计数

如果使用了 Claude API，记录实际消耗的 Token：

```python
from anthropic import Anthropic

client = Anthropic()

def call_claude(prompt):
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )
    
    tokens_used = message.usage.input_tokens + message.usage.output_tokens
    return message.content[0].text, tokens_used

def main(input_data):
    result_text, tokens = call_claude("请分析...")
    
    return {
        "status": "success",
        "data": {"analysis": result_text},
        "tokens_used": tokens
    }
```

### 5. 超时处理

对于长时间运行的操作，使用超时控制：

```python
import signal

def timeout_handler(signum, frame):
    raise TimeoutError("Operation timed out")

def main(input_data):
    # 设置 30 秒超时
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(30)
    
    try:
        # 执行可能耗时的操作
        result = long_running_operation()
        signal.alarm(0)  # 取消闹钟
    except TimeoutError:
        return {
            "status": "timeout",
            "error": "Operation exceeded 30s timeout",
            "tokens_used": 0
        }
```

## 测试

### 本地测试

```bash
# 创建测试输入
cat > test_input.json << 'EOF'
{
  "skill_name": "deep_research",
  "query": "市场调研",
  "context": {
    "user_id": "test_user",
    "session_id": "test_session"
  },
  "parameters": {}
}
EOF

# 测试脚本
python3 execute.py < test_input.json
```

### 单元测试

```python
import unittest
import json
from io import StringIO
from unittest.mock import patch

class TestExecuteScript(unittest.TestCase):
    
    def test_success_case(self):
        """测试成功执行"""
        input_data = {
            "skill_name": "test",
            "query": "test query",
            "context": {},
            "parameters": {}
        }
        
        result = main(input_data)
        
        self.assertEqual(result["status"], "success")
        self.assertIn("data", result)
        self.assertIn("tokens_used", result)
    
    def test_missing_query(self):
        """测试缺失 query"""
        input_data = {
            "skill_name": "test",
            "context": {},
            "parameters": {}
        }
        
        result = main(input_data)
        
        self.assertEqual(result["status"], "failed")
        self.assertIn("error", result)
    
    def test_invalid_input(self):
        """测试无效输入"""
        input_data = "invalid json"
        
        with self.assertRaises(json.JSONDecodeError):
            json.loads(input_data)

if __name__ == "__main__":
    unittest.main()
```

## 集成到 Agent

完成 `execute.py` 后，Skill 会自动被 Agent 发现和执行：

```
用户: "帮我调研 AI Agent 市场"
  ↓
Agent 匹配到 deep_research Skill
  ↓
SkillExecutor 执行 execute.py
  ↓
接收 JSON 结果
  ↓
将结果注入 Context
  ↓
Agent 基于结果继续处理
```

## 故障排查

| 问题 | 原因 | 解决方案 |
|------|------|--------|
| `FileNotFoundError: No module named 'xxx'` | 缺少依赖 | 在 `check_dependencies()` 中检查并返回错误 |
| `json.JSONDecodeError` | 输出不是有效 JSON | 确保 stdout 只输出 JSON，日志写到 stderr |
| 脚本超时 | 执行耗时过长 | 使用超时控制，或优化算法 |
| 返回 `{"status": "failed"}` | 脚本异常 | 检查 stderr 输出或添加日志 |

## 下一步

- 为现有 Skill (`deep_research`, `ppt`, `image_generation`) 实现 `execute.py`
- 为科学计算 Skill 编写执行脚本
- 建立 Skill 市场，共享优秀的执行脚本
