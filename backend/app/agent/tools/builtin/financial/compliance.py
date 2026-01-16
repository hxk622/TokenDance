"""Compliance checker for financial data crawling."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
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
            with open(self.config_path, "r", encoding="utf-8") as f:
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
