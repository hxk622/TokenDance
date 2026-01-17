# TokenDance Skill系统设计

> Version: 1.1.0 | MVP阶段
> Last Updated: 2026-01-17

## 1. 设计目标

Skill系统是TokenDance的核心架构创新，旨在解决传统Agent系统的以下问题：

| 问题 | 传统方案 | Skill方案 | 优势 |
|-----|---------|----------|------|
| **Context膨胀** | 所有指令塞入prompt | 三级懒加载 | Token节省90%+ |
| **能力扩展难** | 修改核心代码 | 插件化 | 零代码新增能力 |
| **指令冗余** | 重复描述流程 | 封装复用 | 提升一致性 |
| **注意力分散** | 大量工具暴露 | 工具子集 | 提升决策质量 |

## 2. 三级懒加载机制

### 2.1 架构图

```
Agent启动
    │
    ▼
┌──────────────────────────────────────────────────────┐
│   Level 1: 元数据（始终加载，约100 tokens/skill）    │
│   ┌────────────────────────────────────────────┐     │
│   │ skills/                                    │     │
│   │   ├─ deep_research/                        │     │
│   │   │   └─ name: "深度研究"                  │     │
│   │   │      description: "多源搜索、信息聚合" │     │
│   │   └─ ppt/                                  │     │
│   │       └─ name: "PPT生成"                   │     │
│   │          description: "智能演示文稿生成"   │     │
│   └────────────────────────────────────────────┘     │
│   ↓ 注入System Prompt                               │
└──────────────────────────────────────────────────────┘
    │
    ▼ 用户消息到达
┌──────────────────────────────────────────────────────┐
│   Skill Matcher: 匹配最相关的Skill                   │
│   Input: "帮我调研AI Agent市场"                     │
│   Output: deep_research (匹配度: 0.92)              │
└──────────────────────────────────────────────────────┘
    │
    ▼ 匹配成功
┌──────────────────────────────────────────────────────┐
│   Level 2: 完整指令（匹配时加载，<5000 tokens）      │
│   ┌────────────────────────────────────────────┐     │
│   │ SKILL.md正文内容：                        │     │
│   │ - 工作流程                                │     │
│   │ - 最佳实践                                │     │
│   │ - 工具使用指南                            │     │
│   │ - 输出格式                                │     │
│   └────────────────────────────────────────────┘     │
│   ↓ 动态注入Context                                 │
└──────────────────────────────────────────────────────┘
    │
    ▼ Agent执行中
┌──────────────────────────────────────────────────────┐
│   Level 3: 资源（按需加载，无大小限制）              │
│   ┌────────────────────────────────────────────┐     │
│   │ resources/                                │     │
│   │   ├─ search.py        # 搜索脚本          │     │
│   │   │   └─ 沙箱执行，返回输出               │     │
│   │   ├─ summarize.md     # 子技能            │     │
│   │   │   └─ 按需读取                        │     │
│   │   └─ templates/       # 参考资源          │     │
│   │       └─ 按需读取                        │     │
│   └────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────┘
```

### 2.2 Level 1: 元数据

#### 作用
- 始终存在于System Prompt中
- 用于意图识别和Skill匹配
- 极简设计，控制在100 tokens以内

#### SKILL.md YAML头部格式

```yaml
---
name: deep_research
display_name: 深度研究
description: 深度研究能力，支持多源搜索、信息聚合、引用回溯。适用于市场调研、竞品分析、学术研究等场景。
version: 1.0.0
author: system
tags: [research, search, analysis]
allowed_tools: [web_search, read_url, create_doc]
max_iterations: 20
timeout: 300
enabled: true
---
```

#### 字段说明

| 字段 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| name | string | ✓ | Skill唯一标识（小写+下划线） |
| display_name | string | ✓ | 显示名称（中文） |
| description | string | ✓ | 详细描述，用于匹配 |
| version | string | ✓ | 版本号（semver） |
| author | string | ○ | 作者 |
| tags | array | ○ | 标签，辅助搜索 |
| allowed_tools | array | ✓ | 允许使用的工具列表（Action Space Pruning） |
| max_iterations | int | ○ | 最大迭代次数（默认30） |
| timeout | int | ○ | 超时时间秒数（默认300） |
| enabled | boolean | ○ | 是否启用（默认true） |

### 2.3 Level 2: 完整指令

#### 作用
- 当Skill被激活时动态注入Context
- 包含详细的工作流程、最佳实践、指导
- 控制在5000 tokens以内

