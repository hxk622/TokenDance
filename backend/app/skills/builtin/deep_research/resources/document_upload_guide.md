# Deep Research - 文档上传使用指南

## 概述

Deep Research Skill 现已支持文档上传功能，用户可以直接上传 PDF/Excel/Word 等文件，Agent 会自动转换为 Markdown 并提取关键信息，极大提升研究效率。

## 支持的文件格式

### 办公文档
- **PDF** (`.pdf`) - 研报、学术论文、白皮书
- **Word** (`.docx`, `.doc`) - 报告、文档、素材
- **Excel** (`.xlsx`, `.xls`) - 财报、数据表、统计数据
- **PowerPoint** (`.pptx`) - 演示文稿、行业报告

### 结构化数据
- **CSV** (`.csv`) - 数据表格
- **JSON** (`.json`) - 结构化数据
- **XML** (`.xml`) - 配置文件、数据交换

### 网页与文本
- **HTML** (`.html`, `.htm`) - 网页保存
- **Markdown** (`.md`) - 已整理的文档
- **纯文本** (`.txt`) - 文本资料

## 使用场景

### 场景 1: 金融投研 - 上传财报分析

**用户操作**:
```
用户: 帮我分析这份财报 [上传: 2024Q3_财报.xlsx]

Agent 自动处理:
1. 检测到 Excel 文件
2. 使用 MarkItDown 转换为表格 Markdown
3. 提取关键财务指标（营收、净利润、毛利率等）
4. 生成结构化分析报告
```

**输出示例**:
```markdown
# XX公司 2024Q3 财报分析

## 关键数据摘要
| 指标 | 数值 | 同比 |
|------|------|------|
| 营业收入 | 150.2亿 | +25.3% |
| 净利润 | 32.5亿 | +18.7% |
| 毛利率 | 45.2% | +2.1pp |

## 详细分析
[基于转换后的 Markdown 数据自动生成...]
```

### 场景 2: 市场调研 - 上传行业报告

**用户操作**:
```
用户: 根据这份报告总结 AI Agent 市场趋势 [上传: AI_Agent_Report_2024.pdf]

Agent 自动处理:
1. 使用 pdfminer 提取 PDF 文本
2. 转换为结构化 Markdown
3. 保留标题层级和表格
4. 提取关键数据点和结论
5. 生成趋势摘要
```

### 场景 3: 竞品分析 - 上传多份文档

**用户操作**:
```
用户: 对比分析这三家公司的产品策略
[上传: CompanyA_WhitePaper.pdf]
[上传: CompanyB_ProductDeck.pptx]
[上传: CompanyC_Analysis.docx]

Agent 自动处理:
1. 批量转换所有文档为 Markdown
2. 统一格式便于对比
3. 提取各公司的产品特点
4. 生成对比分析表格
```

## 技术细节

### 自动触发条件

Deep Research 会在以下情况自动调用 `file_converter` 工具：

1. 用户消息中包含文件附件
2. 用户明确提及"上传"、"这份文档"、"这个文件"
3. 用户提供文件路径（如 `/workspace/documents/report.pdf`）

### 转换流程

```python
# 内部流程（用户无需关心）
from document_preprocessor import DocumentPreprocessor

preprocessor = DocumentPreprocessor(llm_client=claude_client)

# 1. 转换文档
doc = preprocessor.convert_document("/path/to/report.pdf")

# 2. 整理为研究上下文
context = preprocessor.prepare_for_research([doc], max_total_chars=50000)

# 3. 注入到 Agent Context
agent_context.add_document_context(context)
```

### Context 管理策略

为避免 Context 爆炸，DocumentPreprocessor 采用以下策略：

1. **智能截断**: 单文件超过 50,000 字符时自动截断
2. **优先级排序**: 多文件时按相关性排序，优先加载
3. **摘要存储**: 长文本先摘要（500-1000 字），原文存文件系统
4. **分批加载**: 需要时再加载完整内容

### 财报专用提取器

对于 Excel 财报，提供自动数据提取：

