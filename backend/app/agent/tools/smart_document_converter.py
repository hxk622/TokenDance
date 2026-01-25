"""
Smart Document Converter - 智能文档转换模块

支持智能路由到不同的解析引擎：
- MarkItDown: 简单文档（快速）
- MinerU: 复杂文档/金融报告（高精度）

Features:
- 自动检测文档复杂度
- 详细日志记录（工具、耗时、指标）
- 远程 API 调用（无需 GPU）

MinerU API:
- 官网: https://mineru.net
- 申请: https://mineru.net/apiManage
- 内测免费: 每日 2000 页高优先级额度
"""
from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

import httpx

logger = logging.getLogger(__name__)


# =============================================================================
# 数据类型定义
# =============================================================================


@dataclass
class ConversionMetrics:
    """
    转换指标 - 用于日志和监控

    记录每次文档转换的完整指标，便于排查问题和性能分析。
    """

    file_path: str
    file_size_bytes: int
    page_count: int | None = None

    # 复杂度检测
    complexity_score: int = 0
    complexity_reasons: list[str] = field(default_factory=list)
    is_complex: bool = False

    # 引擎选择
    engine_used: Literal["markitdown", "mineru"] = "markitdown"
    engine_reason: str = ""

    # 性能指标
    detection_latency_ms: float = 0
    conversion_latency_ms: float = 0
    total_latency_ms: float = 0

    # 结果
    success: bool = False
    error_message: str | None = None
    output_chars: int = 0

    def to_log_dict(self) -> dict[str, Any]:
        """转换为日志字典"""
        return {
            "file": Path(self.file_path).name,
            "size_kb": round(self.file_size_bytes / 1024, 1),
            "pages": self.page_count,
            "complexity": {
                "score": self.complexity_score,
                "is_complex": self.is_complex,
                "reasons": self.complexity_reasons,
            },
            "engine": {
                "used": self.engine_used,
                "reason": self.engine_reason,
            },
            "latency": {
                "detection_ms": round(self.detection_latency_ms, 1),
                "conversion_ms": round(self.conversion_latency_ms, 1),
                "total_ms": round(self.total_latency_ms, 1),
            },
            "result": {
                "success": self.success,
                "output_chars": self.output_chars,
                "error": self.error_message,
            },
            "timestamp": datetime.now().isoformat(),
        }


# =============================================================================
# PDF 复杂度检测器
# =============================================================================


