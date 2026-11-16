"""
single_agent_rag.py
--------------------
Config 4: RAG, single-agent, no refinement loop.

One code-generation LLM call combining design + generation. To isolate the
multi-agent axis (RQ3), the agent receives the SAME knowledge base as the
multi-agent pipeline (C1/C3), retrieved with the same AdvancedRAG settings:

  - erc_standards        (C1/C3 Test Designer; skipped when no ERC is detected)
  - swc_vulnerabilities  (C1/C3 Test Designer; truncated to 6000 chars as there)
  - langchain            (C1/C3 Generator/Corrector: example contracts and tests)

No Test Designer / Analyzer / Evaluator / Corrector nodes.

History: the benchmark96_5reps_20261019 campaign used an earlier version that
queried erc_standards only (kept in docs/legacy_c4_erc_only_benchmark96/).
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

# Same collections and settings as the multi-agent pipeline (C1/C3):
# backend/agents/test_designer.py (erc_standards, swc_vulnerabilities) and
# backend/utils/generator_utils.py (GENERATOR_RAG_COLLECTION = "langchain").
ERC_COLLECTION = "erc_standards"
SWC_COLLECTION = "swc_vulnerabilities"
EXAMPLES_COLLECTION = "langchain"
_SWC_CONTEXT_CHAR_LIMIT = 6000  # identical to test_designer.py


def _retrieve(collection: str, contract_code: str, compress: bool, fallback: str) -> dict:
    try:
        result = AdvancedRAG(collection_name=collection, compress_context=compress).retrieve(contract_code)
        context = result.get("context") or fallback
        out = {"context": context, "detected_ercs": result.get("detected_ercs", []), "error": None}
    except Exception as exc:
        print(f"[SingleAgentRAG] {collection} retrieval failed: {exc}")
        out = {"context": fallback, "detected_ercs": [], "error": str(exc)}
    print(f"[SingleAgentRAG] {collection}: {len(out['context'])} chars.")
    return out


def single_agent_rag_node(state: dict) -> dict:
    print("--- SINGLE AGENT + RAG (config_4) ---")

    contract_code: str = state.get("contract_code", "")
    user_story: str = state.get("user_story", "")
    contract_name = _extract_contract_name(contract_code)
    compress = "no_compression" not in str(state.get("experiment_config", ""))

    if _count_callable_api(contract_code) == 0:
        print("[SingleAgentRAG] No callable function detected — minimal deploy test.")
        test_code = _build_minimal_deploy_test(contract_name, contract_code)
        _log_code("SingleAgentRAG", test_code)
        _save_artifact("test_code.json", {"test_code": test_code})
        return {"test_code": test_code}

    erc = _retrieve(ERC_COLLECTION, contract_code, compress, "ERC context unavailable.")
    swc = _retrieve(SWC_COLLECTION, contract_code, compress, "SWC context unavailable.")
    ex = _retrieve(EXAMPLES_COLLECTION, contract_code, compress, "No RAG context available.")

    swc_context = swc["context"]
    if len(swc_context) > _SWC_CONTEXT_CHAR_LIMIT:
        swc_context = swc_context[:_SWC_CONTEXT_CHAR_LIMIT] + "\n...[truncated]"

    _save_artifact("rag_context_c4.json", {
        "collections": [ERC_COLLECTION, SWC_COLLECTION, EXAMPLES_COLLECTION],
        "compress_context": compress,
        "detected_ercs": erc["detected_ercs"],
        "erc_chars": len(erc["context"]),
        "swc_chars": len(swc_context),
        "examples_chars": len(ex["context"]),
        "errors": {c: r["error"] for c, r in ((ERC_COLLECTION, erc), (SWC_COLLECTION, swc), (EXAMPLES_COLLECTION, ex)) if r["error"]},
    })

    llm = get_code_llm()
    chain = SINGLE_AGENT_RAG_PROMPT | llm | StrOutputParser()

    print("[SingleAgentRAG] Calling Codestral via SINGLE_AGENT_RAG_PROMPT...")

    try:
        raw: str = invoke_with_retry(chain, {
            "contract_code": contract_code,
            "user_story": user_story,
            "erc_context": erc["context"],
            "swc_context": swc_context,
            "relevant_examples": ex["context"],
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
