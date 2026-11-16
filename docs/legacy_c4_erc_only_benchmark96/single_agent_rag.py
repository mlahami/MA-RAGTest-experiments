"""
single_agent_rag.py
--------------------
Config 4: RAG, single-agent, no refinement loop.

One LLM call combining design + generation, with a single AdvancedRAG retrieval
call feeding the prompt. No Test Designer / Analyzer / Evaluator / Corrector
nodes — this isolates the contribution of multi-agent decomposition (RQ3)
while keeping RAG on, matching protocol Config 4 (RAG, single-agent, no loop).
"""

from langchain_core.output_parsers import StrOutputParser

from backend.config.prompts import SINGLE_AGENT_RAG_PROMPT
from backend.rag.advanced_rag import AdvancedRAG
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

# Same collection used by the multi-agent Test Designer for ERC/standard context
# (backend/agents/test_designer.py) — kept identical so the RAG axis itself is
# not confounded with a different retrieval corpus.
SINGLE_AGENT_RAG_COLLECTION = "erc_standards"


def single_agent_rag_node(state: dict) -> dict:
    print("--- SINGLE AGENT + RAG (config_4) ---")

    contract_code: str = state.get("contract_code", "")
    user_story: str = state.get("user_story", "")
    contract_name = _extract_contract_name(contract_code)

    if _count_callable_api(contract_code) == 0:
        print("[SingleAgentRAG] No callable function detected — minimal deploy test.")
        test_code = _build_minimal_deploy_test(contract_name, contract_code)
        _log_code("SingleAgentRAG", test_code)
        _save_artifact("test_code.json", {"test_code": test_code})
        return {"test_code": test_code}

    try:
        rag = AdvancedRAG(collection_name=SINGLE_AGENT_RAG_COLLECTION, compress_context=True)
        rag_result = rag.retrieve(contract_code)
        rag_context = rag_result.get("context", "No RAG context found.")
        print(f"[SingleAgentRAG] RAG context retrieved ({len(rag_context)} chars).")
    except Exception as exc:
        print(f"[SingleAgentRAG] RAG retrieval failed: {exc}")
        rag_context = "No RAG context available."

    llm = get_code_llm()
    chain = SINGLE_AGENT_RAG_PROMPT | llm | StrOutputParser()

    print("[SingleAgentRAG] Calling Codestral via SINGLE_AGENT_RAG_PROMPT...")

    try:
        raw: str = invoke_with_retry(chain, {
            "contract_code": contract_code,
            "user_story": user_story,
            "rag_context": rag_context,
        })
        print(f"[SingleAgentRAG] Raw response: {len(raw)} chars.")
    except Exception as exc:
        print(f"[SingleAgentRAG] LLM error: {exc}")
        raw = _build_minimal_deploy_test(contract_name, contract_code)
        print("[SingleAgentRAG] Local fallback used.")

    test_code = _deterministic_auto_fix_pass(
        _clean_js_output(raw),
        contract_code=contract_code,
        analyzer_report=None,
    )

    _log_code("SingleAgentRAG", test_code)
    _save_artifact("test_code.json", {"test_code": test_code})

    return {"test_code": test_code}
