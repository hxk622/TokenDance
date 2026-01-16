# -*- coding: utf-8 -*-
"""
Files API - 文件索引与搜索 API 端点

提供文件索引和语义搜索功能：
- POST /files/index - 索引目录
- GET /files/search - 语义搜索
- GET /files/tree - 获取目录树
- GET /files/stats - 获取索引统计
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
import logging

from ...services.file_indexer import FileIndexerService, create_file_indexer
from ...services.code_analyzer import CodeAnalyzerService, create_code_analyzer
from ...services.vector_indexer import VectorIndexerService, create_vector_indexer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/files", tags=["files"])


# ==================== 请求/响应模型 ====================

class IndexRequest(BaseModel):
    """索引请求"""
    path: str = Field(..., description="要索引的目录路径")
    extensions: Optional[List[str]] = Field(
        default=None,
        description="要索引的文件扩展名"
    )
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "path": "/Users/user/project",
            "extensions": [".py", ".js", ".ts", ".md"]
        }
    })


class SearchRequest(BaseModel):
    """搜索请求"""
    query: str = Field(..., description="搜索查询")
    top_k: int = Field(default=10, ge=1, le=50, description="返回结果数量")
    language: Optional[str] = Field(default=None, description="过滤语言")


class FileInfo(BaseModel):
    """文件信息"""
    path: str
    name: str
    extension: str
    size: int
    language: Optional[str] = None
    modified_at: str


class SearchResult(BaseModel):
    """搜索结果"""
    content: str
    file_path: str
    start_line: int
    end_line: int
    score: float
    language: Optional[str] = None


class IndexStats(BaseModel):
    """索引统计"""
    indexed_files: int
    total_size: int
    languages: Dict[str, int]
    indexed_at: Optional[str] = None


class DirectoryTree(BaseModel):
    """目录树"""
    name: str
    type: str  # "directory" or "file"
    language: Optional[str] = None
    size: Optional[int] = None
    children: Optional[List["DirectoryTree"]] = None


DirectoryTree.model_rebuild()


class SymbolInfo(BaseModel):
    """符号信息"""
    name: str
    type: str
    line: int
    end_line: Optional[int] = None
    signature: Optional[str] = None
    docstring: Optional[str] = None


class FileAnalysis(BaseModel):
    """文件分析结果"""
    path: str
    language: str
    line_count: int
    complexity: int
    symbols: List[SymbolInfo]
    imports: List[str]


# ==================== 服务实例（全局）====================

_file_indexer: Optional[FileIndexerService] = None
_code_analyzer: Optional[CodeAnalyzerService] = None
_vector_indexer: Optional[VectorIndexerService] = None


def get_file_indexer(path: str) -> FileIndexerService:
    """获取或创建文件索引服务"""
    global _file_indexer
    if _file_indexer is None or str(_file_indexer.root_path) != path:
        _file_indexer = create_file_indexer(path)
    return _file_indexer


def get_code_analyzer(path: str) -> CodeAnalyzerService:
    """获取或创建代码分析服务"""
    global _code_analyzer
    if _code_analyzer is None or str(_code_analyzer.root_path) != path:
        _code_analyzer = create_code_analyzer(path)
    return _code_analyzer


def get_vector_indexer() -> VectorIndexerService:
    """获取或创建向量索引服务"""
    global _vector_indexer
    if _vector_indexer is None:
        _vector_indexer = create_vector_indexer(use_openai=False, use_pgvector=False)
    return _vector_indexer


# ==================== API 端点 ====================

@router.post("/index", response_model=IndexStats)
async def index_directory(request: IndexRequest):
    """索引目录
    
    对指定目录进行全量索引，包括：
    - 文件系统索引
    - 代码分析
    - 向量化（可选）
    """
    import os
    
    if not os.path.exists(request.path):
        raise HTTPException(status_code=404, detail=f"Path not found: {request.path}")
    
    if not os.path.isdir(request.path):
        raise HTTPException(status_code=400, detail=f"Path is not a directory: {request.path}")
    
    logger.info(f"Indexing directory: {request.path}")
    
    # 文件索引
    indexer = get_file_indexer(request.path)
    state = await indexer.index_all()
    
    # 代码分析
    analyzer = get_code_analyzer(request.path)
    await analyzer.analyze_project()
    
    return IndexStats(
        indexed_files=state.file_count,
        total_size=state.total_size,
        languages=state.languages,
        indexed_at=state.indexed_at.isoformat()
    )


@router.post("/search", response_model=List[SearchResult])
async def semantic_search(request: SearchRequest):
    """语义搜索
    
    使用向量化索引进行语义搜索。
    """
    vector_indexer = get_vector_indexer()
    
    # 构建过滤条件
    filter_dict = None
    if request.language:
        filter_dict = {"language": request.language}
    
    results = await vector_indexer.search(
        query=request.query,
        top_k=request.top_k,
        filter_dict=filter_dict
    )
    
    return [
        SearchResult(
            content=r.content,
            file_path=r.file_path,
            start_line=r.start_line,
            end_line=r.end_line,
            score=r.score,
            language=r.metadata.get("language")
        )
        for r in results
    ]


@router.get("/tree", response_model=DirectoryTree)
async def get_directory_tree(
    path: str = Query(..., description="目录路径"),
    max_depth: int = Query(default=3, ge=1, le=10, description="最大深度")
):
    """获取目录树"""
    import os
    
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"Path not found: {path}")
    
    indexer = get_file_indexer(path)
    tree = indexer.get_directory_tree(max_depth=max_depth)
    
    return tree


@router.get("/stats", response_model=IndexStats)
async def get_index_stats(path: str = Query(..., description="目录路径")):
    """获取索引统计"""
    indexer = get_file_indexer(path)
    
    return IndexStats(
        indexed_files=indexer.state.file_count,
        total_size=indexer.state.total_size,
        languages=indexer.state.languages,
        indexed_at=indexer.state.indexed_at.isoformat() if indexer.state.indexed_at else None
    )


@router.get("/analyze/{file_path:path}", response_model=FileAnalysis)
async def analyze_file(file_path: str):
    """分析单个文件
    
    返回文件的符号、导入、复杂度等信息。
    """
    import os
    from pathlib import Path
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
    
    # 获取分析器
    root_path = str(Path(file_path).parent)
    analyzer = get_code_analyzer(root_path)
    
    analysis = await analyzer.analyze_file(file_path)
    
    if not analysis:
        raise HTTPException(status_code=400, detail=f"Cannot analyze file: {file_path}")
    
    return FileAnalysis(
        path=analysis.path,
        language=analysis.language,
        line_count=analysis.line_count,
        complexity=analysis.complexity,
        symbols=[
            SymbolInfo(
                name=s.name,
                type=s.type,
                line=s.line,
                end_line=s.end_line,
                signature=s.signature,
                docstring=s.docstring
            )
            for s in analysis.symbols
        ],
        imports=analysis.imports
    )


@router.get("/search/symbol", response_model=List[Dict[str, Any]])
async def search_symbol(
    name: str = Query(..., description="符号名称"),
    path: str = Query(..., description="搜索路径")
):
    """搜索符号"""
    analyzer = get_code_analyzer(path)
    
    # 确保已分析
    if not analyzer.project_analysis:
        await analyzer.analyze_project()
    
    results = analyzer.search_symbol(name)
    
    return [
        {
            "file_path": file_path,
            "symbol": {
                "name": symbol.name,
                "type": symbol.type,
                "line": symbol.line,
                "signature": symbol.signature
            }
        }
        for file_path, symbol in results
    ]


@router.get("/languages", response_model=Dict[str, int])
async def get_language_stats(path: str = Query(..., description="目录路径")):
    """获取语言统计"""
    indexer = get_file_indexer(path)
    return indexer.get_language_stats()


@router.post("/index/incremental", response_model=Dict[str, Any])
async def incremental_index(path: str = Query(..., description="目录路径")):
    """增量索引
    
    只索引自上次索引以来修改的文件。
    """
    indexer = get_file_indexer(path)
    updated_files = await indexer.index_incremental()
    
    return {
        "updated_count": len(updated_files),
        "files": [f.name for f in updated_files[:20]]  # 最多返回20个
    }
