# Sandbox设计文档

## 1. 核心目标

**为Agent提供安全、隔离、多层次的代码执行环境**

```
安全隔离 + 资源限制 + 可观测性 + 渐进式能力 = 可信的代码执行
```

## 2. 混合架构设计

### 2.0 设计哲学：根据任务复杂度选择 Sandbox

```
任务类型              Sandbox选择            启动时间    资源占用    能力范围
─────────────────────────────────────────────────────────────────────────────
简单计算              Subprocess             ~0ms        极低        Python/JS基础
安全隔离              DockerSimple          ~100ms       低         代码执行+文件
浏览器自动化          AIOSandbox            ~3-5s        高         全功能
Web研究+截图          AIOSandbox            ~3-5s        高         Browser+File+MCP
Coworker本地操作      AIOSandbox(可选)      ~3-5s        高         隔离用户数据
```

**核心原则**：
1. **渐进式增强**：简单任务用轻量方案，复杂任务用重量级方案
2. **用户体验优先**：需要浏览器/可视化时，10个并发 AIO Sandbox 也值得
3. **安全底线**：任何涉及用户数据/网络访问的代码，必须隔离

### 2.1 Sandbox 类型

#### 2.1.1 Subprocess Sandbox（最轻量）

**适用场景**：
- 简单计算：数学运算、字符串处理、JSON 解析
- 低风险代码：已验证的工具脚本
- 快速原型：开发测试阶段

**限制**：
- 黑名单过滤（`os`, `subprocess`, `eval`, `exec`）
- 超时控制（默认 10s）
- 输出大小限制（10MB）

**实现**：当前 `executor.py` 实现

#### 2.1.2 DockerSimple Sandbox（轻量 Docker）

**适用场景**：
- 需要安全隔离的代码执行
- 文件系统操作（读写、转换）
- 标准库 + 常用第三方库（pandas, numpy, requests）

**特点**：
- 完整 Docker 隔离（网络、文件系统、进程）
- 资源限制（内存 512MB, CPU 50%）
- Volume 挂载工作空间
- 容器复用（Session 级）

