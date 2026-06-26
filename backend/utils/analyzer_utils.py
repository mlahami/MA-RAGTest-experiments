from typing import Any
import re


_SECURITY_TAG_RE = re.compile(r"^\[SECURITY:([A-Za-z0-9\-]+)\]\s*(.*)$")


def _extract_test_tags(test_report: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract functional/security tags and pass status from executed tests."""
    tags: list[dict[str, Any]] = []
    for test in _iter_tests(test_report.get("results", [])):
        title = str(test.get("title") or test.get("fullTitle") or "")
        display_title = str(test.get("fullTitle") or title)
        state = (test.get("state") or "").lower()
        passed = state == "passed" or test.get("pass") is True
        match = _SECURITY_TAG_RE.match(title.strip())
        if match:
            swc_id = match.group(1).upper()
            tags.append({
                "test": display_title,
                "category": "security",
                "swc_id": None if swc_id == "NA" else swc_id,
                "passed": passed,
            })
        else:
            tags.append({
                "test": display_title,
                "category": "functional",
                "swc_id": None,
                "passed": passed,
            })
    return tags


def _iter_tests(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Flatten mochawesome-like test entries recursively."""
    out: list[dict[str, Any]] = []
    for item in results or []:
        if not isinstance(item, dict):
            continue
        if item.get("type") == "test":
            out.append(item)
        children = item.get("suites") or []
        if isinstance(children, list) and children:
            out.extend(_iter_tests(children))
        direct_tests = item.get("tests") or []
        if isinstance(direct_tests, list):
            for test in direct_tests:
                if isinstance(test, dict):
                    out.append(test)
    return out


def _extract_failures(test_report: dict[str, Any]) -> list[dict[str, str]]:
    failures: list[dict[str, str]] = []

    if str(test_report.get("error", "")).lower().startswith("invalid generated test suite"):
        combined = f"{test_report.get('stderr', '')}\n{test_report.get('stdout', '')}"
        reason = _extract_primary_runtime_error(combined)
        failure_type, fix = _classify_failure(reason)
        return [{
            "test": "<invalid generated test suite>",
            "reason": reason,
            "type": failure_type,
            "fix": fix,
            "test_code": "",
        }]

    for test in _iter_tests(test_report.get("results", [])):
        state = (test.get("state") or "").lower()
        if state != "failed":
            continue
        title = test.get("fullTitle") or test.get("title") or "<unknown test>"
        err = test.get("err") if isinstance(test.get("err"), dict) else {}
        reason = err.get("message") or err.get("estack") or "Test failed with unknown reason."
        reason = str(reason).splitlines()[0][:500]
        failure_type, fix = _classify_failure(reason)
        failures.append({
            "test": str(title),
            "reason": reason,
            "type": failure_type,
            "fix": fix,
            "test_code": str(test.get("code") or "").strip(),
        })

    stdout_failures = _extract_failures_from_stdout(str(test_report.get("stdout", "") or ""))
    if not stdout_failures:
        return failures

    by_title = {_normalize_title(item.get("test", "")): item for item in failures}
    for stdout_failure in stdout_failures:
        key = _normalize_title(stdout_failure.get("test", ""))
        if key in by_title:
            current = by_title[key]
            if "unknown reason" in current.get("reason", "").lower() or current.get("type") == "OTHER":
                current.update(stdout_failure)
        else:
            failures.append(stdout_failure)

    return failures


def _extract_primary_runtime_error(text: str) -> str:
    if not text:
        return "Invalid generated test suite."

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        ansi_clean = re.sub(r"\x1b\[[0-9;]*m", "", stripped)
        if ansi_clean.startswith((
            "SyntaxError:",
            "TypeError:",
            "ReferenceError:",
            "Error:",
            "ProviderError:",
            "HardhatError:",
        )):
            return ansi_clean[:500]

    return re.sub(r"\x1b\[[0-9;]*m", "", text.strip().splitlines()[0])[:500]


def _normalize_title(title: str) -> str:
    title = str(title or "").strip()
    title = re.sub(r"^\d+\)\s*", "", title)
    title = re.sub(r"\s+", " ", title)
    return title.lower()


def _classify_failure(reason: str) -> tuple[str, str]:
    reason_l = reason.lower()
    if "is not defined" in reason_l and any(
        name in reason_l
        for name in ("maliciouscontract", "reentrancyattacker", "attacker", "mockcontract", "fakecontract")
    ):
        return (
            "UNDEFINED_HELPER_CONTRACT",
            "Option A: remove or skip this test; do not use nonexistent helper/attacker contracts.",
        )
    if "is not defined" in reason_l:
        return ("UNDEFINED_SYMBOL", "Fix the undefined JavaScript symbol or remove the invalid test.")
    if "is not a function" in reason_l:
        return (
            "CALL_ERROR",
            "Check the function name and visibility; remove calls to absent/private/internal functions.",
        )
    if "cannot mix bigint" in reason_l:
        return (
            "BIGINT_MIX",
            "Fix Ethers v6 arithmetic: convert timestamps with Number(...) or use BigInt operands consistently.",
        )
    if "syntaxerror" in reason_l:
        return (
            "INVALID_JS_SYNTAX",
            "Fix the generated JavaScript or remove the test containing an invalid string/literal.",
        )
    if "reverted with" in reason_l or "revert" in reason_l:
        return (
            "REVERT_MISMATCH",
            "Fix test preconditions: role, state, msg.value, call order, or revert expectation.",
        )
    if "expected undefined to deeply equal" in reason_l:
        return ("ASSERTION_DATA_SHAPE", "Replace the fragile assertion with an ABI-safe assertion.")
    if "expected event" in reason_l:
        return (
            "EVENT_ASSERTION_MISMATCH",
            "Correct the event expectation according to the contract's actual behavior.",
        )
    if "assertionerror" in reason_l or "expected" in reason_l:
        return ("ASSERTION_MISMATCH", "Correct the expected value according to actual on-chain behavior.")
    return ("OTHER", "Fix only the generated test; do not modify the Solidity contract.")


def _extract_failures_from_stdout(stdout: str) -> list[dict[str, str]]:
    if not stdout or " failing" not in stdout:
        return []

    blocks = re.findall(
        r"\n\s*\d+\)\s+([\s\S]*?)(?=\n\s*\d+\)\s+|\n\n\n\n|$)",
        stdout,
    )
    failures: list[dict[str, str]] = []

    for block in blocks:
        lines = [line.rstrip() for line in block.splitlines()]
        non_empty = [line.strip() for line in lines if line.strip()]
        if not non_empty:
            continue

        title = "<unknown test>"
        error_start_idx = 0
        for idx, line in enumerate(non_empty):
            stripped = line.strip()
            if stripped.endswith(":") and not stripped.startswith((
                "AssertionError:",
                "ReferenceError:",
                "TypeError:",
                "Error:",
                "ProviderError:",
            )):
                title = stripped[:-1].strip()
                error_start_idx = idx + 1

        error_lines = non_empty[error_start_idx:]
        reason = "Test failed with unknown reason."
        for line in error_lines:
            if line.startswith("at ") or "\\node_modules\\" in line:
                continue
            reason = line.strip()
            break

        if title == "<unknown test>" and not re.match(
            r"^(AssertionError|ReferenceError|TypeError|Error|ProviderError):",
            reason,
        ):
            continue

        failure_type, fix = _classify_failure(reason)
        failures.append({
            "test": title,
            "reason": reason[:500],
            "type": failure_type,
            "fix": fix,
            "test_code": "",
        })

    return failures


def _extract_missing_coverage(coverage_report: dict[str, Any]) -> dict[str, list[str]]:
    missing = {"functions": [], "branches": [], "edge_cases": []}

    total = coverage_report.get("total") if isinstance(coverage_report, dict) else None
    if isinstance(total, dict):
        branches = total.get("branches") if isinstance(total.get("branches"), dict) else {}
        if branches.get("total", 0) and branches.get("pct", 0) < 80:
            missing["branches"].append(
                f"Insufficient branch coverage: {branches.get('pct', 0)}% / 80%"
            )

        functions = total.get("functions") if isinstance(total.get("functions"), dict) else {}
        if functions.get("total", 0) and functions.get("pct", 0) < 85:
            missing["functions"].append(
                f"Insufficient function coverage: {functions.get('pct', 0)}% / 85%"
            )

        statements = total.get("statements") if isinstance(total.get("statements"), dict) else {}
        if statements.get("total", 0) and statements.get("pct", 0) < 85:
            missing["edge_cases"].append(
                f"Insufficient statement coverage: {statements.get('pct', 0)}% / 85%"
            )

    return missing