```python
# 自动提取关键财务指标
financial_data = preprocessor.extract_financial_data(doc)

# 返回结构化数据
{
  "metrics_found": ["营业收入", "净利润", "毛利率"],
  "details": {
    "营业收入": "在文档中发现「营收」相关数据",
    "净利润": "在文档中发现「净利润」相关数据"
  }
}
```

## Best Practices

### 1. 文件命名规范

使用描述性文件名，便于 Agent 识别：
- ✅ `2024Q3_阿里巴巴_财报.xlsx`
- ✅ `AI_Agent_市场分析_Gartner_2024.pdf`
- ❌ `文件1.pdf`
- ❌ `下载.xlsx`

### 2. 文件大小控制

- 单个 PDF 建议 < 10MB
- Excel 表格行数 < 10,000
- Word 文档页数 < 50 页
- 超大文件建议先分割或摘要

### 3. 多文件上传顺序

按重要性排序上传：
1. 核心文档（主要分析对象）
2. 参考资料（补充信息）
3. 背景资料（可选）

### 4. 结合 Web Search

文档提供基础数据，Web 搜索补充最新信息：

```
用户: 分析这份财报 [上传: Q3财报.xlsx]，
     并搜索最新的行业动态和竞品信息

Agent 工作流:
1. 转换财报 → 提取数据
2. Web 搜索 → 获取行业动态
3. 交叉验证 → 生成综合分析
```

## 限制与注意事项

### 当前限制

1. **PDF OCR**: 扫描版 PDF 需预先 OCR 处理（未来支持 Azure Document Intelligence）
2. **图片提取**: 图片描述需配置 LLM client（默认未开启）
3. **格式保真**: 复杂格式可能丢失（如 Word 样式、Excel 公式）
4. **语言支持**: 中英文最佳，其他语言可能有乱码

### 隐私与安全

- ✅ 所有文档本地处理，不上传云端
- ✅ 转换后的 Markdown 存储在 workspace
- ✅ 用户可随时删除上传文件
- ⚠️ 敏感文档请先脱敏处理

## 示例代码

### 直接使用 DocumentPreprocessor

```python
from app.skills.builtin.deep_research.resources.document_preprocessor import (
    DocumentPreprocessor,
    ConvertedDocument
)

# 初始化
preprocessor = DocumentPreprocessor()

# 转换单个文档
doc = preprocessor.convert_document("/workspace/report.pdf")
print(f"Converted: {doc.source_name}")
print(f"Markdown length: {doc.char_count} chars")

# 批量转换
docs = preprocessor.convert_multiple([
    "/workspace/doc1.pdf",
    "/workspace/doc2.xlsx",
    "/workspace/doc3.docx"
])

# 整理为研究上下文
context = preprocessor.prepare_for_research(list(docs.values()))

# 保存到文件系统
with open("/workspace/research_context.md", "w") as f:
    f.write(context)
```

### 在 Skill 中集成

```python
# 在 deep_research skill 的执行逻辑中
if user_uploaded_files:
    preprocessor = DocumentPreprocessor(llm_client=self.llm_client)
    
    converted_docs = preprocessor.convert_multiple(user_uploaded_files)
    
    # 注入 Context
    context = preprocessor.prepare_for_research(list(converted_docs.values()))
    
    # 添加到 Agent 提示词
    agent_prompt += f"\n\n{context}\n\n请基于以上文档进行分析..."
```

## FAQ

### Q: 支持哪些语言的文档？
A: 中文和英文效果最佳。其他语言取决于 MarkItDown 的支持情况。

### Q: PDF 转换后格式乱了怎么办？
A: 1) 检查是否为扫描版（需 OCR）; 2) 尝试将 PDF 转为 Word 后再上传; 3) 使用 Azure Document Intelligence（高级功能）。

### Q: Excel 公式能否保留？
A: 当前仅提取数值结果，不保留公式。如需公式请在文档中明确标注。

### Q: 如何上传多个文件？
A: 一次上传多个文件，Agent 会自动批量处理。建议单次不超过 5 个文件。

### Q: 转换需要多久？
A: 单个文档通常 < 5 秒。大文件（>5MB）可能需要 10-30 秒。

---

**更新日期**: 2026-01-16  
**版本**: v1.0.0  
**相关模块**: `document_preprocessor.py`, `file_converter.py`