```python
# app/sandbox/docker_simple.py

class DockerSimpleSandbox:
    """轻量 Docker 沙箱执行器"""
    
    # 基础镜像
    BASE_IMAGES = {
        "python": "python:3.11-slim",
        "node": "node:20-alpine",
        "shell": "ubuntu:22.04"
    }
    
    # 资源限制
    DEFAULT_LIMITS = {
        "memory": "512m",
        "cpu_quota": 50000,  # 50% CPU
        "pids_limit": 100,
        "network": "none",  # 默认无网络
        "read_only": True
    }
    
    def __init__(self, session_id: str, filesystem: AgentFileSystem):
        self.session_id = session_id
        self.fs = filesystem
        self.container = None
        self.container_name = f"tokendance_sandbox_{session_id[:8]}"
    
    async def create_container(self, language: str = "python"):
        """创建沙箱容器"""
        
        import docker
        client = docker.from_env()
        
        # 挂载工作空间
        workspace_path = self.fs.get_workspace_path(self.session_id)
        
        self.container = client.containers.create(
            image=self.BASE_IMAGES[language],
            name=self.container_name,
            
            # 资源限制
            mem_limit=self.DEFAULT_LIMITS["memory"],
            cpu_quota=self.DEFAULT_LIMITS["cpu_quota"],
            pids_limit=self.DEFAULT_LIMITS["pids_limit"],
            
            # 安全设置
            security_opt=["no-new-privileges"],
            cap_drop=["ALL"],
            cap_add=["CHOWN", "SETUID", "SETGID"],  # 最小权限
            read_only=self.DEFAULT_LIMITS["read_only"],
            
            # 网络隔离
            network_mode=self.DEFAULT_LIMITS["network"],
            
            # 挂载卷
            volumes={
                workspace_path: {
                    "bind": "/workspace",
                    "mode": "rw"
                },
                # 临时目录（可写）
                f"/tmp/tokendance_{self.session_id}": {
                    "bind": "/tmp",
                    "mode": "rw"
                }
            },
            
            # 工作目录
            working_dir="/workspace",
            
            # 自动清理
            detach=True,
            remove=False  # 手动清理以便查看日志
        )
        
        self.container.start()
        
        return self.container.id
    
    async def execute_code(
        self,
        code: str,
        language: str = "python",
        timeout: int = 30
    ) -> ExecutionResult:
        """执行代码"""
        
        try:
            # 1. 创建容器（如果不存在）
            if not self.container:
                await self.create_container(language)
            
            # 2. 写入代码文件
            code_file = f"/workspace/temp_{uuid4().hex[:8]}.py"
            await self.fs.write(code_file, code)
            
            # 3. 执行
            exec_result = self.container.exec_run(
                cmd=self._get_exec_command(language, code_file),
                stdout=True,
                stderr=True,
                stream=False,
                demux=True,
                timeout=timeout
            )
            
            stdout, stderr = exec_result.output
            
            # 4. 解析结果
            return ExecutionResult(
                success=exec_result.exit_code == 0,
                stdout=stdout.decode() if stdout else "",
                stderr=stderr.decode() if stderr else "",
                exit_code=exec_result.exit_code,
                execution_time_ms=...
            )
            
        except docker.errors.ContainerError as e:
            return ExecutionResult(
                success=False,
                error=f"Container error: {str(e)}"
            )
        except TimeoutError:
            # 超时，强制停止容器
            self.container.stop(timeout=1)
            return ExecutionResult(
                success=False,
                error=f"Execution timeout ({timeout}s)"
            )
    
    async def execute_shell_command(
        self,
        command: str,
        timeout: int = 10
    ) -> ExecutionResult:
        """执行Shell命令"""
        
        # 危险命令黑名单
        BLACKLIST = ["rm -rf /", "dd if=", ":(){ :|:& };:", "mkfs"]
        
        for dangerous in BLACKLIST:
            if dangerous in command:
                return ExecutionResult(
                    success=False,
                    error=f"Dangerous command blocked: {dangerous}"
                )
        
        exec_result = self.container.exec_run(
            cmd=["sh", "-c", command],
            stdout=True,
            stderr=True,
            timeout=timeout
        )
        
        return ExecutionResult(
            success=exec_result.exit_code == 0,
            stdout=exec_result.output.decode(),
            exit_code=exec_result.exit_code
        )
    
    async def cleanup(self):
        """清理容器"""
        if self.container:
            try:
                self.container.stop(timeout=5)
                self.container.remove()
            except Exception as e:
                logger.error(f"Failed to cleanup container: {e}")
    
    def _get_exec_command(self, language: str, file_path: str) -> list:
        """获取执行命令"""
        commands = {
            "python": ["python", file_path],
            "node": ["node", file_path],
            "shell": ["bash", file_path]
        }
        return commands.get(language, ["python", file_path])
```

#### 2.1.3 AIOSandbox（全功能）

**适用场景**：
- 浏览器自动化（Web 抓取、截图、表单填写）
- Deep Research（浏览器 + 文件系统 + 搜索）
- VSCode Server（完整开发环境）
- Jupyter Notebook（交互式数据分析）
- MCP 服务集成（Browser, File, Shell, Markitdown）

**特点**：
- 全功能环境：Browser（VNC + CDP）、VSCode、Jupyter、Terminal
- 统一文件系统：浏览器下载的文件可直接被 Agent 访问
- MCP-Ready：预配置的 MCP 服务
- 资源占用高（~1-2GB 内存），启动时间长（~3-5s）

**集成方式**：

