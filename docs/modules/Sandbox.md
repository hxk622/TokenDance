# Sandbox 设计文档

## 1. 核心目标

**为 Agent 提供安全、隔离、统一的代码执行环境**

```
统一入口 + 智能路由 + 安全隔离 + 容器池化 = 可信的执行基础设施
```

## 2. 解决的问题

### 2.1 发现的逻辑问题

| # | 问题 | 影响 |
|---|------|------|
| 1 | 工具系统与 Sandbox 割裂 | ShellTool 绕过 Sandbox 直接执行 |
| 2 | 风险评估不统一 | ShellTool 和 SandboxSecurityPolicy 两套系统 |
| 3 | ExecutionEngine 与 SandboxManager 重叠 | 职责不清晰 |
| 4 | AIO Sandbox 生命周期管理缺失 | 无容器池化，资源浪费 |
| 5 | Browser 操作两个入口 | BrowserTool vs AIO Sandbox 内置浏览器 |
| 6 | Subprocess 安全漏洞 | 黑名单易绕过 |
| 7 | 文件路径边界不一致 | 不同 Sandbox 使用不同路径 |

### 2.2 架构原则

```
                          Agent Tool 调用
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│                    WorldInterface.execute()                       │
│                    (工具是世界接口，不是插件)                        │
└──────────────────────────────────────────────────────────────────┘
                               │
            ┌──────────────────┼──────────────────┐
            ▼                  ▼                  ▼
       run_code            browser_*         file_ops
            │                  │                  │
            ▼                  ▼                  ▼
┌───────────────────┐  ┌───────────────┐  ┌───────────────┐
│  SandboxManager   │  │ BrowserRouter │  │ AgentWorkspace│
│  (统一代码执行)    │  │ (统一浏览器)   │  │ (统一文件系统)  │
└───────────────────┘  └───────────────┘  └───────────────┘
      │                      │
      ├─→ Subprocess         ├─→ External Browser
      ├─→ DockerSimple       └─→ AIO Sandbox Browser
      └─→ AIOSandboxPool
```

## 3. 统一风险评估系统

### 3.1 UnifiedRiskPolicy

**解决问题 #2：合并 ShellTool 和 SandboxSecurityPolicy 的风险评估**

```python
# app/sandbox/risk_policy.py

from enum import Enum
from dataclasses import dataclass
import re
import ast
from typing import Literal

class RiskLevel(Enum):
    """统一的风险级别"""
    SAFE = "safe"           # 只读操作，无副作用
    LOW = "low"             # 低风险，可自动执行
    MEDIUM = "medium"       # 中风险，建议确认
    HIGH = "high"           # 高风险，需要确认
    CRITICAL = "critical"   # 危险操作，强制确认或拒绝

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
    
    合并 Python 代码、JavaScript 代码、Shell 命令的风险评估
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
        "ls", "tree", "find", "pwd", "file", "stat",
        "cat", "head", "tail", "less", "more",
        "grep", "rg", "ag", "ack",
        "wc", "du", "echo", "which", "whereis",
    }
    
    # ==================== 核心方法 ====================
    
    @classmethod
    def assess(
        cls,
        content: str,
        content_type: Literal["python", "javascript", "shell", "browser"],
        params: dict = None
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
                detected_patterns=[]
            )
    
    @classmethod
    def _assess_python(cls, code: str) -> RiskAssessment:
        """评估 Python 代码"""
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
                detected_patterns=detected
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
                detected_patterns=detected
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
                detected_patterns=detected
            )
        
        # AST 深度检查（解决问题 #6：增强安全检查）
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in ['os', 'sys', 'subprocess', 'ctypes']:
                            detected.append(f"[AST] 导入 {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module.split('.')[0] in ['os', 'sys', 'subprocess']:
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
                detected_patterns=detected
            )
        
        # 安全
        return RiskAssessment(
            level=RiskLevel.SAFE,
            reason="未检测到风险",
            requires_confirmation=False,
            requires_isolation=False,
            suggested_sandbox="subprocess",
            detected_patterns=[]
        )
    
    @classmethod
    def _assess_shell(cls, command: str) -> RiskAssessment:
        """评估 Shell 命令"""
        import shlex
        import os
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
                detected_patterns=detected
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
                detected_patterns=detected
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
                        detected_patterns=[]
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
            detected_patterns=["非白名单"]
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
                detected_patterns=detected
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
                detected_patterns=detected
            )
        
        return RiskAssessment(
            level=RiskLevel.SAFE,
            reason="未检测到风险",
            requires_confirmation=False,
            requires_isolation=False,
            suggested_sandbox="subprocess",
            detected_patterns=[]
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
                    detected_patterns=[desc]
                )
        
        return RiskAssessment(
            level=RiskLevel.LOW,
            reason="普通浏览器操作",
            requires_confirmation=False,
            requires_isolation=False,
            suggested_sandbox="aio_sandbox",
            detected_patterns=[]
        )
```

