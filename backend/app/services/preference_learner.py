"""
PreferenceLearner - 用户偏好学习服务

从用户行为中学习偏好，实现：
1. 隐式学习 - 从用户的跳过、点赞、深度调整等行为中学习
2. 显式设置 - 用户主动配置的偏好
3. 偏好应用 - 将学习到的偏好应用到研究配置中
"""
import logging
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.datetime_utils import utc_now_naive
from app.models.user_preference import (
    ExpertiseLevel,
    ReportStyle,
    ResearchDepth,
    UserResearchPreference,
)

logger = logging.getLogger(__name__)


class PreferenceLearner:
    """用户偏好学习器

    负责从用户行为中学习偏好，并将偏好应用到研究配置中。
    """

    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = user_id
        self._preference: UserResearchPreference | None = None

    async def get_or_create_preference(self) -> UserResearchPreference:
        """获取或创建用户偏好"""
        if self._preference:
            return self._preference

        result = await self.db.execute(
            select(UserResearchPreference)
            .where(UserResearchPreference.user_id == self.user_id)
        )
        preference = result.scalar_one_or_none()

        if not preference:
            preference = UserResearchPreference(user_id=self.user_id)
            self.db.add(preference)
            await self.db.commit()
            await self.db.refresh(preference)
            logger.info(f"Created new preference for user {self.user_id}")

        self._preference = preference
        return preference

    async def learn_from_interaction(
        self,
        event_type: str,
        context: dict
    ) -> None:
        """从用户交互中学习偏好

        Args:
            event_type: 交互类型
                - skip_source: 跳过某来源
                - like_finding: 点赞某发现
                - dislike_finding: 踩某发现
                - adjust_depth: 调整研究深度
                - select_source: 选择某来源
                - block_domain: 屏蔽某域名
            context: 交互上下文
        """
        preference = await self.get_or_create_preference()

        if event_type == "skip_source":
            await self._learn_from_skip(preference, context)
        elif event_type == "like_finding":
            await self._learn_from_like(preference, context)
        elif event_type == "dislike_finding":
            await self._learn_from_dislike(preference, context)
        elif event_type == "adjust_depth":
            await self._learn_from_depth_adjustment(preference, context)
        elif event_type == "select_source":
            await self._learn_from_selection(preference, context)
        elif event_type == "block_domain":
            await self._learn_from_block(preference, context)

        # 更新交互计数
        preference.interaction_count += 1
        await self.db.commit()

    async def _learn_from_skip(
        self,
        preference: UserResearchPreference,
        context: dict
    ) -> None:
        """从跳过来源中学习"""
        url = context.get("url", "")
        context.get("reason", "")

        if not url:
            return

        domain = self._extract_domain(url)
        if not domain:
            return

        # 更新域名分数 (降低)
        scores = dict(preference.domain_scores or {})
        current_score = scores.get(domain, 0)
        scores[domain] = current_score - 1
        preference.domain_scores = scores

        # 如果连续跳过多次，自动加入屏蔽列表
        if scores[domain] <= -3:
            blocked = list(preference.blocked_domains or [])
            if domain not in blocked:
                blocked.append(domain)
                preference.blocked_domains = blocked
                logger.info(f"Auto-blocked domain {domain} for user {self.user_id}")

        logger.debug(f"Learned skip: {domain} -> score={scores[domain]}")

    async def _learn_from_like(
        self,
        preference: UserResearchPreference,
        context: dict
    ) -> None:
        """从点赞中学习"""
        source_type = context.get("source_type", "")
        url = context.get("url", "")

        # 更新来源类型分数
        if source_type:
            scores = dict(preference.source_type_scores or {})
            scores[source_type] = scores.get(source_type, 0) + 1
            preference.source_type_scores = scores

        # 更新域名分数
        if url:
            domain = self._extract_domain(url)
            if domain:
                d_scores = dict(preference.domain_scores or {})
                d_scores[domain] = d_scores.get(domain, 0) + 1
                preference.domain_scores = d_scores

                # 如果多次点赞，加入信任列表
                if d_scores[domain] >= 3:
                    trusted = list(preference.trusted_domains or [])
                    if domain not in trusted:
                        trusted.append(domain)
                        preference.trusted_domains = trusted
                        logger.info(f"Auto-trusted domain {domain} for user {self.user_id}")

    async def _learn_from_dislike(
        self,
        preference: UserResearchPreference,
        context: dict
    ) -> None:
        """从踩中学习"""
        source_type = context.get("source_type", "")
        url = context.get("url", "")

        if source_type:
            scores = dict(preference.source_type_scores or {})
            scores[source_type] = scores.get(source_type, 0) - 1
            preference.source_type_scores = scores

        if url:
            domain = self._extract_domain(url)
            if domain:
                d_scores = dict(preference.domain_scores or {})
                d_scores[domain] = d_scores.get(domain, 0) - 1
                preference.domain_scores = d_scores

    async def _learn_from_depth_adjustment(
        self,
        preference: UserResearchPreference,
        context: dict
    ) -> None:
        """从深度调整中学习"""
        new_depth = context.get("new_depth", "")
        previous_depth = context.get("previous_depth", "")

        # 记录调整历史
        adjustments = list(preference.depth_adjustments or [])
        adjustments.append({
            "from": previous_depth,
            "to": new_depth,
            "timestamp": utc_now_naive().isoformat()
        })

        # 只保留最近 10 次调整
        preference.depth_adjustments = adjustments[-10:]

        # 如果连续 3 次调整到同一深度，更新默认深度
        if len(adjustments) >= 3:
            recent = [a["to"] for a in adjustments[-3:]]
            if len(set(recent)) == 1:
                depth_str = recent[0]
                try:
                    new_default = ResearchDepth(depth_str)
                    if preference.default_depth != new_default:
                        preference.default_depth = new_default
                        logger.info(
                            f"Auto-updated default depth to {depth_str} "
                            f"for user {self.user_id}"
                        )
                except ValueError:
                    pass

    async def _learn_from_selection(
        self,
        preference: UserResearchPreference,
        context: dict
    ) -> None:
        """从来源选择中学习"""
        url = context.get("url", "")
        source_type = context.get("source_type", "")

        if url:
            domain = self._extract_domain(url)
            if domain:
                scores = dict(preference.domain_scores or {})
                scores[domain] = scores.get(domain, 0) + 0.5
                preference.domain_scores = scores

        if source_type:
            scores = dict(preference.source_type_scores or {})
            scores[source_type] = scores.get(source_type, 0) + 0.5
            preference.source_type_scores = scores

    async def _learn_from_block(
        self,
        preference: UserResearchPreference,
        context: dict
    ) -> None:
        """从屏蔽操作中学习"""
        domain = context.get("domain", "")
        if not domain:
            url = context.get("url", "")
            domain = self._extract_domain(url) if url else ""

        if domain:
            blocked = list(preference.blocked_domains or [])
            if domain not in blocked:
                blocked.append(domain)
                preference.blocked_domains = blocked

            # 更新域名分数
            scores = dict(preference.domain_scores or {})
            scores[domain] = -10  # 强制负分
            preference.domain_scores = scores

    async def update_explicit_preference(
        self,
        updates: dict
    ) -> UserResearchPreference:
        """更新用户显式设置的偏好

        Args:
            updates: 要更新的字段字典
        """
        preference = await self.get_or_create_preference()

        # 允许更新的字段
        allowed_fields = {
            "preferred_source_types",
            "trusted_domains",
            "blocked_domains",
            "preferred_languages",
            "default_depth",
            "default_breadth",
            "expertise_level",
            "expertise_domains",
            "preferred_report_style",
            "include_charts",
            "include_citations",
        }

        for key, value in updates.items():
            if key not in allowed_fields:
                continue

            # 枚举类型转换
            if key == "default_depth" and isinstance(value, str):
                value = ResearchDepth(value)
            elif key == "expertise_level" and isinstance(value, str):
                value = ExpertiseLevel(value)
            elif key == "preferred_report_style" and isinstance(value, str):
                value = ReportStyle(value)

            setattr(preference, key, value)

        await self.db.commit()
        await self.db.refresh(preference)

        logger.info(f"Updated explicit preference for user {self.user_id}")
        return preference

    async def get_research_config(self) -> dict:
        """获取用于研究的配置

        将用户偏好转换为研究配置参数。
        """
        preference = await self.get_or_create_preference()

        # 深度转换为来源数量
        depth_to_sources = {
            ResearchDepth.QUICK: 5,
            ResearchDepth.STANDARD: 10,
            ResearchDepth.DEEP: 18,
        }

        # 根据来源类型分数排序偏好
        source_types = preference.preferred_source_types or []
        type_scores = preference.source_type_scores or {}

        # 按分数排序
        sorted_types = sorted(
            source_types,
            key=lambda t: type_scores.get(t, 0),
            reverse=True
        )

        return {
            "max_sources": depth_to_sources.get(
                preference.default_depth,
                preference.default_breadth
            ),
            "preferred_source_types": sorted_types,
            "trusted_domains": preference.trusted_domains or [],
            "blocked_domains": preference.blocked_domains or [],
            "preferred_languages": preference.preferred_languages or ["zh", "en"],
            "expertise_level": preference.expertise_level.value,
            "report_style": preference.preferred_report_style.value,
            "include_charts": preference.include_charts,
            "include_citations": preference.include_citations,
            "domain_scores": preference.domain_scores or {},
        }

    def _extract_domain(self, url: str) -> str:
        """从 URL 提取域名"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            # 去掉 www. 前缀
            if domain.startswith("www."):
                domain = domain[4:]
            return domain
        except Exception:
            return ""


async def get_preference_learner(
    db: AsyncSession,
    user_id: str
) -> PreferenceLearner:
    """获取偏好学习器实例"""
    return PreferenceLearner(db, user_id)