```python
# app/sandbox/aio_sandbox.py

from agent_sandbox import Sandbox as AIOSandboxClient

class AIOSandbox:
    """AIO Sandbox 集成封装"""
    
    def __init__(self, session_id: str, base_url: str = None):
        """
        Args:
            session_id: Session ID
            base_url: AIO Sandbox 服务地址（默认 http://localhost:8080）
        """
        self.session_id = session_id
        self.base_url = base_url or "http://localhost:8080"
        self.client = AIOSandboxClient(base_url=self.base_url)
        self.home_dir = self.client.sandbox.get_context().home_dir
    
    async def execute_code(self, code: str, language: str = "python") -> ExecutionResult:
        """执行代码"""
        try:
            # 写入代码文件
            code_file = f"{self.home_dir}/temp_{uuid4().hex[:8]}.py"
            self.client.file.write_file(file=code_file, content=code)
            
            # 执行
            result = self.client.shell.exec_command(
                command=f"python {code_file}"
            )
            
            return ExecutionResult(
                success=result.exit_code == 0,
                stdout=result.data.output,
                stderr=result.data.error,
                exit_code=result.exit_code
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                error=str(e)
            )
    
    async def browser_screenshot(self, url: str = None) -> bytes:
        """浏览器截图"""
        screenshot = self.client.browser.screenshot(url=url)
        return screenshot.data.image
    
    async def browser_navigate(self, url: str):
        """浏览器导航"""
        self.client.browser.navigate(url=url)
    
    async def read_file(self, path: str) -> str:
        """读取文件"""
        content = self.client.file.read_file(file=path)
        return content.data.content
    
    async def write_file(self, path: str, content: str):
        """写入文件"""
        self.client.file.write_file(file=path, content=content)
    
    async def cleanup(self):
        """清理资源"""
        # AIO Sandbox 容器由外部管理，这里不需要清理
        pass
```

**部署方式**：

```yaml
# docker-compose.yml 中添加 AIO Sandbox 服务

services:
  # ... 其他服务
  
  aio-sandbox:
    image: ghcr.io/agent-infra/sandbox:latest
    security_opt:
      - seccomp=unconfined
    ports:
      - "8080:8080"
    volumes:
      - aio_workspace:/home/gem/workspace
    environment:
      - MAX_CONCURRENT_SESSIONS=10  # 支持 10 个并发
    deploy:
      resources:
        limits:
          memory: 4G  # 每个容器 4GB
          cpus: '2'
        reservations:
          memory: 2G
```

**成本评估**（10 个并发）：
- 内存：10 × 2GB = 20GB
- CPU：10 × 0.5 核 = 5 核
- 存储：10 × 1GB = 10GB

### 2.2 SandboxRouter - 智能路由