## 4. 统一文件路径

### 4.1 AgentWorkspace

**解决问题 #7：统一所有 Sandbox 类型的文件路径**

```python
# app/sandbox/workspace.py

from pathlib import Path
from dataclasses import dataclass
from typing import Optional
import shutil

@dataclass
class WorkspaceConfig:
    """工作空间配置"""
    base_dir: str = "/var/tokendance/workspaces"
    max_size_mb: int = 1024
    cleanup_after_hours: int = 24

class AgentWorkspace:
    """Agent 统一工作空间
    
    解决问题：
    - DockerSimple 挂载 /workspace
    - AIOSandbox 使用 /home/gem/workspace
    - ShellTool 使用 os.getcwd()
    
    统一为：
    - 宿主机: /var/tokendance/workspaces/{session_id}/
    - 容器内: /workspace (Volume 挂载)
    """
    
    def __init__(self, session_id: str, config: Optional[WorkspaceConfig] = None):
        self.session_id = session_id
        self.config = config or WorkspaceConfig()
        
        # 宿主机路径
        self.host_path = Path(self.config.base_dir) / session_id
        
        # 容器内路径（统一）
        self.container_path = "/workspace"
        
        self._init_workspace()
    
    def _init_workspace(self):
        """初始化目录结构"""
        self.host_path.mkdir(parents=True, exist_ok=True)
        
        for subdir in ["code", "data", "output", "artifacts", "temp", ".memory"]:
            (self.host_path / subdir).mkdir(exist_ok=True)
        
        # 初始化 Working Memory
        for f in ["task_plan.md", "findings.md", "progress.md"]:
            filepath = self.host_path / ".memory" / f
            if not filepath.exists():
                filepath.write_text(f"# {f.replace('.md', '').replace('_', ' ').title()}\n\n")
    
    def get_host_path(self, relative: str = "") -> Path:
        """获取宿主机路径"""
        return self.host_path / relative if relative else self.host_path
    
    def get_container_path(self, relative: str = "") -> str:
        """获取容器内路径"""
        return f"{self.container_path}/{relative}" if relative else self.container_path
    
    def get_volume_mount(self) -> dict:
        """获取 Docker Volume 挂载配置"""
        return {
            str(self.host_path): {"bind": self.container_path, "mode": "rw"}
        }
    
    def write_file(self, relative: str, content: str | bytes):
        """写入文件"""
        filepath = self.host_path / relative
        filepath.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            filepath.write_bytes(content)
        else:
            filepath.write_text(content)
    
    def read_file(self, relative: str) -> str:
        """读取文件"""
        return (self.host_path / relative).read_text()
    
    def list_files(self, relative: str = "") -> list[str]:
        """列出文件"""
        dirpath = self.host_path / relative if relative else self.host_path
        if not dirpath.exists():
            return []
        return [str(p.relative_to(self.host_path)) for p in dirpath.rglob("*") if p.is_file()]
    
    def cleanup(self):
        """清理工作空间"""
        if self.host_path.exists():
            shutil.rmtree(self.host_path)
```

## 5. Sandbox 类型与执行器

