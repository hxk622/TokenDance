# TokenDance Scientific Skills Catalog

> 来源: [K-Dense-AI/claude-scientific-skills](https://github.com/K-Dense-AI/claude-scientific-skills) (MIT License)
> 导入日期: 2026-01-15
> 总计: 139 个科学技能

本目录包含从 K-Dense 科学技能库导入的全部技能，涵盖生物信息学、化学、数据科学、物理等多个领域。

## 快速开始

### 安装依赖

根据需要安装特定领域的依赖：

```bash
# 生物信息学
cd backend && uv pip install -e ".[science-bio]"

# 化学与药物发现
cd backend && uv pip install -e ".[science-chem]"

# 数据科学与机器学习
cd backend && uv pip install -e ".[science-ml]"

# 数据可视化
cd backend && uv pip install -e ".[science-viz]"

# 全部核心依赖
cd backend && uv pip install -e ".[science-all]"
```

---

## 分类目录

### 1. 🧬 Bioinformatics & Genomics (生物信息学) - 21个

| Skill | 说明 |
|-------|------|
| **biopython** | 综合分子生物学工具包，序列操作、FASTA/GenBank解析、NCBI访问 |
| **scanpy** | 单细胞RNA测序分析，聚类、轨迹推断、差异表达 |
| **anndata** | 注释数据矩阵，单细胞数据的标准存储格式 |
| **pydeseq2** | 差异基因表达分析，RNA-seq数据统计分析 |
| **gget** | 基因组数据检索，快速访问Ensembl、UniProt等数据库 |
| **pysam** | SAM/BAM文件处理，高通量测序数据操作 |
| **scikit-bio** | 生物信息学算法库，序列比对、系统发育树 |
| **scvi-tools** | 单细胞变分推断，深度学习驱动的单细胞分析 |
| **arboreto** | 基因调控网络推断 |
| **etetoolkit** | 系统发育树可视化与分析 |
| **deeptools** | 高通量测序数据可视化 |
| **geniml** | 基因组区间机器学习 |
| **cellxgene-census** | CellxGene单细胞数据访问 |
| **esm** | ESM蛋白质语言模型 |
| **ensembl-database** | Ensembl基因组数据库访问 |
| **gene-database** | NCBI Gene数据库访问 |
| **geo-database** | GEO表达数据库访问 |
| **ena-database** | ENA核酸数据库访问 |
| **biorxiv-database** | bioRxiv预印本搜索 |
| **uniprot-database** | UniProt蛋白质数据库访问 |
| **string-database** | STRING蛋白质相互作用网络 |

### 2. 🧪 Chemistry & Drug Discovery (化学与药物发现) - 18个

| Skill | 说明 |
|-------|------|
| **rdkit** | 化学信息学工具包，SMILES解析、分子描述符、指纹 |
| **deepchem** | 分子机器学习，属性预测、图神经网络 |
| **datamol** | RDKit封装，简化分子操作 |
| **medchem** | 药物化学分析，ADMET属性 |
| **molfeat** | 分子特征化，多种分子表示方法 |
| **matchms** | 质谱匹配，代谢组学分析 |
| **torchdrug** | PyTorch药物发现，图神经网络 |
| **pytdc** | 治疗数据共享，MoleculeNet基准数据集 |
| **diffdock** | 分子对接，蛋白质-配体结合预测 |
| **chembl-database** | ChEMBL生物活性数据库 |
| **pubchem-database** | PubChem化合物数据库 |
| **drugbank-database** | DrugBank药物数据库 |
| **zinc-database** | ZINC化合物库 |
| **brenda-database** | BRENDA酶数据库 |
| **hmdb-database** | 人类代谢组数据库 |
| **opentargets-database** | Open Targets药物靶点 |
| **denario** | 化学结构可视化 |
| **rowan** | 量子化学计算接口 |

### 3. 📊 Data Science & ML (数据科学与机器学习) - 14个

| Skill | 说明 |
|-------|------|
| **scikit-learn** | 经典机器学习算法库 |
| **statsmodels** | 统计建模与假设检验 |
| **torch_geometric** | 图神经网络PyTorch扩展 |
| **transformers** | HuggingFace Transformer模型 |
| **shap** | 模型可解释性，Shapley值分析 |
| **pytorch-lightning** | PyTorch训练框架 |
| **stable-baselines3** | 强化学习算法 |
| **dask** | 分布式并行计算 |
| **polars** | 高性能DataFrame |
| **vaex** | 大规模数据分析 |
| **umap-learn** | UMAP降维 |
| **exploratory-data-analysis** | 探索性数据分析指南 |
| **statistical-analysis** | 统计分析方法 |
| **pufferlib** | 强化学习环境 |

### 4. 📈 Visualization (数据可视化) - 5个

| Skill | 说明 |
|-------|------|
| **matplotlib** | Python绑图库 |
| **seaborn** | 统计数据可视化 |
| **plotly** | 交互式可视化 |
| **scientific-visualization** | 科学可视化最佳实践 |
| **networkx** | 网络图分析与可视化 |

### 5. ✍️ Scientific Writing (科学写作) - 11个

| Skill | 说明 |
|-------|------|
| **scientific-writing** | 科学论文写作指南 |
| **latex-posters** | LaTeX科学海报制作 |
| **pptx-posters** | PowerPoint海报制作 |
| **citation-management** | 引用管理 |
| **literature-review** | 文献综述方法 |
| **scientific-slides** | 科学演示制作 |
| **peer-review** | 同行评审指南 |
| **scientific-schematics** | 科学图表设计 |
| **venue-templates** | 期刊/会议模板 |
| **paper-2-web** | 论文转网页展示 |
| **markitdown** | Markdown文档转换 |

### 6. 🗃️ Database Access (数据库访问) - 13个

| Skill | 说明 |
|-------|------|
| **clinicaltrials-database** | ClinicalTrials.gov临床试验 |
| **clinvar-database** | ClinVar变异数据库 |
| **cosmic-database** | COSMIC肿瘤变异数据库 |
| **kegg-database** | KEGG通路数据库 |
| **reactome-database** | Reactome通路数据库 |
| **fda-database** | FDA药物数据库 |
| **gwas-database** | GWAS Catalog |
| **pdb-database** | PDB蛋白质结构数据库 |
| **pubmed-database** | PubMed文献数据库 |
| **openalex-database** | OpenAlex学术数据库 |
| **clinpgx-database** | 临床药物基因组学 |
| **datacommons-client** | Google Data Commons |
| **uspto-database** | USPTO专利数据库 |

### 7. 🔬 Lab Automation (实验室自动化) - 9个

| Skill | 说明 |
|-------|------|
| **pylabrobot** | 实验室机器人编程 |
| **opentrons-integration** | Opentrons液体处理 |
| **protocolsio-integration** | protocols.io实验方案 |
| **benchling-integration** | Benchling LIMS集成 |
| **latchbio-integration** | Latch生物信息平台 |
| **labarchive-integration** | LabArchive电子实验记录 |
| **dnanexus-integration** | DNAnexus云平台 |
| **omero-integration** | OMERO图像管理 |
| **lamindb** | LaminDB数据管理 |

### 8. ⚛️ Physics & Materials (物理与材料) - 12个

| Skill | 说明 |
|-------|------|
| **pymatgen** | 材料科学Python库 |
| **qiskit** | IBM量子计算 |
| **pennylane** | 量子机器学习 |
| **cirq** | Google量子计算 |
| **qutip** | 量子工具箱 |
| **astropy** | 天文数据分析 |
| **fluidsim** | 流体力学模拟 |
| **sympy** | 符号数学计算 |
| **simpy** | 离散事件模拟 |
| **matlab** | MATLAB接口 |
| **aeon** | 时间序列机器学习 |
| **zarr-python** | 大规模数组存储 |

### 9. 🏥 Clinical & Medical (临床医学) - 11个

| Skill | 说明 |
|-------|------|
| **clinical-reports** | 临床报告生成 |
| **clinical-decision-support** | 临床决策支持 |
| **pyhealth** | 医疗AI库 |
| **pydicom** | DICOM医学图像处理 |
| **neurokit2** | 神经生理信号分析 |
| **neuropixels-analysis** | 神经像素电极分析 |
| **treatment-plans** | 治疗方案制定 |
| **flowio** | 流式细胞术数据 |
| **histolab** | 组织病理学图像分析 |
| **pathml** | 病理学机器学习 |
| **iso-13485-certification** | ISO 13485医疗器械认证 |

### 10. 🛠️ Research Tools (研究工具) - 25个

| Skill | 说明 |
|-------|------|
| **perplexity-search** | AI驱动的网络搜索 |
| **hypothesis-generation** | 科学假设生成 |
| **scientific-brainstorming** | 科学头脑风暴 |
| **scientific-critical-thinking** | 科学批判性思维 |
| **research-lookup** | 研究资料查找 |
| **research-grants** | 基金申请写作 |
| **scholar-evaluation** | 学术评价分析 |
| **market-research-reports** | 市场研究报告 |
| **generate-image** | AI图像生成 |
| **biomni** | 生物医学AI代理 |
| **hypogenic** | 假设生成框架 |
| **bioservices** | 生物信息服务接口 |
| **geopandas** | 地理空间数据分析 |
| **pyopenms** | 质谱数据处理 |
| **pymc** | 概率编程与贝叶斯推断 |
| **pymoo** | 多目标优化 |
| **gtars** | 基因组工具 |
| **modal** | 云计算平台 |
| **adaptyv** | 自适应实验设计 |
| **cobrapy** | 代谢网络约束分析 |
| **scikit-survival** | 生存分析 |
| **metabolomics-workbench-database** | 代谢组学数据库 |
| **alphafold-database** | AlphaFold蛋白质结构 |
| **get-available-resources** | 资源可用性检查 |
| **offer-k-dense-web** | K-Dense Web服务 |

---

## 使用说明

### 在 Agent 中使用

Skills 会自动被 SkillRegistry 加载，Agent 可以根据用户意图自动匹配和激活相关技能。

```python
from app.skills.registry import get_skill_registry

registry = get_skill_registry()

# 按标签筛选
bio_skills = registry.get_by_tag("bioinformatics")
chem_skills = registry.get_by_tag("chemistry")

# 获取所有技能
all_skills = registry.get_all()
print(f"Total skills: {len(all_skills)}")
```

### 技能匹配

```python
from app.skills.matcher import SkillMatcher

matcher = SkillMatcher(registry, embedding_model, llm)
match = await matcher.match("分析这个基因序列")
# -> 可能匹配到 biopython, scanpy 等
```

---

## 许可证

所有导入的技能均来自 [K-Dense-AI/claude-scientific-skills](https://github.com/K-Dense-AI/claude-scientific-skills)，采用 MIT 许可证。

每个技能可能有其独立的许可证要求，请在使用前查看各技能的 `SKILL.md` 文件中的 `license` 字段。

---

## 致谢

感谢 K-Dense Inc. 开源了这套优秀的科学技能库，使得 TokenDance 能够快速获得强大的科学计算能力。

> Claude Scientific Skills by K-Dense Inc. (2025)  
> https://github.com/K-Dense-AI/claude-scientific-skills