#### SKILL.md正文结构

```markdown
---
[Level 1 YAML头部]
---

## 能力概述
简述该Skill的核心能力和适用场景。

## 工作流程
详细描述Skill的执行步骤：
1. 步骤1：做什么
2. 步骤2：做什么
3. ...

## 工具使用
### web_search
- 用途：...
- 参数：...
- 示例：...

### read_url
- 用途：...

## 最佳实践
- 实践1：...
- 实践2：...

## 输出格式
描述最终输出的格式和结构。

## 注意事项
- 注意1：...
- 注意2：...
```

#### 示例：Deep Research Skill

```markdown
---
name: deep_research
display_name: 深度研究
description: 深度研究能力，支持多源搜索、信息聚合、引用回溯
version: 1.0.0
author: system
tags: [research, search, analysis]
allowed_tools: [web_search, read_url, browser_open, browser_click, browser_screenshot, create_doc]
max_iterations: 20
timeout: 300
---

## 能力概述
深度研究能力让你能够系统性地调研某个主题，通过多源搜索、信息聚合、交叉验证，生成结构化的研究报告。每个结论都标注来源引用，确保可追溯性。

## 工作流程
1. **需求澄清**：与用户确认研究主题、深度、范围
2. **查询拆解**：将主题拆解为多个搜索子查询
3. **并行搜索**：对每个子查询执行web_search（至少3个来源）
4. **内容提取**：对搜索结果调用read_url获取完整内容
5. **信息聚合**：
   - 去重相同信息
   - 识别共识与分歧
   - 评估来源可信度
6. **结构化输出**：生成报告，标注引用
7. **用户确认**：询问是否需要深入某个方向

## 工具使用
### web_search
- **用途**：搜索网页信息
- **参数**：
  - query: 搜索查询（精确、具体）
  - num_results: 结果数量（建议5-10）
- **示例**：
  ```python
  web_search(query="AI Agent market size 2024", num_results=5)
  ```
- **注意**：
  - 查询要具体，避免泛泛而谈
  - 多个维度分别搜索，而非一次搜全部

### read_url
- **用途**：提取网页完整内容
- **参数**：
  - url: 目标URL
  - mode: "text" | "markdown" | "html"
- **注意**：
  - 只读取搜索结果中的高相关性页面
  - 优先选择官方网站、权威媒体

### create_doc
- **用途**：创建研究报告
- **参数**：
  - title: 报告标题
  - content: Markdown格式内容
  - format: "markdown" | "pdf"

## 最佳实践
- **Read-then-Summarize**：
  - 对于长文本（>2000字），先用小模型摘要
  - 摘要放入context，原文存储到文件系统
  
- **引用回溯**：
  - 每个关键结论必须标注[1][2]引用
  - 引用格式：`[编号] 标题 - 来源域名`
  
- **来源可信度评分**：
  - 官方网站/政府机构：★★★★★
  - 知名媒体/研究机构：★★★★
  - 专业博客：★★★
  - 社交媒体/论坛：★★
  - 未知来源：★
  
- **交叉验证**：
  - 关键数据至少2个来源确认
  - 存在分歧时明确标注

## 输出格式
```markdown
# [研究主题]

## 摘要
3-5句话概括核心发现

## 目录
- 1. ...
- 2. ...

## 正文
### 1. ...
具体内容...[1][2]

### 2. ...

## 参考来源
[1] 标题 - example.com/... (★★★★)
[2] 标题 - example.org/... (★★★★★)
```

## 注意事项
- 不要一次性搜索太多query，容易context爆炸
- 优先使用英文搜索，信息更丰富
- 对于时效性强的内容，注明搜索日期
```

### 2.4 Level 3: 资源

#### 作用
- Agent执行过程中按需访问
- 不占用context空间（脚本代码不入context）
- 无大小限制

#### 资源类型

##### 1. 子技能文档 (Sub-SKILL.md)

**使用场景**：复杂Skill的独立子模块

```markdown
# resources/summarize.md

## 子技能：内容摘要
当搜索结果内容超过2000字时，使用此流程进行摘要。

### 步骤
1. 识别文章结构（标题、段落）
2. 提取关键句
3. 生成200字以内摘要
4. 保留数据和引用

### 输出格式
- 摘要：...
- 关键数据：...
- 原文链接：...
```

##### 2. 可执行脚本 (Scripts)