### 5.1 类型定义

```python
# app/sandbox/types.py

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any

class SandboxType(Enum):
    """Sandbox 类型"""
    SUBPROCESS = "subprocess"      # 最轻量
    DOCKER_SIMPLE = "docker_simple"  # Docker 隔离
    AIO_SANDBOX = "aio_sandbox"    # 完整环境

@dataclass
class ExecutionRequest:
    """执行请求"""
    code: str
    language: str = "python"  # python | javascript | shell
    timeout: int = 30
    sandbox_type: Optional[SandboxType] = None  # None = 自动选择
    session_id: str = ""
    max_memory_mb: int = 512
    max_output_mb: int = 10

@dataclass
class ExecutionResult:
    """执行结果"""
    success: bool
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    error: Optional[str] = None
    sandbox_type: SandboxType = SandboxType.SUBPROCESS
    execution_time_ms: float = 0.0
    files_created: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "exit_code": self.exit_code,
            "error": self.error,
            "sandbox_type": self.sandbox_type.value,
            "execution_time_ms": self.execution_time_ms,
        }
```

### 5.2 SandboxManager - 统一入口

**解决问题 #1：工具系统与 Sandbox 统一**

```python
# app/sandbox/manager.py

import logging
from typing import Optional
from .types import SandboxType, ExecutionRequest, ExecutionResult
from .risk_policy import UnifiedRiskPolicy, RiskLevel
from .workspace import AgentWorkspace
from .pool import AIOSandboxPool

logger = logging.getLogger(__name__)

class SandboxManager:
    """Sandbox 管理器 - 统一代码执行入口
    
    解决问题 #1：所有代码执行都通过这里
    
    职责：
    1. 接收执行请求
    2. 风险评估（使用 UnifiedRiskPolicy）
    3. 智能路由到合适的 Sandbox
    4. 执行并返回结果
    """
    
    def __init__(
        self,
        session_id: str,
        workspace: Optional[AgentWorkspace] = None,
        aio_pool: Optional[AIOSandboxPool] = None
    ):
        self.session_id = session_id
        self.workspace = workspace or AgentWorkspace(session_id)
        self.aio_pool = aio_pool
        
        # 懒加载执行器
        self._subprocess = None
        self._docker_simple = None
        self._aio_sandbox = None
    
    async def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """执行代码 - 统一入口"""
        
        # 1. 风险评估
        content_type = "shell" if request.language == "shell" else request.language
        risk = UnifiedRiskPolicy.assess(request.code, content_type)
        
        logger.info(f"Risk: {risk.level.value}, suggested: {risk.suggested_sandbox}")
        
        # 2. 检查是否拒绝
        if risk.suggested_sandbox == "REJECT":
            return ExecutionResult(
                success=False,
                error=f"执行被拒绝: {risk.reason}",
                stderr=f"检测到: {risk.detected_patterns}",
                exit_code=-1
            )
        
        # 3. 确定 Sandbox 类型
        sandbox_type = request.sandbox_type or self._select_sandbox(risk, request)
        logger.info(f"Selected sandbox: {sandbox_type.value}")
        
        # 4. 路由执行
        if sandbox_type == SandboxType.SUBPROCESS:
            return await self._execute_subprocess(request)
        elif sandbox_type == SandboxType.DOCKER_SIMPLE:
            return await self._execute_docker_simple(request)
        elif sandbox_type == SandboxType.AIO_SANDBOX:
            return await self._execute_aio_sandbox(request)
        else:
            raise ValueError(f"Unknown sandbox: {sandbox_type}")
    
    def _select_sandbox(self, risk, request: ExecutionRequest) -> SandboxType:
        """智能选择 Sandbox"""
        
        # 根据风险建议
        if risk.suggested_sandbox == "aio_sandbox":
            return SandboxType.AIO_SANDBOX
        
        if risk.requires_isolation:
            if self._needs_browser(request.code):
                return SandboxType.AIO_SANDBOX
            return SandboxType.DOCKER_SIMPLE
        
        return SandboxType.SUBPROCESS
    
    def _needs_browser(self, code: str) -> bool:
        """检查是否需要浏览器"""
        keywords = ["selenium", "playwright", "puppeteer", "browser", "screenshot"]
        return any(kw in code.lower() for kw in keywords)
    
    async def _execute_subprocess(self, request: ExecutionRequest) -> ExecutionResult:
        """Subprocess 执行"""
        if not self._subprocess:
            from .executors.subprocess_executor import SubprocessExecutor
            self._subprocess = SubprocessExecutor(self.workspace)
        return await self._subprocess.execute(request)
    
    async def _execute_docker_simple(self, request: ExecutionRequest) -> ExecutionResult:
        """DockerSimple 执行"""
        if not self._docker_simple:
            from .executors.docker_simple import DockerSimpleSandbox
            self._docker_simple = DockerSimpleSandbox(self.session_id, self.workspace)
        return await self._docker_simple.execute(request)
    
    async def _execute_aio_sandbox(self, request: ExecutionRequest) -> ExecutionResult:
        """AIO Sandbox 执行"""
        if self.aio_pool:
            sandbox = await self.aio_pool.acquire(self.session_id)
            try:
                return await sandbox.execute(request)
            finally:
                await self.aio_pool.release(self.session_id)
        else:
            if not self._aio_sandbox:
                from .executors.aio_sandbox import AIOSandboxClient
                self._aio_sandbox = AIOSandboxClient(self.session_id, self.workspace)
            return await self._aio_sandbox.execute(request)
    
    async def cleanup(self):
        """清理资源"""
        if self._subprocess:
            self._subprocess.cleanup()
        if self._docker_simple:
            await self._docker_simple.cleanup()
        if self._aio_sandbox:
            await self._aio_sandbox.cleanup()
```