class PDFComplexityDetector:
    """
    PDF 复杂度检测器

    使用 PyMuPDF 分析 PDF 文档结构，判断是否需要使用 MinerU 处理。

    判断逻辑：
    1. 文件名包含金融关键词 → 复杂
    2. 扫描件（文字少但有图片）→ 复杂（需 OCR）
    3. 包含表格 → 复杂
    4. 多栏布局 → 复杂
    5. 页数多 (>20) → 可能是正式报告
    """

    # 金融/研报关键词
    FINANCE_KEYWORDS: list[str] = [
        # 中文
        "年报",
        "财报",
        "研报",
        "招股",
        "季报",
        "半年报",
        "年度报告",
        "行业报告",
        "研究报告",
        "分析报告",
        "白皮书",
        "投资",
        "证券",
        "基金",
        "债券",
        "IPO",
        "ESG",
        "尽调",
        "审计",
        # 英文
        "annual_report",
        "financial",
        "quarterly",
        "prospectus",
        "investment",
        "securities",
        "earnings",
        "10-k",
        "10-q",
        "8-k",
    ]

    # 复杂度阈值
    COMPLEXITY_THRESHOLD: int = 4

    def detect(self, file_path: str) -> tuple[bool, int, list[str]]:
        """
        检测 PDF 复杂度

        Args:
            file_path: PDF 文件路径

        Returns:
            tuple: (is_complex, score, reasons)
                - is_complex: 是否为复杂文档
                - score: 复杂度分数
                - reasons: 判断原因列表
        """
        try:
            import fitz  # type: ignore[import-untyped]  # PyMuPDF
        except ImportError:
            logger.warning(
                "[PDFComplexityDetector] PyMuPDF not installed, "
                "defaulting to complex. Install with: uv pip install pymupdf"
            )
            return True, 99, ["PyMuPDF 未安装，保守使用 MinerU"]

        path = Path(file_path)
        score = 0
        reasons: list[str] = []

        # 1. 文件名关键词检测（最高优先级）
        filename_lower = path.stem.lower()
        for kw in self.FINANCE_KEYWORDS:
            if kw.lower() in filename_lower:
                logger.debug(
                    f"[PDFComplexityDetector] Finance keyword detected: {kw}"
                )
                return True, 100, [f"文件名含金融关键词: {kw}"]

        # 2. PDF 结构分析
        try:
            doc = fitz.open(file_path)
            page_count = doc.page_count

            # 页数多 = 可能是正式报告
            if page_count > 20:
                score += 3
                reasons.append(f"页数多({page_count}页)")
            elif page_count > 10:
                score += 1
                reasons.append(f"中等页数({page_count}页)")

            # 采样分析前 3 页
            sample_pages = min(3, page_count)

            for i in range(sample_pages):
                page = doc[i]

                # 2.1 表格检测
                try:
                    tables = page.find_tables()
                    if tables.tables:
                        score += 3
                        if "含表格" not in reasons:
                            reasons.append("含表格")
                except Exception:
                    # find_tables 可能在某些 PDF 上失败
                    pass

                # 2.2 图片检测
                images = page.get_images()
                image_count = len(images)

                if image_count > 3:
                    score += 1
                    if "图片丰富" not in reasons:
                        reasons.append("图片丰富")

                # 2.3 扫描件检测（文字少但有图）
                text = page.get_text()
                text_len = len(text.strip())

                if text_len < 100 and image_count > 0:
                    score += 5
                    reasons.append("疑似扫描件")
                    doc.close()
                    return True, score, reasons

                # 2.4 多栏布局检测
                try:
                    blocks = page.get_text("dict")["blocks"]
                    text_blocks = [b for b in blocks if b.get("type") == 0]

                    if len(text_blocks) > 8:
                        x_positions = [b["bbox"][0] for b in text_blocks]
                        if x_positions:
                            x_spread = max(x_positions) - min(x_positions)
                            page_width = page.rect.width
                            if x_spread > page_width * 0.4:
                                score += 2
                                if "多栏布局" not in reasons:
                                    reasons.append("多栏布局")
                except Exception:
                    pass

            doc.close()

            # 决定阈值
            is_complex = score >= self.COMPLEXITY_THRESHOLD
            return is_complex, score, reasons

        except Exception as e:
            logger.warning(f"[PDFComplexityDetector] PDF 分析失败: {e}")
            return True, 99, [f"分析失败，保守使用 MinerU: {str(e)[:50]}"]


# =============================================================================
# MinerU 客户端
# =============================================================================