```python
# app/sandbox/router.py

from enum import Enum
from typing import Optional

class SandboxType(Enum):
    """Sandbox 类型"""
    SUBPROCESS = "subprocess"      # 最轻量
    DOCKER_SIMPLE = "docker_simple"  # 轻量 Docker
    AIO_SANDBOX = "aio_sandbox"    # 全功能

class TaskRequirements:
    """任务需求"""
    needs_browser: bool = False
    needs_vscode: bool = False
    needs_jupyter: bool = False
    needs_isolation: bool = False  # 是否需要安全隔离
    needs_network: bool = False
    needs_file_system: bool = False
    risk_level: str = "safe"  # safe, low, medium, high, critical

class SandboxRouter:
    """Sandbox 路由器 - 根据任务需求选择最优 Sandbox"""
    
    @staticmethod
    def select_sandbox(task: TaskRequirements) -> SandboxType:
        """选择 Sandbox 类型
        
        Args:
            task: 任务需求
            
        Returns:
            推荐的 Sandbox 类型
        """
        # 1. 需要浏览器/可视化 → AIO Sandbox
        if task.needs_browser or task.needs_vscode or task.needs_jupyter:
            return SandboxType.AIO_SANDBOX
        
        # 2. 高风险代码 → 必须隔离
        if task.risk_level in ["high", "critical"]:
            # 如果需要网络，用 AIO Sandbox（支持网络配置）
            if task.needs_network:
                return SandboxType.AIO_SANDBOX
            # 否则用轻量 Docker
            return SandboxType.DOCKER_SIMPLE
        
        # 3. 需要文件系统操作 → Docker Simple
        if task.needs_file_system or task.needs_isolation:
            return SandboxType.DOCKER_SIMPLE
        
        # 4. 简单计算 → Subprocess（最快）
        return SandboxType.SUBPROCESS
    
    @staticmethod
    def infer_from_code(code: str, language: str = "python") -> TaskRequirements:
        """从代码推断任务需求
        
        Args:
            code: 代码内容
            language: 编程语言
            
        Returns:
            任务需求
        """
        import re
        
        task = TaskRequirements()
        code_lower = code.lower()
        
        # 检测浏览器操作
        if any(keyword in code_lower for keyword in 
               ["selenium", "playwright", "puppeteer", "browser", "screenshot"]):
            task.needs_browser = True
        
        # 检测文件操作
        if any(keyword in code_lower for keyword in 
               ["open(", "file(", "read", "write", "pathlib"]):
            task.needs_file_system = True
        
        # 检测网络访问
        if any(keyword in code_lower for keyword in 
               ["requests.", "urllib", "http", "socket", "aiohttp"]):
            task.needs_network = True
        
        # 风险评估
        task.risk_level = SandboxSecurityPolicy.assess_code_risk(code, language).value
        
        # 高风险代码必须隔离
        if task.risk_level in ["high", "critical"]:
            task.needs_isolation = True
        
        return task


class SandboxManager:
    """Sandbox 管理器 - 统一接口"""
    
    def __init__(self, session_id: str, filesystem: AgentFileSystem):
        self.session_id = session_id
        self.fs = filesystem
        
        # 缓存不同类型的 Sandbox 实例
        self._subprocess_sandbox: Optional[MCPCodeExecutor] = None
        self._docker_sandbox: Optional[DockerSimpleSandbox] = None
        self._aio_sandbox: Optional[AIOSandbox] = None
    
    async def execute(
        self,
        code: str,
        language: str = "python",
        sandbox_type: Optional[SandboxType] = None
    ) -> ExecutionResult:
        """执行代码
        
        Args:
            code: 代码内容
            language: 编程语言
            sandbox_type: 指定 Sandbox 类型（None = 自动选择）
            
        Returns:
            执行结果
        """
        # 自动选择 Sandbox
        if sandbox_type is None:
            task_req = SandboxRouter.infer_from_code(code, language)
            sandbox_type = SandboxRouter.select_sandbox(task_req)
            
            logger.info(
                f"Auto-selected sandbox: {sandbox_type.value} "
                f"(risk={task_req.risk_level}, browser={task_req.needs_browser})"
            )
        
        # 路由到对应的 Sandbox
        if sandbox_type == SandboxType.SUBPROCESS:
            return await self._execute_subprocess(code, language)
        
        elif sandbox_type == SandboxType.DOCKER_SIMPLE:
            return await self._execute_docker_simple(code, language)
        
        elif sandbox_type == SandboxType.AIO_SANDBOX:
            return await self._execute_aio_sandbox(code, language)
        
        else:
            raise ValueError(f"Unknown sandbox type: {sandbox_type}")
    
    async def _execute_subprocess(self, code: str, language: str) -> ExecutionResult:
        """使用 Subprocess Sandbox"""
        if not self._subprocess_sandbox:
            self._subprocess_sandbox = get_mcp_executor()
        
        request = ExecutionRequest(code=code, language=language)
        return await self._subprocess_sandbox.execute(request)
    
    async def _execute_docker_simple(self, code: str, language: str) -> ExecutionResult:
        """使用 DockerSimple Sandbox"""
        if not self._docker_sandbox:
            self._docker_sandbox = DockerSimpleSandbox(self.session_id, self.fs)
        
        return await self._docker_sandbox.execute_code(code, language)
    
    async def _execute_aio_sandbox(self, code: str, language: str) -> ExecutionResult:
        """使用 AIO Sandbox"""
        if not self._aio_sandbox:
            # 从配置获取 AIO Sandbox URL
            aio_url = settings.AIO_SANDBOX_URL or "http://aio-sandbox:8080"
            self._aio_sandbox = AIOSandbox(self.session_id, base_url=aio_url)
        
        return await self._aio_sandbox.execute_code(code, language)
    
    async def cleanup(self):
        """清理所有 Sandbox"""
        if self._subprocess_sandbox:
            self._subprocess_sandbox.cleanup()
        
        if self._docker_sandbox:
            await self._docker_sandbox.cleanup()
        
        if self._aio_sandbox:
            await self._aio_sandbox.cleanup()
```