## 6. AIO Sandbox 容器池

**解决问题 #4：容器生命周期管理**

```python
# app/sandbox/pool.py

import asyncio
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional
from collections import OrderedDict

logger = logging.getLogger(__name__)

@dataclass
class PooledSandbox:
    """池化的 Sandbox 实例"""
    sandbox: "AIOSandboxClient"
    session_id: str
    created_at: datetime = field(default_factory=datetime.now)
    last_used_at: datetime = field(default_factory=datetime.now)
    use_count: int = 0
    is_busy: bool = False

@dataclass
class PoolConfig:
    """池配置"""
    max_instances: int = 10           # 最大实例数
    min_instances: int = 2            # 最小预热数
    idle_timeout_seconds: int = 300   # 5分钟空闲超时
    max_use_count: int = 100          # 单实例最大使用次数
    cleanup_interval: int = 60        # 清理检查间隔

class AIOSandboxPool:
    """AIO Sandbox 容器池
    
    策略：
    - 维护 N 个热实例，按需分配
    - Session 绑定：同一 Session 复用同一实例
    - 空闲回收：超时销毁
    - 使用次数限制：防止内存泄漏
    """
    
    def __init__(self, config: Optional[PoolConfig] = None, base_url: str = "http://localhost:8080"):
        self.config = config or PoolConfig()
        self.base_url = base_url
        
        self._session_map: dict[str, PooledSandbox] = {}
        self._idle_queue: OrderedDict[str, PooledSandbox] = OrderedDict()
        self._semaphore = asyncio.Semaphore(self.config.max_instances)
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start(self):
        """启动池"""
        self._running = True
        await self._warmup()
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info(f"AIOSandboxPool started, min={self.config.min_instances}")
    
    async def stop(self):
        """停止池"""
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
        
        async with self._lock:
            for pooled in list(self._session_map.values()):
                await self._destroy(pooled)
            self._session_map.clear()
            self._idle_queue.clear()
    
    async def _warmup(self):
        """预热实例"""
        for i in range(self.config.min_instances):
            try:
                pooled = await self._create(f"warmup_{i}")
                async with self._lock:
                    self._idle_queue[pooled.session_id] = pooled
            except Exception as e:
                logger.error(f"Warmup {i} failed: {e}")
    
    async def acquire(self, session_id: str) -> "AIOSandboxClient":
        """获取实例"""
        async with self._lock:
            # 已有绑定
            if session_id in self._session_map:
                pooled = self._session_map[session_id]
                pooled.is_busy = True
                pooled.last_used_at = datetime.now()
                pooled.use_count += 1
                return pooled.sandbox
            
            # 从空闲队列获取
            if self._idle_queue:
                old_id, pooled = self._idle_queue.popitem(last=False)
                
                if pooled.use_count >= self.config.max_use_count:
                    await self._destroy(pooled)
                    pooled = await self._create(session_id)
                else:
                    pooled.session_id = session_id
                
                pooled.is_busy = True
                pooled.last_used_at = datetime.now()
                pooled.use_count += 1
                self._session_map[session_id] = pooled
                return pooled.sandbox
        
        # 创建新实例
        await self._semaphore.acquire()
        try:
            pooled = await self._create(session_id)
            async with self._lock:
                pooled.is_busy = True
                self._session_map[session_id] = pooled
            return pooled.sandbox
        except Exception:
            self._semaphore.release()
            raise
    
    async def release(self, session_id: str):
        """释放实例"""
        async with self._lock:
            if session_id in self._session_map:
                pooled = self._session_map[session_id]
                pooled.is_busy = False
                pooled.last_used_at = datetime.now()
    
    async def _create(self, session_id: str) -> PooledSandbox:
        """创建实例"""
        from .executors.aio_sandbox import AIOSandboxClient
        from .workspace import AgentWorkspace
        
        workspace = AgentWorkspace(session_id)
        sandbox = AIOSandboxClient(session_id, workspace, base_url=self.base_url)
        await sandbox.connect()
        
        return PooledSandbox(sandbox=sandbox, session_id=session_id)
    
    async def _destroy(self, pooled: PooledSandbox):
        """销毁实例"""
        try:
            await pooled.sandbox.disconnect()
        except Exception as e:
            logger.error(f"Destroy failed: {e}")
        finally:
            self._semaphore.release()
    
    async def _cleanup_loop(self):
        """清理循环"""
        while self._running:
            try:
                await asyncio.sleep(self.config.cleanup_interval)
                await self._cleanup_idle()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
    
    async def _cleanup_idle(self):
        """清理空闲实例"""
        cutoff = datetime.now() - timedelta(seconds=self.config.idle_timeout_seconds)
        to_destroy = []
        
        async with self._lock:
            for sid, pooled in list(self._session_map.items()):
                if not pooled.is_busy and pooled.last_used_at < cutoff:
                    to_destroy.append(pooled)
                    del self._session_map[sid]
            
            # 保持最小实例
            current = len(self._session_map) + len(self._idle_queue)
            keep = max(0, self.config.min_instances - current)
            to_destroy = to_destroy[keep:]
        
        for pooled in to_destroy:
            await self._destroy(pooled)
            logger.info(f"Destroyed idle: {pooled.session_id}")
    
    def get_stats(self) -> dict:
        """获取统计"""
        busy = sum(1 for p in self._session_map.values() if p.is_busy)
        return {
            "total": len(self._session_map),
            "busy": busy,
            "idle": len(self._session_map) - busy,
            "max": self.config.max_instances,
        }
```

