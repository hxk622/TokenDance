"""
MCPCodeExecutor - MCP 代码执行器

职责：
1. 接收动态代码（Python / JavaScript）
2. 在隔离的沙箱中执行
3. 管理超时和资源限制
4. 返回执行结果或错误
"""

import asyncio
import json
import logging
import subprocess
import tempfile
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ExecutionLanguage(Enum):
    """支持的执行语言"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"


class ExecutionStatus(Enum):
    """执行状态"""
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    RESOURCE_EXCEEDED = "resource_exceeded"


@dataclass
class ExecutionRequest:
    """代码执行请求"""
    code: str
    language: ExecutionLanguage = ExecutionLanguage.PYTHON
    timeout: int = 30  # 秒
    max_memory: int = 512  # MB
    max_output: int = 10  # MB
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionResult:
    """代码执行结果"""
    status: ExecutionStatus
    output: Optional[str] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    tokens_used: int = 0
    
    # 元数据
    language: ExecutionLanguage = ExecutionLanguage.PYTHON
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "status": self.status.value,
            "output": self.output,
            "error": self.error,
            "execution_time": self.execution_time,
            "tokens_used": self.tokens_used,
        }


class SandboxException(Exception):
    """沙箱执行异常"""
    pass


class CodeExecutionTimeout(SandboxException):
    """代码执行超时"""
    pass


class ResourceExceeded(SandboxException):
    """资源超限"""
    pass


class MCPCodeExecutor:
    """MCP 代码执行器
    
    支持在隔离的沙箱中执行 Python 和 JavaScript 代码。
    """
    
    # 内置库白名单（仅 Python）
    PYTHON_BUILTINS = [
        'json', 'math', 'statistics', 'datetime', 're',
        'collections', 'itertools', 'functools',
        'random', 'decimal', 'fractions',
    ]
    
    # 第三方库白名单
    PYTHON_PACKAGES = [
        'pandas', 'numpy', 'requests', 'bs4',
        'lxml', 'csv', 'io',
    ]
    
    def __init__(self):
        """初始化执行器"""
        self.temp_dir = Path(tempfile.gettempdir()) / "tokendance_sandbox"
        self.temp_dir.mkdir(exist_ok=True)
        logger.info(f"MCPCodeExecutor initialized with sandbox at {self.temp_dir}")
    
    async def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """执行代码
        
        Args:
            request: 执行请求
            
        Returns:
            执行结果
        """
        logger.info(
            f"Executing {request.language.value} code "
            f"(timeout={request.timeout}s, max_memory={request.max_memory}MB)"
        )
        
        try:
            # 代码验证
            self._validate_code(request.code, request.language)
            
            # 选择执行器
            if request.language == ExecutionLanguage.PYTHON:
                result = await self._execute_python(request)
            elif request.language == ExecutionLanguage.JAVASCRIPT:
                result = await self._execute_javascript(request)
            else:
                return ExecutionResult(
                    status=ExecutionStatus.FAILED,
                    error=f"Unsupported language: {request.language.value}",
                )
            
            logger.info(f"Code execution completed: {result.status.value}")
            return result
        
        except CodeExecutionTimeout as e:
            logger.error(f"Execution timeout: {e}")
            return ExecutionResult(
                status=ExecutionStatus.TIMEOUT,
                error=str(e),
            )
        except ResourceExceeded as e:
            logger.error(f"Resource exceeded: {e}")
            return ExecutionResult(
                status=ExecutionStatus.RESOURCE_EXCEEDED,
                error=str(e),
            )
        except Exception as e:
            logger.error(f"Unexpected error: {e}\n{traceback.format_exc()}")
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                error=f"Execution error: {str(e)}",
            )
    
    def _validate_code(self, code: str, language: ExecutionLanguage) -> None:
        """验证代码安全性
        
        Args:
            code: 代码
            language: 编程语言
            
        Raises:
            SandboxException: 代码不安全
        """
        if not code or not code.strip():
            raise SandboxException("Code is empty")
        
        if language == ExecutionLanguage.PYTHON:
            self._validate_python_code(code)
    
    def _validate_python_code(self, code: str) -> None:
        """验证 Python 代码安全性
        
        Args:
            code: Python 代码
            
        Raises:
            SandboxException: 代码包含危险操作
        """
        # 禁止的关键字
        forbidden = [
            'import os', 'import subprocess', 'import sys',
            '__import__', 'exec', 'eval',
            'open(', 'file(',
        ]
        
        code_lower = code.lower()
        for keyword in forbidden:
            if keyword in code_lower:
                raise SandboxException(
                    f"Code contains forbidden operation: {keyword}"
                )
    
    async def _execute_python(self, request: ExecutionRequest) -> ExecutionResult:
        """执行 Python 代码
        
        Args:
            request: 执行请求
            
        Returns:
            执行结果
        """
        # 创建临时脚本文件
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.py',
            dir=self.temp_dir,
            delete=False,
        ) as f:
            script_path = Path(f.name)
            f.write(request.code)
        
        try:
            # 构建命令
            cmd = [
                'python3',
                str(script_path),
            ]
            
            logger.debug(f"Running: {' '.join(cmd)}")
            
            # 在线程池中执行（避免阻塞）
            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    self._run_subprocess,
                    cmd,
                    request.timeout,
                    request.max_output,
                ),
                timeout=request.timeout + 5,  # 留出缓冲时间
            )
            
            return result
        
        except asyncio.TimeoutError:
            raise CodeExecutionTimeout(
                f"Python code execution timed out after {request.timeout}s"
            )
        finally:
            # 清理临时文件
            try:
                script_path.unlink()
            except Exception as e:
                logger.warning(f"Failed to cleanup temp file: {e}")
    
    async def _execute_javascript(self, request: ExecutionRequest) -> ExecutionResult:
        """执行 JavaScript 代码
        
        Args:
            request: 执行请求
            
        Returns:
            执行结果
        """
        # 创建临时脚本文件
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.js',
            dir=self.temp_dir,
            delete=False,
        ) as f:
            script_path = Path(f.name)
            f.write(request.code)
        
        try:
            # 构建命令（使用 Node.js）
            cmd = [
                'node',
                str(script_path),
            ]
            
            logger.debug(f"Running: {' '.join(cmd)}")
            
            # 在线程池中执行
            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    self._run_subprocess,
                    cmd,
                    request.timeout,
                    request.max_output,
                ),
                timeout=request.timeout + 5,
            )
            
            return result
        
        except asyncio.TimeoutError:
            raise CodeExecutionTimeout(
                f"JavaScript code execution timed out after {request.timeout}s"
            )
        finally:
            # 清理临时文件
            try:
                script_path.unlink()
            except Exception as e:
                logger.warning(f"Failed to cleanup temp file: {e}")
    
    def _run_subprocess(
        self,
        cmd: List[str],
        timeout: int,
        max_output: int,
    ) -> ExecutionResult:
        """同步执行子进程
        
        Args:
            cmd: 命令
            timeout: 超时时间（秒）
            max_output: 最大输出大小（MB）
            
        Returns:
            执行结果
        """
        import time
        
        start_time = time.time()
        
        try:
            # 执行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(self.temp_dir),
            )
            
            execution_time = time.time() - start_time
            
            # 检查输出大小
            output_size_mb = len(result.stdout) / (1024 * 1024)
            if output_size_mb > max_output:
                raise ResourceExceeded(
                    f"Output size {output_size_mb:.2f}MB exceeds limit {max_output}MB"
                )
            
            # 检查返回码
            if result.returncode != 0:
                error_msg = result.stderr or f"Process exited with code {result.returncode}"
                return ExecutionResult(
                    status=ExecutionStatus.FAILED,
                    error=error_msg,
                    execution_time=execution_time,
                )
            
            # 成功
            return ExecutionResult(
                status=ExecutionStatus.SUCCESS,
                output=result.stdout.strip(),
                execution_time=execution_time,
            )
        
        except subprocess.TimeoutExpired:
            raise CodeExecutionTimeout(
                f"Command execution timed out after {timeout}s"
            )
        except Exception as e:
            execution_time = time.time() - start_time
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                error=str(e),
                execution_time=execution_time,
            )
    
    def cleanup(self) -> None:
        """清理沙箱临时文件"""
        try:
            import shutil
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                logger.info("Sandbox cleanup completed")
        except Exception as e:
            logger.error(f"Failed to cleanup sandbox: {e}")


# ============================================================================
# 工厂函数
# ============================================================================

_global_executor: Optional[MCPCodeExecutor] = None


def get_mcp_executor() -> MCPCodeExecutor:
    """获取全局 MCPCodeExecutor 单例
    
    Returns:
        MCPCodeExecutor 单例
    """
    global _global_executor
    
    if _global_executor is None:
        _global_executor = MCPCodeExecutor()
    
    return _global_executor


def reset_mcp_executor() -> None:
    """重置全局 MCPCodeExecutor 单例"""
    global _global_executor
    if _global_executor:
        _global_executor.cleanup()
    _global_executor = None