### 2.3 安全策略

```python
class SandboxSecurityPolicy:
    """沙箱安全策略"""
    
    # 风险级别
    class RiskLevel(Enum):
        SAFE = "safe"          # 只读操作
        LOW = "low"            # 文件读写
        MEDIUM = "medium"      # 网络访问
        HIGH = "high"          # 系统调用
        CRITICAL = "critical"  # 危险操作
    
    @staticmethod
    def assess_code_risk(code: str, language: str) -> RiskLevel:
        """评估代码风险"""
        
        risk_patterns = {
            RiskLevel.CRITICAL: [
                r"__import__\(['\"]os['\"]\)",
                r"eval\(",
                r"exec\(",
                r"compile\(",
                r"subprocess",
                r"os\.system"
            ],
            RiskLevel.HIGH: [
                r"open\(.+,\s*['\"]w",  # 写文件
                r"requests\.",          # 网络请求
                r"urllib",
                r"socket"
            ],
            RiskLevel.MEDIUM: [
                r"open\(.+,\s*['\"]r",  # 读文件
                r"json\.load",
                r"pickle"
            ]
        }
        
        import re
        
        for level, patterns in risk_patterns.items():
            for pattern in patterns:
                if re.search(pattern, code):
                    return level
        
        return RiskLevel.SAFE
    
    @staticmethod
    def require_approval(risk_level: RiskLevel) -> bool:
        """是否需要用户批准"""
        return risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
```

### 2.4 使用示例

#### 2.4.1 自动路由模式（推荐）

```python
# Agent 代码中使用

from app.sandbox.router import SandboxManager

class AgentExecutor:
    def __init__(self, session_id: str):
        self.sandbox_manager = SandboxManager(session_id, filesystem)
    
    async def run_code(self, code: str, language: str = "python"):
        """Agent 执行代码 - 自动选择 Sandbox"""
        
        # 自动路由
        result = await self.sandbox_manager.execute(code, language)
        
        if result.success:
            return f"执行成功：{result.stdout}"
        else:
            return f"执行失败：{result.error}"
```

**例子 1：简单计算（自动选择 Subprocess）**

```python
code = """
import statistics
data = [1, 2, 3, 4, 5]
print(f"Mean: {statistics.mean(data)}")
"""

result = await sandbox_manager.execute(code)
# Auto-selected: subprocess (risk=safe, browser=False)
# Output: Mean: 3.0
```

**例子 2：文件操作（自动选择 DockerSimple）**

```python
code = """
import pandas as pd
df = pd.read_csv("data.csv")
print(df.head())
"""

result = await sandbox_manager.execute(code)
# Auto-selected: docker_simple (risk=medium, file_system=True)
```

**例子 3：Web 截图（自动选择 AIOSandbox）**

```python
code = """
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto("https://example.com")
    page.screenshot(path="screenshot.png")
    browser.close()
"""

result = await sandbox_manager.execute(code)
# Auto-selected: aio_sandbox (browser=True)
```

#### 2.4.2 手动指定 Sandbox

```python
# 强制使用 AIO Sandbox
result = await sandbox_manager.execute(
    code=code,
    sandbox_type=SandboxType.AIO_SANDBOX
)
```

#### 2.4.3 Deep Research 场景

```python
# Deep Research 使用 AIO Sandbox 的浏览器功能

class DeepResearchSkill:
    async def research_with_screenshots(self, query: str):
        # 1. 搜索
        search_results = await tavily_search(query)
        
        # 2. 访问网站 + 截图
        aio_sandbox = AIOSandbox(session_id)
        
        screenshots = []
        for url in search_results[:3]:
            aio_sandbox.client.browser.navigate(url=url)
            screenshot = await aio_sandbox.browser_screenshot()
            
            # 保存截图
            screenshot_path = f"research/screenshot_{url_hash}.png"
            await filesystem.write_binary(screenshot_path, screenshot)
            screenshots.append(screenshot_path)
        
        # 3. 提取内容
        content = await aio_sandbox.read_file(f"{aio_sandbox.home_dir}/page_content.txt")
        
        return {
            "screenshots": screenshots,
            "content": content
        }
```

