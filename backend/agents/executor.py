"""
executor.py
-----------
Executor final robuste pour MA-RAGTest.

Objectifs :
- Exécuter les tests générés.
- Compter honnêtement passed/failed/acceptance_rate.
- Si la suite est invalide et aucun test n'est exécuté, signaler un échec réel.
- Calculer le coverage du contrat cible uniquement.
- Si certains tests échouent, calculer un coverage partiel sur les tests passants
  en utilisant un fichier temporaire où les tests failing sont marqués it.skip.
"""

import json
import os
import re

from backend.config.settings import BASE_DIR, OUTPUT_DIR
from backend.utils.executor_utils import (
    _clean_hardhat_build_artifacts,
    _coverage_artifacts_exist,
    _ensure_contract_file,
    _load_json,
    _parse_stdout_stats,
    _run_cmd,
    _summarize_hardhat_error,
)

_HARDHAT_TEST_TIMEOUT_SECONDS = float(os.getenv("HARDHAT_TEST_TIMEOUT_SECONDS", "180"))
_HARDHAT_COVERAGE_TIMEOUT_SECONDS = float(os.getenv("HARDHAT_COVERAGE_TIMEOUT_SECONDS", "300"))


def _extract_tests_from_code(test_code: str) -> list[dict]:
    tests = []
    pattern = r'it\s*\(\s*["\']([^"\']+)["\']'

    for match in re.finditer(pattern, test_code or ""):
        title = match.group(1)
        tests.append({
            "title": title,
            "fullTitle": title,
            "state": "unknown",
            "pass": None,
            "pending": False,
        })

    return tests


def _extract_failing_test_titles(stdout: str) -> list[str]:
    failing_titles = []
    lines = (stdout or "").splitlines()

    for i, line in enumerate(lines):
        stripped = line.strip()

        if re.match(r"^\d+\)\s+", stripped):
            for j in range(i + 1, min(i + 10, len(lines))):
                candidate = lines[j].strip()
                candidate = candidate.replace("✔", "").strip()
                candidate = candidate.rstrip(":").strip()

                if not candidate:
                    continue

                if candidate.startswith(("Error", "AssertionError", "HardhatError", "ProviderError", "at ")):
                    break

                if "[SECURITY:" in candidate or candidate.startswith("should "):
                    failing_titles.append(candidate)
                    break

    return list(dict.fromkeys(failing_titles))


def _skip_failing_tests_for_coverage(test_code: str, failing_titles: list[str]) -> str:
    patched = test_code or ""

    for title in failing_titles:
        escaped = re.escape(title)

        patched = re.sub(
            rf'it\s*\(\s*"{escaped}"',
            f'it.skip("{title}"',
            patched,
            count=1,
        )

        patched = re.sub(
            rf"it\s*\(\s*'{escaped}'",
            f"it.skip('{title}'",
            patched,
            count=1,
        )

    return patched


def _mark_test_statuses_from_stdout(test_report: dict, stdout: str) -> dict:
    failing_titles = set(_extract_failing_test_titles(stdout))
    passing_titles = set()

    for line in (stdout or "").splitlines():
        stripped = line.strip()
        if stripped.startswith("✔"):
            title = stripped.replace("✔", "", 1).strip()
            title = re.sub(r"\(\d+ms\)$", "", title).strip()
            passing_titles.add(title)

    for result in test_report.get("results", []):
        for suite in result.get("suites", []):
            for test in suite.get("tests", []):
                title = test.get("title", "")

                if title in failing_titles:
                    test["state"] = "failed"
                    test["pass"] = False
                elif title in passing_titles:
                    test["state"] = "passed"
                    test["pass"] = True

    return test_report


def _find_target_coverage_entry(coverage_report: dict, target_filename: str):
    if not coverage_report:
        return None, {}

    target_filename = target_filename.replace("\\", "/")

    for key, value in coverage_report.items():
        if key == "total":
            continue

        normalized_key = key.replace("\\", "/")

        if normalized_key.endswith(f"/{target_filename}") or normalized_key.endswith(target_filename):
            return key, value

    return None, {}


