"""
Sandbox 类型和异常测试
"""

import pytest

from app.sandbox.exceptions import (
    ConcurrentAccessError,
    ConfirmationRejectedError,
    ConfirmationTimeoutError,
    ExecutionRejectedError,
    PathTraversalError,
    SandboxError,
    SandboxNotAvailableError,
    SandboxTimeoutError,
)
from app.sandbox.types import (
    ExecutionRequest,
    ExecutionResult,
    SandboxType,
    SecurityMode,
)


class TestSandboxType:
    """SandboxType 枚举测试"""

    def test_values(self):
        """检查所有值"""
        assert SandboxType.SUBPROCESS.value == "subprocess"
        assert SandboxType.DOCKER_SIMPLE.value == "docker_simple"
        assert SandboxType.AIO_SANDBOX.value == "aio_sandbox"

    def test_string_conversion(self):
        """字符串转换"""
        assert str(SandboxType.SUBPROCESS) == "SandboxType.SUBPROCESS"


class TestSecurityMode:
    """SecurityMode 枚举测试"""

    def test_values(self):
        """检查所有值"""
        assert SecurityMode.PERMISSIVE.value == "permissive"
        assert SecurityMode.STRICT.value == "strict"


class TestExecutionRequest:
    """ExecutionRequest 测试"""

    def test_default_values(self):
        """默认值"""
        request = ExecutionRequest(code="print(1)")

        assert request.code == "print(1)"
        assert request.language == "python"
        assert request.timeout == 30
        assert request.sandbox_type is None
        assert request.session_id == ""
        assert request.max_memory_mb == 512

    def test_custom_values(self):
        """自定义值"""
        request = ExecutionRequest(
            code="console.log(1)",
            language="javascript",
            timeout=60,
            sandbox_type=SandboxType.DOCKER_SIMPLE,
            session_id="session_123",
            max_memory_mb=1024,
        )

        assert request.language == "javascript"
        assert request.timeout == 60
        assert request.sandbox_type == SandboxType.DOCKER_SIMPLE


class TestExecutionResult:
    """ExecutionResult 测试"""

    def test_success_result(self):
        """成功结果"""
        result = ExecutionResult(
            success=True,
            stdout="Hello",
            exit_code=0,
        )

        assert result.success
        assert result.stdout == "Hello"
        assert result.exit_code == 0
        assert result.error is None

    def test_failure_result(self):
        """失败结果"""
        result = ExecutionResult(
            success=False,
            stderr="Error message",
            error="执行失败",
            exit_code=1,
        )

        assert not result.success
        assert result.error == "执行失败"
        assert result.exit_code == 1

    def test_to_dict(self):
        """转换为字典"""
        result = ExecutionResult(
            success=True,
            stdout="output",
            stderr="",
            exit_code=0,
            sandbox_type=SandboxType.SUBPROCESS,
            execution_time_ms=100.5,
        )

        d = result.to_dict()

        assert d["success"] is True
        assert d["stdout"] == "output"
        assert d["sandbox_type"] == "subprocess"
        assert d["execution_time_ms"] == 100.5


class TestExceptions:
    """异常测试"""

    def test_sandbox_error_hierarchy(self):
        """异常继承层次"""
        assert issubclass(PathTraversalError, SandboxError)
        assert issubclass(ConcurrentAccessError, SandboxError)
        assert issubclass(SandboxTimeoutError, SandboxError)
        assert issubclass(SandboxNotAvailableError, SandboxError)
        assert issubclass(ExecutionRejectedError, SandboxError)
        assert issubclass(ConfirmationTimeoutError, SandboxError)
        assert issubclass(ConfirmationRejectedError, SandboxError)

    def test_path_traversal_error(self):
        """PathTraversalError"""
        with pytest.raises(PathTraversalError) as exc_info:
            raise PathTraversalError("检测到路径遍历: ../etc/passwd")

        assert "路径遍历" in str(exc_info.value)

    def test_concurrent_access_error(self):
        """ConcurrentAccessError"""
        with pytest.raises(ConcurrentAccessError) as exc_info:
            raise ConcurrentAccessError("Session 正在使用")

        assert "Session" in str(exc_info.value)

    def test_sandbox_timeout_error(self):
        """SandboxTimeoutError"""
        with pytest.raises(SandboxTimeoutError) as exc_info:
            raise SandboxTimeoutError("执行超时 (30s)")

        assert "超时" in str(exc_info.value)
