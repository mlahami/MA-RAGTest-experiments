"""
run_all_contracts.py
--------------------
Run the backend workflow sequentially for all Solidity contracts found in
the root contracts folder, with matching .specs.md files when available.

Usage:
    python backend/run_all_contracts.py

Output:
- Console TABLE WITHOUT ITERATIONS (single pass)
- Console FINAL TABLE AFTER ITERATIONS
- outputs/batch_reports/batch_results_no_iterations.json
- outputs/batch_reports/batch_results_no_iterations.csv
- outputs/batch_reports/batch_results_final.json
- outputs/batch_reports/batch_results_final.csv
"""

from __future__ import annotations

import csv
import json
import shutil
import sys
import time
from pathlib import Path


# Allow direct execution from project root.
_ROOT = Path(__file__).parent.parent.resolve()
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from backend.config.settings import (
    BASE_DIR,
    DEFAULT_BRANCH_COVERAGE_THRESHOLD,
    DEFAULT_MAX_RETRIES,
    DEFAULT_STATEMENT_COVERAGE_THRESHOLD,
    OUTPUT_DIR,
)
from backend.utils.llm import get_llm_stats, reset_llm_stats
from backend.workflows.orchestrator import build_graph


CONTRACTS_BATCH_DIR: Path = BASE_DIR / "contracts"

# Runtime artifacts to clean between contract runs.
_RUNTIME_DIRS_TO_CLEAN: list[Path] = [
    BASE_DIR / "coverage",
    BASE_DIR / "mochawesome-report",
    BASE_DIR / "artifacts",
    BASE_DIR / "cache",
    BASE_DIR / ".coverage_contracts",
    BASE_DIR / ".nyc_output",
    BASE_DIR / "test",
    BASE_DIR / "tests",
]
_RUNTIME_FILES_TO_CLEAN: list[Path] = [
    BASE_DIR / "test" / "generated_test.js",
    BASE_DIR / "tests" / "generated_test.js",
    BASE_DIR / "coverage.json",
]


def clean_runtime_artifacts() -> None:
    """Clean build/test artifacts while preserving outputs/batch_reports."""
    for folder in _RUNTIME_DIRS_TO_CLEAN:
        if folder.exists():
            shutil.rmtree(folder, ignore_errors=True)

    for file_path in _RUNTIME_FILES_TO_CLEAN:
        if file_path.exists():
            try:
                file_path.unlink()
            except OSError:
                pass


def list_contract_files() -> list[Path]:
    """List Solidity files directly inside root contracts/ (ignore subfolders)."""
    return sorted(CONTRACTS_BATCH_DIR.glob("*.sol"), key=lambda p: p.name.lower())


def load_user_story(contract_name: str) -> str:
    story_path = CONTRACTS_BATCH_DIR / f"{contract_name}.specs.md"
    if story_path.exists():
        return story_path.read_text(encoding="utf-8")
    return ""


def count_solidity_loc(source: str) -> int:
    """
    Count Solidity LOC as non-empty, non-comment lines.
    Supports // line comments and /* ... */ block comments.
    """
    loc = 0
    in_block_comment = False

    for raw_line in source.splitlines():
        line = raw_line

        if in_block_comment:
            end_idx = line.find("*/")
            if end_idx == -1:
                continue
            line = line[end_idx + 2 :]
            in_block_comment = False

        while True:
            block_start = line.find("/*")
            line_comment = line.find("//")

            if block_start != -1 and (line_comment == -1 or block_start < line_comment):
                block_end = line.find("*/", block_start + 2)
                if block_end == -1:
                    line = line[:block_start]
                    in_block_comment = True
                    break
                line = line[:block_start] + line[block_end + 2 :]
                continue
            break

        if not in_block_comment:
            line_comment = line.find("//")
            if line_comment != -1:
                line = line[:line_comment]

        if line.strip():
            loc += 1

    return loc


