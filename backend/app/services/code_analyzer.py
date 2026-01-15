# -*- coding: utf-8 -*-
"""
Code Analyzer Service - 代码分析服务

功能：
- AST 解析 (基于 Python ast 模块)
- 依赖关系提取 (package.json, pyproject.toml)
- 符号提取 (函数/类/变量)
- 代码结构图生成
"""
import os
import ast
import json
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set
import re

logger = logging.getLogger(__name__)


# ==================== 数据模型 ====================

@dataclass
class Symbol:
    """代码符号"""
    name: str
    type: str  # "function", "class", "variable", "import"
    line: int
    end_line: Optional[int] = None
    docstring: Optional[str] = None
    signature: Optional[str] = None
    parent: Optional[str] = None  # 父类/父函数
    decorators: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type,
            "line": self.line,
            "end_line": self.end_line,
            "docstring": self.docstring,
            "signature": self.signature,
            "parent": self.parent,
            "decorators": self.decorators
        }


@dataclass
class Dependency:
    """项目依赖"""
    name: str
    version: Optional[str] = None
    dev: bool = False
    source: str = ""  # "package.json", "pyproject.toml", "import"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "dev": self.dev,
            "source": self.source
        }


@dataclass
class FileAnalysis:
    """文件分析结果"""
    path: str
    language: str
    symbols: List[Symbol] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    complexity: int = 0
    line_count: int = 0
    comment_count: int = 0


@dataclass
class ProjectAnalysis:
    """项目分析结果"""
    root_path: str
    dependencies: List[Dependency] = field(default_factory=list)
    dev_dependencies: List[Dependency] = field(default_factory=list)
    files: Dict[str, FileAnalysis] = field(default_factory=dict)
    entry_points: List[str] = field(default_factory=list)


# ==================== Python AST 分析 ====================

class PythonAnalyzer:
    """Python 代码分析器"""
    
    def analyze_file(self, file_path: str) -> FileAnalysis:
        """分析 Python 文件"""
        analysis = FileAnalysis(path=file_path, language="python")
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            analysis.line_count = len(content.splitlines())
            analysis.comment_count = self._count_comments(content)
            
            tree = ast.parse(content)
            analysis.symbols = self._extract_symbols(tree)
            analysis.imports = self._extract_imports(tree)
            analysis.complexity = self._calculate_complexity(tree)
            
        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}: {e}")
        except Exception as e:
            logger.warning(f"Error analyzing {file_path}: {e}")
        
        return analysis
    
    def _extract_symbols(self, tree: ast.AST) -> List[Symbol]:
        """提取符号"""
        symbols = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                symbols.append(Symbol(
                    name=node.name,
                    type="function",
                    line=node.lineno,
                    end_line=node.end_lineno,
                    docstring=ast.get_docstring(node),
                    signature=self._get_function_signature(node),
                    decorators=[self._get_decorator_name(d) for d in node.decorator_list]
                ))
            
            elif isinstance(node, ast.AsyncFunctionDef):
                symbols.append(Symbol(
                    name=node.name,
                    type="async_function",
                    line=node.lineno,
                    end_line=node.end_lineno,
                    docstring=ast.get_docstring(node),
                    signature=self._get_function_signature(node),
                    decorators=[self._get_decorator_name(d) for d in node.decorator_list]
                ))
            
            elif isinstance(node, ast.ClassDef):
                symbols.append(Symbol(
                    name=node.name,
                    type="class",
                    line=node.lineno,
                    end_line=node.end_lineno,
                    docstring=ast.get_docstring(node),
                    decorators=[self._get_decorator_name(d) for d in node.decorator_list]
                ))
        
        return symbols
    
    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """提取导入"""
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                imports.append(module)
        
        return list(set(imports))
    
    def _get_function_signature(self, node) -> str:
        """获取函数签名"""
        args = []
        
        # 普通参数
        for arg in node.args.args:
            arg_str = arg.arg
            if arg.annotation:
                arg_str += f": {ast.unparse(arg.annotation)}"
            args.append(arg_str)
        
        # 默认值
        defaults = node.args.defaults
        num_defaults = len(defaults)
        if num_defaults > 0:
            for i, default in enumerate(defaults):
                idx = len(args) - num_defaults + i
                args[idx] += f"={ast.unparse(default)}"
        
        # *args
        if node.args.vararg:
            args.append(f"*{node.args.vararg.arg}")
        
        # **kwargs
        if node.args.kwarg:
            args.append(f"**{node.args.kwarg.arg}")
        
        signature = f"({', '.join(args)})"
        
        # 返回类型
        if node.returns:
            signature += f" -> {ast.unparse(node.returns)}"
        
        return signature
    
    def _get_decorator_name(self, node) -> str:
        """获取装饰器名称"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_decorator_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Call):
            return self._get_decorator_name(node.func)
        return str(node)
    
    def _calculate_complexity(self, tree: ast.AST) -> int:
        """计算圈复杂度"""
        complexity = 1
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        
        return complexity
    
    def _count_comments(self, content: str) -> int:
        """计算注释数量"""
        lines = content.splitlines()
        count = 0
        in_docstring = False
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('"""') or stripped.startswith("'''"):
                if in_docstring:
                    in_docstring = False
                else:
                    in_docstring = True
                count += 1
            elif in_docstring:
                count += 1
            elif stripped.startswith("#"):
                count += 1
        
        return count