## 3. 执行模式

### 3.1 一次性执行

```python
async def run_code_once(code: str, language: str):
    """一次性执行（用后即焚）"""
    
    sandbox = DockerSandbox(session_id=uuid4().hex)
    
    try:
        result = await sandbox.execute_code(code, language, timeout=30)
        return result
    finally:
        await sandbox.cleanup()
```

### 3.2 会话级沙箱

```python
class SessionSandbox:
    """会话级沙箱（Session期间持久化）"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.sandbox = DockerSandbox(session_id)
    
    async def __aenter__(self):
        await self.sandbox.create_container()
        return self.sandbox
    
    async def __aexit__(self, *args):
        await self.sandbox.cleanup()

# 使用
async with SessionSandbox(session_id) as sandbox:
    result1 = await sandbox.execute_code("print('hello')")
    result2 = await sandbox.execute_code("print('world')")
    # 容器在Session结束后自动清理
```

## 4. 测试驱动执行

```python
class TestDrivenSandbox:
    """测试驱动的代码执行"""
    
    async def execute_with_tests(
        self,
        code: str,
        test_cases: List[TestCase]
    ) -> TestResult:
        """执行代码并运行测试"""
        
        sandbox = DockerSandbox(self.session_id)
        
        try:
            # 1. 写入代码
            await self.fs.write("code/solution.py", code)
            
            # 2. 写入测试
            test_code = self._generate_test_file(test_cases)
            await self.fs.write("code/test_solution.py", test_code)
            
            # 3. 运行测试
            result = await sandbox.execute_code(
                "pytest test_solution.py -v",
                language="python",
                timeout=60
            )
            
            # 4. 解析测试结果
            return self._parse_pytest_output(result.stdout)
            
        finally:
            await sandbox.cleanup()
```

## 5. 资源监控

```python
class SandboxMonitor:
    """沙箱资源监控"""
    
    async def collect_metrics(self, container) -> dict:
        """收集容器资源使用"""
        
        stats = container.stats(stream=False)
        
        return {
            "cpu_usage_percent": self._calc_cpu_percent(stats),
            "memory_usage_mb": stats["memory_stats"]["usage"] / (1024 * 1024),
            "memory_limit_mb": stats["memory_stats"]["limit"] / (1024 * 1024),
            "network_rx_bytes": stats["networks"]["eth0"]["rx_bytes"],
            "network_tx_bytes": stats["networks"]["eth0"]["tx_bytes"],
            "pids_current": stats["pids_stats"]["current"]
        }
    
    async def check_resource_limits(self, container):
        """检查是否超限"""
        
        metrics = await self.collect_metrics(container)
        
        alerts = []
        
        if metrics["cpu_usage_percent"] > 80:
            alerts.append("CPU usage high")
        
        if metrics["memory_usage_mb"] > metrics["memory_limit_mb"] * 0.9:
            alerts.append("Memory usage critical")
        
        return alerts
```

## 6. 与其他模块集成

### 6.1 与Tool-Use集成

```python
@tool_registry.register
class RunCodeTool(BaseTool):
    """运行代码工具"""
    
    name = "run_code"
    description = "在安全沙箱中执行Python代码"
    risk_level = ToolRiskLevel.MEDIUM
    
    async def execute(self, code: str) -> ToolResult:
        # 风险评估
        risk = SandboxSecurityPolicy.assess_code_risk(code, "python")
        
        if SandboxSecurityPolicy.require_approval(risk):
            # 需要用户批准
            approved = await self.request_user_approval(
                message=f"代码包含{risk.value}级操作，是否允许执行？",
                code=code
            )
            
            if not approved:
                return ToolResult(
                    status="rejected",
                    summary="用户拒绝执行高风险代码"
                )
        
        # 执行
        sandbox = DockerSandbox(self.session_id)
        result = await sandbox.execute_code(code)
        
        return ToolResult(
            status="success" if result.success else "error",
            data={"stdout": result.stdout, "stderr": result.stderr},
            summary=f"代码执行{'成功' if result.success else '失败'}"
        )
```