## 7. Browser 路由

**解决问题 #5：统一浏览器入口**

```python
# app/sandbox/browser_router.py

import logging
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Any

logger = logging.getLogger(__name__)

class BrowserBackend(Enum):
    """浏览器后端"""
    EXTERNAL = "external"       # 外部浏览器 (agent-browser)
    AIO_SANDBOX = "aio_sandbox" # AIO Sandbox 内置

@dataclass
class BrowserAction:
    action: str  # navigate, click, fill, screenshot, close
    params: dict

@dataclass
class BrowserResult:
    success: bool
    data: Any = None
    error: Optional[str] = None
    screenshot: Optional[bytes] = None

class BrowserRouter:
    """浏览器路由器
    
    路由策略：
    - 需要与 Sandbox 共享文件系统 → AIO Sandbox
    - Deep Research → AIO Sandbox（结果持久化）
    - 简单操作 → External（更轻量）
    """
    
    def __init__(self, session_id: str, aio_sandbox=None, external_browser=None):
        self.session_id = session_id
        self._aio = aio_sandbox
        self._external = external_browser
    
    def select_backend(self, context: dict) -> BrowserBackend:
        """选择后端"""
        if context.get("needs_file_access"):
            return BrowserBackend.AIO_SANDBOX
        if context.get("is_research"):
            return BrowserBackend.AIO_SANDBOX
        return BrowserBackend.EXTERNAL
    
    async def execute(
        self,
        action: BrowserAction,
        backend: Optional[BrowserBackend] = None,
        context: dict = None
    ) -> BrowserResult:
        """执行浏览器操作"""
        backend = backend or self.select_backend(context or {})
        logger.info(f"Browser: {action.action} via {backend.value}")
        
        if backend == BrowserBackend.AIO_SANDBOX:
            return await self._exec_aio(action)
        return await self._exec_external(action)
    
    async def _exec_aio(self, action: BrowserAction) -> BrowserResult:
        """AIO Sandbox 浏览器"""
        if not self._aio:
            return BrowserResult(success=False, error="AIO Sandbox 不可用")
        
        try:
            if action.action == "navigate":
                await self._aio.browser_navigate(action.params["url"])
                return BrowserResult(success=True)
            elif action.action == "screenshot":
                img = await self._aio.browser_screenshot(action.params.get("url"))
                return BrowserResult(success=True, screenshot=img)
            elif action.action == "click":
                await self._aio.browser_click(action.params["selector"])
                return BrowserResult(success=True)
            elif action.action == "fill":
                await self._aio.browser_fill(action.params["selector"], action.params["value"])
                return BrowserResult(success=True)
            else:
                return BrowserResult(success=False, error=f"未知操作: {action.action}")
        except Exception as e:
            return BrowserResult(success=False, error=str(e))
    
    async def _exec_external(self, action: BrowserAction) -> BrowserResult:
        """外部浏览器"""
        if not self._external:
            from app.agent.tools.builtin.browser_ops import create_browser_session
            self._external = await create_browser_session(self.session_id)
        
        try:
            if action.action == "navigate":
                result = await self._external.navigate(action.params["url"])
                return BrowserResult(success=True, data=result)
            elif action.action == "screenshot":
                img = await self._external.screenshot()
                return BrowserResult(success=True, screenshot=img)
            elif action.action == "close":
                await self._external.close()
                return BrowserResult(success=True)
            else:
                return BrowserResult(success=False, error=f"未知操作: {action.action}")
        except Exception as e:
            return BrowserResult(success=False, error=str(e))
    
    async def cleanup(self):
        if self._external:
            await self._external.close()
```