# ==================== 依赖分析 ====================

class DependencyAnalyzer:
    """依赖分析器"""
    
    def analyze_project(self, root_path: str) -> List[Dependency]:
        """分析项目依赖"""
        dependencies = []
        
        # Python: pyproject.toml
        pyproject_path = Path(root_path) / "pyproject.toml"
        if pyproject_path.exists():
            dependencies.extend(self._parse_pyproject(pyproject_path))
        
        # Python: requirements.txt
        requirements_path = Path(root_path) / "requirements.txt"
        if requirements_path.exists():
            dependencies.extend(self._parse_requirements(requirements_path))
        
        # Node: package.json
        package_json_path = Path(root_path) / "package.json"
        if package_json_path.exists():
            dependencies.extend(self._parse_package_json(package_json_path))
        
        # Go: go.mod
        go_mod_path = Path(root_path) / "go.mod"
        if go_mod_path.exists():
            dependencies.extend(self._parse_go_mod(go_mod_path))
        
        return dependencies
    
    def _parse_pyproject(self, path: Path) -> List[Dependency]:
        """解析 pyproject.toml"""
        dependencies = []
        
        try:
            # 简单解析 TOML (不依赖 tomllib)
            content = path.read_text(encoding="utf-8")
            
            # 提取 dependencies
            dep_match = re.search(r'\[project\].*?dependencies\s*=\s*\[(.*?)\]', content, re.DOTALL)
            if dep_match:
                deps_str = dep_match.group(1)
                for dep in re.findall(r'"([^"]+)"', deps_str):
                    name, version = self._parse_dep_string(dep)
                    dependencies.append(Dependency(
                        name=name,
                        version=version,
                        source="pyproject.toml"
                    ))
            
            # 提取 dev dependencies
            dev_match = re.search(r'\[project\.optional-dependencies\].*?dev\s*=\s*\[(.*?)\]', content, re.DOTALL)
            if dev_match:
                deps_str = dev_match.group(1)
                for dep in re.findall(r'"([^"]+)"', deps_str):
                    name, version = self._parse_dep_string(dep)
                    dependencies.append(Dependency(
                        name=name,
                        version=version,
                        dev=True,
                        source="pyproject.toml"
                    ))
                    
        except Exception as e:
            logger.warning(f"Error parsing pyproject.toml: {e}")
        
        return dependencies
    
    def _parse_requirements(self, path: Path) -> List[Dependency]:
        """解析 requirements.txt"""
        dependencies = []
        
        try:
            content = path.read_text(encoding="utf-8")
            for line in content.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                
                name, version = self._parse_dep_string(line)
                dependencies.append(Dependency(
                    name=name,
                    version=version,
                    source="requirements.txt"
                ))
        except Exception as e:
            logger.warning(f"Error parsing requirements.txt: {e}")
        
        return dependencies
    
    def _parse_package_json(self, path: Path) -> List[Dependency]:
        """解析 package.json"""
        dependencies = []
        
        try:
            content = json.loads(path.read_text(encoding="utf-8"))
            
            # dependencies
            for name, version in content.get("dependencies", {}).items():
                dependencies.append(Dependency(
                    name=name,
                    version=version,
                    source="package.json"
                ))
            
            # devDependencies
            for name, version in content.get("devDependencies", {}).items():
                dependencies.append(Dependency(
                    name=name,
                    version=version,
                    dev=True,
                    source="package.json"
                ))
        except Exception as e:
            logger.warning(f"Error parsing package.json: {e}")
        
        return dependencies
    
    def _parse_go_mod(self, path: Path) -> List[Dependency]:
        """解析 go.mod"""
        dependencies = []
        
        try:
            content = path.read_text(encoding="utf-8")
            for line in content.splitlines():
                line = line.strip()
                if line.startswith("require"):
                    continue
                
                match = re.match(r'^\s*(\S+)\s+v?(\S+)', line)
                if match:
                    dependencies.append(Dependency(
                        name=match.group(1),
                        version=match.group(2),
                        source="go.mod"
                    ))
        except Exception as e:
            logger.warning(f"Error parsing go.mod: {e}")
        
        return dependencies
    
    def _parse_dep_string(self, dep_str: str) -> tuple:
        """解析依赖字符串"""
        # 支持格式: name, name==version, name>=version, name[extras]
        match = re.match(r'^([a-zA-Z0-9_-]+)(?:\[.*?\])?(?:([<>=!]+)(.+))?$', dep_str)
        if match:
            name = match.group(1)
            version = match.group(3) if match.group(3) else None
            return name, version
        return dep_str, None


