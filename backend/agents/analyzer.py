"""
analyzer.py
-----------
LangGraph agent responsible for analyzing generated-test results.

The implementation is deterministic (no LLM call) to avoid hallucinated
recommendations that ask to modify the Solidity contract.
"""

from __future__ import annotations

from backend.utils.analyzer_utils import _extract_failures, _extract_missing_coverage, _extract_test_tags


def analyzer_node(state: dict) -> dict:
    """
    LangGraph node: ANALYZER.

    Inputs:
    - contract_code
    - test_code
    - test_report
    - coverage_report

    Output:
    - analyzer_report
    """
    print("--- ANALYZER ---")

    test_report = state.get("test_report", {})

    if not state.get("test_code", "").strip():
        print("[Analyzer] Warning: empty test_code in state.")
    if not test_report:
        print("[Analyzer] Warning: empty test_report; Hardhat did not produce a report.")
    else:
        stats = test_report.get("stats", {})
        print(
            "[Analyzer] Report received: "
            f"{stats.get('passes', 0)} passed, "
            f"{stats.get('failures', 0)} failed "
            f"(total {stats.get('tests', 0)})."
        )

    failures = _extract_failures(test_report)
    missing_coverage = _extract_missing_coverage(state.get("coverage_report", {}))
    test_tags = _extract_test_tags(test_report)

    security_tags = [tag for tag in test_tags if tag["category"] == "security"]
    security_summary = {
        "total": len(security_tags),
        "passed": sum(1 for tag in security_tags if tag["passed"]),
        "failed": sum(1 for tag in security_tags if not tag["passed"]),
        "swc_ids_covered": sorted({tag["swc_id"] for tag in security_tags if tag["swc_id"]}),
    }

    invalid_failure_types = {
        "UNDEFINED_HELPER_CONTRACT",
        "UNDEFINED_SYMBOL",
        "CALL_ERROR",
        "INVALID_JS_SYNTAX",
        "BIGINT_MIX",
    }
    invalid_failures = [
        failure for failure in failures
        if isinstance(failure, dict)
        and str(failure.get("type", "")).upper() in invalid_failure_types
    ]
    invalid_summary = {
        "total": len(invalid_failures),
        "undefined_helper_contract": sum(
            1 for failure in invalid_failures
            if str(failure.get("type", "")).upper() == "UNDEFINED_HELPER_CONTRACT"
        ),
        "undefined_symbol": sum(
            1 for failure in invalid_failures
            if str(failure.get("type", "")).upper() == "UNDEFINED_SYMBOL"
        ),
        "call_error": sum(
            1 for failure in invalid_failures
            if str(failure.get("type", "")).upper() == "CALL_ERROR"
        ),
        "invalid_js_syntax": sum(
            1 for failure in invalid_failures
            if str(failure.get("type", "")).upper() == "INVALID_JS_SYNTAX"
        ),
        "bigint_mix": sum(
            1 for failure in invalid_failures
            if str(failure.get("type", "")).upper() == "BIGINT_MIX"
        ),
    }

    suggestions: list[str] = []
    if failures:
        suggestions.append("Fix the failing generated tests listed in failures.")
    if missing_coverage["branches"]:
        suggestions.append("Add executable tests for the contract's existing branch paths.")

    result = {
        "failures": failures,
        "missing_coverage": missing_coverage,
        "suggestions": suggestions,
        "test_tags": test_tags,
        "security_summary": security_summary,
        "invalid_summary": invalid_summary,
    }

    covered_swc = ", ".join(security_summary["swc_ids_covered"]) or "none"
    print(f"[Analyzer] Identified {len(failures)} failure(s).")
    print(
        "[Analyzer] Security-tagged tests: "
        f"{security_summary['passed']}/{security_summary['total']} passed "
        f"(covered SWC IDs: {covered_swc})."
    )

    return {"analyzer_report": result}