## 8. ExecutionEngine 集成

**解决问题 #3：明确 ExecutionEngine 与 SandboxManager 的关系**

```python
# app/execution/engine.py

import logging
from enum import Enum
from dataclasses import dataclass
from typing import Optional

from app.sandbox.manager import SandboxManager
from app.sandbox.browser_router import BrowserRouter, BrowserAction
from app.sandbox.workspace import AgentWorkspace
from app.sandbox.pool import AIOSandboxPool
from app.sandbox.types import ExecutionRequest, ExecutionResult

logger = logging.getLogger(__name__)

class ActionType(Enum):
    CODE_EXECUTION = "code_execution"
    WEB_BROWSING = "web_browsing"
    FILE_OPERATION = "file_operation"

@dataclass
class Action:
    type: ActionType
    data: dict

class ExecutionEngine:
    """统一执行引擎
    
    职责：高层调度器
    - code_execution → SandboxManager（不重复实现）
    - web_browsing → BrowserRouter
    - file_operation → AgentWorkspace
    
    与 SandboxManager 的关系：
    - ExecutionEngine 是调度器
    - SandboxManager 是代码执行的具体实现
    - ExecutionEngine 调用 SandboxManager
    """
    
    def __init__(self, session_id: str, aio_pool: Optional[AIOSandboxPool] = None):
        self.session_id = session_id
        self.workspace = AgentWorkspace(session_id)
        self.sandbox_manager = SandboxManager(session_id, self.workspace, aio_pool)
        self.browser_router = BrowserRouter(session_id)
    
    async def execute(self, action: Action) -> ExecutionResult:
        """执行动作"""
        logger.info(f"ExecutionEngine: {action.type.value}")
        
        try:
            if action.type == ActionType.CODE_EXECUTION:
                return await self._exec_code(action)
            elif action.type == ActionType.WEB_BROWSING:
                return await self._exec_browser(action)
            elif action.type == ActionType.FILE_OPERATION:
                return await self._exec_file(action)
            else:
                return ExecutionResult(success=False, error=f"Unknown: {action.type}")
        except Exception as e:
            logger.error(f"Execution failed: {e}", exc_info=True)
            return ExecutionResult(success=False, error=str(e))
    
    async def _exec_code(self, action: Action) -> ExecutionResult:
        """代码执行 - 委托给 SandboxManager"""
        request = ExecutionRequest(
            code=action.data["code"],
            language=action.data.get("language", "python"),
            timeout=action.data.get("timeout", 30),
            session_id=self.session_id
        )
        return await self.sandbox_manager.execute(request)
    
    async def _exec_browser(self, action: Action) -> ExecutionResult:
        """浏览器操作 - 委托给 BrowserRouter"""
        browser_action = BrowserAction(
            action=action.data["action"],
            params=action.data.get("params", {})
        )
        context = {
            "needs_file_access": action.data.get("needs_file_access", False),
            "is_research": action.data.get("is_research", False)
        }
        result = await self.browser_router.execute(browser_action, context=context)
        return ExecutionResult(
            success=result.success,
            stdout=str(result.data) if result.data else "",
            error=result.error
        )
    
    async def _exec_file(self, action: Action) -> ExecutionResult:
        """文件操作 - 使用 AgentWorkspace"""
        op = action.data["operation"]
        path = action.data["path"]
        
        try:
            if op == "read":
                content = self.workspace.read_file(path)
                return ExecutionResult(success=True, stdout=content)
            elif op == "write":
                self.workspace.write_file(path, action.data["content"])
                return ExecutionResult(success=True)
            elif op == "list":
                files = self.workspace.list_files(path)
                return ExecutionResult(success=True, stdout="\n".join(files))
            else:
                return ExecutionResult(success=False, error=f"Unknown op: {op}")
        except Exception as e:
            return ExecutionResult(success=False, error=str(e))
    
    async def cleanup(self):
        await self.sandbox_manager.cleanup()
        await self.browser_router.cleanup()
```

