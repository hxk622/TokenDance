from app.agent.quality.output_checker import OutputQualityChecker


def test_output_checker_detects_missing_parts():
    text = """
# Test Report

## Executive Summary
- Summary here

## Financial Analysis
- Details

## Valuation Analysis
- Details

## References
[1] Example - example.com
"""
    qc = OutputQualityChecker()
    result = qc.check(report=text, symbol="AAPL")
    # Missing risk factors and disclaimer
    assert not result.passed
    codes = {i.code for i in result.issues}
    assert "missing_section" in codes or "no_disclaimer" in codes


def test_output_checker_passes_reasonable_report():
    text = """
# Report

## Executive Summary
- Summary

## Financial Analysis
- ROE: 20%

## Valuation Analysis
- PE 25x

## Risk Factors
- Regulation

## References
[1] Title - example.com
[2] Title - example.org

## ⚠️ 免责声明 / Disclaimer
本报告仅为信息整合与分析参考，不构成任何投资建议。
"""
    qc = OutputQualityChecker()
    result = qc.check(report=text, symbol="AAPL")
    assert result.passed
    assert result.score >= 70
