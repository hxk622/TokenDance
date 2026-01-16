# Skill Discovery Architecture

## Overview

The TokenDance skill system uses a **hierarchical, multi-level directory structure** that supports:
1. Built-in skills (`builtin/`)
2. Scientific computing skills (`scientific/` with categorization)
3. Recursive SKILL.md discovery at any directory level
4. Extensibility for 100+ future skills

---

## Directory Structure

### Standard Layout

```
backend/app/skills/
├── __init__.py
├── registry.py                 # SkillRegistry - discovers & indexes skills
├── loader.py                   # SkillLoader - loads L1, L2, L3 content
├── matcher.py                  # SkillMatcher - intent matching
├── types.py                    # Core data types
├── embedding.py                # Embedding service
├── template_registry.py         # Template management
├── presets/
│   └── scenes.yaml             # Scene presets config
│
├── builtin/                    # Built-in skills (Manus + Vibe features)
│   ├── deep_research/
│   │   ├── SKILL.md           # L1 metadata + L2 instructions
│   │   └── resources/          # L3 assets
│   │       ├── financial_research_template.md
│   │       ├── sentiment_analysis_template.md
│   │       ├── query_generator.py
│   │       └── ...
│   ├── ppt/
│   │   ├── SKILL.md
│   │   └── resources/
│   │       └── ...
│   └── image_generation/
│       ├── SKILL.md
│       └── resources/
│
└── scientific/                 # Scientific computing skills (100+ planned)
    ├── visualization/          # Category: Data visualization
    │   ├── matplotlib/
    │   │   ├── SKILL.md       # Level 1: Matplotlib skill
    │   │   └── resources/
    │   ├── plotly/
    │   │   ├── SKILL.md
    │   │   └── resources/
    │   ├── seaborn/
    │   │   ├── SKILL.md
    │   │   └── resources/
    │   └── networkx/
    │       ├── SKILL.md
    │       └── resources/
    │
    ├── statistics/             # Category: Statistical analysis
    │   ├── scipy/
    │   │   ├── SKILL.md
    │   │   └── resources/
    │   └── statsmodels/
    │       ├── SKILL.md
    │       └── resources/
    │
    ├── ml/                     # Category: Machine learning
    │   ├── sklearn/
    │   │   ├── SKILL.md
    │   │   └── resources/
    │   └── pytorch/
    │       ├── SKILL.md
    │       └── resources/
    │
    └── bioinformatics/         # Category: Biological analysis
        ├── biopython/
        │   ├── SKILL.md
        │   └── resources/
        └── ...
```

---

## Answer to Question 1: Standardization of `builtin` vs `scientific`

### Current State (Problem)
```
❌ Inconsistent:
backend/app/skills/builtin/deep_research/SKILL.md      (uses builtin/)
backend/app/skills/scientific/visualization/matplotlib/ (flat, no builtin/)
```

### Recommended Solution: **Two-Directory Categorization**

**Philosophy**: Separate by **purpose/maintainability**, not by implementation location.

```
builtin/                    # Manus + Vibe core features
├── deep_research/          - AI-powered multi-source research
├── ppt_generation/         - PPT/演示文稿生成
├── image_generation/       - Image synthesis
└── code_execution/         - Code sandbox execution (future)

scientific/                 # Domain knowledge + scientific computing
├── visualization/          - Data visualization libraries
├── statistics/             - Statistical analysis
├── ml/                     - Machine learning frameworks
├── bioinformatics/         - Biological analysis
└── domains/                - Domain-specific (finance, chemistry, etc.)
```

### Rationale

| Aspect | builtin/ | scientific/ |
|--------|----------|------------|
| **Purpose** | Core Agent capabilities | Domain expertise |
| **Maintainer** | TokenDance team | Domain experts / community |
| **Priority** | High (always loaded) | Medium (lazy-loaded per request) |
| **Update Frequency** | Less frequent | Frequent (new libraries, updates) |
| **Discovery Scope** | One-level (no recursion needed) | Multi-level (categorized by domain) |

### Migration Path

