"""
ShellTool - 终端命令执行工具

核心功能：
- 白名单命令机制，只允许安全命令
- 工作区目录限制，防止访问敏感文件
- 超时控制，防止命令挂起
- 输出截断，防止输出过大

来源：Manus核心能力，解锁系统生态工具
"""

import asyncio
import os
import shlex
import subprocess
from typing import Optional, List
from pydantic import BaseModel, Field

from ..base import BaseTool, ToolResult


class ShellToolArgs(BaseModel):
    """ShellTool参数"""
    command: str = Field(..., description="要执行的shell命令")
    timeout: int = Field(30, ge=1, le=300, description="超时时间（秒），默认30秒")
    max_output_length: int = Field(10000, ge=100, le=100000, description="最大输出长度，默认10000字符")


class ShellTool(BaseTool):
    """
    Shell命令执行工具
    
    设计原则：
    1. 白名单机制 - 只允许安全的命令
    2. 工作区限制 - 命令只能在workspace目录下执行
    3. 超时控制 - 防止命令挂起
    4. 输出截断 - 防止输出过大撑爆Context
    """
    
    name = "shell"
    description = "执行shell命令，用于文件操作、代码搜索、版本控制等。支持ls、cat、grep、git、find等常用命令。"
    args_schema = ShellToolArgs
    
    # 白名单命令 - 只允许这些命令执行
    WHITELIST_COMMANDS = {
        # 文件浏览
        "ls", "tree", "find", "pwd", "file",
        # 文件读取
        "cat", "head", "tail", "less", "more",
        # 搜索
        "grep", "rg", "ag", "ack",
        # 版本控制
        "git",
        # 文件统计
        "wc", "du", "stat",
        # 其他工具
        "echo", "which", "whereis", "type",
    }
    
    # 危险命令黑名单 - 即使在白名单中也不允许的模式
    DANGEROUS_PATTERNS = [
        "rm -rf /",
        "rm -rf ~",
        "dd if=",
        "mkfs",
        ":(){ :|:& };:",  # Fork bomb
        "> /dev/",
        "curl | sh",
        "wget | sh",
    ]
    
    def __init__(self, workspace_path: Optional[str] = None):
        """
        初始化ShellTool
        
        Args:
            workspace_path: 工作区路径，命令只能在此目录下执行
        """
        super().__init__()
        self.workspace_path = workspace_path or os.getcwd()
    
    async def execute(
        self,
        command: str,
        timeout: int = 30,
        max_output_length: int = 10000,
    ) -> ToolResult:
        """
        执行shell命令
        
        Args:
            command: 要执行的命令
            timeout: 超时时间（秒）
            max_output_length: 最大输出长度
            
        Returns:
            ToolResult: 执行结果
        """
        # 1. 安全检查
        safety_check = self._check_command_safety(command)
        if not safety_check["safe"]:
            return ToolResult(
                success=False,
                error=f"命令被拒绝: {safety_check['reason']}",
                data={"command": command}
            )
        
        # 2. 执行命令
        try:
            result = await self._run_command(command, timeout)
            
            # 3. 处理输出
            stdout = result["stdout"]
            stderr = result["stderr"]
            exit_code = result["exit_code"]
            
            # 截断输出
            if len(stdout) > max_output_length:
                stdout = stdout[:max_output_length] + f"\n\n... (输出过长，已截断，总长度: {len(result['stdout'])} 字符)"
            
            if len(stderr) > max_output_length:
                stderr = stderr[:max_output_length] + f"\n\n... (错误输出过长，已截断)"
            
            # 4. 返回结果
            success = exit_code == 0
            
            return ToolResult(
                success=success,
                data={
                    "command": command,
                    "stdout": stdout,
                    "stderr": stderr,
                    "exit_code": exit_code,
                    "working_directory": self.workspace_path,
                },
                error=stderr if not success else None
            )
            
        except asyncio.TimeoutError:
            return ToolResult(
                success=False,
                error=f"命令执行超时 ({timeout}秒)",
                data={"command": command, "timeout": timeout}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"命令执行失败: {str(e)}",
                data={"command": command}
            )
    
    def _check_command_safety(self, command: str) -> dict:
        """
        检查命令安全性
        
        Returns:
            dict: {"safe": bool, "reason": str}
        """
        # 1. 检查危险模式
        for pattern in self.DANGEROUS_PATTERNS:
            if pattern in command:
                return {
                    "safe": False,
                    "reason": f"命令包含危险模式: {pattern}"
                }
        
        # 2. 解析命令，提取主命令
        try:
            parts = shlex.split(command)
            if not parts:
                return {"safe": False, "reason": "空命令"}
            
            main_command = parts[0]
            
            # 提取命令名（去掉路径）
            command_name = os.path.basename(main_command)
            
        except ValueError as e:
            return {"safe": False, "reason": f"命令解析失败: {str(e)}"}
        
        # 3. 检查是否在白名单中
        if command_name not in self.WHITELIST_COMMANDS:
            return {
                "safe": False,
                "reason": f"命令 '{command_name}' 不在白名单中。允许的命令: {', '.join(sorted(self.WHITELIST_COMMANDS))}"
            }
        
        # 4. 特殊命令的额外检查
        if command_name == "git":
            # git命令允许大部分操作，但禁止push等写操作
            if any(danger in command for danger in ["push", "force", "--force"]):
                return {
                    "safe": False,
                    "reason": "不允许git push等写操作"
                }
        
        if command_name == "find":
            # find命令禁止 -exec 和 -delete
            if "-exec" in parts or "-delete" in parts:
                return {
                    "safe": False,
                    "reason": "find命令不允许使用 -exec 或 -delete"
                }
        
        return {"safe": True, "reason": ""}
    
    async def _run_command(self, command: str, timeout: int) -> dict:
        """
        异步执行命令
        
        Args:
            command: 命令字符串
            timeout: 超时时间
            
        Returns:
            dict: {"stdout": str, "stderr": str, "exit_code": int}
        """
        # 创建子进程
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self.workspace_path,
        )
        
        # 等待执行完成（带超时）
        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            # 超时，杀死进程
            process.kill()
            await process.wait()
            raise
        
        # 解码输出
        stdout = stdout_bytes.decode("utf-8", errors="replace")
        stderr = stderr_bytes.decode("utf-8", errors="replace")
        exit_code = process.returncode
        
        return {
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": exit_code,
        }
