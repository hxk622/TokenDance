"""Compliance checker for financial data crawling.

合规检查模块，确保金融数据处理符合法规要求：
- 网络爬取白名单/黑名单控制
- 投资建议拦截
- 内幕信息拦截
- 市场操纵等禁止行为检测

重要：任何金融分析结果都不构成投资建议
"""

import os
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from urllib.parse import urlparse

import yaml


@dataclass
class DomainConfig:
    """Configuration for a single domain."""
    domain: str
    enabled: bool = True
    rate_limit: int = 10  # requests per minute
    description: str = ""
    paths: list[str] = field(default_factory=list)
    reason: str = ""  # For blacklisted domains


@dataclass
class CrawlingRules:
    """Global crawling rules."""
    respect_robots_txt: bool = True
    max_concurrent_requests: int = 3
    default_delay: int = 2
    user_agent: str = "TokenDance/1.0"
    timeout: int = 30
    max_retries: int = 3
    retry_delay: int = 5


class ComplianceViolationType(Enum):
    """合规违规类型"""
    INVESTMENT_ADVICE = "investment_advice"       # 投资建议
    INSIDER_INFORMATION = "insider_information"   # 内幕信息
    MARKET_MANIPULATION = "market_manipulation"   # 市场操纵
    PRICE_PREDICTION = "price_prediction"         # 价格预测
    GUARANTEE_RETURN = "guarantee_return"         # 承诺收益
    DOMAIN_BLOCKED = "domain_blocked"             # 域名被拦截


@dataclass
class ComplianceCheckResult:
    """合规检查结果"""
    passed: bool
    violation_type: ComplianceViolationType | None = None
    reason: str = ""
    suggestion: str = ""


@dataclass
class ComplianceConfig:
    """Full compliance configuration."""
    enable_web_crawling: bool = True
    mode: str = "whitelist"  # whitelist | blacklist | disabled
    whitelist: list[DomainConfig] = field(default_factory=list)
    blacklist: list[DomainConfig] = field(default_factory=list)
    crawling_rules: CrawlingRules = field(default_factory=CrawlingRules)
    disclaimer: str = ""

    # Structured data sources
    openbb_enabled: bool = True
    openbb_providers: list[str] = field(default_factory=list)
    akshare_enabled: bool = True
    tushare_enabled: bool = False

    # Content compliance
    block_investment_advice: bool = True
    block_price_predictions: bool = True
    block_insider_info: bool = True