**使用场景**：复杂逻辑、数据处理

```python
# resources/search.py
"""
搜索策略脚本
输入：主题
输出：多个搜索query
"""
def generate_queries(topic: str, depth: str) -> list[str]:
    """根据主题和深度生成搜索query"""
    if depth == "shallow":
        return [topic]
    elif depth == "deep":
        # 生成多角度query
        return [
            f"{topic} market size",
            f"{topic} trends 2024",
            f"{topic} key players",
            f"{topic} challenges"
        ]

if __name__ == "__main__":
    import sys
    topic = sys.argv[1]
    depth = sys.argv[2]
    queries = generate_queries(topic, depth)
    for q in queries:
        print(q)
```

**执行方式**：
- Agent调用：`code_execute(script_path="resources/search.py", args=["AI Agent", "deep"])`
- 沙箱执行，只返回stdout
- 脚本代码不进入context

##### 3. 参考文档 (Reference)

**使用场景**：模板、示例、知识库

```markdown
# resources/report_template.md

# 研究报告模板

## 市场概述
- 市场规模：...
- 增长率：...
- 主要驱动因素：...

## 主要玩家
| 公司 | 产品 | 市场份额 | 特点 |
|------|------|---------|------|

## 技术趋势
1. 趋势1：...
2. 趋势2：...

## 结论与展望
...
```

##### 4. 资产文件 (Assets)

**使用场景**：图片、模板文件等

```
resources/
  templates/
    business_template.pptx
    creative_template.pptx
  images/
    logo.png
```

## 3. Skill系统组件

### 3.1 架构图

```
┌──────────────────────────────────────────────────────┐
│                  Skill System                         │
│                                                       │
│  ┌───────────────────────────────────────────────┐   │
│  │            SkillRegistry                      │   │
│  │  启动时扫描skills/目录                        │   │
│  │  构建L1元数据索引（内存）                     │   │
│  │  生成System Prompt片段                        │   │
│  └───────────────────────────────────────────────┘   │
│                        │                             │
│                        ▼                             │
│  ┌───────────────────────────────────────────────┐   │
│  │            SkillMatcher                       │   │
│  │  - 关键词匹配（快速）                        │   │
│  │  - Embedding匹配（精确）                     │   │
│  │  - LLM Rerank（可选）                        │   │
│  └───────────────────────────────────────────────┘   │
│                        │                             │
│                        ▼                             │
│  ┌───────────────────────────────────────────────┐   │
│  │            SkillLoader                        │   │
│  │  - 加载L2指令                                │   │
│  │  - 按需读取L3资源                            │   │
│  │  - 注入Context                               │   │
│  └───────────────────────────────────────────────┘   │
│                                                       │
└──────────────────────────────────────────────────────┘
```

### 3.2 SkillRegistry

#### 职责
- 启动时扫描`skills/`目录
- 解析所有SKILL.md的YAML头
- 构建L1元数据索引
- 生成System Prompt中的Skill列表

#### 实现

```python
# app/skills/registry.py

from pathlib import Path
from typing import Dict, List
import yaml
from dataclasses import dataclass

@dataclass
class SkillMetadata:
    """Level 1 元数据"""
    id: str
    name: str
    display_name: str
    description: str
    version: str
    tags: List[str]
    allowed_tools: List[str]
    enabled: bool

class SkillRegistry:
    """Skill注册表"""
    
    def __init__(self, skills_dir: Path):
        self.skills_dir = skills_dir
        self.skills: Dict[str, SkillMetadata] = {}
        self._load_all()
    
    def _load_all(self):
        """扫描并加载所有Skill元数据"""
        for skill_dir in self.skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            
            skill_file = skill_dir / "SKILL.md"
            if not skill_file.exists():
                continue
            
            metadata = self._parse_metadata(skill_file)
            if metadata and metadata.enabled:
                self.skills[metadata.id] = metadata
    
    def _parse_metadata(self, skill_file: Path) -> SkillMetadata:
        """解析SKILL.md的YAML头"""
        with open(skill_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取YAML frontmatter
        if not content.startswith('---'):
            return None
        
        parts = content.split('---', 2)
        if len(parts) < 3:
            return None
        
        yaml_content = parts[1]
        data = yaml.safe_load(yaml_content)
        
        return SkillMetadata(
            id=data['name'],
            name=data['name'],
            display_name=data.get('display_name', data['name']),
            description=data['description'],
            version=data['version'],
            tags=data.get('tags', []),
            allowed_tools=data.get('allowed_tools', []),
            enabled=data.get('enabled', True)
        )
    
    def get(self, skill_id: str) -> SkillMetadata:
        """获取Skill元数据"""
        return self.skills.get(skill_id)
    
    def get_all(self) -> List[SkillMetadata]:
        """获取所有启用的Skill元数据"""
        return list(self.skills.values())
    
    def generate_system_prompt_fragment(self) -> str:
        """生成System Prompt中的Skill列表片段"""
        lines = ["[Available Skills]"]
        for skill in self.skills.values():
            lines.append(f"- {skill.display_name}: {skill.description}")
        return "\n".join(lines)
```