1. **Keep current structure** - Existing `builtin/` and `scientific/` both work
2. **Add Meta Rule** - Document in WARP.md:
   - `builtin/` = Manus + Vibe core features (3-5 skills)
   - `scientific/` = Scientific computing (100+ planned)
3. **Future**: Consider moving `deep_research` to a new `core/` if it becomes a framework skill

---

## Answer to Question 2: SKILL.md Discovery Mechanism

### Design Decision: **Recursive Multi-Level Discovery**

The registry **automatically discovers SKILL.md at ANY directory level** under `skills/`.

### How It Works

**SkillRegistry._load_from_directory()** (registry.py:73-112):

```python
def _load_from_directory(self, skills_dir: Path, recursive: bool = True) -> int:
    """Recursively scan for SKILL.md at any level"""
    loaded_count = 0
    
    for item in skills_dir.iterdir():
        if not item.is_dir():
            continue
        
        # Skip special directories
        if item.name.startswith("_") or item.name.startswith("."):
            continue
        
        skill_file = item / "SKILL.md"
        
        if skill_file.exists():
            # ✅ Found SKILL.md - this is a skill
            metadata = self._parse_skill_file(skill_file)
            if metadata:
                self.skills[metadata.name] = metadata
                loaded_count += 1
        elif recursive:
            # 📁 No SKILL.md here - recurse into subdirectory
            sub_count = self._load_from_directory(item, recursive=False)
            loaded_count += sub_count
    
    return loaded_count
```

### Discovery Patterns Supported

**Pattern 1: Direct skill directory** ✅
```
builtin/deep_research/SKILL.md
         └── SKILL.md found → register as "deep_research"
```

**Pattern 2: Category + Skill** ✅
```
scientific/visualization/matplotlib/SKILL.md
                         └── SKILL.md found → register as "matplotlib"
```

**Pattern 3: Deep nesting** ✅ (if needed)
```
scientific/visualization/advanced_plots/matplotlib/SKILL.md
                                        └── SKILL.md found → register as "matplotlib"
```

### Key Properties

1. **Flat Registration**: All discovered skills are registered with their `name` field (from SKILL.md metadata), regardless of directory depth
   ```python
   # skill_path = "backend/app/skills/scientific/visualization/matplotlib"
   # name = "matplotlib" (from SKILL.md YAML)
   self.skills["matplotlib"] = metadata  # Registration key is name, not path
   ```

2. **Smart Recursion**:
   - First level: tries to find `SKILL.md` 
   - If found: registers it, **stops recursing**
   - If not found: recurses into subdirectories