# ==================== 代码分析服务 ====================

class CodeAnalyzerService:
    """代码分析服务
    
    使用示例:
        analyzer = CodeAnalyzerService("/path/to/project")
        
        # 分析单个文件
        file_analysis = await analyzer.analyze_file("src/main.py")
        
        # 分析整个项目
        project_analysis = await analyzer.analyze_project()
        
        # 获取符号
        symbols = analyzer.get_symbols("src/main.py")
    """
    
    def __init__(self, root_path: str):
        self.root_path = Path(root_path).resolve()
        self.python_analyzer = PythonAnalyzer()
        self.dependency_analyzer = DependencyAnalyzer()
        self.project_analysis: Optional[ProjectAnalysis] = None
        
        logger.info(f"CodeAnalyzerService initialized: {self.root_path}")
    
    async def analyze_file(self, file_path: str) -> Optional[FileAnalysis]:
        """分析单个文件"""
        path = Path(file_path)
        
        if not path.exists():
            return None
        
        ext = path.suffix.lower()
        
        if ext == ".py":
            return self.python_analyzer.analyze_file(str(path))
        
        # TODO: 添加更多语言支持
        return None
    
    async def analyze_project(self) -> ProjectAnalysis:
        """分析整个项目"""
        self.project_analysis = ProjectAnalysis(root_path=str(self.root_path))
        
        # 分析依赖
        dependencies = self.dependency_analyzer.analyze_project(str(self.root_path))
        for dep in dependencies:
            if dep.dev:
                self.project_analysis.dev_dependencies.append(dep)
            else:
                self.project_analysis.dependencies.append(dep)
        
        # 分析 Python 文件
        for py_file in self.root_path.rglob("*.py"):
            # 跳过虚拟环境等
            if any(p in str(py_file) for p in ["venv", ".venv", "node_modules", "__pycache__"]):
                continue
            
            analysis = await self.analyze_file(str(py_file))
            if analysis:
                self.project_analysis.files[str(py_file)] = analysis
        
        # 检测入口点
        self.project_analysis.entry_points = self._detect_entry_points()
        
        logger.info(f"Project analysis complete: {len(self.project_analysis.files)} files")
        return self.project_analysis
    
    def _detect_entry_points(self) -> List[str]:
        """检测入口点"""
        entry_points = []
        
        # 常见入口文件
        common_entries = ["main.py", "app.py", "__main__.py", "cli.py", "run.py"]
        
        for entry in common_entries:
            path = self.root_path / entry
            if path.exists():
                entry_points.append(str(path))
        
        # 检查 src 目录
        src_dir = self.root_path / "src"
        if src_dir.exists():
            for entry in common_entries:
                path = src_dir / entry
                if path.exists():
                    entry_points.append(str(path))
        
        return entry_points
    
    def get_symbols(self, file_path: str) -> List[Symbol]:
        """获取文件符号"""
        if self.project_analysis and file_path in self.project_analysis.files:
            return self.project_analysis.files[file_path].symbols
        return []
    
    def search_symbol(self, name: str) -> List[tuple]:
        """搜索符号"""
        results = []
        
        if not self.project_analysis:
            return results
        
        for file_path, analysis in self.project_analysis.files.items():
            for symbol in analysis.symbols:
                if name.lower() in symbol.name.lower():
                    results.append((file_path, symbol))
        
        return results
    
    def get_dependency_graph(self) -> Dict[str, List[str]]:
        """获取依赖图"""
        graph = {}
        
        if not self.project_analysis:
            return graph
        
        for file_path, analysis in self.project_analysis.files.items():
            graph[file_path] = analysis.imports
        
        return graph
    
    def to_dict(self) -> Dict[str, Any]:
        """导出为字典"""
        if not self.project_analysis:
            return {}
        
        return {
            "root_path": self.project_analysis.root_path,
            "dependencies": [d.to_dict() for d in self.project_analysis.dependencies],
            "dev_dependencies": [d.to_dict() for d in self.project_analysis.dev_dependencies],
            "entry_points": self.project_analysis.entry_points,
            "file_count": len(self.project_analysis.files),
            "files": {
                path: {
                    "language": a.language,
                    "line_count": a.line_count,
                    "symbol_count": len(a.symbols),
                    "complexity": a.complexity
                }
                for path, a in self.project_analysis.files.items()
            }
        }


# ==================== 工厂函数 ====================

def create_code_analyzer(root_path: str) -> CodeAnalyzerService:
    """创建代码分析服务"""
    return CodeAnalyzerService(root_path=root_path)
