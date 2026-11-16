"""
single_agent_llm_only.py
-------------------------
Config 5: LLM-only baseline (single-agent, no RAG, no refinement loop).

One LLM call combining design + generation, with no retrieval at all — the
absolute floor baseline. No Test Designer / Analyzer / Evaluator / Corrector
nodes and no RAG context, matching protocol Config 5.
"""

from langchain_core.output_parsers import StrOutputParser

from backend.config.prompts import SINGLE_AGENT_LLM_ONLY_PROMPT
from backend.utils.llm import get_code_llm, invoke_with_retry
from backend.utils.generator_utils import (
    _build_minimal_deploy_test,
    _clean_js_output,
    _count_callable_api,
    _deterministic_auto_fix_pass,
    _extract_contract_name,
    _log_code,
    _save_artifact,
)


def single_agent_llm_only_node(state: dict) -> dict:
    print("--- SINGLE AGENT, LLM-ONLY (config_5) ---")

    contract_code: str = state.get("contract_code", "")
    user_story: str = state.get("user_story", "")
    contract_name = _extract_contract_name(contract_code)

    if _count_callable_api(contract_code) == 0:
        print("[SingleAgentLLMOnly] No callable function detected — minimal deploy test.")
        test_code = _build_minimal_deploy_test(contract_name, contract_code)
        _log_code("SingleAgentLLMOnly", test_code)
        _save_artifact("test_code.json", {"test_code": test_code})
        return {"test_code": test_code}

    llm = get_code_llm()
    chain = SINGLE_AGENT_LLM_ONLY_PROMPT | llm | StrOutputParser()

    print("[SingleAgentLLMOnly] Calling Codestral via SINGLE_AGENT_LLM_ONLY_PROMPT...")

    try:
        raw: str = invoke_with_retry(chain, {
            "contract_code": contract_code,
            "user_story": user_story,
        })
        print(f"[SingleAgentLLMOnly] Raw response: {len(raw)} chars.")
    except Exception as exc:
        print(f"[SingleAgentLLMOnly] LLM error: {exc}")
        raw = _build_minimal_deploy_test(contract_name, contract_code)
        print("[SingleAgentLLMOnly] Local fallback used.")

    test_code = _deterministic_auto_fix_pass(
        _clean_js_output(raw),
        contract_code=contract_code,
        analyzer_report=None,
    )

    _log_code("SingleAgentLLMOnly", test_code)
    _save_artifact("test_code.json", {"test_code": test_code})

    return {"test_code": test_code}