def _coverage_pct_from_final_entry(entry: dict) -> dict:
    s = entry.get("s", {})
    f = entry.get("f", {})
    b = entry.get("b", {})

    stmt_total = len(s)
    stmt_cov = sum(1 for v in s.values() if v > 0)

    func_total = len(f)
    func_cov = sum(1 for v in f.values() if v > 0)

    branch_total = 0
    branch_cov = 0

    for values in b.values():
        branch_total += len(values)
        branch_cov += sum(1 for v in values if v > 0)

    def pct(covered: int, total: int) -> float:
        return round((covered / total) * 100, 2) if total else 100.0

    return {
        "statements": pct(stmt_cov, stmt_total),
        "branches": pct(branch_cov, branch_total),
        "functions": pct(func_cov, func_total),
        "lines": pct(stmt_cov, stmt_total),
    }


def _build_target_cov_summary(coverage_report: dict, target_filename: str) -> dict:
    key, entry = _find_target_coverage_entry(coverage_report, target_filename)

    if not entry:
        print(f"[Executor] ⚠️ Coverage du contrat cible introuvable : {target_filename}")
        return {
            "statements": 0.0,
            "branches": 0.0,
            "functions": 0.0,
            "lines": 0.0,
        }

    print(f"[Executor] Coverage cible détecté : {key}")

    if "statements" in entry and isinstance(entry.get("statements"), dict):
        return {
            "statements": float(entry.get("statements", {}).get("pct", 0.0) or 0.0),
            "branches": float(entry.get("branches", {}).get("pct", 0.0) or 0.0),
            "functions": float(entry.get("functions", {}).get("pct", 0.0) or 0.0),
            "lines": float(entry.get("lines", {}).get("pct", 0.0) or 0.0),
        }

    if "s" in entry or "statementMap" in entry:
        return _coverage_pct_from_final_entry(entry)

    return {
        "statements": 0.0,
        "branches": 0.0,
        "functions": 0.0,
        "lines": 0.0,
    }


def _build_target_coverage_report(coverage_report: dict, target_filename: str) -> dict:
    key, _entry = _find_target_coverage_entry(coverage_report, target_filename)

    if not key:
        return {}

    summary = _build_target_cov_summary(coverage_report, target_filename)

    normalized_entry = {
        "statements": {"pct": summary["statements"]},
        "branches": {"pct": summary["branches"]},
        "functions": {"pct": summary["functions"]},
        "lines": {"pct": summary["lines"]},
    }

    return {
        key: normalized_entry,
        "total": normalized_entry,
    }


def _persist_outputs(
    test_code: str,
    test_report: dict,
    execution_summary: dict,
    coverage_report: dict | None = None,
    raw_coverage_report: dict | None = None,
) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_DIR / "generated_test.js", "w", encoding="utf-8") as f:
        f.write(test_code or "")

    with open(OUTPUT_DIR / "test_report.json", "w", encoding="utf-8") as f:
        json.dump(test_report or {}, f, indent=2, ensure_ascii=False)

    with open(OUTPUT_DIR / "execution_summary.json", "w", encoding="utf-8") as f:
        json.dump(execution_summary or {}, f, indent=2, ensure_ascii=False)

    if coverage_report is not None:
        with open(OUTPUT_DIR / "coverage_report.json", "w", encoding="utf-8") as f:
            json.dump(coverage_report or {}, f, indent=2, ensure_ascii=False)

    if raw_coverage_report is not None:
        with open(OUTPUT_DIR / "coverage_report_all_contracts.json", "w", encoding="utf-8") as f:
            json.dump(raw_coverage_report or {}, f, indent=2, ensure_ascii=False)