### 3.3 SkillMatcher

#### 职责
- 根据用户消息匹配最相关的Skill
- 支持多种匹配策略

#### 匹配策略

| 策略 | 速度 | 精度 | 成本 | 适用场景 |
|-----|-----|------|------|---------|
| 关键词匹配 | ★★★★★ | ★★ | 无 | 快速初筛 |
| Embedding匹配 | ★★★★ | ★★★★ | 低 | 语义理解 |
| LLM Rerank | ★★ | ★★★★★ | 高 | 精确判断 |

#### 实现

```python
# app/skills/matcher.py

from typing import List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class SkillMatch:
    skill_id: str
    score: float
    reason: str

class SkillMatcher:
    """Skill匹配器"""
    
    def __init__(self, registry: SkillRegistry, embedding_model, llm):
        self.registry = registry
        self.embedding_model = embedding_model
        self.llm = llm
        
        # 预计算所有Skill的embedding
        self._skill_embeddings = {}
        self._precompute_embeddings()
    
    def _precompute_embeddings(self):
        """预计算Skill描述的embedding"""
        for skill in self.registry.get_all():
            text = f"{skill.display_name}: {skill.description}"
            self._skill_embeddings[skill.id] = self.embedding_model.encode(text)
    
    async def match(self, user_message: str, top_k: int = 3) -> Optional[SkillMatch]:
        """匹配Skill"""
        # 策略1: 关键词匹配（快速初筛）
        keyword_candidates = self._keyword_match(user_message, top_k=5)
        
        if not keyword_candidates:
            return None
        
        # 策略2: Embedding匹配（语义理解）
        embedding_candidates = self._embedding_match(user_message, keyword_candidates, top_k=top_k)
        
        # 策略3: LLM Rerank（可选，精确判断）
        # if len(embedding_candidates) > 1:
        #     final = await self._llm_rerank(user_message, embedding_candidates)
        # else:
        #     final = embedding_candidates[0]
        
        final = embedding_candidates[0] if embedding_candidates else None
        
        # 阈值过滤
        if final and final.score > 0.7:
            return final
        return None
    
    def _keyword_match(self, message: str, top_k: int) -> List[str]:
        """关键词匹配"""
        candidates = []
        message_lower = message.lower()
        
        for skill in self.registry.get_all():
            # 检查标签匹配
            for tag in skill.tags:
                if tag.lower() in message_lower:
                    candidates.append(skill.id)
                    break
            
            # 检查显示名匹配
            if skill.display_name in message:
                if skill.id not in candidates:
                    candidates.append(skill.id)
        
        return candidates[:top_k]
    
    def _embedding_match(self, message: str, candidates: List[str], top_k: int) -> List[SkillMatch]:
        """Embedding匹配"""
        message_emb = self.embedding_model.encode(message)
        
        scores = []
        for skill_id in candidates:
            skill_emb = self._skill_embeddings[skill_id]
            similarity = self._cosine_similarity(message_emb, skill_emb)
            scores.append((skill_id, similarity))
        
        # 排序
        scores.sort(key=lambda x: x[1], reverse=True)
        
        return [
            SkillMatch(skill_id=sid, score=score, reason="Semantic match")
            for sid, score in scores[:top_k]
        ]
    
    async def _llm_rerank(self, message: str, candidates: List[SkillMatch]) -> SkillMatch:
        """LLM重排序"""
        skill_list = "\n".join([
            f"{i+1}. {self.registry.get(c.skill_id).display_name}: {self.registry.get(c.skill_id).description}"
            for i, c in enumerate(candidates)
        ])
        
        prompt = f"""
        User message: "{message}"
        
        Available skills:
        {skill_list}
        
        Which skill is most relevant? Respond with just the number (1-{len(candidates)}).
        """
        
        response = await self.llm.chat([{"role": "user", "content": prompt}])
        try:
            idx = int(response.content.strip()) - 1
            return candidates[idx]
        except:
            return candidates[0]
    
    def _cosine_similarity(self, a, b):
        """计算余弦相似度"""
        import numpy as np
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
```

