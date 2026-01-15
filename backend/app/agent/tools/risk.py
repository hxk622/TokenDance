"""
风险等级和操作类别定义

用于信任等级机制，支持细粒度的操作授权控制。
"""
from enum import Enum


class RiskLevel(str, Enum):
    """工具操作风险等级

    风险等级从低到高：
    - NONE: 纯读取操作，无任何副作用
    - LOW: 创建性操作，可能产生新文件但不修改现有内容
    - MEDIUM: 修改性操作，可能改变现有文件或状态
    - HIGH: 危险操作，可能造成数据丢失或系统变更
    - CRITICAL: 不可逆操作，始终需要用户确认
    """
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class OperationCategory(str, Enum):
    """操作类别

    用于细粒度的操作授权，用户可以预授权特定类别的操作。
    """
    # 网络操作
    WEB_SEARCH = "web_search"           # 网页搜索
    WEB_READ = "web_read"               # 读取网页内容
    WEB_INTERACT = "web_interact"       # 网页交互（点击、填充等）

    # 文件操作
    FILE_READ = "file_read"             # 读取文件
    FILE_CREATE = "file_create"         # 创建新文件
    FILE_MODIFY = "file_modify"         # 修改现有文件
    FILE_DELETE = "file_delete"         # 删除文件

    # Shell 操作
    SHELL_SAFE = "shell_safe"           # 安全 Shell 命令（ls, cat, grep 等只读命令）
    SHELL_WRITE = "shell_write"         # 写入类 Shell 命令
    SHELL_DANGEROUS = "shell_dangerous" # 危险 Shell 命令

    # 文档操作
    DOCUMENT_CREATE = "document_create" # 创建文档（Markdown, PDF 等）


# 风险等级优先级映射（用于比较）
RISK_PRIORITY: dict[RiskLevel, int] = {
    RiskLevel.NONE: 0,
    RiskLevel.LOW: 1,
    RiskLevel.MEDIUM: 2,
    RiskLevel.HIGH: 3,
    RiskLevel.CRITICAL: 4,
}


# 操作类别到默认风险等级的映射
CATEGORY_DEFAULT_RISK: dict[OperationCategory, RiskLevel] = {
    OperationCategory.WEB_SEARCH: RiskLevel.NONE,
    OperationCategory.WEB_READ: RiskLevel.NONE,
    OperationCategory.WEB_INTERACT: RiskLevel.LOW,
    OperationCategory.FILE_READ: RiskLevel.NONE,
    OperationCategory.FILE_CREATE: RiskLevel.LOW,
    OperationCategory.FILE_MODIFY: RiskLevel.MEDIUM,
    OperationCategory.FILE_DELETE: RiskLevel.MEDIUM,
    OperationCategory.SHELL_SAFE: RiskLevel.LOW,
    OperationCategory.SHELL_WRITE: RiskLevel.HIGH,
    OperationCategory.SHELL_DANGEROUS: RiskLevel.CRITICAL,
    OperationCategory.DOCUMENT_CREATE: RiskLevel.LOW,
}


def compare_risk_levels(level1: RiskLevel, level2: RiskLevel) -> int:
    """比较两个风险等级

    Args:
        level1: 第一个风险等级
        level2: 第二个风险等级

    Returns:
        int: 负数表示 level1 < level2，0 表示相等，正数表示 level1 > level2
    """
    return RISK_PRIORITY[level1] - RISK_PRIORITY[level2]


def is_risk_within_threshold(risk: RiskLevel, threshold: RiskLevel) -> bool:
    """检查风险等级是否在阈值范围内

    Args:
        risk: 要检查的风险等级
        threshold: 阈值风险等级

    Returns:
        bool: 如果 risk <= threshold 返回 True
    """
    return RISK_PRIORITY[risk] <= RISK_PRIORITY[threshold]
