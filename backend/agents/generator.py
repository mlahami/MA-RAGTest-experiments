import json
import re

from langchain_core.output_parsers import StrOutputParser

from backend.config.prompts import GENERATOR_NORMAL_PROMPT, GENERATOR_CORRECTOR_PROMPT
from backend.utils.llm import get_code_llm, invoke_with_retry
from backend.utils.generator_utils import (
    _build_minimal_deploy_test,
    _clean_js_output,
    _count_callable_api,
    _deterministic_auto_fix_pass,
    _extract_contract_name,
    _get_rag_context,
    _log_code,
    _save_artifact,
)

GENERATOR_RAG_COLLECTION = "langchain"

_HELPER_CONTRACT_NAMES = (
    "MaliciousContract",
    "ReentrancyAttacker",
    "ReentrantAttacker",
    "Attacker",
    "MockContract",
    "FakeContract",
    "MockReentrant",
    "NonPayableContract",
    "ForceSend",
    "ForceSender",
    "SelfDestructSender",
)

_HELPER_SYMBOL_RE = re.compile(
    r"\b(" + "|".join(re.escape(name) for name in _HELPER_CONTRACT_NAMES) + r")\b",
    flags=re.IGNORECASE,
)


def _sanitize_invalid_helper_contracts(test_code: str, target_contract_name: str) -> str:
    """
    Neutralise les tests qui utilisent des contrats inventés par le LLM.
    Exemple : MockReentrant, MockOverflow, Attacker, etc.
    Ces tests sont marqués it.skip afin de préserver une évaluation honnête :
    ils restent présents mais ne cassent pas toute l'exécution.
    """
    code = test_code or ""

    code = re.sub(
        r'\n\s*//\s*Mock contract[\s\S]*$',
        '\n',
        code,
        flags=re.MULTILINE,
    )

    factories = re.findall(
        r'ethers\.getContractFactory\(\s*["\']([^"\']+)["\']',
        code,
    )

    invalid_factories = {
        name for name in factories
        if name != target_contract_name
    }

    has_helper_symbols = bool(_HELPER_SYMBOL_RE.search(code))

    if not invalid_factories and not has_helper_symbols:
        return code

    print(f"[Generator AutoFix] Contrats helper inventés détectés : {sorted(invalid_factories)}")

    lines = code.splitlines()
    result = []
    i = 0

    while i < len(lines):
        line = lines[i]

        if re.search(r'\bit\s*\(\s*["\']', line):
            block_lines = [line]
            brace_balance = line.count("{") - line.count("}")
            j = i + 1

            while j < len(lines):
                block_lines.append(lines[j])
                brace_balance += lines[j].count("{") - lines[j].count("}")

                if brace_balance <= 0 and re.search(r'\}\s*\)\s*;', lines[j]):
                    break

                j += 1

            block_text = "\n".join(block_lines)

            uses_invalid_factory = any(
                f'getContractFactory("{name}"' in block_text
                or f"getContractFactory('{name}'" in block_text
                for name in invalid_factories
            )

            if uses_invalid_factory:
                block_lines[0] = block_lines[0].replace("it(", "it.skip(", 1)
                print("[Generator AutoFix] Test utilisant un helper inventé marqué it.skip.")

            result.extend(block_lines)
            i = j + 1
        else:
            result.append(line)
            i += 1

    return "\n".join(result)


