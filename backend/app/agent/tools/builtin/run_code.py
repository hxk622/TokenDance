"""
RunCodeTool - 代码执行工具

核心 4 工具之一：run_code

所有代码执行都通过 SandboxManager，确保：
- 统一的风险评估
- 自动的 Sandbox 选择
- 可选的用户确认

风险等级：动态（根据代码内容）
"""

from pydantic import BaseModel, Field

from app.agent.tools.base import BaseTool, ToolResult
from app.agent.tools.risk import OperationCategory, RiskLevel
from app.sandbox.manager import SandboxManager
from app.sandbox.risk_policy import UnifiedRiskPolicy
from app.sandbox.types import ExecutionRequest


class RunCodeToolArgs(BaseModel):
    """RunCodeTool 参数"""

    code: str = Field(..., description="要执行的代码")
    language: str = Field("python", description="编程语言: python | javascript | shell")
    timeout: int = Field(30, ge=1, le=300, description="超时时间（秒）")


class RunCodeTool(BaseTool):
    """代码执行工具 - 核心 4 工具之一

    通过 SandboxManager 执行代码，自动风险评估和 Sandbox 选择。

    特点：
    - 支持 Python、JavaScript、Shell
    - 动态风险评估
    - 自动选择合适的 Sandbox（Subprocess/Docker/AIO）
    - 可选的用户确认机制

    示例：
        result = await run_code.execute(
            code="print('Hello, World!')",
            language="python"
        )
    """

    name = "run_code"
    description = "在安全沙箱中执行代码。支持 Python、JavaScript、Shell。"
    args_schema = RunCodeToolArgs

    # 默认风险配置（会被动态覆盖）
    risk_level = RiskLevel.HIGH
    operation_categories = [OperationCategory.SHELL_WRITE]
    requires_confirmation = False

    def __init__(self, sandbox_manager: SandboxManager):
        """
        Args:
            sandbox_manager: Sandbox 管理器实例
        """
        super().__init__()
        self.sandbox_manager = sandbox_manager

    def get_risk_level(self, **kwargs) -> RiskLevel:
        """根据代码动态评估风险等级"""
        code = kwargs.get("code", "")
        lang = kwargs.get("language", "python")
        content_type = "shell" if lang == "shell" else lang

        assessment = UnifiedRiskPolicy.assess(code, content_type)

        # 映射到工具风险等级
        level_map = {
            "safe": RiskLevel.NONE,
            "low": RiskLevel.LOW,
            "medium": RiskLevel.MEDIUM,
            "high": RiskLevel.HIGH,
            "critical": RiskLevel.CRITICAL,
        }
        return level_map.get(assessment.level.value, RiskLevel.HIGH)

    def get_operation_categories(self, **kwargs) -> list[OperationCategory]:
        """根据代码返回操作类别"""
        risk = self.get_risk_level(**kwargs)

        if risk == RiskLevel.CRITICAL:
            return [OperationCategory.SHELL_DANGEROUS]
        elif risk in (RiskLevel.NONE, RiskLevel.LOW):
            return [OperationCategory.SHELL_SAFE]
        else:
            return [OperationCategory.SHELL_WRITE]

    def requires_confirmation_for(self, **kwargs) -> bool:
        """检查是否需要确认"""
        code = kwargs.get("code", "")
        lang = kwargs.get("language", "python")
        content_type = "shell" if lang == "shell" else lang

        assessment = UnifiedRiskPolicy.assess(code, content_type)
        return assessment.requires_confirmation

    def get_confirmation_description(self, **kwargs) -> str:
        """提供详细的确认描述"""
        code = kwargs.get("code", "")
        lang = kwargs.get("language", "python")
        risk = self.get_risk_level(**kwargs)

        # 截断代码预览
        code_preview = code[:200] + "..." if len(code) > 200 else code

        return f"执行 {lang} 代码:\n```{lang}\n{code_preview}\n```\n风险等级: {risk.value}"

    async def execute(
        self,
        code: str,
        language: str = "python",
        timeout: int = 30,
    ) -> ToolResult:
        """执行代码

        Args:
            code: 要执行的代码
            language: 编程语言
            timeout: 超时时间（秒）

        Returns:
            ToolResult: 执行结果
        """
        request = ExecutionRequest(
            code=code,
            language=language,
            timeout=timeout,
            session_id=self.sandbox_manager.session_id,
        )

        result = await self.sandbox_manager.execute(request)

        if result.success:
            return ToolResult(
                success=True,
                data={
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "exit_code": result.exit_code,
                    "sandbox_type": result.sandbox_type.value,
                    "execution_time_ms": result.execution_time_ms,
                },
            )
        else:
            return ToolResult(
                success=False,
                error=result.error or result.stderr,
                data={
                    "stdout": result.stdout,
                    "exit_code": result.exit_code,
                },
            )