def _run_coverage(test_file: str, target_filename: str):
    _clean_hardhat_build_artifacts()

    print(f"[Executor] Lancement coverage sur {test_file}…")

    cov_result = _run_cmd(
        ["npx", "--no-install", "hardhat", "coverage", "--testfiles", test_file],
        timeout_seconds=_HARDHAT_COVERAGE_TIMEOUT_SECONDS,
    )

    cov_stdout = (cov_result.stdout or "").strip()
    cov_stderr = (cov_result.stderr or "").strip()

    windows_crash = (
        cov_result.returncode != 0
        and _coverage_artifacts_exist()
        and "UV_HANDLE_CLOSING" in f"{cov_stdout}\n{cov_stderr}"
    )

    if cov_result.returncode != 0:
        if windows_crash:
            print("[Executor] ℹ️ Coverage terminé malgré crash Windows UV_HANDLE_CLOSING.")
        else:
            print(f"[Executor] ⚠️ hardhat coverage → {_summarize_hardhat_error(f'{cov_stdout}{cov_stderr}')}")

    raw_coverage_report = _load_json(BASE_DIR / "coverage" / "coverage-summary.json")

    if not raw_coverage_report:
        raw_coverage_report = _load_json(BASE_DIR / "coverage" / "coverage-final.json")

    coverage_report = _build_target_coverage_report(raw_coverage_report, target_filename)
    cov_summary = _build_target_cov_summary(raw_coverage_report, target_filename)

    return {
        "returncode": 0 if windows_crash else cov_result.returncode,
        "raw_coverage_report": raw_coverage_report,
        "coverage_report": coverage_report,
        "cov_summary": cov_summary,
    }


def _invalid_suite_return(
    test_code: str,
    test_report: dict,
    target_filename: str,
    test_returncode: int,
):
    print("[Executor] ⛔ Suite de tests invalide — aucun test exécuté.")

    cov_summary = {
        "statements": 0.0,
        "branches": 0.0,
        "functions": 0.0,
        "lines": 0.0,
    }

    test_report["stats"] = {
        "passes": 0,
        "failures": 1,
        "tests": 1,
    }
    test_report["error"] = "Invalid generated test suite"

    execution_summary = {
        "total": 1,
        "passed": 0,
        "failed": 1,
        "acceptance_rate": 0.0,
        "invalid_suite": True,
        "coverage": cov_summary,
        "coverage_valid": False,
        "partial_coverage": False,
        "target_contract": target_filename,
        "commands": {
            "test_returncode": test_returncode,
            "coverage_returncode": None,
        },
    }

    _persist_outputs(
        test_code=test_code,
        test_report=test_report,
        execution_summary=execution_summary,
        coverage_report={},
        raw_coverage_report={},
    )

    return {
        "test_report": test_report,
        "coverage_report": {},
        "execution_summary": execution_summary,
    }