class ComplianceChecker:
    """
    Compliance checker for financial data crawling.

    Enforces whitelist/blacklist rules for web crawling to ensure
    compliance with platform ToS and legal requirements.
    """

    def __init__(self, config_path: str | None = None):
        """
        Initialize compliance checker.

        Args:
            config_path: Path to compliance config file.
                        If None, uses default path.
        """
        if config_path is None:
            # Default config path
            config_path = os.path.join(
                Path(__file__).parent.parent.parent.parent.parent.parent,
                "config",
                "financial_compliance.yaml"
            )

        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> ComplianceConfig:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, encoding="utf-8") as f:
                raw_config = yaml.safe_load(f)
        except FileNotFoundError:
            # Return default config if file not found
            return ComplianceConfig()

        compliance = raw_config.get("compliance", {})

        # Parse whitelist
        whitelist = []
        for item in compliance.get("unstructured_data", {}).get("whitelist", []):
            whitelist.append(DomainConfig(
                domain=item.get("domain", ""),
                enabled=item.get("enabled", True),
                rate_limit=item.get("rate_limit", 10),
                description=item.get("description", ""),
                paths=item.get("paths", []),
            ))

        # Parse blacklist
        blacklist = []
        for item in compliance.get("unstructured_data", {}).get("blacklist", []):
            blacklist.append(DomainConfig(
                domain=item.get("domain", ""),
                reason=item.get("reason", ""),
            ))

        # Parse crawling rules
        rules_config = compliance.get("crawling_rules", {})
        crawling_rules = CrawlingRules(
            respect_robots_txt=rules_config.get("respect_robots_txt", True),
            max_concurrent_requests=rules_config.get("max_concurrent_requests", 3),
            default_delay=rules_config.get("default_delay", 2),
            user_agent=rules_config.get("user_agent", "TokenDance/1.0"),
            timeout=rules_config.get("timeout", 30),
            max_retries=rules_config.get("max_retries", 3),
            retry_delay=rules_config.get("retry_delay", 5),
        )

        # Parse structured data config
        structured = compliance.get("structured_data", {})
        openbb_config = structured.get("openbb", {})

        return ComplianceConfig(
            enable_web_crawling=compliance.get("enable_web_crawling", True),
            mode=compliance.get("unstructured_data", {}).get("mode", "whitelist"),
            whitelist=whitelist,
            blacklist=blacklist,
            crawling_rules=crawling_rules,
            disclaimer=compliance.get("disclaimer", ""),
            openbb_enabled=openbb_config.get("enabled", True),
            openbb_providers=openbb_config.get("providers", []),
            akshare_enabled=structured.get("akshare", {}).get("enabled", True),
            tushare_enabled=structured.get("tushare", {}).get("enabled", False),
        )

    def can_crawl(self, url: str) -> tuple[bool, str]:
        """
        Check if a URL can be crawled.

        Args:
            url: The URL to check.

        Returns:
            Tuple of (can_crawl, reason).
        """
        # Global switch
        if not self.config.enable_web_crawling:
            return False, "Web crawling is globally disabled"

        # Mode check
        if self.config.mode == "disabled":
            return False, "Unstructured data crawling is disabled"

        # Parse domain from URL
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        # Remove www. prefix if present
        if domain.startswith("www."):
            domain = domain[4:]

        # Check blacklist (always enforced)
        for blocked in self.config.blacklist:
            if domain == blocked.domain or domain.endswith("." + blocked.domain):
                return False, f"Domain {domain} is blacklisted: {blocked.reason}"

        # Whitelist mode
        if self.config.mode == "whitelist":
            for allowed in self.config.whitelist:
                if not allowed.enabled:
                    continue
                if domain == allowed.domain or domain.endswith("." + allowed.domain):
                    return True, f"Domain {domain} is whitelisted"
            return False, f"Domain {domain} is not in whitelist"

        # Blacklist mode (default allow)
        return True, "OK"

    def get_rate_limit(self, url: str) -> int:
        """
        Get rate limit for a URL.

        Args:
            url: The URL to check.

        Returns:
            Rate limit in requests per minute.
        """
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        if domain.startswith("www."):
            domain = domain[4:]

        for allowed in self.config.whitelist:
            if domain == allowed.domain or domain.endswith("." + allowed.domain):
                return allowed.rate_limit

        return 10  # Default rate limit

    def get_domain_config(self, url: str) -> DomainConfig | None:
        """
        Get configuration for a domain.

        Args:
            url: The URL to check.

        Returns:
            DomainConfig if found, None otherwise.
        """
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        if domain.startswith("www."):
            domain = domain[4:]

        for config in self.config.whitelist:
            if domain == config.domain or domain.endswith("." + config.domain):
                return config

        return None

    def is_structured_source_enabled(self, source: str) -> bool:
        """
        Check if a structured data source is enabled.

        Args:
            source: Source name (openbb, akshare, tushare).

        Returns:
            True if enabled.
        """
        source = source.lower()
        if source == "openbb":
            return self.config.openbb_enabled
        elif source == "akshare":
            return self.config.akshare_enabled
        elif source == "tushare":
            return self.config.tushare_enabled
        return False

    def get_disclaimer(self) -> str:
        """Get the disclaimer text."""
        return self.config.disclaimer

    def get_crawling_rules(self) -> CrawlingRules:
        """Get crawling rules."""
        return self.config.crawling_rules

    def reload_config(self) -> None:
        """Reload configuration from file."""
        self.config = self._load_config()

    # ========== 内容合规检查 ==========

    def check_content(self, text: str) -> ComplianceCheckResult:
        """
        检查文本内容是否合规.

        Args:
            text: 要检查的文本内容

        Returns:
            ComplianceCheckResult
        """
        text_lower = text.lower()

        # 检查投资建议
        if self.config.block_investment_advice:
            result = self._check_investment_advice(text_lower)
            if not result.passed:
                return result

        # 检查价格预测
        if self.config.block_price_predictions:
            result = self._check_price_prediction(text_lower)
            if not result.passed:
                return result

        # 检查内幕信息
        if self.config.block_insider_info:
            result = self._check_insider_info(text_lower)
            if not result.passed:
                return result

        # 检查收益承诺
        result = self._check_guarantee_return(text_lower)
        if not result.passed:
            return result

        return ComplianceCheckResult(passed=True)

    def _check_investment_advice(self, text: str) -> ComplianceCheckResult:
        """检查是否包含投资建议"""
        # 投资建议关键词（中文 + 英文）
        advice_patterns = [
            # 直接建议
            r"建议.{0,5}买入", r"建议.{0,5}卖出", r"建议.{0,5}持有",
            r"建议.{0,5}增持", r"建议.{0,5}减持", r"建议.{0,5}清仓",
            r"应该.{0,5}买入", r"应该.{0,5}卖出",
            r"推荐.{0,5}买入", r"推荐.{0,5}卖出", r"强烈推荐",
            r"buy.{0,10}recommendation", r"sell.{0,10}recommendation",
            r"strong buy", r"strong sell",
            # 目标价
            r"目标价.{0,5}\d+", r"target price",
            # 评级
            r"评级.{0,3}买入", r"评级.{0,3}增持",
        ]

        for pattern in advice_patterns:
            if re.search(pattern, text):
                return ComplianceCheckResult(
                    passed=False,
                    violation_type=ComplianceViolationType.INVESTMENT_ADVICE,
                    reason="检测到投资建议内容",
                    suggestion="请修改为客观分析，避免直接给出买卖建议",
                )

        return ComplianceCheckResult(passed=True)

    def _check_price_prediction(self, text: str) -> ComplianceCheckResult:
        """检查是否包含价格预测"""
        prediction_patterns = [
            r"将会?.{0,5}上涨", r"将会?.{0,5}下跌",
            r"股价.{0,5}到达", r"涨到.{0,3}\d+",
            r"预计.{0,5}上涨", r"预计.{0,5}下跌",
            r"必将.{0,5}突破", r"肯定.{0,5}涨",
            r"will rise", r"will fall", r"will reach",
            r"guaranteed to", r"definitely",
        ]

        for pattern in prediction_patterns:
            if re.search(pattern, text):
                return ComplianceCheckResult(
                    passed=False,
                    violation_type=ComplianceViolationType.PRICE_PREDICTION,
                    reason="检测到价格预测内容",
                    suggestion="请使用不确定性语言，如'可能'、'或许'",
                )

        return ComplianceCheckResult(passed=True)

    def _check_insider_info(self, text: str) -> ComplianceCheckResult:
        """检查是否包含内幕信息"""
        insider_patterns = [
            r"内幕.{0,5}消息", r"内部.{0,5}消息",
            r"尚未公开", r"即将公布",
            r"秘密.{0,5}消息", r"独家.{0,5}消息",
            r"insider", r"non-public", r"confidential",
        ]

        for pattern in insider_patterns:
            if re.search(pattern, text):
                return ComplianceCheckResult(
                    passed=False,
                    violation_type=ComplianceViolationType.INSIDER_INFORMATION,
                    reason="检测到疑似内幕信息",
                    suggestion="请确保所有信息来源于公开渠道",
                )

        return ComplianceCheckResult(passed=True)

    def _check_guarantee_return(self, text: str) -> ComplianceCheckResult:
        """检查是否包含收益承诺"""
        guarantee_patterns = [
            r"保证.{0,5}收益", r"保证.{0,5}回报",
            r"稳赚不赔", r"零风险",
            r"年化.{0,5}\d+%", r"收益率.{0,5}\d+%",
            r"guaranteed return", r"no risk", r"risk-free",
        ]

        for pattern in guarantee_patterns:
            if re.search(pattern, text):
                return ComplianceCheckResult(
                    passed=False,
                    violation_type=ComplianceViolationType.GUARANTEE_RETURN,
                    reason="检测到收益承诺内容",
                    suggestion="投资有风险，不应承诺固定收益",
                )

        return ComplianceCheckResult(passed=True)

    def add_disclaimer(self, content: str) -> str:
        """
        为内容添加免责声明.

        Args:
            content: 原始内容

        Returns:
            添加了免责声明的内容
        """
        disclaimer = self.get_disclaimer() or self.DEFAULT_DISCLAIMER
        return f"{content}\n\n---\n**免责声明**: {disclaimer}"

    DEFAULT_DISCLAIMER = (
        "以上内容仅供参考，不构成任何投资建议。"
        "投资有风险，入市须谨慎。"
        "请根据自身情况独立判断，并咨询专业顾问。"
    )


# Singleton instance
_compliance_checker: ComplianceChecker | None = None


def get_compliance_checker(config_path: str | None = None) -> ComplianceChecker:
    """
    Get the global compliance checker instance.

    Args:
        config_path: Optional path to config file.

    Returns:
        ComplianceChecker instance.
    """
    global _compliance_checker

    if _compliance_checker is None or config_path is not None:
        _compliance_checker = ComplianceChecker(config_path)

    return _compliance_checker