def _skip_blocks_with_forbidden_helper_symbols(test_code: str) -> str:
    code = test_code or ""
    if not _HELPER_SYMBOL_RE.search(code):
        return code

    lines = code.splitlines()
    result = []
    i = 0
    skipped = 0

    while i < len(lines):
        line = lines[i]
        if re.search(r'\bit\s*\(\s*["\']', line) and "it.skip" not in line:
            block_lines = [line]
            brace_balance = line.count("{") - line.count("}")
            j = i + 1
            while j < len(lines):
                block_lines.append(lines[j])
                brace_balance += lines[j].count("{") - lines[j].count("}")
                if brace_balance <= 0 and re.search(r'\}\s*\)\s*;', lines[j]):
                    break
                j += 1

            block_text = "\n".join(block_lines)
            if _HELPER_SYMBOL_RE.search(block_text):
                block_lines[0] = block_lines[0].replace("it(", "it.skip(", 1)
                block_lines.insert(
                    1,
                    "      // [INVALID_GENERATED_TEST:HELPER_CONTRACT_FORBIDDEN] "
                    "Skipped by MA-RAGTest Option A: helper/attacker contracts are disabled for config_1.",
                )
                skipped += 1

            result.extend(block_lines)
            i = j + 1
        else:
            result.append(line)
            i += 1

    if skipped:
        print(f"[Generator AutoFix] {skipped} test(s) avec helper/attaquant interdit marquÃ©s it.skip.")

    return "\n".join(result)


def generator_normal_node(state: dict) -> dict:
    print("--- GENERATOR (NORMAL) ---")

    contract_code: str = state.get("contract_code", "")
    test_design: dict = state.get("test_design", {})
    contract_name = _extract_contract_name(contract_code)

    if _count_callable_api(contract_code) == 0:
        print("[Generator Normal] ℹ️ Aucune fonction callable détectée — génération d'un test minimal.")
        test_code = _build_minimal_deploy_test(contract_name, contract_code)
        _log_code("Generator Normal", test_code)
        _save_artifact("test_code.json", {"test_code": test_code})
        return {"test_code": test_code}

    erc_context, detected_ercs = _get_rag_context(state)
    relevant_examples: str = ""

    llm = get_code_llm()
    chain = GENERATOR_NORMAL_PROMPT | llm | StrOutputParser()

    print("[Generator Normal] Appel Codestral via GENERATOR_NORMAL_PROMPT…")

    try:
        raw: str = invoke_with_retry(chain, {
            "erc_context": erc_context,
            "relevant_examples": relevant_examples,
            "contract_code": contract_code,
            "test_design_json": json.dumps(test_design, indent=2, ensure_ascii=False),
        })
        print(f"[Generator Normal] Réponse brute : {len(raw)} caractères.")
    except Exception as exc:
        print(f"[Generator Normal] ❌ Erreur Codestral : {exc}")
        raw = _build_minimal_deploy_test(contract_name, contract_code)
        print("[Generator Normal] ℹ️ Fallback local activé.")

    test_code = _deterministic_auto_fix_pass(
        _clean_js_output(raw),
        contract_code=contract_code,
        analyzer_report=None,
    )

    test_code = _skip_blocks_with_forbidden_helper_symbols(
        _sanitize_invalid_helper_contracts(test_code, contract_name)
    )

    _log_code("Generator Normal", test_code)
    _save_artifact("test_code.json", {"test_code": test_code})

    return {"test_code": test_code}