class MinerUClient:
    """
    MinerU 官方 API 客户端

    API 文档: https://mineru.net/apiManage/docs

    费用说明:
    - 内测阶段免费
    - 每日 2000 页高优先级额度
    - 单文件限制: 200MB / 600页
    """

    BASE_URL = "https://mineru.net"

    # API 路径
    UPLOAD_PATH = "/api/v4/file-urls/batch"
    STATUS_PATH = "/api/v4/extract-results/batch"

    def __init__(self, api_token: str | None = None):
        """
        初始化 MinerU 客户端

        Args:
            api_token: MinerU API Token (从 mineru.net/apiManage 获取)
        """
        self.api_token = api_token
        self.client = httpx.Client(timeout=300)  # 5分钟超时

    def _get_headers(self) -> dict[str, str]:
        """获取请求头"""
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

    def parse_pdf(self, file_path: str) -> tuple[str, dict[str, Any]]:
        """
        解析 PDF 文件

        Args:
            file_path: PDF 文件路径

        Returns:
            tuple: (markdown_content, metadata)

        Raises:
            ValueError: API Token 未配置或上传失败
            RuntimeError: 解析失败
            TimeoutError: 解析超时
        """
        if not self.api_token:
            raise ValueError(
                "MinerU API Token 未配置。"
                "请在 .env 中设置 MINERU_API_TOKEN，"
                "或访问 https://mineru.net/apiManage 申请"
            )

        path = Path(file_path)
        logger.info(f"[MinerU] 开始解析: {path.name}")

        # 1. 上传文件获取预签名 URL
        # MinerU V4 API 使用批量上传接口
        upload_url = f"{self.BASE_URL}{self.UPLOAD_PATH}"

        # 先获取上传 URL
        upload_request = {
            "files": [{"name": path.name, "is_ocr": True, "data_id": path.stem}]
        }

        try:
            response = self.client.post(
                upload_url,
                json=upload_request,
                headers=self._get_headers(),
            )
            response.raise_for_status()
            result = response.json()

            if result.get("code") != 0:
                raise ValueError(f"获取上传 URL 失败: {result.get('msg', 'Unknown error')}")

            file_urls = result.get("data", {}).get("file_urls", [])
            if not file_urls:
                raise ValueError("未获取到上传 URL")

            presigned_url = file_urls[0].get("presigned_url")
            batch_id = result.get("data", {}).get("batch_id")

            if not presigned_url or not batch_id:
                raise ValueError(f"响应缺少必要字段: {result}")

        except httpx.HTTPStatusError as e:
            logger.error(f"[MinerU] HTTP 错误: {e.response.status_code}")
            raise ValueError(f"MinerU API 请求失败: {e.response.status_code}") from e

        # 2. 上传文件到预签名 URL
        logger.debug(f"[MinerU] 上传文件到预签名 URL, batch_id={batch_id}")

        with open(file_path, "rb") as f:
            upload_response = self.client.put(
                presigned_url,
                content=f.read(),
                headers={"Content-Type": "application/pdf"},
            )
            upload_response.raise_for_status()

        # 3. 轮询解析状态
        status_url = f"{self.BASE_URL}{self.STATUS_PATH}"
        max_attempts = 120  # 最多等待 10 分钟 (120 * 5s)

        for attempt in range(max_attempts):
            time.sleep(5)

            try:
                status_response = self.client.post(
                    status_url,
                    json={"batch_id": batch_id},
                    headers=self._get_headers(),
                )
                status_response.raise_for_status()
                status_result = status_response.json()

                if status_result.get("code") != 0:
                    logger.warning(
                        f"[MinerU] 状态查询返回错误: {status_result.get('msg')}"
                    )
                    continue

                extract_results = status_result.get("data", {}).get("extract_results", [])

                if not extract_results:
                    continue

                file_result = extract_results[0]
                status = file_result.get("status")

                if status == "success":
                    markdown = file_result.get("full_md", "")
                    metadata = {
                        "batch_id": batch_id,
                        "pages": file_result.get("page_count"),
                        "data_id": file_result.get("data_id"),
                    }
                    logger.info(
                        f"[MinerU] 解析成功: {path.name}, "
                        f"pages={metadata.get('pages')}, "
                        f"chars={len(markdown)}"
                    )
                    return markdown, metadata

                elif status == "failed":
                    error = file_result.get("error", "Unknown error")
                    logger.error(f"[MinerU] 解析失败: {error}")
                    raise RuntimeError(f"MinerU 解析失败: {error}")

                else:
                    # processing / pending
                    if attempt % 6 == 0:  # 每 30 秒日志一次
                        logger.debug(
                            f"[MinerU] 解析中... status={status}, "
                            f"attempt={attempt + 1}/{max_attempts}"
                        )

            except httpx.HTTPStatusError as e:
                logger.warning(f"[MinerU] 状态查询 HTTP 错误: {e.response.status_code}")
                continue

        raise TimeoutError(
            f"MinerU 解析超时 (>{max_attempts * 5}s)。"
            "请检查网络或稍后重试。"
        )

    def close(self) -> None:
        """关闭 HTTP 客户端"""
        self.client.close()


