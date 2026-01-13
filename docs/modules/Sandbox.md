# Sandbox设计文档

## 1. 核心目标

**为Agent提供安全、隔离的代码执行环境**

```
安全隔离 + 资源限制 + 可观测性 = 可信的代码执行
```

## 2. 架构设计

### 2.1 Docker隔离方案

```python
# packages/sandbox/docker_sandbox.py

class DockerSandbox:
    """Docker沙箱执行器"""
    
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

### 2.2 安全策略

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

### 2.3 与文件系统集成

```python
class SandboxFileSystemBridge:
    """沙箱与文件系统的桥接"""
    
    def __init__(self, sandbox: DockerSandbox, filesystem: AgentFileSystem):
        self.sandbox = sandbox
        self.fs = filesystem
    
    async def sync_workspace_to_container(self):
        """同步工作空间到容器"""
        # Docker volume已自动挂载，无需手动同步
        pass
    
    async def sync_container_to_workspace(self):
        """同步容器输出到工作空间"""
        # 读取容器中的文件变更
        exec_result = self.sandbox.container.exec_run(
            cmd=["find", "/workspace", "-type", "f", "-newer", "/tmp/sync_marker"],
            stdout=True
        )
        
        changed_files = exec_result.output.decode().strip().split("\n")
        
        # 记录到Context Graph
        for file_path in changed_files:
            await self.context_graph.record_file_change(
                session_id=self.sandbox.session_id,
                file_path=file_path,
                change_type="created_by_sandbox"
            )
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

## 7. 最佳实践

### 7.1 容器复用策略

```python
# ❌ 每次都创建新容器（慢）
for _ in range(10):
    sandbox = DockerSandbox(session_id)
    await sandbox.create_container()
    await sandbox.execute_code(code)
    await sandbox.cleanup()

# ✅ 复用容器
async with SessionSandbox(session_id) as sandbox:
    for _ in range(10):
        await sandbox.execute_code(code)
```

### 7.2 网络访问控制

```python
# 需要网络时，使用受限网络
sandbox = DockerSandbox(session_id)
sandbox.DEFAULT_LIMITS["network"] = "tokendance_sandbox_net"

# 创建受限网络（只允许白名单域名）
# Docker network create --driver bridge \
#   --opt com.docker.network.bridge.name=td_sandbox \
#   tokendance_sandbox_net
```

## 8. 总结

**TokenDance Sandbox设计要点**：
1. **安全优先**：Docker隔离 + 最小权限 + 危险命令黑名单
2. **资源限制**：内存、CPU、进程数、网络
3. **文件系统集成**：Volume挂载工作空间
4. **测试驱动**：External-Loop反思的基础
5. **Human-in-the-Loop**：高风险操作需用户批准

**与其他模块关系**：
- Tool-Use的`run_code`工具依赖Sandbox
- Self-Reflection的External-Loop模式依赖Sandbox验证
- Context Graph记录代码执行轨迹
- Monitor监控资源使用
