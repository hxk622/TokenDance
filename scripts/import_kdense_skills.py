#!/usr/bin/env python3
"""
K-Dense Scientific Skills 批量导入脚本

功能：
1. 从 K-Dense-AI/claude-scientific-skills 仓库导入所有科学技能
2. 转换 SKILL.md 格式为 TokenDance 格式
3. 按类别组织 skills
4. 生成导入报告

使用方法：
    python scripts/import_kdense_skills.py --source /path/to/kdense-repo --target backend/app/skills/scientific
"""

import argparse
import json
import re
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


# =============================================================================
# 分类定义
# =============================================================================

SKILL_CATEGORIES = {
    "bioinformatics": {
        "display_name": "生物信息学",
        "tags": ["bioinformatics", "genomics", "biology"],
        "priority": 10,
        "skills": [
            "biopython", "scanpy", "anndata", "pydeseq2", "gget", "pysam",
            "scikit-bio", "scvi-tools", "arboreto", "etetoolkit", "deeptools",
            "geniml", "cellxgene-census", "ensembl-database", "gene-database",
            "geo-database", "ena-database", "biorxiv-database", "uniprot-database",
            "string-database", "esm"
        ]
    },
    "chemistry": {
        "display_name": "化学与药物发现",
        "tags": ["chemistry", "drug-discovery", "molecular"],
        "priority": 10,
        "skills": [
            "rdkit", "deepchem", "datamol", "medchem", "molfeat", "matchms",
            "torchdrug", "pytdc", "diffdock", "chembl-database", "pubchem-database",
            "drugbank-database", "zinc-database", "brenda-database", "hmdb-database",
            "opentargets-database", "denario", "rowan"
        ]
    },
    "data-science": {
        "display_name": "数据科学与机器学习",
        "tags": ["data-science", "machine-learning", "statistics"],
        "priority": 8,
        "skills": [
            "scikit-learn", "statsmodels", "torch_geometric", "transformers",
            "shap", "pytorch-lightning", "stable-baselines3", "dask", "polars",
            "vaex", "umap-learn", "exploratory-data-analysis", "statistical-analysis",
            "pufferlib"
        ]
    },
    "visualization": {
        "display_name": "数据可视化",
        "tags": ["visualization", "plotting", "charts"],
        "priority": 7,
        "skills": [
            "matplotlib", "seaborn", "plotly", "scientific-visualization", "networkx"
        ]
    },
    "writing": {
        "display_name": "科学写作与交流",
        "tags": ["writing", "publication", "documentation"],
        "priority": 9,
        "skills": [
            "scientific-writing", "latex-posters", "pptx-posters", "citation-management",
            "literature-review", "scientific-slides", "peer-review", "scientific-schematics",
            "venue-templates", "document-skills", "paper-2-web", "markitdown"
        ]
    },
    "database": {
        "display_name": "数据库访问",
        "tags": ["database", "api", "data-access"],
        "priority": 6,
        "skills": [
            "clinicaltrials-database", "clinvar-database", "cosmic-database",
            "kegg-database", "reactome-database", "fda-database", "gwas-database",
            "pdb-database", "pubmed-database", "openalex-database", "clinpgx-database",
            "datacommons-client", "uspto-database"
        ]
    },
    "lab-automation": {
        "display_name": "实验室自动化",
        "tags": ["lab-automation", "integration", "workflow"],
        "priority": 5,
        "skills": [
            "pylabrobot", "opentrons-integration", "protocolsio-integration",
            "benchling-integration", "latchbio-integration", "labarchive-integration",
            "dnanexus-integration", "omero-integration", "lamindb"
        ]
    },
    "physics": {
        "display_name": "物理与材料科学",
        "tags": ["physics", "materials", "quantum"],
        "priority": 7,
        "skills": [
            "pymatgen", "qiskit", "pennylane", "cirq", "qutip", "astropy",
            "fluidsim", "sympy", "simpy", "matlab", "aeon", "zarr-python"
        ]
    },
    "clinical": {
        "display_name": "临床医学",
        "tags": ["clinical", "medical", "healthcare"],
        "priority": 9,
        "skills": [
            "clinical-reports", "clinical-decision-support", "pyhealth", "pydicom",
            "neurokit2", "neuropixels-analysis", "treatment-plans", "flowio",
            "histolab", "pathml", "iso-13485-certification"
        ]
    },
    "research-tools": {
        "display_name": "研究工具",
        "tags": ["research", "tools", "analysis"],
        "priority": 8,
        "skills": [
            "perplexity-search", "hypothesis-generation", "scientific-brainstorming",
            "scientific-critical-thinking", "research-lookup", "research-grants",
            "scholar-evaluation", "market-research-reports", "generate-image",
            "biomni", "hypogenic", "get-available-resources", "offer-k-dense-web",
            "geopandas", "pyopenms", "pymc", "pymoo", "gtars", "modal",
            "adaptyv", "cobrapy"
        ]
    }
}