### 3.4 SkillLoader

#### 职责
- 加载L2完整指令
- 按需读取L3资源
- 注入到Context

#### 实现

```python
# app/skills/loader.py

from pathlib import Path
from typing import Optional

class SkillLoader:
    """Skill加载器"""
    
    def __init__(self, skills_dir: Path):
        self.skills_dir = skills_dir
        self._l2_cache = {}  # L2指令缓存
    
    async def load_l2(self, skill_id: str) -> str:
        """加载L2完整指令"""
        if skill_id in self._l2_cache:
            return self._l2_cache[skill_id]
        
        skill_file = self.skills_dir / skill_id / "SKILL.md"
        if not skill_file.exists():
            raise FileNotFoundError(f"Skill file not found: {skill_file}")
        
        with open(skill_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取正文（去除YAML头）
        parts = content.split('---', 2)
        if len(parts) >= 3:
            l2_content = parts[2].strip()
        else:
            l2_content = content
        
        self._l2_cache[skill_id] = l2_content
        return l2_content
    
    async def load_l3_resource(self, skill_id: str, resource_path: str) -> str:
        """加载L3资源"""
        full_path = self.skills_dir / skill_id / "resources" / resource_path
        if not full_path.exists():
            raise FileNotFoundError(f"Resource not found: {full_path}")
        
        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def get_resource_path(self, skill_id: str, resource_name: str) -> Path:
        """获取资源文件路径"""
        return self.skills_dir / skill_id / "resources" / resource_name
```

## 4. MVP Skill列表

### 4.1 Deep Research Skill

**目标**：多源搜索、信息聚合、引用回溯

**文件结构**：
```
skills/deep_research/
  ├── SKILL.md
  └── resources/
      ├── search_strategy.py    # 查询生成策略
      ├── summarize.md          # 摘要子技能
      └── report_template.md    # 报告模板
```

### 4.2 PPT Skill

**目标**：智能PPT生成、模板应用、单页重生成

**文件结构**：
```
skills/ppt/
  ├── SKILL.md
  └── resources/
      ├── layout.py             # 布局算法
      ├── templates/
      │   ├── business.pptx
      │   ├── creative.pptx
      │   └── minimal.pptx
      └── examples/
          └── good_ppt.md       # 优秀案例
```

## 5. Skill开发指南

### 5.1 创建新Skill

```bash
# 1. 创建目录
mkdir -p skills/my_skill/resources

# 2. 创建SKILL.md
cat > skills/my_skill/SKILL.md << 'EOF'
---
name: my_skill
display_name: 我的技能
description: 这是一个示例技能
version: 1.0.0
author: yourname
tags: [example]
allowed_tools: [tool1, tool2]
max_iterations: 30
timeout: 300
---

## 能力概述
...

## 工作流程
...
EOF

# 3. 重启服务，自动热加载
```

### 5.2 Skill测试

```python
# tests/test_skill.py

async def test_skill_match():
    matcher = SkillMatcher(registry, embedding_model, llm)
    match = await matcher.match("帮我调研AI市场")
    assert match.skill_id == "deep_research"
    assert match.score > 0.7

async def test_skill_load():
    loader = SkillLoader(skills_dir)
    l2_content = await loader.load_l2("deep_research")
    assert "工作流程" in l2_content
```

### 5.3 Skill版本管理

- 遵循Semantic Versioning
- 大版本变更：API不兼容
- 小版本变更：功能增加
- 补丁版本：Bug修复

## 6. 附录

### A. Skill最佳实践

1. **保持L2指令简洁**：<5000 tokens
2. **工具子集化**：只暴露必要工具
3. **资源外置化**：复杂逻辑放L3脚本
4. **模板化输出**：统一格式，提升一致性
5. **可测试性**：每个Skill都有独立测试

### B. 相关文档

- [HLD文档](../architecture/HLD.md)
- [LLD文档](../architecture/LLD.md)
- [Memory设计](./Memory-Design.md)
- [Sandbox设计](./Sandbox-Design.md)

---

## 7. 实现状态与待完成工作 (2026-01-17)