def extract_execution_metrics(final_state: dict) -> dict:
    summary = final_state.get("execution_summary", {}) if isinstance(final_state, dict) else {}
    coverage = summary.get("coverage", {}) if isinstance(summary, dict) else {}

    passed = int(summary.get("passed", 0) or 0)
    failed = int(summary.get("failed", 0) or 0)
    total = int(summary.get("total", passed + failed) or (passed + failed))

    return {
        "tests_total": total,
        "tests_passed": passed,
        "tests_failed": failed,
        "coverage_statements": float(coverage.get("statements", 0.0) or 0.0),
        "coverage_branches": float(coverage.get("branches", 0.0) or 0.0),
        "coverage_functions": float(coverage.get("functions", 0.0) or 0.0),
        "iterations": int(final_state.get("iterations", 0) or 0),
        "evaluation_decision": str(final_state.get("evaluation_decision", "")),
        "evaluation_reason": str(final_state.get("evaluation_reason", "")),
    }


def _suite_matches(title: str, keywords: tuple[str, ...]) -> bool:
    lowered = title.lower()
    return any(keyword in lowered for keyword in keywords)


def summarize_test_categories(test_report: dict) -> dict:
    functional_keywords = (
        "functionality",
        "functional",
        "view",
        "deposit",
        "claim",
        "mint",
        "transfer",
        "stake",
        "register",
        "withdraw",
        "balance",
        "reward",
    )
    security_keywords = (
        "security",
        "protection",
        "reentrancy",
        "access control",
        "unauthorized",
        "edge case",
        "attack",
        "revert",
        "reject",
        "fail",
        "bypass",
    )

    counts = {"functional_tests": 0, "security_tests": 0}

    def walk_suites(suites: list[dict]) -> None:
        for suite in suites:
            if not isinstance(suite, dict):
                continue

            title = str(suite.get("title", "") or "")
            tests = suite.get("tests", [])
            direct_count = len(tests) if isinstance(tests, list) else 0

            if title:
                if _suite_matches(title, security_keywords):
                    counts["security_tests"] += direct_count
                elif _suite_matches(title, functional_keywords):
                    counts["functional_tests"] += direct_count

            nested = suite.get("suites", [])
            if isinstance(nested, list) and nested:
                walk_suites(nested)

    results = test_report.get("results", []) if isinstance(test_report, dict) else []
    if isinstance(results, list):
        for result in results:
            if not isinstance(result, dict):
                continue
            suites = result.get("suites", [])
            if isinstance(suites, list):
                walk_suites(suites)

    counts["total"] = counts["functional_tests"] + counts["security_tests"]
    return counts


def format_float(value: float) -> str:
    return f"{value:.2f}"


def print_results_table(results: list[dict], title: str) -> None:
    if not results:
        print("No result to display.")
        return

    columns = [
        ("contract", "Contract"),
        ("loc", "LOC"),
        ("iterations", "Iter"),
        ("coverage_statements", "Stmt%"),
        ("coverage_branches", "Br%"),
        ("coverage_functions", "Fn%"),
        ("tests_passed", "Pass"),
        ("tests_failed", "Fail"),
        ("api_time_seconds", "API_s"),
        ("api_total_tokens", "Tokens"),
    ]

    rows: list[list[str]] = []
    for item in results:
        rows.append(
            [
                str(item.get("contract", "")),
                str(int(item.get("loc", 0) or 0)),
                str(int(item.get("iterations", 0) or 0)),
                format_float(float(item.get("coverage_statements", 0.0) or 0.0)),
                format_float(float(item.get("coverage_branches", 0.0) or 0.0)),
                format_float(float(item.get("coverage_functions", 0.0) or 0.0)),
                str(int(item.get("tests_passed", 0) or 0)),
                str(int(item.get("tests_failed", 0) or 0)),
                format_float(float(item.get("api_time_seconds", 0.0) or 0.0)),
                str(int(item.get("api_total_tokens", 0) or 0)),
            ]
        )

    widths = []
    for idx, (_, header) in enumerate(columns):
        max_width = len(header)
        for row in rows:
            max_width = max(max_width, len(row[idx]))
        widths.append(max_width)

    def line(parts: list[str]) -> str:
        return " | ".join(part.ljust(widths[idx]) for idx, part in enumerate(parts))

    headers = [header for _, header in columns]
    divider = "-+-".join("-" * width for width in widths)

    print(f"\n{title}")
    print(line(headers))
    print(divider)
    for row in rows:
        print(line(row))