def get_skill_category(skill_name: str) -> tuple[str, dict]:
    """获取 skill 的分类信息"""
    for cat_id, cat_info in SKILL_CATEGORIES.items():
        if skill_name in cat_info["skills"]:
            return cat_id, cat_info
    # 默认分类
    return "research-tools", SKILL_CATEGORIES["research-tools"]


def name_to_display_name(name: str) -> str:
    """将 skill name 转换为 display_name"""
    # 处理特殊情况
    special_names = {
        "rdkit": "RDKit",
        "esm": "ESM (Evolutionary Scale Modeling)",
        "shap": "SHAP",
        "pdb-database": "PDB Database",
        "ncbi": "NCBI",
        "gwas-database": "GWAS Database",
        "fda-database": "FDA Database",
        "umap-learn": "UMAP",
        "iso-13485-certification": "ISO 13485 Certification",
        "pptx-posters": "PPTX Posters",
        "latex-posters": "LaTeX Posters",
        "qiskit": "Qiskit",
        "qutip": "QuTiP",
        "pytorch-lightning": "PyTorch Lightning",
        "scikit-learn": "Scikit-learn",
        "scikit-bio": "Scikit-bio",
        "scikit-survival": "Scikit-survival",
        "torch_geometric": "PyTorch Geometric",
    }
    
    if name in special_names:
        return special_names[name]
    
    # 通用转换：将 - 替换为空格，首字母大写
    words = name.replace("-", " ").replace("_", " ").split()
    return " ".join(word.capitalize() for word in words)


def determine_allowed_tools(skill_name: str, description: str) -> list[str]:
    """根据 skill 特性确定允许的工具"""
    # 基础工具
    tools = ["code_execute"]
    
    # 需要网络访问的 skills
    network_keywords = ["database", "api", "search", "lookup", "fetch", "download", "web"]
    if any(kw in skill_name.lower() or kw in description.lower() for kw in network_keywords):
        tools.append("web_search")
        tools.append("read_url")
    
    # 需要文件创建的 skills
    file_keywords = ["report", "document", "write", "export", "poster", "slides", "visualization"]
    if any(kw in skill_name.lower() or kw in description.lower() for kw in file_keywords):
        tools.append("create_document")
    
    return tools


@dataclass
class SkillImportResult:
    """Skill 导入结果"""
    name: str
    category: str
    status: str  # success, error, skipped
    source_path: str
    target_path: str
    error: str = ""


@dataclass
class ImportReport:
    """导入报告"""
    total: int = 0
    success: int = 0
    error: int = 0
    skipped: int = 0
    results: list[SkillImportResult] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


def parse_kdense_skill(skill_path: Path) -> dict[str, Any]:
    """解析 K-Dense SKILL.md 文件"""
    skill_file = skill_path / "SKILL.md"
    if not skill_file.exists():
        raise FileNotFoundError(f"SKILL.md not found in {skill_path}")
    
    content = skill_file.read_text(encoding="utf-8")
    
    # 解析 YAML frontmatter
    if not content.startswith("---"):
        raise ValueError(f"No YAML frontmatter found in {skill_file}")
    
    parts = content.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"Invalid YAML frontmatter format in {skill_file}")
    
    yaml_content = parts[1].strip()
    body_content = parts[2].strip()
    
    # 简单解析 YAML（避免依赖 pyyaml）
    metadata = {}
    current_key = None
    for line in yaml_content.split("\n"):
        line = line.strip()
        if not line:
            continue
        if ":" in line and not line.startswith(" "):
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            if value:
                metadata[key] = value
            else:
                metadata[key] = {}
                current_key = key
        elif current_key and line.startswith(" "):
            # 处理嵌套的 metadata
            if ":" in line:
                k, v = line.strip().split(":", 1)
                if isinstance(metadata[current_key], dict):
                    metadata[current_key][k.strip()] = v.strip()
    
    return {
        "metadata": metadata,
        "body": body_content,
        "raw_yaml": yaml_content
    }


def convert_to_tokendance_format(
    skill_name: str,
    parsed_skill: dict[str, Any],
) -> str:
    """将 K-Dense 格式转换为 TokenDance 格式"""
    
    metadata = parsed_skill["metadata"]
    body = parsed_skill["body"]
    
    # 获取分类信息
    category_id, category_info = get_skill_category(skill_name)
    
    # 构建 TokenDance 格式的 YAML
    description = metadata.get("description", f"Scientific skill: {skill_name}")
    license_info = metadata.get("license", "Unknown")
    
    # 获取原作者
    original_author = "K-Dense Inc."
    if isinstance(metadata.get("metadata"), dict):
        original_author = metadata["metadata"].get("skill-author", "K-Dense Inc.")
    
    # 确定允许的工具
    allowed_tools = determine_allowed_tools(skill_name, description)
    
    # 构建新的 YAML 头
    yaml_header = f"""---
name: {skill_name}
display_name: {name_to_display_name(skill_name)}
description: {description}
version: 1.0.0
author: {original_author}
license: {license_info}
tags: {json.dumps(category_info["tags"])}
category: {category_id}
allowed_tools: {json.dumps(allowed_tools)}
max_iterations: 30
timeout: 600
enabled: true
match_threshold: 0.7
priority: {category_info["priority"]}
source: K-Dense-AI/claude-scientific-skills
---"""
    
    return yaml_header + "\n\n" + body


