"""
统一风险评估策略

合并 Python、JavaScript、Shell 命令的风险评估。

核心原则：
1. 静态分析用于提示，不作为安全边界
2. 非 SAFE 代码应在隔离环境执行
3. 支持 PERMISSIVE（开发）和 STRICT（生产）模式
"""

import ast
import re
from dataclasses import dataclass
from enum import Enum
from typing import Literal

from app.sandbox.types import SandboxType, SecurityMode


class RiskLevel(str, Enum):
    """风险等级"""

    SAFE = "safe"  # 只读操作，无副作用
    LOW = "low"  # 低风险，可自动执行
    MEDIUM = "medium"  # 中风险，建议确认
    HIGH = "high"  # 高风险，需要确认
    CRITICAL = "critical"  # 危险操作，强制确认或拒绝


@dataclass
class RiskAssessment:
    """风险评估结果"""

    level: RiskLevel
    reason: str
    requires_confirmation: bool
    requires_isolation: bool
    suggested_sandbox: str  # subprocess | docker_simple | aio_sandbox | REJECT
    detected_patterns: list[str]


class UnifiedRiskPolicy:
    """统一风险评估策略

    合并 Python 代码、JavaScript 代码、Shell 命令的风险评估。

    注意：静态分析可被绕过，因此：
    - 静态分析结果仅用于用户提示和日志
    - 真正的安全边界是 Docker/AIO Sandbox 隔离
    - SecurityMode 控制是否强制隔离
    """

    # ==================== Python 风险模式 ====================

    PYTHON_CRITICAL = [
        (r"__import__\s*\(", "动态导入"),
        (r"\beval\s*\(", "eval 执行"),
        (r"\bexec\s*\(", "exec 执行"),
        (r"\bcompile\s*\(", "compile 调用"),
        (r"__builtins__", "builtins 访问"),
        (r"getattr\s*\(.+__", "反射访问 dunder"),
        (r"os\.system\s*\(", "系统命令"),
        (r"subprocess\.", "subprocess 调用"),
        (r"popen\s*\(", "popen 调用"),
    ]

    PYTHON_HIGH = [
        (r"open\s*\(.+['\"]w", "文件写入"),
        (r"\.write\s*\(", "write 操作"),
        (r"shutil\.", "shutil 操作"),
        (r"requests\.", "网络请求"),
        (r"urllib\.", "urllib 请求"),
        (r"socket\.", "socket 操作"),
        (r"import\s+os\b", "os 模块"),
        (r"import\s+sys\b", "sys 模块"),
        (r"import\s+pickle\b", "pickle 反序列化"),
    ]

    PYTHON_MEDIUM = [
        (r"open\s*\(.+['\"]r", "文件读取"),
        (r"\.read\s*\(", "read 操作"),
        (r"json\.load", "JSON 加载"),
        (r"os\.environ", "环境变量"),
    ]

    # ==================== Shell 风险模式 ====================

    SHELL_CRITICAL = [
        (r"rm\s+-rf\s+/", "删除根目录"),
        (r"rm\s+-rf\s+~", "删除 home"),
        (r"dd\s+if=", "磁盘写入"),
        (r"mkfs\.", "格式化"),
        (r":\(\)\s*\{", "Fork bomb"),
        (r">\s*/dev/", "写入设备"),
        (r"curl.+\|\s*sh", "远程脚本"),
        (r"wget.+\|\s*sh", "远程脚本"),
    ]

    SHELL_HIGH = [
        (r"\brm\s+", "删除文件"),
        (r"\bmv\s+", "移动文件"),
        (r">\s*\w", "重定向写入"),
        (r"git\s+push", "git push"),
        (r"git.+--force", "git force"),
        (r"\bsudo\s+", "sudo"),
        (r"\bchmod\s+", "权限修改"),
    ]

    SHELL_SAFE_COMMANDS = {
        "ls",
        "tree",
        "find",
        "pwd",
        "file",
        "stat",
        "cat",
        "head",
        "tail",
        "less",
        "more",
        "grep",
        "rg",
        "ag",
        "ack",
        "wc",
        "du",
        "echo",
        "which",
        "whereis",
    }

    # ==================== 核心方法 ====================

    @classmethod
    def assess(
        cls,
        content: str,
        content_type: Literal["python", "javascript", "shell", "browser"],
        params: dict | None = None,
    ) -> RiskAssessment:
        """统一入口：评估任意类型内容的风险"""
        if content_type == "python":
            return cls._assess_python(content)
        elif content_type == "javascript":
            return cls._assess_javascript(content)
        elif content_type == "shell":
            return cls._assess_shell(content)
        elif content_type == "browser":
            return cls._assess_browser(content, params or {})
        else:
            return RiskAssessment(
                level=RiskLevel.HIGH,
                reason=f"未知类型: {content_type}",
                requires_confirmation=True,
                requires_isolation=True,
                suggested_sandbox="docker_simple",
                detected_patterns=[],
            )

    @classmethod
    def get_required_sandbox(
        cls, assessment: RiskAssessment, mode: SecurityMode = SecurityMode.STRICT
    ) -> SandboxType:
        """根据安全模式决定 Sandbox 类型

        这是真正的安全决策点，而非静态分析。

        Args:
            assessment: 风险评估结果
            mode: 安全模式

        Returns:
            SandboxType: 必须使用的 Sandbox 类型
        """
        # STRICT 模式：非 SAFE 全部用 Docker
        if mode == SecurityMode.STRICT:
            if assessment.level != RiskLevel.SAFE:
                if assessment.suggested_sandbox == "aio_sandbox":
                    return SandboxType.AIO_SANDBOX
                return SandboxType.DOCKER_SIMPLE

        # PERMISSIVE 模式：按静态分析建议
        if assessment.suggested_sandbox == "subprocess":
            return SandboxType.SUBPROCESS
        elif assessment.suggested_sandbox == "docker_simple":
            return SandboxType.DOCKER_SIMPLE
        elif assessment.suggested_sandbox == "aio_sandbox":
            return SandboxType.AIO_SANDBOX
        else:
            # REJECT 情况，返回最严格的隔离
            return SandboxType.DOCKER_SIMPLE

    @classmethod
    def _assess_python(cls, code: str) -> RiskAssessment:
        """评估 Python 代码

        注意：此方法可被绕过，仅用于提示！
        """
        detected = []

        # CRITICAL 检查
        for pattern, desc in cls.PYTHON_CRITICAL:
            if re.search(pattern, code, re.IGNORECASE):
                detected.append(f"[CRITICAL] {desc}")

        if detected:
            return RiskAssessment(
                level=RiskLevel.CRITICAL,
                reason="包含危险操作",
                requires_confirmation=True,
                requires_isolation=True,
                suggested_sandbox="docker_simple",
                detected_patterns=detected,
            )

        # HIGH 检查
        for pattern, desc in cls.PYTHON_HIGH:
            if re.search(pattern, code, re.IGNORECASE):
                detected.append(f"[HIGH] {desc}")

        if detected:
            return RiskAssessment(
                level=RiskLevel.HIGH,
                reason="包含高风险操作",
                requires_confirmation=True,
                requires_isolation=True,
                suggested_sandbox="docker_simple",
                detected_patterns=detected,
            )

        # MEDIUM 检查
        for pattern, desc in cls.PYTHON_MEDIUM:
            if re.search(pattern, code, re.IGNORECASE):
                detected.append(f"[MEDIUM] {desc}")

        if detected:
            return RiskAssessment(
                level=RiskLevel.MEDIUM,
                reason="包含中风险操作",
                requires_confirmation=False,
                requires_isolation=True,
                suggested_sandbox="docker_simple",
                detected_patterns=detected,
            )

        # AST 深度检查（增强但仍可绕过）
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in ["os", "sys", "subprocess", "ctypes"]:
                            detected.append(f"[AST] 导入 {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module.split(".")[0] in ["os", "sys", "subprocess"]:
                        detected.append(f"[AST] 从 {node.module} 导入")
        except SyntaxError:
            pass  # 语法错误时跳过

        if detected:
            return RiskAssessment(
                level=RiskLevel.HIGH,
                reason="AST 检测到危险导入",
                requires_confirmation=True,
                requires_isolation=True,
                suggested_sandbox="docker_simple",
                detected_patterns=detected,
            )

        # 安全
        return RiskAssessment(
            level=RiskLevel.SAFE,
            reason="未检测到风险",
            requires_confirmation=False,
            requires_isolation=False,
            suggested_sandbox="subprocess",
            detected_patterns=[],
        )

    @classmethod
    def _assess_shell(cls, command: str) -> RiskAssessment:
        """评估 Shell 命令"""
        import os
        import shlex

        detected = []

        # CRITICAL 检查
        for pattern, desc in cls.SHELL_CRITICAL:
            if re.search(pattern, command, re.IGNORECASE):
                detected.append(f"[CRITICAL] {desc}")

        if detected:
            return RiskAssessment(
                level=RiskLevel.CRITICAL,
                reason="危险命令，已拒绝",
                requires_confirmation=True,
                requires_isolation=True,
                suggested_sandbox="REJECT",
                detected_patterns=detected,
            )

        # HIGH 检查
        for pattern, desc in cls.SHELL_HIGH:
            if re.search(pattern, command, re.IGNORECASE):
                detected.append(f"[HIGH] {desc}")

        if detected:
            return RiskAssessment(
                level=RiskLevel.HIGH,
                reason="高风险命令",
                requires_confirmation=True,
                requires_isolation=True,
                suggested_sandbox="docker_simple",
                detected_patterns=detected,
            )

        # 解析主命令
        try:
            parts = shlex.split(command)
            if parts:
                main_cmd = os.path.basename(parts[0])
                if main_cmd in cls.SHELL_SAFE_COMMANDS:
                    return RiskAssessment(
                        level=RiskLevel.SAFE,
                        reason=f"安全命令: {main_cmd}",
                        requires_confirmation=False,
                        requires_isolation=False,
                        suggested_sandbox="subprocess",
                        detected_patterns=[],
                    )
        except ValueError:
            pass

        # 默认中风险
        return RiskAssessment(
            level=RiskLevel.MEDIUM,
            reason="非白名单命令",
            requires_confirmation=False,
            requires_isolation=True,
            suggested_sandbox="docker_simple",
            detected_patterns=["非白名单"],
        )

    @classmethod
    def _assess_javascript(cls, code: str) -> RiskAssessment:
        """评估 JavaScript 代码"""
        detected = []

        js_critical = [
            (r"\beval\s*\(", "eval"),
            (r"new\s+Function", "动态函数"),
            (r"child_process", "子进程"),
        ]

        js_high = [
            (r"require\s*\(['\"]fs", "fs 模块"),
            (r"require\s*\(['\"]http", "http 模块"),
            (r"\bfetch\s*\(", "网络请求"),
        ]

        for pattern, desc in js_critical:
            if re.search(pattern, code, re.IGNORECASE):
                detected.append(f"[CRITICAL] {desc}")

        if detected:
            return RiskAssessment(
                level=RiskLevel.CRITICAL,
                reason="危险操作",
                requires_confirmation=True,
                requires_isolation=True,
                suggested_sandbox="docker_simple",
                detected_patterns=detected,
            )

        for pattern, desc in js_high:
            if re.search(pattern, code, re.IGNORECASE):
                detected.append(f"[HIGH] {desc}")

        if detected:
            return RiskAssessment(
                level=RiskLevel.HIGH,
                reason="高风险操作",
                requires_confirmation=True,
                requires_isolation=True,
                suggested_sandbox="docker_simple",
                detected_patterns=detected,
            )

        return RiskAssessment(
            level=RiskLevel.SAFE,
            reason="未检测到风险",
            requires_confirmation=False,
            requires_isolation=False,
            suggested_sandbox="subprocess",
            detected_patterns=[],
        )

    @classmethod
    def _assess_browser(cls, action: str, params: dict) -> RiskAssessment:
        """评估浏览器操作"""
        action_str = f"{action} {str(params)}".lower()

        high_patterns = [
            (r"password", "密码操作"),
            (r"credit", "信用卡"),
            (r"pay", "支付"),
        ]

        for pattern, desc in high_patterns:
            if re.search(pattern, action_str):
                return RiskAssessment(
                    level=RiskLevel.HIGH,
                    reason=f"敏感操作: {desc}",
                    requires_confirmation=True,
                    requires_isolation=False,
                    suggested_sandbox="aio_sandbox",
                    detected_patterns=[desc],
                )

        return RiskAssessment(
            level=RiskLevel.LOW,
            reason="普通浏览器操作",
            requires_confirmation=False,
            requires_isolation=False,
            suggested_sandbox="aio_sandbox",
            detected_patterns=[],
        )