def save_results_files(results: list[dict], out_dir: Path, base_name: str) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{base_name}.json"
    csv_path = out_dir / f"{base_name}.csv"

    with open(json_path, "w", encoding="utf-8") as f_json:
        json.dump(results, f_json, indent=2, ensure_ascii=False)

    fieldnames = [
        "contract",
        "loc",
        "status",
        "functional_tests",
        "security_tests",
        "total",
        "tests_total",
        "tests_passed",
        "tests_failed",
        "coverage_statements",
        "coverage_branches",
        "coverage_functions",
        "elapsed_seconds",
        "api_calls",
        "api_time_seconds",
        "api_prompt_tokens",
        "api_completion_tokens",
        "api_total_tokens",
        "iterations",
        "evaluation_decision",
        "evaluation_reason",
        "error",
    ]

    with open(csv_path, "w", newline="", encoding="utf-8") as f_csv:
        writer = csv.DictWriter(f_csv, fieldnames=fieldnames)
        writer.writeheader()
        for item in results:
            writer.writerow({name: item.get(name, "") for name in fieldnames})

    return json_path, csv_path


def _build_result_row(contract_path: Path, contract_code: str) -> dict:
    return {
        "contract": contract_path.stem,
        "loc": count_solidity_loc(contract_code),
        "status": "success",
        "functional_tests": 0,
        "security_tests": 0,
        "total": 0,
        "tests_total": 0,
        "tests_passed": 0,
        "tests_failed": 0,
        "coverage_statements": 0.0,
        "coverage_branches": 0.0,
        "coverage_functions": 0.0,
        "elapsed_seconds": 0.0,
        "api_calls": 0,
        "api_time_seconds": 0.0,
        "api_prompt_tokens": 0,
        "api_completion_tokens": 0,
        "api_total_tokens": 0,
        "iterations": 0,
        "evaluation_decision": "",
        "evaluation_reason": "",
        "error": "",
    }


def _apply_llm_stats(result_row: dict, stats: dict) -> None:
    result_row["api_calls"] = int(stats.get("calls", 0) or 0)
    result_row["api_time_seconds"] = round(float(stats.get("total_time_seconds", 0.0) or 0.0), 3)
    result_row["api_prompt_tokens"] = int(stats.get("prompt_tokens", 0) or 0)
    result_row["api_completion_tokens"] = int(stats.get("completion_tokens", 0) or 0)
    result_row["api_total_tokens"] = int(stats.get("total_tokens", 0) or 0)


def run_contract_with_snapshots(
    app,
    contract_path: Path,
    contract_code: str,
    user_story: str,
) -> tuple[dict, dict]:
    initial_state = {
        "contract_code": contract_code,
        "user_story": user_story,
        "source_filename": contract_path.name,
        "iterations": 0,
        "max_retries": DEFAULT_MAX_RETRIES,
        "statement_coverage_threshold": DEFAULT_STATEMENT_COVERAGE_THRESHOLD,
        "branch_coverage_threshold": DEFAULT_BRANCH_COVERAGE_THRESHOLD,
    }

    no_iter_row = _build_result_row(contract_path, contract_code)
    final_row = _build_result_row(contract_path, contract_code)
    current_state = dict(initial_state)
    captured_no_iter = False

    reset_llm_stats()
    run_start = time.perf_counter()

    try:
        for chunk in app.stream(initial_state):
            for node_name, node_update in chunk.items():
                if isinstance(node_update, dict):
                    current_state.update(node_update)

                # Snapshot after the first evaluator pass (before any correction iteration).
                if node_name == "evaluator" and not captured_no_iter:
                    no_iter_row.update(extract_execution_metrics(current_state))
                    no_iter_row["elapsed_seconds"] = round(time.perf_counter() - run_start, 3)
                    _apply_llm_stats(no_iter_row, get_llm_stats())
                    captured_no_iter = True

        # Final snapshot at the end of the same run (after iterations if any).
        final_row.update(extract_execution_metrics(current_state))
        final_row.update(summarize_test_categories(current_state.get("test_report", {})))
    except Exception as exc:
        no_iter_row["status"] = "error"
        final_row["status"] = "error"
        no_iter_row["error"] = str(exc)
        final_row["error"] = str(exc)
        print(f"Pipeline error: {exc}")

    elapsed = time.perf_counter() - run_start
    stats = get_llm_stats()

    final_row["elapsed_seconds"] = round(elapsed, 3)
    _apply_llm_stats(final_row, stats)

    # Fallback if no evaluator snapshot was captured (early failure path).
    if not captured_no_iter:
        no_iter_row["status"] = final_row.get("status", "success")
        no_iter_row["error"] = final_row.get("error", "")
        no_iter_row.update(extract_execution_metrics(current_state))
        no_iter_row.update(summarize_test_categories(current_state.get("test_report", {})))
        no_iter_row["elapsed_seconds"] = final_row["elapsed_seconds"]
        _apply_llm_stats(no_iter_row, stats)

    return no_iter_row, final_row


