"""
Output Quality Checker for Financial Research Reports.

Lightweight, deterministic checks that run after report generation.
- Data completeness: required sections present
- Relevance: report mentions target symbol/topic
- Citations: has a References section and numbered items
- Compliance: disclaimer exists
- Numeric sanity: detect obviously broken numbers (e.g., absurd percentages)

Return a structured result that can be logged or surfaced in UI.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import List, Optional


@dataclass
class QualityIssue:
    code: str
    message: str
    severity: str = "medium"  # low | medium | high


@dataclass
class QualityResult:
    passed: bool
    score: float
    issues: List[QualityIssue] = field(default_factory=list)


class OutputQualityChecker:
    """Heuristic quality checks for financial research outputs."""

    REQUIRED_SECTIONS = [
        "Executive Summary",
        "Financial Analysis",
        "Valuation Analysis",
        "References",
        "Risk Factors",
    ]

    DISCLAIMER_KEYWORDS = [
        "Disclaimer",
        "免责声明",
        "投资有风险",
        "does NOT constitute investment advice",
    ]

    def check(self, *, report: str, symbol: Optional[str] = None, topic: Optional[str] = None) -> QualityResult:
        issues: List[QualityIssue] = []

        # 1) Data completeness: required headings
        present = 0
        for sec in self.REQUIRED_SECTIONS:
            if re.search(rf"^##\s+{re.escape(sec)}\b", report, flags=re.IGNORECASE | re.MULTILINE):
                present += 1
            else:
                issues.append(QualityIssue(code="missing_section", message=f"Section '{sec}' is missing", severity="high"))

        # 2) Relevance: symbol/topic mentioned multiple times
        relevance_hits = 0
        tokens = []
        if symbol:
            tokens.append(symbol)
        if topic:
            tokens.append(topic)
        for t in filter(None, tokens):
            # count occurrences case-insensitively
            hits = len(re.findall(re.escape(t), report, flags=re.IGNORECASE))
            relevance_hits += hits
        if (symbol or topic) and relevance_hits < 3:
            issues.append(QualityIssue(code="low_relevance", message="Report barely mentions target (symbol/topic)", severity="medium"))

        # 3) Citations: References section + at least 2 numbered entries
        has_refs = re.search(r"^##\s+(References|参考来源)\b", report, flags=re.IGNORECASE | re.MULTILINE) is not None
        if not has_refs:
            issues.append(QualityIssue(code="no_references", message="References section missing", severity="high"))
        else:
            numbered = len(re.findall(r"^\s*\[\d+\]", report, flags=re.MULTILINE))
            if numbered < 2:
                issues.append(QualityIssue(code="insufficient_citations", message="Fewer than 2 citations", severity="medium"))

        # 4) Compliance: disclaimer keywords present
        has_disclaimer = any(kw.lower() in report.lower() for kw in self.DISCLAIMER_KEYWORDS)
        if not has_disclaimer:
            issues.append(QualityIssue(code="no_disclaimer", message="Compliance disclaimer missing", severity="high"))

        # 5) Numeric sanity: extremely large percentages (> 1000%) suggest hallucination
        percents = [float(p) for p in re.findall(r"(-?\d+(?:\.\d+)?)%", report)]
        if any(abs(p) > 1000 for p in percents):
            issues.append(QualityIssue(code="absurd_percentage", message="Found absurd percentage value (>1000%)", severity="low"))

        # Score: start at 100 and subtract penalties
        score = 100.0
        for issue in issues:
            if issue.severity == "high":
                score -= 25
            elif issue.severity == "medium":
                score -= 12
            else:
                score -= 5
        score = max(0.0, min(100.0, score))

        # Pass criteria: score >= 70 and no high-severity missing sections
        passed = score >= 70 and not any(i.severity == "high" and i.code in {"missing_section", "no_references", "no_disclaimer"} for i in issues)

        return QualityResult(passed=passed, score=score, issues=issues)