### 7.1 当前 Skill 清单

#### 一级 builtin skill（6个）
| Skill ID | 显示名 | 状态 | 说明 |
|----------|--------|------|------|
| deep_research | 深度研究 | ✅ L1+L2 | 有 templates.yaml |
| ppt | PPT生成 | ✅ L1+L2 | 有 templates.yaml |
| image_generation | 图片生成 | ✅ L1+L2 | - |
| frontend-design | 前端设计 | ✅ L1+L2 | - |
| planning-with-files | 三文件规划法 | ✅ L1+L2 | - |
| ui-ux-pro-max | UI/UX Pro Max | ✅ L1+L2 | - |

#### Scientific skills（139个）
按分类：visualization (5)、database (13+)、data-science、biology、chemistry、physics、clinical 等

### 7.2 核心组件状态

| 组件 | 文件 | 状态 | 说明 |
|------|------|------|------|
| SkillRegistry | `registry.py` | ✅ 完成 | 启动时扫描加载所有 SKILL.md |
| SkillMatcher | `matcher.py` | ✅ 完成 | 关键词 + Embedding + LLM Rerank |
| SkillLoader | `loader.py` | ✅ 完成 | L2/L3 内容加载、缓存 |
| SkillExecutor | `executor.py` | ✅ 完成 | L3 脚本执行框架 |
| Embedding | `embedding.py` | ✅ 完成 | SentenceTransformer (all-MiniLM-L6-v2) |
| TemplateRegistry | `template_registry.py` | ✅ 完成 | 模板管理 |
| ExecutionRouter | `routing/router.py` | ⚠️ 有Bug | 见下方问题 |
| API 端点 | `api/v1/skills.py` | ✅ 完成 | Skill/模板/场景 API |
| Agent 集成 | `agent/engine.py` | ✅ 完成 | 完整的混合执行路由 |
| 测试 | `tests/test_skill_system.py` | ✅ 基础 | 覆盖 Registry/Matcher/Loader |

### 7.3 🚨 待完成工作（按优先级）

#### P0 - 阻塞自动化执行

**1. 所有 Skill 缺少 `execute.py`（L3 脚本）**
```
问题：145+ 个 Skill 都没有 resources/execute.py
影响：SkillExecutor.can_execute() 始终返回 False
      导致 Skill 只能注入 L2 指令，无法自动化执行任务
解决：为核心 Skill（deep_research, ppt 等）实现 execute.py
```

**2. ExecutionRouter 同步调用异步方法 Bug**
```python
# router.py:129 - 错误代码
skill_match = self.skill_matcher.match(user_message)  # match() 是 async!

# 修复方案：将 route() 改为 async，或创建同步匹配方法
```

#### P1 - 提升触发准确性

**3. 增加更多测试用例验证匹配准确性**
```
当前匹配策略：
- 关键词匹配：基于 tags 和 display_name（权重 0.3-0.4）
- Embedding 匹配：SentenceTransformer 语义相似度
- 阈值：默认 0.7，路由时用 0.85

建议：
- 创建 benchmark 测试集
- 评估不同阈值的 precision/recall
- 考虑添加 few-shot examples 提升匹配
```

**4. 为更多 Skill 添加 templates.yaml**
```
当前只有 deep_research 和 ppt 有模板
建议为 scientific skills 中的高频使用 Skill 添加模板
```

#### P2 - 增强功能

**5. 实现 Skill 热重载**
```
当前需重启服务才能加载新 Skill
可通过文件监听实现热重载
```

**6. Skill 执行监控和统计**
```
- 执行成功率
- 平均耗时
- Token 消耗
```

### 7.4 Skill 触发准确性分析

**匹配流程**：
```
用户消息 → 关键词初筛 → Embedding 语义匹配 → (可选) LLM Rerank → 阈值过滤
```

**当前阈值设置**：
- `SkillMatch.is_confident()`: 默认 0.7 或 Skill 自定义
- `ExecutionRouter.skill_confidence_threshold`: 0.85（更严格）

**评估**：
- 关键词匹配：快速但依赖 tags 质量
- Embedding 匹配：语义理解较好，但中英文混合场景可能不够准确
- LLM Rerank：默认关闭，开启后准确性最高但增加延迟和成本

**建议优化**：
1. 丰富 Skill 的 tags 和 description
2. 考虑使用多语言 Embedding 模型（如 multilingual-MiniLM）
3. 对高频 Skill 调优 match_threshold