def generator_corrector_node(state: dict) -> dict:
    print("--- GENERATOR (CORRECTOR) ---")

    contract_code: str = state.get("contract_code", "")
    existing_code: str = state.get("test_code", "")
    analyzer_report: dict = state.get("analyzer_report", {}) or {}
    execution_summary: dict = state.get("execution_summary", {}) or {}
    test_report: dict = state.get("test_report", {}) or {}

    contract_name = _extract_contract_name(contract_code)

    if _count_callable_api(contract_code) == 0:
        print("[Generator Corrector] ℹ️ Contrat sans API callable — retour au test minimal.")
        return {"test_code": _build_minimal_deploy_test(contract_name, contract_code)}

    if not existing_code or not existing_code.strip():
        print("[Generator Corrector] ⚠️ test_code vide dans le state.")
        fallback = _build_minimal_deploy_test(contract_name, contract_code)
        _log_code("Generator Corrector", fallback)
        return {"test_code": fallback}

    print(f"[Generator Corrector] Code existant : {existing_code.count(chr(10)) + 1} lignes.")

    failures = analyzer_report.get("failures", [])
    failed_titles = list({
        f["test"]
        for f in failures
        if isinstance(f, dict) and f.get("test")
    })

    failed_count = int(execution_summary.get("failed", 0) or 0)
    coverage = execution_summary.get("coverage", {}) or {}
    stmts = float(coverage.get("statements", 0) or 0)
    branches = float(coverage.get("branches", 0) or 0)
    coverage_valid = bool(execution_summary.get("coverage_valid", False))

    if failed_count > 0:
        correction_mode = "fix_failing_tests"
        print("[Generator Corrector] Mode correction des tests en échec activé.")
    elif coverage_valid and (stmts < 85 or branches < 80):
        correction_mode = "improve_coverage"
        print("[Generator Corrector] Mode amélioration coverage activé.")
    else:
        correction_mode = "general_refinement"
        print("[Generator Corrector] Mode raffinement général activé.")

    base_code = _deterministic_auto_fix_pass(
        existing_code,
        contract_code=contract_code,
        analyzer_report=analyzer_report,
    )

    base_code = _skip_blocks_with_forbidden_helper_symbols(
        _sanitize_invalid_helper_contracts(base_code, contract_name)
    )

    print(f"[Generator Corrector] {len(failed_titles)} test(s) en échec identifiés par Analyzer.")
    print(
        f"[Generator Corrector] failed_count={failed_count}, "
        f"coverage_valid={coverage_valid}, stmts={stmts}, branches={branches}"
    )

    if not base_code or not base_code.strip():
        print("[Generator Corrector] ℹ️ Code vide après AutoFix — fallback local.")
        fallback = _build_minimal_deploy_test(contract_name, contract_code)
        _log_code("Generator Corrector", fallback)
        return {"test_code": fallback}

    _save_artifact("base_code_before_correction.json", {"test_code": base_code})
    _save_artifact("analyzer_report.json", analyzer_report)
    _save_artifact("failed_tests.json", {"failed": failed_titles, "details": failures})
    _save_artifact("execution_summary.json", execution_summary)

    erc_context, detected_ercs = _get_rag_context(state)
    relevant_examples: str = ""

    llm = get_code_llm()
    chain = GENERATOR_CORRECTOR_PROMPT | llm | StrOutputParser()

    print("[Generator Corrector] Appel Codestral via GENERATOR_CORRECTOR_PROMPT…")

    test_stdout = test_report.get("stdout", "")
    test_stderr = test_report.get("stderr", "")

    try:
        raw: str = invoke_with_retry(chain, {
            "erc_context": erc_context,
            "relevant_examples": relevant_examples,
            "contract_code": contract_code,
            "test_code": base_code,
            "failed_tests_json": json.dumps(failures, ensure_ascii=False),
            "analyzer_json": json.dumps(analyzer_report, ensure_ascii=False),
            "execution_summary_json": json.dumps(execution_summary, ensure_ascii=False),
            "coverage_summary_json": json.dumps(coverage, ensure_ascii=False),
            "correction_mode": correction_mode,
            "test_stdout": test_stdout,
            "test_stderr": test_stderr,
        })
        print(f"[Generator Corrector] Réponse brute : {len(raw)} caractères.")
    except Exception as exc:
        print(f"[Generator Corrector] ❌ Erreur Codestral : {exc}")
        raw = base_code

    corrected_code = _deterministic_auto_fix_pass(
        _clean_js_output(raw),
        contract_code=contract_code,
        analyzer_report=analyzer_report,
    )

    corrected_code = _skip_blocks_with_forbidden_helper_symbols(
        _sanitize_invalid_helper_contracts(corrected_code, contract_name)
    )

    _log_code("Generator Corrector", corrected_code)

    return {"test_code": corrected_code}