def executor_node(state: dict) -> dict:
    print("--- EXECUTOR ---")

    contract_code: str = state.get("contract_code", "")
    test_code: str = state.get("test_code", "")
    source_filename: str = state.get("source_filename", "")

    test_dir = BASE_DIR / "test"
    test_dir.mkdir(parents=True, exist_ok=True)

    test_path = test_dir / "generated_test.js"
    test_path.write_text(test_code or "", encoding="utf-8")

    lines = (test_code or "").count("\n") + 1
    print(f"[Executor] Test écrit : {test_path} ({lines} lignes)")

    _clean_hardhat_build_artifacts()

    contract_path = _ensure_contract_file(contract_code, source_filename or None)
    target_filename = source_filename or contract_path.name

    print(f"[Executor] Contrat cible : {contract_path}")
    print(f"[Executor] Fichier cible coverage : {target_filename}")

    test_result = _run_cmd(
        ["npx", "--no-install", "hardhat", "test", "test/generated_test.js"],
        timeout_seconds=_HARDHAT_TEST_TIMEOUT_SECONDS,
    )

    if test_result.returncode != 0:
        combined = f"{test_result.stdout or ''}\n{test_result.stderr or ''}"
        print(f"[Executor] ⚠️ hardhat test → {_summarize_hardhat_error(combined)}")

    test_report: dict = _load_json(BASE_DIR / "mochawesome-report" / "mochawesome.json")

    if not test_report:
        print("[Executor] ⚠️ mochawesome.json absent — parsing stdout.")
        test_report = _parse_stdout_stats(test_result.stdout)

    test_report["stdout"] = test_result.stdout or ""
    test_report["stderr"] = test_result.stderr or ""

    if not test_report.get("results"):
        test_report["results"] = [{
            "suites": [{
                "title": "Generated Tests",
                "tests": _extract_tests_from_code(test_code),
            }]
        }]

    test_report = _mark_test_statuses_from_stdout(test_report, test_result.stdout or "")

    passed = int(test_report.get("stats", {}).get("passes", 0) or 0)
    failed = int(test_report.get("stats", {}).get("failures", 0) or 0)
    total = int(test_report.get("stats", {}).get("tests", passed + failed) or 0)

    if test_result.returncode != 0 and total == 0:
        return _invalid_suite_return(
            test_code=test_code,
            test_report=test_report,
            target_filename=target_filename,
            test_returncode=test_result.returncode,
        )

    if test_result.returncode == 124:
        failed = max(failed, 1)
        total = max(total, 1)

    acceptance_rate = round((passed / total) * 100, 2) if total else 0.0

    coverage_valid = False
    partial_coverage = False
    coverage_report = {}
    raw_coverage_report = {}
    cov_summary = {
        "statements": 0.0,
        "branches": 0.0,
        "functions": 0.0,
        "lines": 0.0,
    }
    coverage_returncode = None

    if failed > 0:
        print("[Executor] ⚠️ Tests en échec — coverage partiel sur tests passants.")

        failing_titles = _extract_failing_test_titles(test_result.stdout or "")
        print(f"[Executor] Tests failing détectés : {failing_titles}")

        if failing_titles:
            coverage_test_code = _skip_failing_tests_for_coverage(test_code, failing_titles)
            coverage_test_path = BASE_DIR / "test" / "generated_test_coverage.js"
            coverage_test_path.write_text(coverage_test_code, encoding="utf-8")

            cov_data = _run_coverage("test/generated_test_coverage.js", target_filename)

            coverage_returncode = cov_data["returncode"]
            raw_coverage_report = cov_data["raw_coverage_report"]
            coverage_report = cov_data["coverage_report"]
            cov_summary = cov_data["cov_summary"]

            coverage_valid = bool(raw_coverage_report)
            partial_coverage = True
        else:
            print("[Executor] ⚠️ Aucun test failing identifié précisément. Coverage non calculé.")
    else:
        cov_data = _run_coverage("test/generated_test.js", target_filename)

        coverage_returncode = cov_data["returncode"]
        raw_coverage_report = cov_data["raw_coverage_report"]
        coverage_report = cov_data["coverage_report"]
        cov_summary = cov_data["cov_summary"]

        coverage_valid = bool(raw_coverage_report)
        partial_coverage = False

    print(f"[Executor] Tests : {passed} ✅  {failed} ❌  (total {total})")
    print(f"[Executor] Acceptance rate : {acceptance_rate:.2f}%")
    print(
        f"[Executor] Coverage cible : "
        f"statements {cov_summary.get('statements', 0):.1f}%  "
        f"branches {cov_summary.get('branches', 0):.1f}%  "
        f"functions {cov_summary.get('functions', 0):.1f}%  "
        f"lines {cov_summary.get('lines', 0):.1f}%"
    )
    print(f"[Executor] Coverage valid : {coverage_valid} | partial : {partial_coverage}")

    execution_summary = {
        "total": total,
        "passed": passed,
        "failed": failed,
        "acceptance_rate": acceptance_rate,
        "coverage": cov_summary,
        "coverage_valid": coverage_valid,
        "partial_coverage": partial_coverage,
        "target_contract": target_filename,
        "commands": {
            "test_returncode": test_result.returncode,
            "coverage_returncode": coverage_returncode,
        },
    }

    _persist_outputs(
        test_code=test_code,
        test_report=test_report,
        execution_summary=execution_summary,
        coverage_report=coverage_report,
        raw_coverage_report=raw_coverage_report,
    )

    return {
        "test_report": test_report,
        "coverage_report": coverage_report,
        "execution_summary": execution_summary,
    }
