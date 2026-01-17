# MarkItDown 集成

## 概述

MarkItDown 是微软开源的轻量级文档转换库，能将各种文件格式转换为 Markdown，便于 LLM 分析和处理。TokenDance 集成了 MarkItDown 以支持文档上传分析功能。

**GitHub**: https://github.com/microsoft/markitdown

## 支持的格式

| 分类 | 格式 | 说明 |
|------|------|------|
| 办公文档 | PDF, DOCX, PPTX, XLSX, XLS | 保留结构、表格、列表 |
| 结构化数据 | CSV, JSON, XML | 转换为 Markdown 表格 |
| 文本 | TXT, MD, HTML | 直接处理或提取内容 |
| 图片 | JPG, PNG, GIF, BMP, TIFF, WEBP | 需 Vision LLM 生成描述 |
| 音频 | WAV, MP3 | 需语音识别转录 |
| 压缩包 | ZIP | 递归处理内部文件 |

## 核心组件

### 1. FileConverterTool

**位置**: `backend/app/agent/tools/file_converter.py`

Agent 可调用的工具，将文件转换为 Markdown。

```python
from app.agent.tools.file_converter import FileConverterTool

# 初始化（无 Vision 能力）
tool = FileConverterTool()

# 初始化（带 Vision 能力，可处理图片）
tool = FileConverterTool(
    openrouter_api_key="your-api-key",
    vision_model="anthropic/claude-3-haiku"
)

# 转换文件
result = tool.execute(file_path="/workspace/report.pdf")
```

**输出格式**:
```markdown
---
Source: report.pdf
Format: .pdf
Size: 12345 bytes
Lines: 150
---

[转换后的 Markdown 内容...]
```

### 2. DocumentPreprocessor

**位置**: `backend/app/skills/builtin/deep_research/resources/document_preprocessor.py`

Deep Research Skill 专用的文档预处理器。

```python
from app.skills.builtin.deep_research.resources.document_preprocessor import (
    DocumentPreprocessor,
    ConvertedDocument
)

# 初始化
preprocessor = DocumentPreprocessor(llm_client=claude_client)

# 转换单个文档
doc = preprocessor.convert_document("/path/to/report.pdf")

# 批量转换
docs = preprocessor.convert_multiple([
    "/path/to/doc1.pdf",
    "/path/to/doc2.xlsx",
    "/path/to/doc3.docx"
])

# 整理为研究上下文（限制 50K 字符）
context = preprocessor.prepare_for_research(list(docs.values()))

# 财务数据提取
financial_data = preprocessor.extract_financial_data(doc)
```

## 使用场景

### 场景 1: 金融投研

用户上传财报 Excel → 自动提取关键指标 → 生成分析报告

```
用户: 帮我分析这份财报 [上传: 2024Q3_财报.xlsx]

Agent 自动:
1. 检测到 Excel 文件
2. 调用 file_converter 转换
3. 提取营收、净利润、毛利率等指标
4. 生成结构化分析报告
```

### 场景 2: 市场调研

用户上传行业报告 PDF → 提取关键数据 → 结合 Web 搜索补充

```
用户: 根据这份报告总结 AI Agent 市场趋势 [上传: AI_Report_2024.pdf]

Agent 自动:
1. 转换 PDF 为 Markdown
2. 提取市场规模、增长率、主要玩家
3. Web 搜索补充最新动态
4. 生成综合趋势报告
```

### 场景 3: 竞品分析

批量上传多份文档 → 统一格式 → 对比分析

```
用户: 对比这三家公司的产品策略
[上传: CompanyA.pdf, CompanyB.pptx, CompanyC.docx]

Agent 自动:
1. 批量转换所有文档
2. 提取各公司产品特点
3. 生成对比分析表格
```

## Vision 能力配置

### OpenRouter 集成

FileConverterTool 支持通过 OpenRouter 调用视觉模型处理图片：

```python
# 环境变量配置
export OPENROUTER_API_KEY="your-api-key"
export OPENROUTER_SITE_URL="https://tokendance.app"
export OPENROUTER_APP_NAME="TokenDance"

# 代码配置
tool = FileConverterTool(
    openrouter_api_key="your-api-key",
    vision_model="anthropic/claude-3-5-sonnet",  # 推荐用于图表分析
    vision_task_type="chart"  # 可选: ocr, chart, diagram, general
)
```

### 模型选择策略

| 任务类型 | 推荐模型 | 说明 |
|----------|----------|------|
| OCR 文字提取 | claude-3-haiku | 快速便宜 |
| 图表分析 | claude-3-5-sonnet | 平衡准确率和成本 |
| 科学示意图 | claude-3-5-sonnet | 需要理解复杂结构 |
| 通用场景 | gemini-pro-vision | 极致性价比 |

## Context 管理策略

为避免 Context 爆炸，DocumentPreprocessor 采用以下策略：

1. **智能截断**: 单文件超过 50,000 字符时自动截断
2. **优先级排序**: 多文件时按大小排序，优先加载
3. **摘要存储**: 长文本先摘要（500-1000 字），原文存文件系统
4. **分批加载**: 需要时再加载完整内容

## Deep Research Skill 集成

SKILL.md 已添加 `file_converter` 到 allowed_tools，工作流新增 Phase 0:

```markdown
### Phase 0: 文档预处理（如有上传）
1. 检测附件类型（PDF/Excel/Word/CSV 等）
2. 使用 `file_converter` 工具转换为 Markdown
3. 提取关键信息并注入 Context
4. 对于财报等结构化数据，自动识别关键指标
```

## 测试

单元测试位于 `backend/tests/test_file_converter_tool.py`，覆盖：

- 工具元数据验证
- 各格式转换（TXT, JSON, CSV）
- 文件验证（不存在、不支持格式）
- 延迟初始化
- 错误处理
- 特殊字符处理

运行测试：
```bash
cd backend && uv run pytest tests/test_file_converter_tool.py -v
```

## 限制与注意事项

### 当前限制

1. **扫描版 PDF**: 需预先 OCR 处理，纯图片无法提取文字
2. **图片描述**: 需配置 LLM client（OpenRouter/Anthropic）
3. **格式保真**: 复杂样式可能丢失（Word 样式、Excel 公式）
4. **语言支持**: 中英文最佳，其他语言可能有乱码
5. **文件大小**: 建议 PDF < 10MB，Excel < 10,000 行

### 隐私与安全

- ✅ 所有文档本地处理，不上传云端
- ✅ 转换后的 Markdown 存储在 workspace
- ⚠️ 敏感文档请先脱敏处理

## 相关文档

- [document_upload_guide.md](../../backend/app/skills/builtin/deep_research/resources/document_upload_guide.md) - 完整使用指南
- [document_preprocessor.py](../../backend/app/skills/builtin/deep_research/resources/document_preprocessor.py) - 预处理器实现
- [file_converter.py](../../backend/app/agent/tools/file_converter.py) - FileConverterTool 实现

## 更新日志

### v1.0.0 (2026-01-17)
- 初始集成 MarkItDown
- 创建 FileConverterTool
- 创建 DocumentPreprocessor
- 集成到 Deep Research Skill
- 14 个单元测试全部通过
