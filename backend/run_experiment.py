"""
run_experiment.py
-----------------
Daily experiment launcher for MA-RAGTest.

This script runs one fixed configuration on a chosen subset of Solidity
contracts, stores every contract/repetition in its own folder, and writes
aggregate CSV/JSON summaries that can be used later for paper tables.

Examples:
    python backend/run_experiment.py --config config_1 --contracts SimpleVoting,AddressBook,EthGame --repetitions 1 --experiment pilot_day01

    python backend/run_experiment.py --config config_1 --contract-list data/experiment_subsets/config1_day01.txt --repetitions 3 --experiment ase_revision_config1_day01

Use --force to rerun completed repetitions. Without --force, completed
repetitions are skipped when metrics.json already exists.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import sys
import time
import traceback
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


# Allow direct execution from the project root.
_ROOT = Path(__file__).parent.parent.resolve()
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from backend.config.settings import BASE_DIR, CONTRACTS_DIR, OUTPUT_DIR
from backend.utils.llm import get_llm_stats, reset_llm_stats
from backend.workflows.orchestrator import build_graph


RUNS_DIR = OUTPUT_DIR / "runs"

RUNTIME_DIRS_TO_CLEAN: list[Path] = [
    BASE_DIR / "coverage",
    BASE_DIR / "mochawesome-report",
    BASE_DIR / "artifacts",
    BASE_DIR / "cache",
    BASE_DIR / ".coverage_contracts",
    BASE_DIR / ".nyc_output",
    BASE_DIR / "test",
    BASE_DIR / "tests",
]

RUNTIME_FILES_TO_CLEAN: list[Path] = [
    BASE_DIR / "coverage.json",
    BASE_DIR / "test" / "generated_test.js",
    BASE_DIR / "tests" / "generated_test.js",
]

OUTPUT_ARTIFACTS: list[str] = [
    "test_design.json",
    "generated_test.js",
    "test_report.json",
    "execution_summary.json",
    "coverage_report.json",
    "coverage_report_all_contracts.json",
]


class Tee:
    """Small stdout/stderr tee used to keep console logs and per-run logs."""

    def __init__(self, *streams: Any) -> None:
        self.streams = streams

    def write(self, data: str) -> None:
        for stream in self.streams:
            try:
                stream.write(data)
            except UnicodeEncodeError:
                # Windows terminals often default to cp1252 and cannot render
                # symbols already printed by the existing pipeline. Keep the
                # run alive and preserve as much log information as possible.
                stream.write(data.encode(stream.encoding or "utf-8", errors="replace").decode(stream.encoding or "utf-8"))

    def flush(self) -> None:
        for stream in self.streams:
            stream.flush()


@dataclass(frozen=True)
class ExperimentArgs:
    config: str
    experiment: str
    repetitions: int
    contracts: list[str]
    force: bool
    dry_run: bool


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def clean_runtime_artifacts() -> None:
    """Clean Hardhat/runtime artifacts while preserving outputs/runs."""
    for folder in RUNTIME_DIRS_TO_CLEAN:
        if folder.exists():
            shutil.rmtree(folder, ignore_errors=True)

    for file_path in RUNTIME_FILES_TO_CLEAN:
        if file_path.exists():
            try:
                file_path.unlink()
            except OSError:
                pass


def load_user_story(contract_name: str) -> str:
    candidates = [
        CONTRACTS_DIR / f"{contract_name}.specs.md",
        CONTRACTS_DIR / f"{contract_name}.txt",
        CONTRACTS_DIR / "user_story.specs.md",
        CONTRACTS_DIR / "user_story.txt",
    ]
    for path in candidates:
        if path.exists():
            return path.read_text(encoding="utf-8")
    return ""


def count_solidity_loc(source: str) -> int:
    """Count non-empty, non-comment Solidity lines."""
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


def safe_read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def safe_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def discover_contracts() -> list[str]:
    return sorted(path.stem for path in CONTRACTS_DIR.glob("*.sol"))


def parse_contract_names(args: argparse.Namespace) -> list[str]:
    names: list[str] = []

    if args.contracts:
        names.extend(
            item.strip()
            for item in args.contracts.split(",")
            if item.strip()
        )

    if args.contract_list:
        list_path = Path(args.contract_list)
        if not list_path.is_absolute():
            list_path = BASE_DIR / list_path
        if not list_path.exists():
            raise FileNotFoundError(f"Contract list not found: {list_path}")
        for raw_line in list_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            names.append(Path(line).stem)

    if not names:
        names = discover_contracts()

    deduped: list[str] = []
    seen: set[str] = set()
    for name in names:
        if name not in seen:
            deduped.append(name)
            seen.add(name)

    missing = [name for name in deduped if not (CONTRACTS_DIR / f"{name}.sol").exists()]
    if missing:
        available = ", ".join(discover_contracts())
        raise FileNotFoundError(
            f"Unknown contract(s): {', '.join(missing)}\n"
            f"Available contracts: {available}"
        )

    return deduped


def extract_execution_metrics(final_state: dict[str, Any]) -> dict[str, Any]:
    summary = final_state.get("execution_summary", {}) or {}
    coverage = summary.get("coverage", {}) or {}
    commands = summary.get("commands", {}) or {}

    passed = int(summary.get("passed", 0) or 0)
    failed = int(summary.get("failed", 0) or 0)
    total = int(summary.get("total", passed + failed) or (passed + failed))

    return {
        "tests_total": total,
        "tests_passed": passed,
        "tests_failed": failed,
        "pass_rate": round((passed / total) * 100, 2) if total else 0.0,
        "acceptance_rate": float(summary.get("acceptance_rate", 0.0) or 0.0),
        "coverage_statements": float(coverage.get("statements", 0.0) or 0.0),
        "coverage_branches": float(coverage.get("branches", 0.0) or 0.0),
        "coverage_functions": float(coverage.get("functions", 0.0) or 0.0),
        "coverage_lines": float(coverage.get("lines", 0.0) or 0.0),
        "coverage_valid": bool(summary.get("coverage_valid", False)),
        "partial_coverage": bool(summary.get("partial_coverage", False)),
        "invalid_suite": bool(summary.get("invalid_suite", False)),
        "test_returncode": commands.get("test_returncode"),
        "coverage_returncode": commands.get("coverage_returncode"),
        "iterations": int(final_state.get("iterations", 0) or 0),
        "evaluation_decision": str(final_state.get("evaluation_decision", "") or ""),
        "evaluation_reason": str(final_state.get("evaluation_reason", "") or ""),
    }


def count_generated_tests_from_design(test_design: dict[str, Any]) -> dict[str, int]:
    """Count planned functional/security tests from the test design JSON."""
    counts = {
        "planned_tests_total": 0,
        "planned_functional_tests": 0,
        "planned_security_tests": 0,
    }

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            lower_values = " ".join(str(v).lower() for v in value.values() if isinstance(v, str))
            looks_like_test = any(
                key in value
                for key in (
                    "test_title",
                    "title",
                    "name",
                    "description",
                    "steps",
                    "expected",
                    "expected_behavior",
                    "target_function",
                )
            )
            if looks_like_test:
                counts["planned_tests_total"] += 1
                category = str(value.get("category", "") or "").lower()
                if category == "security" or "security" in lower_values or "swc-" in lower_values:
                    counts["planned_security_tests"] += 1
                else:
                    counts["planned_functional_tests"] += 1
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(test_design)
    return counts


def refresh_metrics_from_archived_artifacts(run_dir: Path, metrics: dict[str, Any]) -> dict[str, Any]:
    """Refresh derived counts for a completed run without rerunning the LLM."""
    test_design = safe_read_json(run_dir / "test_design.json")
    test_code = ""
    generated_test_path = run_dir / "generated_test.js"
    if generated_test_path.exists():
        test_code = generated_test_path.read_text(encoding="utf-8")

    metrics.update(count_generated_tests_from_design(test_design))
    metrics.update(count_generated_tests_from_code(test_code))
    metrics.update(count_invalid_failures_from_analyzer(safe_read_json(run_dir / "analyzer_report.json")))
    return add_quality_outcome(metrics)


def count_generated_tests_from_code(test_code: str) -> dict[str, int]:
    total = len(re.findall(r"\bit\s*(?:\.skip)?\s*\(", test_code or ""))
    skipped = len(re.findall(r"\bit\s*\.skip\s*\(", test_code or ""))
    security = len(re.findall(r"\bit\s*(?:\.skip)?\s*\(\s*['\"]\[SECURITY:", test_code or ""))
    invalid_helper = len(re.findall(r"INVALID_GENERATED_TEST:HELPER_CONTRACT_FORBIDDEN", test_code or ""))
    return {
        "generated_tests_total": total,
        "generated_tests_skipped_static": skipped,
        "generated_security_tests_static": security,
        "invalid_helper_contract_tests_static": invalid_helper,
    }


def count_invalid_failures_from_analyzer(analyzer_report: dict[str, Any]) -> dict[str, int]:
    invalid_summary = analyzer_report.get("invalid_summary", {}) if isinstance(analyzer_report, dict) else {}
    return {
        "invalid_failures_total": int(invalid_summary.get("total", 0) or 0),
        "invalid_undefined_helper_failures": int(invalid_summary.get("undefined_helper_contract", 0) or 0),
        "invalid_undefined_symbol_failures": int(invalid_summary.get("undefined_symbol", 0) or 0),
        "invalid_call_error_failures": int(invalid_summary.get("call_error", 0) or 0),
        "invalid_js_syntax_failures": int(invalid_summary.get("invalid_js_syntax", 0) or 0),
        "invalid_bigint_mix_failures": int(invalid_summary.get("bigint_mix", 0) or 0),
    }


def add_quality_outcome(metrics: dict[str, Any]) -> dict[str, Any]:
    """Add an experiment outcome separate from script/runtime status."""
    if metrics.get("status") == "error":
        metrics["outcome"] = "runtime_error"
        return metrics

    tests_total = int(metrics.get("tests_total", 0) or 0)
    tests_failed = int(metrics.get("tests_failed", 0) or 0)
    coverage_valid = bool(metrics.get("coverage_valid", False))
    invalid_suite = bool(metrics.get("invalid_suite", False))

    if invalid_suite:
        metrics["outcome"] = "invalid_suite"
    elif tests_total > 0 and tests_failed == 0 and coverage_valid:
        metrics["outcome"] = "accepted"
    elif tests_total > 0:
        metrics["outcome"] = "needs_correction"
    else:
        metrics["outcome"] = "invalid_or_no_tests"

    return metrics


def archive_output_artifacts(run_dir: Path, final_state: dict[str, Any]) -> None:
    for filename in OUTPUT_ARTIFACTS:
        src = OUTPUT_DIR / filename
        if src.exists():
            shutil.copy2(src, run_dir / filename)

    safe_write_json(run_dir / "final_state_summary.json", {
        "evaluation_decision": final_state.get("evaluation_decision", ""),
        "evaluation_reason": final_state.get("evaluation_reason", ""),
        "iterations": final_state.get("iterations", 0),
        "has_test_design": bool(final_state.get("test_design")),
        "has_test_code": bool(final_state.get("test_code")),
        "has_execution_summary": bool(final_state.get("execution_summary")),
        "has_analyzer_report": bool(final_state.get("analyzer_report")),
    })

    if final_state.get("analyzer_report") is not None:
        safe_write_json(run_dir / "analyzer_report.json", final_state.get("analyzer_report"))
    if final_state.get("test_design") is not None and not (run_dir / "test_design.json").exists():
        safe_write_json(run_dir / "test_design.json", final_state.get("test_design"))
    if final_state.get("test_code") is not None and not (run_dir / "generated_test.js").exists():
        (run_dir / "generated_test.js").write_text(str(final_state.get("test_code") or ""), encoding="utf-8")


def build_manifest(
    *,
    experiment_args: ExperimentArgs,
    contract_name: str,
    contract_path: Path,
    repetition: int,
    run_dir: Path,
    status: str,
    started_at: str,
    finished_at: str,
) -> dict[str, Any]:
    return {
        "experiment": experiment_args.experiment,
        "config": experiment_args.config,
        "contract": contract_name,
        "contract_path": str(contract_path.relative_to(BASE_DIR)),
        "repetition": repetition,
        "status": status,
        "started_at": started_at,
        "finished_at": finished_at,
        "run_dir": str(run_dir.relative_to(BASE_DIR)),
        "command": " ".join(sys.argv),
    }


def run_one_repetition(
    *,
    app: Any,
    experiment_args: ExperimentArgs,
    contract_name: str,
    repetition: int,
) -> dict[str, Any]:
    contract_path = CONTRACTS_DIR / f"{contract_name}.sol"
    run_dir = RUNS_DIR / experiment_args.experiment / experiment_args.config / contract_name / f"rep_{repetition:02d}"
    metrics_path = run_dir / "metrics.json"

    if metrics_path.exists() and not experiment_args.force:
        metrics = safe_read_json(metrics_path)
        metrics = refresh_metrics_from_archived_artifacts(run_dir, metrics)
        metrics["resumed_from_existing"] = True
        safe_write_json(metrics_path, metrics)
        print(f"[Experiment] Skip completed: {contract_name} rep {repetition:02d}")
        return metrics

    run_dir.mkdir(parents=True, exist_ok=True)
    clean_runtime_artifacts()
    reset_llm_stats()

    contract_code = contract_path.read_text(encoding="utf-8")
    user_story = load_user_story(contract_name)

    initial_state = {
        "contract_code": contract_code,
        "user_story": user_story,
        "source_filename": contract_path.name,
        "experiment_config": experiment_args.config,
        "iterations": 0,
    }

    started_at = utc_now_iso()
    wall_start = time.perf_counter()
    process_start = time.process_time()
    final_state: dict[str, Any] = dict(initial_state)
    status = "success"
    error = ""

    log_path = run_dir / "logs.txt"
    with log_path.open("w", encoding="utf-8") as log_file:
        tee_out = Tee(sys.stdout, log_file)
        tee_err = Tee(sys.stderr, log_file)
        with redirect_stdout(tee_out), redirect_stderr(tee_err):
            print(f"[Experiment] Start {contract_name} rep {repetition:02d} at {started_at}")
            print(f"[Experiment] Config={experiment_args.config} | User story chars={len(user_story)}")
            try:
                for chunk in app.stream(initial_state):
                    for node_name, node_update in chunk.items():
                        if isinstance(node_update, dict):
                            final_state.update(node_update)
                        print(f"[Experiment] Node completed: {node_name}")
            except Exception as exc:
                status = "error"
                error = str(exc)
                print("[Experiment] ERROR during pipeline execution")
                print(traceback.format_exc())

    finished_at = utc_now_iso()
    wall_seconds = round(time.perf_counter() - wall_start, 3)
    process_seconds = round(time.process_time() - process_start, 3)
    llm_stats = get_llm_stats()

    archive_output_artifacts(run_dir, final_state)

    test_design = final_state.get("test_design") if isinstance(final_state.get("test_design"), dict) else safe_read_json(run_dir / "test_design.json")
    test_code = str(final_state.get("test_code") or "")
    if not test_code and (run_dir / "generated_test.js").exists():
        test_code = (run_dir / "generated_test.js").read_text(encoding="utf-8")

    manifest = build_manifest(
        experiment_args=experiment_args,
        contract_name=contract_name,
        contract_path=contract_path,
        repetition=repetition,
        run_dir=run_dir,
        status=status,
        started_at=started_at,
        finished_at=finished_at,
    )
    safe_write_json(run_dir / "manifest.json", manifest)

    metrics = {
        **manifest,
        "loc": count_solidity_loc(contract_code),
        "user_story_chars": len(user_story),
        "wall_time_seconds": wall_seconds,
        "process_time_seconds": process_seconds,
        "llm_calls": int(llm_stats.get("calls", 0) or 0),
        "llm_time_seconds": round(float(llm_stats.get("total_time_seconds", 0.0) or 0.0), 3),
        "error": error,
        "resumed_from_existing": False,
        **count_generated_tests_from_design(test_design),
        **count_generated_tests_from_code(test_code),
        **count_invalid_failures_from_analyzer(final_state.get("analyzer_report", {}) or {}),
        **extract_execution_metrics(final_state),
    }
    metrics = add_quality_outcome(metrics)

    safe_write_json(metrics_path, metrics)
    print(
        f"[Experiment] Done {contract_name} rep {repetition:02d}: "
        f"status={status}, tests={metrics['tests_passed']}/{metrics['tests_total']}, "
        f"stmt={metrics['coverage_statements']:.1f}%, wall={wall_seconds:.1f}s"
    )

    return metrics


def write_aggregate_files(
    *,
    experiment_args: ExperimentArgs,
    metrics_rows: list[dict[str, Any]],
    batch_started_at: str,
    batch_wall_seconds: float,
    batch_process_seconds: float,
) -> tuple[Path, Path, Path]:
    out_dir = RUNS_DIR / experiment_args.experiment / experiment_args.config
    out_dir.mkdir(parents=True, exist_ok=True)

    summary_payload = {
        "experiment": experiment_args.experiment,
        "config": experiment_args.config,
        "contracts": experiment_args.contracts,
        "repetitions": experiment_args.repetitions,
        "started_at": batch_started_at,
        "finished_at": utc_now_iso(),
        "wall_time_seconds": round(batch_wall_seconds, 3),
        "process_time_seconds": round(batch_process_seconds, 3),
        "run_count": len(metrics_rows),
        "successful_runs": sum(1 for row in metrics_rows if row.get("status") == "success"),
        "error_runs": sum(1 for row in metrics_rows if row.get("status") == "error"),
        "total_llm_calls": sum(int(row.get("llm_calls", 0) or 0) for row in metrics_rows),
        "total_llm_time_seconds": round(sum(float(row.get("llm_time_seconds", 0.0) or 0.0) for row in metrics_rows), 3),
        "total_run_wall_time_seconds": round(sum(float(row.get("wall_time_seconds", 0.0) or 0.0) for row in metrics_rows), 3),
        "rows": metrics_rows,
    }

    summary_json = out_dir / "summary.json"
    summary_csv = out_dir / "summary.csv"
    batch_manifest = out_dir / "batch_manifest.json"

    safe_write_json(summary_json, summary_payload)
    safe_write_json(batch_manifest, {k: v for k, v in summary_payload.items() if k != "rows"})

    fieldnames = [
        "experiment",
        "config",
        "contract",
        "repetition",
        "status",
        "outcome",
        "loc",
        "planned_tests_total",
        "planned_functional_tests",
        "planned_security_tests",
        "generated_tests_total",
        "generated_security_tests_static",
        "generated_tests_skipped_static",
        "invalid_helper_contract_tests_static",
        "invalid_failures_total",
        "invalid_undefined_helper_failures",
        "invalid_undefined_symbol_failures",
        "invalid_call_error_failures",
        "invalid_js_syntax_failures",
        "invalid_bigint_mix_failures",
        "tests_total",
        "tests_passed",
        "tests_failed",
        "pass_rate",
        "acceptance_rate",
        "coverage_statements",
        "coverage_branches",
        "coverage_functions",
        "coverage_lines",
        "coverage_valid",
        "partial_coverage",
        "invalid_suite",
        "iterations",
        "evaluation_decision",
        "evaluation_reason",
        "test_returncode",
        "coverage_returncode",
        "wall_time_seconds",
        "process_time_seconds",
        "llm_calls",
        "llm_time_seconds",
        "user_story_chars",
        "run_dir",
        "error",
        "resumed_from_existing",
    ]

    with summary_csv.open("w", newline="", encoding="utf-8") as f_csv:
        writer = csv.DictWriter(f_csv, fieldnames=fieldnames)
        writer.writeheader()
        for row in metrics_rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})

    return summary_json, summary_csv, batch_manifest


def print_plan(experiment_args: ExperimentArgs) -> None:
    print("\n[Experiment] Plan")
    print(f"  Config       : {experiment_args.config}")
    print(f"  Experiment   : {experiment_args.experiment}")
    print(f"  Repetitions  : {experiment_args.repetitions}")
    print(f"  Contracts    : {', '.join(experiment_args.contracts)}")
    print(f"  Force rerun  : {experiment_args.force}")
    print(f"  Output root  : {RUNS_DIR / experiment_args.experiment / experiment_args.config}")


def iter_run_plan(contracts: Iterable[str], repetitions: int) -> Iterable[tuple[str, int]]:
    for contract_name in contracts:
        for repetition in range(1, repetitions + 1):
            yield contract_name, repetition


def parse_args() -> ExperimentArgs:
    parser = argparse.ArgumentParser(
        description="Run MA-RAGTest experiments for a selected daily subset of contracts."
    )
    parser.add_argument("--config", default="config_1", help="Configuration label recorded in outputs.")
    parser.add_argument("--experiment", required=True, help="Experiment/run label, e.g. ase_revision_config1_day01.")
    parser.add_argument("--contracts", help="Comma-separated contract names without .sol.")
    parser.add_argument("--contract-list", help="Text file containing one contract name per line.")
    parser.add_argument("--repetitions", type=int, default=1, help="Number of repetitions per contract.")
    parser.add_argument("--force", action="store_true", help="Rerun even if metrics.json already exists.")
    parser.add_argument("--dry-run", action="store_true", help="Only print the plan; do not call the LLM or Hardhat.")

    args = parser.parse_args()
    contracts = parse_contract_names(args)

    if args.repetitions < 1:
        raise ValueError("--repetitions must be >= 1")

    return ExperimentArgs(
        config=args.config,
        experiment=args.experiment,
        repetitions=args.repetitions,
        contracts=contracts,
        force=bool(args.force),
        dry_run=bool(args.dry_run),
    )


def main() -> None:
    experiment_args = parse_args()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    RUNS_DIR.mkdir(parents=True, exist_ok=True)

    print_plan(experiment_args)

    if experiment_args.dry_run:
        print("[Experiment] Dry run complete. No pipeline execution performed.")
        return

    batch_started_at = utc_now_iso()
    batch_wall_start = time.perf_counter()
    batch_process_start = time.process_time()

    print("\n[Experiment] Building LangGraph once...")
    app = build_graph()

    rows: list[dict[str, Any]] = []
    for index, (contract_name, repetition) in enumerate(
        iter_run_plan(experiment_args.contracts, experiment_args.repetitions),
        start=1,
    ):
        total = len(experiment_args.contracts) * experiment_args.repetitions
        print(f"\n[Experiment] Run {index}/{total}: {contract_name} rep {repetition:02d}")
        rows.append(
            run_one_repetition(
                app=app,
                experiment_args=experiment_args,
                contract_name=contract_name,
                repetition=repetition,
            )
        )

    batch_wall_seconds = time.perf_counter() - batch_wall_start
    batch_process_seconds = time.process_time() - batch_process_start
    summary_json, summary_csv, batch_manifest = write_aggregate_files(
        experiment_args=experiment_args,
        metrics_rows=rows,
        batch_started_at=batch_started_at,
        batch_wall_seconds=batch_wall_seconds,
        batch_process_seconds=batch_process_seconds,
    )

    print("\n[Experiment] Batch complete")
    print(f"  Wall time    : {batch_wall_seconds:.1f}s")
    print(f"  Process time : {batch_process_seconds:.1f}s")
    print(f"  Summary JSON : {summary_json}")
    print(f"  Summary CSV  : {summary_csv}")
    print(f"  Manifest     : {batch_manifest}")


if __name__ == "__main__":
    main()