## 9. 工具集成

### 9.1 更新 run_code 工具

```python
# app/agent/tools/builtin/run_code.py

from pydantic import BaseModel, Field
from ..base import BaseTool, ToolResult
from ..risk import RiskLevel
from app.sandbox.manager import SandboxManager
from app.sandbox.types import ExecutionRequest
from app.sandbox.risk_policy import UnifiedRiskPolicy

class RunCodeToolArgs(BaseModel):
    code: str = Field(..., description="要执行的代码")
    language: str = Field("python", description="python | javascript | shell")
    timeout: int = Field(30, ge=1, le=300, description="超时秒数")

class RunCodeTool(BaseTool):
    """代码执行工具 - 核心4工具之一
    
    通过 SandboxManager 执行，自动风险评估和 Sandbox 选择
    """
    
    name = "run_code"
    description = "在安全沙箱中执行代码"
    args_schema = RunCodeToolArgs
    
    def __init__(self, sandbox_manager: SandboxManager):
        super().__init__()
        self.sandbox_manager = sandbox_manager
    
    def get_risk_level(self, **kwargs) -> RiskLevel:
        code = kwargs.get("code", "")
        lang = kwargs.get("language", "python")
        content_type = "shell" if lang == "shell" else lang
        assessment = UnifiedRiskPolicy.assess(code, content_type)
        
        level_map = {
            "safe": RiskLevel.LOW, "low": RiskLevel.LOW,
            "medium": RiskLevel.MEDIUM, "high": RiskLevel.HIGH,
            "critical": RiskLevel.CRITICAL
        }
        return level_map.get(assessment.level.value, RiskLevel.HIGH)
    
    def requires_confirmation_for(self, **kwargs) -> bool:
        code = kwargs.get("code", "")
        lang = kwargs.get("language", "python")
        content_type = "shell" if lang == "shell" else lang
        return UnifiedRiskPolicy.assess(code, content_type).requires_confirmation
    
    async def execute(self, code: str, language: str = "python", timeout: int = 30) -> ToolResult:
        request = ExecutionRequest(
            code=code,
            language=language,
            timeout=timeout,
            session_id=self.sandbox_manager.session_id
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
                }
            )
        else:
            return ToolResult(
                success=False,
                error=result.error or result.stderr,
                data={"stdout": result.stdout, "exit_code": result.exit_code}
            )
```