# =============================================================================
# 智能文档转换器
# =============================================================================


class SmartDocumentConverter:
    """
    智能文档转换器 - 自动路由到最优引擎

    根据文档复杂度自动选择：
    - MarkItDown: 简单文档，快速处理
    - MinerU: 复杂文档/金融报告，高精度

    使用示例:
        converter = SmartDocumentConverter(
            mineru_api_token=os.getenv("MINERU_API_TOKEN")
        )
        markdown, metrics = converter.convert("/path/to/file.pdf")

        # metrics 包含详细的转换指标
        print(metrics.engine_used)  # "markitdown" 或 "mineru"
        print(metrics.total_latency_ms)  # 总耗时
    """

    def __init__(
        self,
        mineru_api_token: str | None = None,
        force_engine: Literal["auto", "markitdown", "mineru"] = "auto",
        log_metrics: bool = True,
        complexity_threshold: int = 4,
    ):
        """
        初始化智能文档转换器

        Args:
            mineru_api_token: MinerU API Token
            force_engine: 强制使用指定引擎
                - "auto": 智能选择（默认）
                - "markitdown": 强制使用 MarkItDown
                - "mineru": 强制使用 MinerU
            log_metrics: 是否记录详细指标日志
            complexity_threshold: 复杂度判断阈值（默认 4）
        """
        self.detector = PDFComplexityDetector()
        self.detector.COMPLEXITY_THRESHOLD = complexity_threshold

        # 从环境变量或参数获取 API Token
        token = mineru_api_token or os.getenv("MINERU_API_TOKEN")
        self.mineru_client = MinerUClient(token) if token else None

        self.force_engine = force_engine
        self.log_metrics = log_metrics

        # 延迟初始化 MarkItDown
        self._markitdown: Any = None

        # 日志初始化状态
        if self.mineru_client:
            logger.info(
                "[SmartDocumentConverter] Initialized with MinerU support"
            )
        else:
            logger.warning(
                "[SmartDocumentConverter] MinerU not configured. "
                "Complex PDFs will use MarkItDown (lower quality). "
                "Set MINERU_API_TOKEN to enable MinerU."
            )

    def _get_markitdown(self) -> Any:
        """延迟加载 MarkItDown"""
        if self._markitdown is None:
            try:
                from markitdown import MarkItDown

                self._markitdown = MarkItDown()
            except ImportError as e:
                raise ImportError(
                    "MarkItDown 未安装: uv pip install markitdown"
                ) from e
        return self._markitdown

    def convert(self, file_path: str) -> tuple[str, ConversionMetrics]:
        """
        转换文档为 Markdown

        Args:
            file_path: 文件路径

        Returns:
            tuple: (markdown_content, metrics)
                - markdown_content: 转换后的 Markdown 文本
                - metrics: 转换指标（包含日志信息）

        Raises:
            FileNotFoundError: 文件不存在
            ImportError: 依赖未安装
            ValueError: MinerU 配置错误
            RuntimeError: 转换失败
        """
        start_time = time.perf_counter()
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        # 初始化指标
        metrics = ConversionMetrics(
            file_path=file_path,
            file_size_bytes=path.stat().st_size,
        )

        try:
            # 1. 复杂度检测
            detection_start = time.perf_counter()

            if path.suffix.lower() == ".pdf":
                is_complex, score, reasons = self.detector.detect(file_path)
                metrics.complexity_score = score
                metrics.complexity_reasons = reasons
                metrics.is_complex = is_complex
            else:
                # 非 PDF 默认用 MarkItDown
                is_complex = False
                metrics.complexity_reasons = ["非 PDF 文件"]

            metrics.detection_latency_ms = (
                time.perf_counter() - detection_start
            ) * 1000

            # 2. 引擎选择
            engine = self._select_engine(is_complex, score if is_complex else 0, reasons if is_complex else [])
            metrics.engine_used = engine
            metrics.engine_reason = self._get_engine_reason(
                engine, is_complex, metrics.complexity_score, metrics.complexity_reasons
            )

            # 3. 执行转换
            conversion_start = time.perf_counter()

            if engine == "mineru":
                if not self.mineru_client:
                    raise ValueError(
                        "MinerU 客户端未初始化。请设置 MINERU_API_TOKEN 环境变量。"
                    )
                markdown, meta = self.mineru_client.parse_pdf(file_path)
                metrics.page_count = meta.get("pages")
            else:
                md = self._get_markitdown()
                result = md.convert(str(path))
                markdown = result.text_content

            metrics.conversion_latency_ms = (
                time.perf_counter() - conversion_start
            ) * 1000

            # 4. 记录结果
            metrics.success = True
            metrics.output_chars = len(markdown)
            metrics.total_latency_ms = (time.perf_counter() - start_time) * 1000

            # 5. 日志输出
            if self.log_metrics:
                self._log_metrics(metrics)

            return markdown, metrics

        except Exception as e:
            metrics.success = False
            metrics.error_message = str(e)
            metrics.total_latency_ms = (time.perf_counter() - start_time) * 1000

            if self.log_metrics:
                self._log_metrics(metrics)

            raise

    def _select_engine(
        self,
        is_complex: bool,
        score: int,
        reasons: list[str],
    ) -> Literal["markitdown", "mineru"]:
        """选择转换引擎"""
        if self.force_engine != "auto":
            # force_engine 已经是 Literal["markitdown", "mineru"] 类型
            if self.force_engine == "markitdown":
                return "markitdown"
            return "mineru"

        if is_complex and self.mineru_client:
            return "mineru"
        else:
            return "markitdown"

    def _get_engine_reason(
        self,
        engine: str,
        is_complex: bool,
        score: int,
        reasons: list[str],
    ) -> str:
        """获取引擎选择原因"""
        if self.force_engine != "auto":
            return f"强制指定: {self.force_engine}"

        if engine == "mineru":
            return f"复杂文档 (score={score}): {', '.join(reasons)}"
        elif is_complex and not self.mineru_client:
            return "复杂文档但 MinerU 未配置，降级使用 MarkItDown"
        else:
            return "简单文档"

    def _log_metrics(self, metrics: ConversionMetrics) -> None:
        """记录详细指标日志"""
        log_data = metrics.to_log_dict()

        if metrics.success:
            logger.info(
                f"[SmartConverter] ✅ {log_data['file']} | "
                f"engine={log_data['engine']['used']} | "
                f"latency={log_data['latency']['total_ms']:.0f}ms | "
                f"output={log_data['result']['output_chars']} chars | "
                f"reason={log_data['engine']['reason']}"
            )
        else:
            logger.error(
                f"[SmartConverter] ❌ {log_data['file']} | "
                f"engine={log_data['engine']['used']} | "
                f"error={log_data['result']['error']}"
            )

        # 详细日志（DEBUG 级别）
        logger.debug(f"[SmartConverter] Full metrics: {log_data}")

    def close(self) -> None:
        """关闭资源"""
        if self.mineru_client:
            self.mineru_client.close()


# =============================================================================
# 便捷函数
# =============================================================================


def convert_document(
    file_path: str,
    mineru_api_token: str | None = None,
    force_engine: Literal["auto", "markitdown", "mineru"] = "auto",
) -> str:
    """
    便捷函数：转换文档为 Markdown

    Args:
        file_path: 文件路径
        mineru_api_token: MinerU API Token（可选，默认从环境变量读取）
        force_engine: 强制使用指定引擎

    Returns:
        str: Markdown 文本
    """
    converter = SmartDocumentConverter(
        mineru_api_token=mineru_api_token,
        force_engine=force_engine,
    )
    try:
        markdown, _ = converter.convert(file_path)
        return markdown
    finally:
        converter.close()
