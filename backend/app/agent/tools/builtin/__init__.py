"""
Built-in Tools - 内置工具集

包含 Agent 常用的工具：

核心工具 (4+2 模型):
- exit: Agent 主动终止工具（铁律三）
- file_ops: 文件操作 (read_file, write_file)
- shell: Shell命令执行 (run_code)

扩展工具:
- web_search: 网页搜索
- read_url: 网页内容读取
- browser_ops: 浏览器操作 (agent-browser)
- report_generator: 研究报告生成
- ppt_generator: PPT 演示文稿生成
"""
from .exit_tool import (
    ExitTool,
    ExitReason,
    ExitContext,
    create_success_exit,
    create_failure_exit,
    create_need_user_exit,
    create_fatal_exit,
)
from .web_search import WebSearchTool, create_web_search_tool
from .read_url import ReadUrlTool, create_read_url_tool
from .shell import ShellTool
from .file_ops import FileOpsTool, create_file_ops_tool
from .report_generator import ReportGeneratorTool, create_report_generator_tool
from .browser_ops import (
    BrowserOpenTool,
    BrowserClickTool,
    BrowserFillTool,
    BrowserSnapshotTool,
    BrowserScreenshotTool,
    BrowserCloseTool,
    create_browser_tools,
    cleanup_browser_session,
)
from .image_generation import (
    GenerateImageTool,
    EditImageTool,
    create_image_generation_tools,
)
from .ppt_generator import (
    GeneratePPTTool,
    QuickPPTTool,
    create_ppt_tools,
)

__all__ = [
    # Core tools (4+2 model) - 铁律三
    "ExitTool",
    "ExitReason",
    "ExitContext",
    "create_success_exit",
    "create_failure_exit",
    "create_need_user_exit",
    "create_fatal_exit",
    "ShellTool",
    "FileOpsTool",
    "create_file_ops_tool",
    # Extended tools
    "WebSearchTool",
    "create_web_search_tool",
    "ReadUrlTool",
    "create_read_url_tool",
    # Report generator
    "ReportGeneratorTool",
    "create_report_generator_tool",
    # Browser tools
    "BrowserOpenTool",
    "BrowserClickTool",
    "BrowserFillTool",
    "BrowserSnapshotTool",
    "BrowserScreenshotTool",
    "BrowserCloseTool",
    "create_browser_tools",
    "cleanup_browser_session",
    # Image generation tools
    "GenerateImageTool",
    "EditImageTool",
    "create_image_generation_tools",
    # PPT generation tools
    "GeneratePPTTool",
    "QuickPPTTool",
    "create_ppt_tools",
]