## 10. 部署配置

### 10.1 Docker Compose

```yaml
# docker-compose.yml

services:
  backend:
    build: ./backend
    environment:
      - SANDBOX_AIO_URL=http://aio-sandbox:8080
      - SANDBOX_WORKSPACE_BASE=/var/tokendance/workspaces
    volumes:
      - workspaces:/var/tokendance/workspaces
    depends_on:
      - aio-sandbox

  aio-sandbox:
    image: ghcr.io/agent-infra/sandbox:latest
    security_opt:
      - seccomp=unconfined
    ports:
      - "8080:8080"
    volumes:
      - workspaces:/var/tokendance/workspaces
    environment:
      - MAX_CONCURRENT_SESSIONS=10
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2'

volumes:
  workspaces:
```

## 11. 总结

### 11.1 问题解决对照表

| # | 问题 | 解决方案 | 关键模块 |
|---|------|---------|---------|
| 1 | 工具与 Sandbox 割裂 | run_code 通过 SandboxManager | `RunCodeTool` → `SandboxManager` |
| 2 | 风险评估不统一 | UnifiedRiskPolicy | `risk_policy.py` |
| 3 | Engine 与 Manager 重叠 | Engine 调用 Manager | `ExecutionEngine` → `SandboxManager` |
| 4 | AIO 生命周期缺失 | AIOSandboxPool | `pool.py` |
| 5 | Browser 两个入口 | BrowserRouter | `browser_router.py` |
| 6 | Subprocess 漏洞 | AST 检查 + 严格模式 | `UnifiedRiskPolicy._assess_python()` |
| 7 | 文件路径不一致 | AgentWorkspace | `workspace.py` |

### 11.2 最终架构

```
┌──────────────────────────────────────────────────────────────────┐
│                           Agent                                   │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                      WorldInterface                               │
│                    (工具是世界接口)                                │
└────────────────────────────┬─────────────────────────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
    run_code             browser_*           file_ops
         │                   │                   │
         ▼                   ▼                   ▼
┌──────────────────────────────────────────────────────────────────┐
│                     ExecutionEngine                               │
│                    (统一执行调度器)                                │
└────────────────────────────┬─────────────────────────────────────┘
         │                   │                   │
         ▼                   ▼                   ▼
┌─────────────┐      ┌─────────────┐     ┌─────────────┐
│  Sandbox    │      │  Browser    │     │   Agent     │
│  Manager    │      │  Router     │     │  Workspace  │
└──────┬──────┘      └──────┬──────┘     └─────────────┘
       │                    │
       │  UnifiedRiskPolicy │
       │  (统一风险评估)     │
       │                    │
       ├─→ Subprocess       ├─→ External Browser
       ├─→ DockerSimple     └─→ AIO Sandbox Browser
       └─→ AIOSandboxPool
              │
              └─→ 容器池化管理
```
