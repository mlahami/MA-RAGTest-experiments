def _has_rate_limit_signal(state: dict) -> bool:
    test_design = state.get("test_design", {}) or {}
    analyzer = state.get("analyzer_report", {}) or {}
    reason = state.get("evaluation_reason", "") or ""

    haystack = [
        str(test_design.get("error", "")),
        str(analyzer),
        str(reason),
    ]
    blob = "\n".join(haystack).lower()
    return ("429" in blob) or ("rate limit" in blob) or ("rate_limited" in blob)


def _coverage_totals_from_report(coverage_report: dict) -> tuple[int, int, int]:
    """
    Retourne (statements_total, branches_total, functions_total).
    Supporte coverage-summary.json et coverage-final.json.
    """
    total = coverage_report.get("total") if isinstance(coverage_report, dict) else None
    if isinstance(total, dict):
        statements_total = int((total.get("statements") or {}).get("total", 0) or 0)
        branches_total = int((total.get("branches") or {}).get("total", 0) or 0)
        functions_total = int((total.get("functions") or {}).get("total", 0) or 0)
        return statements_total, branches_total, functions_total

    # coverage-final.json fallback
    statements_total = branches_total = functions_total = 0
    if isinstance(coverage_report, dict):
        for file_data in coverage_report.values():
            if not isinstance(file_data, dict):
                continue
            statements_total += len(file_data.get("s", {}) or {})
            functions_total += len(file_data.get("f", {}) or {})
            for hits in (file_data.get("b", {}) or {}).values():
                if isinstance(hits, list):
                    branches_total += len(hits)
    return statements_total, branches_total, functions_total
