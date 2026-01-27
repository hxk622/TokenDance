"""
Datetime 工具函数

解决 Python 3.12+ 废弃 datetime.utcnow() 的问题。
统一使用 timezone-aware datetime 对象。

用法：
    from app.core.datetime_utils import utc_now

    # 替代 datetime.utcnow()
    now = utc_now()
"""

from datetime import UTC, datetime


def utc_now() -> datetime:
    """获取当前 UTC 时间（timezone-aware）

    替代已废弃的 datetime.utcnow()

    Returns:
        当前 UTC 时间，带 timezone 信息
    """
    return datetime.now(UTC)


def utc_now_naive() -> datetime:
    """获取当前 UTC 时间（naive，无 timezone 信息）

    用于兼容现有代码，避免 timezone-aware vs naive 比较问题。
    新代码应该使用 utc_now()。

    Returns:
        当前 UTC 时间，不带 timezone 信息
    """
    return datetime.now(UTC).replace(tzinfo=None)