### 6.2 与Self-Reflection集成

```python
# External-Loop反思模式的基础

async def code_with_reflection(task: str, max_iterations: int = 3):
    """代码生成 + 测试驱动反思"""
    
    for i in range(max_iterations):
        # 生成代码
        code = await llm.generate_code(task)
        
        # 沙箱执行测试
        sandbox = TestDrivenSandbox(session_id)
        test_result = await sandbox.execute_with_tests(code, test_cases)
        
        if test_result.all_passed:
            return code
        
        # 失败：真实错误反馈给Agent
        task += f"\n\n测试失败：{test_result.failures}"
```

## 3. 最佳实践

### 3.1 选择正确的 Sandbox

```python
# ✅ 推荐：让 SandboxManager 自动选择
result = await sandbox_manager.execute(code)

# ❌ 不推荐：所有代码都用 AIO Sandbox（过度设计）
result = await aio_sandbox.execute_code(code)

# ✅ 例外：明确需要浏览器时，直接指定
result = await sandbox_manager.execute(
    code,
    sandbox_type=SandboxType.AIO_SANDBOX
)
```

### 3.2 容器复用策略

```python
# ❌ 每次都创建新容器（慢）
for _ in range(10):
    sandbox = DockerSimpleSandbox(session_id, filesystem)
    await sandbox.create_container()
    await sandbox.execute_code(code)
    await sandbox.cleanup()

# ✅ Session 级复用（SandboxManager 自动处理）
sandbox_manager = SandboxManager(session_id, filesystem)
for _ in range(10):
    await sandbox_manager.execute(code)  # 自动复用

# 清理
await sandbox_manager.cleanup()
```

### 3.3 并发控制

```python
# AIO Sandbox 并发池管理

from asyncio import Semaphore

class AIOSandboxPool:
    """AIO Sandbox 连接池"""
    
    def __init__(self, max_concurrent: int = 10):
        self.semaphore = Semaphore(max_concurrent)
        self.active_sandboxes = {}
    
    async def acquire(self, session_id: str) -> AIOSandbox:
        await self.semaphore.acquire()
        
        if session_id not in self.active_sandboxes:
            self.active_sandboxes[session_id] = AIOSandbox(session_id)
        
        return self.active_sandboxes[session_id]
    
    async def release(self, session_id: str):
        self.semaphore.release()

# 使用
pool = AIOSandboxPool(max_concurrent=10)
sandbox = await pool.acquire(session_id)
try:
    result = await sandbox.execute_code(code)
finally:
    await pool.release(session_id)
```

### 3.4 监控与告警

```python
# 记录 Sandbox 使用指标

from prometheus_client import Counter, Histogram

sandbox_executions = Counter(
    "sandbox_executions_total",
    "Total sandbox executions",
    ["sandbox_type", "status"]
)

sandbox_duration = Histogram(
    "sandbox_execution_duration_seconds",
    "Sandbox execution duration",
    ["sandbox_type"]
)

class MonitoredSandboxManager(SandboxManager):
    async def execute(self, code: str, language: str = "python", sandbox_type=None):
        start_time = time.time()
        
        result = await super().execute(code, language, sandbox_type)
        
        # 记录指标
        duration = time.time() - start_time
        sandbox_duration.labels(sandbox_type=sandbox_type.value).observe(duration)
        sandbox_executions.labels(
            sandbox_type=sandbox_type.value,
            status="success" if result.success else "error"
        ).inc()
        
        return result
```

## 4. 部署指南

### 4.1 开发环境

```bash
# 1. 启动 AIO Sandbox
docker run --security-opt seccomp=unconfined --rm -it -p 8080:8080 \
  ghcr.io/agent-infra/sandbox:latest

# 2. 启动 Backend
cd backend
uv run uvicorn app.main:app --reload

# 3. 访问 AIO Sandbox
curl http://localhost:8080/v1/docs
```

