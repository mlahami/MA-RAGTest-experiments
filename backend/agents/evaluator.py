"""
evaluator.py
------------
LangGraph agent responsible for deciding whether to stop or regenerate tests.
"""

from __future__ import annotations

from backend.utils.evaluator_utils import _coverage_totals_from_report, _has_rate_limit_signal


def evaluator_node(state: dict) -> dict:
    """
    LangGraph node: EVALUATOR.

    Inputs:
    - execution_summary
    - analyzer_report

    Outputs:
    - evaluation_decision
    - evaluation_reason
    """
    print("--- EVALUATOR ---")

    summary = state.get("execution_summary", {}) or {}
    coverage = summary.get("coverage", {}) or {}
    total = int(summary.get("total", 0) or 0)
    failed = int(summary.get("failed", 0) or 0)
    stmts_pct = float(coverage.get("statements", 0) or 0)
    branches_pct = float(coverage.get("branches", 0) or 0)
    rate_limited = _has_rate_limit_signal(state)

    coverage_report = state.get("coverage_report", {}) or {}
    _stmts_total, branches_total, _funcs_total = _coverage_totals_from_report(coverage_report)

    # Deterministic policy:
    # - If tests still fail, regenerate.
    # - Branch coverage >= 80% is required only when the contract has instrumented branches.
    # - If all tests pass and applicable thresholds are satisfied, stop.
    if total == 0:
        decision = "stop"
        reason = "No tests were executed; stopping to avoid an empty regeneration loop."
    elif failed > 0:
        decision = "regenerate"
        reason = f"{failed} test(s) failed; generated tests need correction."
    elif rate_limited:
        decision = "stop"
        reason = "API rate limit signal detected (429); stop and rerun after the quota cooldown."
    else:
        # Robust stop condition: when all tests pass and statement coverage is already high,
        # avoid costly extra iterations.
        if stmts_pct >= 90:
            decision = "stop"
            reason = (
                "All tests pass and statement coverage is high "
                f"({stmts_pct:.1f}%). Stopping to avoid unnecessary regeneration."
            )
            return {
                "evaluation_decision": decision,
                "evaluation_reason": reason,
            }

        statements_ok = stmts_pct >= 85
        branches_required = branches_total > 0
        branches_ok = (branches_pct >= 80) if branches_required else True

        if statements_ok and branches_ok:
            decision = "stop"
            if branches_required:
                reason = "All tests pass and the applicable coverage thresholds are satisfied."
            else:
                reason = "All tests pass; the target contract has no instrumented branches to cover."
        else:
            decision = "regenerate"
            if not statements_ok:
                reason = f"Insufficient statement coverage ({stmts_pct:.1f}% < 85%)."
            else:
                reason = f"Insufficient branch coverage ({branches_pct:.1f}% < 80%)."

    return {
        "evaluation_decision": decision,
        "evaluation_reason": reason,
    }