3. **Load Timing**:
   - **builtin/** loaded at L1 metadata parse time (fast)
   - **scientific/** loaded on-demand during skill matching

---

## SKILL.md File Format

### Standard Location & Structure

**Required**: Every skill must have exactly ONE `SKILL.md` file in its root directory.

```yaml
---
name: matplotlib                  # Unique identifier (lowercase, no spaces)
display_name: Matplotlib          # User-facing name
description: "Professional 2D plotting library for Python..."
version: "1.0.0"                  # Semantic versioning

author: "TokenDance Scientific"
tags: ["visualization", "plotting", "scientific"]

# L1 Metadata (always in System Prompt)
allowed_tools: ["code_execution", "file_write"]
max_iterations: 20
timeout: 120
enabled: true

# Matching & Priority
match_threshold: 0.75
priority: 5                       # Higher = more priority in skill selection

# Coordination
conflicts_with: []                # Skills that can't run together
requires: []                      # Dependent skills

---
## 完整使用指南

### 基础用法
...（L2 instructions content）
```

### Naming Rules

```
❌ Bad names:
- "Matplotlib Advanced Features" (spaces, too specific)
- "VISUALIZATION_LIB" (all caps)
- "matplotlib2024" (version in name)

✅ Good names:
- matplotlib
- seaborn
- networkx
- sklearn
- deep_research (for compound concepts)
```

---

## Extension Strategy for 100+ Skills

### Phase 1: Current (3-10 skills)
```
builtin/
  ├── deep_research/
  ├── ppt/
  └── image_generation/

scientific/
  └── visualization/
      ├── matplotlib/
      ├── plotly/
      ├── seaborn/
      └── networkx/
```

### Phase 2: Expansion (20-50 skills)
```
scientific/
  ├── visualization/          (5 skills)
  ├── statistics/             (5 skills)
  ├── ml/                     (8 skills)
  ├── nlp/                    (5 skills)
  ├── cv/                     (computer vision)
  └── timeseries/             (time-series analysis)
```

### Phase 3: Scale (50-100+ skills)
```
scientific/
  ├── visualization/
  ├── statistics/
  ├── ml/
  ├── nlp/
  ├── cv/
  ├── bioinformatics/
  ├── chemistry/
  ├── physics/
  ├── geospatial/
  ├── finance/
  ├── domains/                (vertical industries)
  │   ├── fintech/
  │   ├── healthcare/
  │   └── energy/
  └── frameworks/             (meta-skills that compose others)
```

### Extensibility Guarantees

1. **No registration code needed** - Just add directory with SKILL.md
2. **No rebuild required** - SkillRegistry auto-discovers on startup
3. **Category-agnostic** - Arbitrary nesting depth supported
4. **Conflict detection** - Via `conflicts_with` field in SKILL.md
5. **Dependency resolution** - Via `requires` field + topological sort

---

## API Reference

### SkillRegistry

```python
# Get single skill
skill = registry.get("matplotlib")
assert skill.name == "matplotlib"

# Get all skills
all_skills = registry.get_all()

# Get by tag
viz_skills = registry.get_by_tag("visualization")

# Generate system prompt
prompt_fragment = registry.generate_system_prompt_fragment()

# Check conflicts
conflicts = registry.check_conflicts(["matplotlib", "plotly"])

# Resolve dependencies
ordered = registry.resolve_dependencies(["skill_a", "skill_b"])
```

### SkillLoader

```python
# Load L2 instructions (cached)
l2_content = await loader.load_l2("matplotlib")

# Load L3 resource
resource = await loader.load_l3_resource("matplotlib", "examples/basic.md")

# Execute L3 script
output = await loader.execute_l3_script("matplotlib", "scripts/gen_plot.py", ["data.csv"])

# List all resources
resources = loader.list_resources("matplotlib")
```

---

## Best Practices

### For Adding New Skills

1. **Create directory structure**:
   ```bash
   mkdir -p backend/app/skills/scientific/[category]/[skill_name]
   mkdir -p backend/app/skills/scientific/[category]/[skill_name]/resources
   ```

2. **Write SKILL.md with all required fields**

3. **Add L3 resources** (optional but recommended):
   ```
   resources/
   ├── reference.md          # API reference
   ├── examples.md           # Usage examples
   ├── troubleshooting.md    # Common issues
   └── scripts/              # Executable scripts
   ```

4. **Test discovery**:
   ```python
   from backend.app.skills.registry import SkillRegistry
   registry = SkillRegistry()
   registry.load_all()
   assert "matplotlib" in registry.get_skill_ids()
   ```

### Naming Conventions

- **skill name**: `lowercase_with_underscores`
- **display_name**: `Title Case with Spaces`
- **tags**: lowercase, comma-separated
- **category dirs**: `lowercase_with_underscores`

### Performance Considerations

- **L1 metadata**: ~100 tokens per skill → cached in memory
- **L2 instructions**: ~5-20KB per skill → cached with TTL
- **L3 resources**: ~1MB+ per skill → loaded on-demand only

---

## Summary

| Question | Answer |
|----------|--------|
| **Q1: builtin vs scientific?** | Keep both. builtin = core Agent features. scientific = domain expertise. Document in WARP.md. |
| **Q2: SKILL.md location?** | Recursive discovery at ANY level. No fixed depth requirement. Supports flat to deeply nested structures. |
| **Scalability** | Supports 100+ skills with automatic discovery. No code changes needed. |
| **Extensibility** | Pure filesystem-based. Add directory + SKILL.md → auto-discovered. |