### 4.2 生产环境

```yaml
# docker-compose.prod.yml

version: '3.8'

services:
  backend:
    image: tokendance/backend:latest
    environment:
      - AIO_SANDBOX_URL=http://aio-sandbox:8080
    depends_on:
      - aio-sandbox
  
  aio-sandbox:
    image: ghcr.io/agent-infra/sandbox:latest
    security_opt:
      - seccomp=unconfined
    deploy:
      replicas: 3  # 3 实例
      resources:
        limits:
          memory: 4G
          cpus: '2'
    volumes:
      - aio_workspace:/home/gem/workspace
    environment:
      - MAX_CONCURRENT_SESSIONS=10

volumes:
  aio_workspace:
```

### 4.3 K8s 部署

```yaml
# aio-sandbox-deployment.yaml

apiVersion: apps/v1
kind: Deployment
metadata:
  name: aio-sandbox
spec:
  replicas: 5  # 5 个 Pod，每个支持 10 并发 = 50 总并发
  selector:
    matchLabels:
      app: aio-sandbox
  template:
    metadata:
      labels:
        app: aio-sandbox
    spec:
      containers:
      - name: aio-sandbox
        image: ghcr.io/agent-infra/sandbox:latest
        ports:
        - containerPort: 8080
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
        securityContext:
          allowPrivilegeEscalation: false
        env:
        - name: MAX_CONCURRENT_SESSIONS
          value: "10"
---
apiVersion: v1
kind: Service
metadata:
  name: aio-sandbox
spec:
  selector:
    app: aio-sandbox
  ports:
  - port: 8080
    targetPort: 8080
  type: ClusterIP
```

## 5. 总结

**TokenDance 混合 Sandbox 架构要点**：

1. **渐进式能力** ⭐⭐⭐
   - 简单任务用 Subprocess（~0ms 启动）
   - 需隔离用 DockerSimple（~100ms 启动）
   - 需浏览器/可视化用 AIO Sandbox（~3-5s 启动）

2. **智能路由** ⭐⭐⭐
   - 自动检测代码风险等级
   - 自动推断任务需求（浏览器/文件/网络）
   - 选择最优 Sandbox 类型

3. **用户体验优先**
   - 10 个并发 AIO Sandbox 支持（~20GB 内存）
   - VNC 可视化让用户看到 Agent 在做什么
   - 统一文件系统（浏览器下载的文件可直接被 Agent 访问）

4. **安全与隔离**
   - Subprocess: 黑名单过滤
   - DockerSimple: 完整隔离 + 资源限制
   - AIO Sandbox: 云原生轻量级沙箱技术

5. **生产可用**
   - Docker Compose 一键部署
   - K8s HPA 自动伸缩
   - Prometheus 监控指标

**与 TokenDance 其他模块的关系**：

| 模块 | 与 Sandbox 的集成 |
|------|-----------------|
| **Tool-Use** | `run_code` 工具调用 SandboxManager |
| **Deep Research** | 使用 AIO Sandbox 的 Browser 功能 |
| **Coworker** | 可选用 AIO Sandbox 隔离本地文件 |
| **Context Graph** | 记录 Sandbox 执行轨迹 |
| **Self-Reflection** | External-Loop 模式依赖 Sandbox 验证 |
| **Monitor** | 监控 Sandbox 资源使用 |

**技术依赖**：
- **Subprocess**: Python `subprocess` 标准库
- **DockerSimple**: Docker SDK for Python
- **AIO Sandbox**: [agent-infra/sandbox](https://github.com/agent-infra/sandbox) (2.1k ⭐)

**下一步**：
1. 实现 `DockerSimpleSandbox` 类
2. 实现 `AIOSandbox` 集成封装
3. 实现 `SandboxRouter` 和 `SandboxManager`
4. 在 `docker-compose.yml` 中添加 AIO Sandbox 服务
5. 更新 Tool-Use 系统调用 SandboxManager