def import_skill(
    skill_path: Path,
    target_dir: Path,
) -> SkillImportResult:
    """导入单个 skill"""
    skill_name = skill_path.name
    
    result = SkillImportResult(
        name=skill_name,
        category="",
        status="",
        source_path=str(skill_path),
        target_path=""
    )
    
    try:
        # 解析源 skill
        parsed = parse_kdense_skill(skill_path)
        
        # 获取分类
        category_id, _ = get_skill_category(skill_name)
        result.category = category_id
        
        # 创建目标目录
        target_skill_dir = target_dir / category_id / skill_name
        target_skill_dir.mkdir(parents=True, exist_ok=True)
        result.target_path = str(target_skill_dir)
        
        # 转换并写入 SKILL.md
        converted_content = convert_to_tokendance_format(skill_name, parsed)
        (target_skill_dir / "SKILL.md").write_text(converted_content, encoding="utf-8")
        
        # 复制 resources 目录（如果存在）
        source_resources = skill_path / "resources"
        if source_resources.exists():
            target_resources = target_skill_dir / "resources"
            if target_resources.exists():
                shutil.rmtree(target_resources)
            shutil.copytree(source_resources, target_resources)
        
        # 复制 references 目录（如果存在）
        source_refs = skill_path / "references"
        if source_refs.exists():
            target_refs = target_skill_dir / "references"
            if target_refs.exists():
                shutil.rmtree(target_refs)
            shutil.copytree(source_refs, target_refs)
        
        result.status = "success"
        
    except Exception as e:
        result.status = "error"
        result.error = str(e)
    
    return result


def import_all_skills(
    source_dir: Path,
    target_dir: Path,
) -> ImportReport:
    """批量导入所有 skills"""
    
    report = ImportReport()
    
    # 获取所有 skill 目录
    skill_dirs = [d for d in source_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]
    report.total = len(skill_dirs)
    
    print(f"\n{'='*60}")
    print(f"K-Dense Scientific Skills 导入")
    print(f"{'='*60}")
    print(f"源目录: {source_dir}")
    print(f"目标目录: {target_dir}")
    print(f"发现 {report.total} 个 skills")
    print(f"{'='*60}\n")
    
    # 按分类统计
    category_stats: dict[str, int] = {}
    
    for skill_dir in sorted(skill_dirs):
        result = import_skill(skill_dir, target_dir)
        report.results.append(result)
        
        if result.status == "success":
            report.success += 1
            category_stats[result.category] = category_stats.get(result.category, 0) + 1
            print(f"✓ {result.name} -> {result.category}")
        elif result.status == "error":
            report.error += 1
            print(f"✗ {result.name}: {result.error}")
        else:
            report.skipped += 1
            print(f"- {result.name}: skipped")
    
    # 打印统计
    print(f"\n{'='*60}")
    print("导入统计")
    print(f"{'='*60}")
    print(f"总计: {report.total}")
    print(f"成功: {report.success}")
    print(f"失败: {report.error}")
    print(f"跳过: {report.skipped}")
    print(f"\n按分类统计:")
    for cat, count in sorted(category_stats.items()):
        cat_info = SKILL_CATEGORIES.get(cat, {})
        display_name = cat_info.get("display_name", cat)
        print(f"  - {display_name} ({cat}): {count}")
    print(f"{'='*60}\n")
    
    return report


def main():
    parser = argparse.ArgumentParser(
        description="Import K-Dense scientific skills into TokenDance"
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("/tmp/claude-scientific-skills/scientific-skills"),
        help="Source directory containing K-Dense skills"
    )
    parser.add_argument(
        "--target",
        type=Path,
        default=Path("backend/app/skills/scientific"),
        help="Target directory for imported skills"
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("import_report.json"),
        help="Path to save import report"
    )
    
    args = parser.parse_args()
    
    # 验证源目录
    if not args.source.exists():
        print(f"Error: Source directory not found: {args.source}")
        return 1
    
    # 创建目标目录
    args.target.mkdir(parents=True, exist_ok=True)
    
    # 执行导入
    report = import_all_skills(args.source, args.target)
    
    # 保存报告
    report_data = {
        "total": report.total,
        "success": report.success,
        "error": report.error,
        "skipped": report.skipped,
        "timestamp": report.timestamp,
        "results": [
            {
                "name": r.name,
                "category": r.category,
                "status": r.status,
                "error": r.error
            }
            for r in report.results
        ]
    }
    args.report.write_text(json.dumps(report_data, indent=2, ensure_ascii=False))
    print(f"导入报告已保存到: {args.report}")
    
    return 0 if report.error == 0 else 1


if __name__ == "__main__":
    exit(main())
