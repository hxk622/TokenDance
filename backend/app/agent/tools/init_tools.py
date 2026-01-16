"""Initialize and register all built-in tools"""
from typing import List
import logging

from app.agent.tools.registry import ToolRegistry
from app.agent.tools.base import BaseTool

logger = logging.getLogger(__name__)


def register_builtin_tools(registry: ToolRegistry) -> List[BaseTool]:
    """Register all built-in tools to registry"""
    
    tools = []
    
    # Import and register built-in tools
    try:
        from app.agent.tools.builtin.web_search import WebSearchTool
        web_search = WebSearchTool()
        registry.register(web_search)
        tools.append(web_search)
        logger.info(f"Registered tool: {web_search.name}")
    except Exception as e:
        logger.error(f"Failed to register web_search tool: {e}")
    
    try:
        from app.agent.tools.builtin.read_url import ReadUrlTool
        read_url = ReadUrlTool()
        registry.register(read_url)
        tools.append(read_url)
        logger.info(f"Registered tool: {read_url.name}")
    except Exception as e:
        logger.error(f"Failed to register read_url tool: {e}")
    
    try:
        from app.agent.tools.builtin.shell import ShellTool
        shell = ShellTool()
        registry.register(shell)
        tools.append(shell)
        logger.info(f"Registered tool: {shell.name}")
    except Exception as e:
        logger.error(f"Failed to register shell tool: {e}")
    
    try:
        from app.agent.tools.builtin.file_ops import FileOpsTool
        from app.filesystem import AgentFileSystem
        file_ops = FileOpsTool(filesystem=AgentFileSystem())
        registry.register(file_ops)
        tools.append(file_ops)
        logger.info(f"Registered tool: {file_ops.name}")
    except Exception as e:
        logger.error(f"Failed to register file_ops tool: {e}")
    
    try:
        from app.agent.tools.builtin.create_document import CreateDocumentTool
        create_doc = CreateDocumentTool()
        registry.register(create_doc)
        tools.append(create_doc)
        logger.info(f"Registered tool: {create_doc.name}")
    except Exception as e:
        logger.error(f"Failed to register create_document tool: {e}")
    
    try:
        from app.agent.tools.builtin.image_generation import ImageGenerationTool
        image_gen = ImageGenerationTool()
        registry.register(image_gen)
        tools.append(image_gen)
        logger.info(f"Registered tool: {image_gen.name}")
    except Exception as e:
        logger.error(f"Failed to register image_generation tool: {e}")
    
    try:
        from app.agent.tools.builtin.ppt_generator import PPTGeneratorTool
        ppt_gen = PPTGeneratorTool()
        registry.register(ppt_gen)
        tools.append(ppt_gen)
        logger.info(f"Registered tool: {ppt_gen.name}")
    except Exception as e:
        logger.error(f"Failed to register ppt_generator tool: {e}")
    
    try:
        from app.agent.tools.builtin.report_generator import ReportGeneratorTool
        report_gen = ReportGeneratorTool()
        registry.register(report_gen)
        tools.append(report_gen)
        logger.info(f"Registered tool: {report_gen.name}")
    except Exception as e:
        logger.error(f"Failed to register report_generator tool: {e}")
    
    try:
        from app.agent.tools.builtin.exit_tool import ExitTool
        exit_tool = ExitTool()
        registry.register(exit_tool)
        tools.append(exit_tool)
        logger.info(f"Registered tool: {exit_tool.name}")
    except Exception as e:
        logger.error(f"Failed to register exit tool: {e}")
    
    # FileConverterTool - Document to Markdown conversion (MarkItDown)
    try:
        from app.agent.tools.file_converter import FileConverterTool
        file_converter = FileConverterTool()
        registry.register(file_converter)
        tools.append(file_converter)
        logger.info(f"Registered tool: {file_converter.name}")
    except Exception as e:
        logger.error(f"Failed to register file_converter tool: {e}")
    
    logger.info(f"Total registered tools: {len(tools)}")
    return tools


def get_tool_categories() -> dict:
    """Get tool categories for UI organization"""
    return {
        "Web & Research": ["web_search", "read_url"],
        "File Operations": ["file_ops", "create_document", "file_converter"],
        "System": ["shell", "exit"],
        "Content Generation": ["image_generation", "ppt_generator", "report_generator"]
    }


def get_tool_descriptions() -> dict:
    """Get tool descriptions for documentation"""
    return {
        "web_search": "Search web using DuckDuckGo",
        "read_url": "Read and extract content from a URL",
        "shell": "Execute shell commands",
        "file_ops": "Perform file operations (read, write, list, delete)",
        "create_document": "Create a new document",
        "file_converter": "Convert files (PDF, DOCX, XLSX, etc.) to Markdown",
        "image_generation": "Generate images using AI",
        "ppt_generator": "Generate PowerPoint presentations",
        "report_generator": "Generate reports from data",
        "exit": "Exit the current task"
    }