def main() -> None:
    CONTRACTS_BATCH_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    contracts = list_contract_files()
    if not contracts:
        print(f"No .sol contract found in {CONTRACTS_BATCH_DIR}")
        sys.exit(1)

    print(f"Detected {len(contracts)} contract(s). Building graph once...")
    app = build_graph()

    run_results_no_iterations: list[dict] = []
    run_results_final: list[dict] = []

    for index, contract_path in enumerate(contracts, start=1):
        contract_name = contract_path.stem
        print(f"\n===== Contract {index}/{len(contracts)}: {contract_name} =====")

        contract_code = contract_path.read_text(encoding="utf-8")
        user_story = load_user_story(contract_name)
        print(
            f"User story: {'loaded' if user_story else 'missing'}"
            f" ({len(user_story)} chars)"
        )

        clean_runtime_artifacts()
        no_iter_row, final_row = run_contract_with_snapshots(
            app=app,
            contract_path=contract_path,
            contract_code=contract_code,
            user_story=user_story,
        )
        run_results_no_iterations.append(no_iter_row)
        run_results_final.append(final_row)
        print(
            f"No-iter {contract_name}: loc={no_iter_row['loc']}, "
            f"pass={no_iter_row['tests_passed']}, "
            f"fail={no_iter_row['tests_failed']}, "
            f"stmt={no_iter_row['coverage_statements']:.1f}%, "
            f"api_time={no_iter_row['api_time_seconds']:.2f}s, "
            f"tokens={no_iter_row['api_total_tokens']}"
        )
        print(
            f"Final {contract_name}: loc={final_row['loc']}, "
            f"pass={final_row['tests_passed']}, "
            f"fail={final_row['tests_failed']}, "
            f"stmt={final_row['coverage_statements']:.1f}%, "
            f"api_time={final_row['api_time_seconds']:.2f}s, "
            f"tokens={final_row['api_total_tokens']}"
        )

    print_results_table(run_results_no_iterations, title="TABLE WITHOUT ITERATIONS")
    print_results_table(run_results_final, title="FINAL TABLE AFTER ITERATIONS")

    report_dir = OUTPUT_DIR / "batch_reports"
    json_path_no_iter, csv_path_no_iter = save_results_files(
        run_results_no_iterations,
        report_dir,
        "batch_results_no_iterations",
    )
    json_path_final, csv_path_final = save_results_files(
        run_results_final,
        report_dir,
        "batch_results_final",
    )

    total_api_calls_no_iter = sum(int(item.get("api_calls", 0) or 0) for item in run_results_no_iterations)
    total_api_time_no_iter = sum(float(item.get("api_time_seconds", 0.0) or 0.0) for item in run_results_no_iterations)
    total_tokens_no_iter = sum(int(item.get("api_total_tokens", 0) or 0) for item in run_results_no_iterations)

    total_api_calls_final = sum(int(item.get("api_calls", 0) or 0) for item in run_results_final)
    total_api_time_final = sum(float(item.get("api_time_seconds", 0.0) or 0.0) for item in run_results_final)
    total_tokens_final = sum(int(item.get("api_total_tokens", 0) or 0) for item in run_results_final)

    print("\nGenerated files:")
    print(f"- {json_path_no_iter}")
    print(f"- {csv_path_no_iter}")
    print(f"- {json_path_final}")
    print(f"- {csv_path_final}")

    print(
        f"\nAPI summary (no-iter): calls={total_api_calls_no_iter}, "
        f"time={total_api_time_no_iter:.2f}s, tokens={total_tokens_no_iter}"
    )
    print(
        f"API summary (final): calls={total_api_calls_final}, "
        f"time={total_api_time_final:.2f}s, tokens={total_tokens_final}"
    )


if __name__ == "__main__":
    main()
