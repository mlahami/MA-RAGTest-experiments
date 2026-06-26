"""LangGraph agent responsible for designing the test strategy."""

import json

from langchain_core.output_parsers import JsonOutputParser

from backend.config.prompts import TEST_DESIGNER_PROMPT
from backend.utils.llm import get_llm, invoke_with_retry
from backend.rag.advanced_rag import AdvancedRAG
from backend.config.settings import OUTPUT_DIR


def test_designer_node(state: dict) -> dict:
    """
    LangGraph node: TEST DESIGNER.

    Inputs:
    - contract_code
    - user_story, optional

    Outputs:
    - test_design
    - erc_context
    - rag_cache
    """
    print("--- TEST DESIGNER ---")

    contract_code: str = state.get("contract_code", "")

    rag_cache: dict = {}
    try:
        rag = AdvancedRAG(collection_name="erc_standards")
        rag_result = rag.retrieve(contract_code)
        erc_context = rag_result.get("context", "No ERC standard detected.")
        rag_cache = {
            "context": erc_context,
            "detected_ercs": rag_result.get("detected_ercs", []),
            "collection_name": "erc_standards",
        }
    except Exception as exc:
        print(f"[Test Designer] ERC RAG failed: {exc}")
        erc_context = "ERC context unavailable."
        rag_cache = {
            "context": erc_context,
            "detected_ercs": [],
            "collection_name": "erc_standards",
        }

    try:
        rag_swc = AdvancedRAG(collection_name="swc_vulnerabilities")
        swc_result = rag_swc.retrieve(contract_code)
        swc_context = swc_result.get("context", "SWC context unavailable.")
        swc_findings = swc_result.get("findings", [])
    except Exception as exc:
        print(f"[Test Designer] SWC RAG failed: {exc}")
        swc_context = "SWC context unavailable."
        swc_findings = []

    # Keep the prompt payload bounded; complete findings remain persisted for analysis.
    _SWC_CONTEXT_CHAR_LIMIT = 6000
    if len(swc_context) > _SWC_CONTEXT_CHAR_LIMIT:
        swc_context = swc_context[:_SWC_CONTEXT_CHAR_LIMIT] + "\n...[truncated]"

    llm = get_llm()
    chain = TEST_DESIGNER_PROMPT | llm
    parser = JsonOutputParser()

    try:
        message = invoke_with_retry(chain, {
            "contract_code": contract_code,
            "user_story": state.get("user_story", ""),
            "erc_context": erc_context,
            "swc_context": swc_context,
        })
        result: dict = parser.invoke(message)
    except Exception as exc:
        print(f"[Test Designer] LLM fallback activated: {exc}")
        result = {
            "contract_name": "Unknown",
            "test_suites": [],
            "error": str(exc),
        }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(OUTPUT_DIR / "test_design.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
    except OSError as exc:
        print(f"[Test Designer] Could not save test_design.json: {exc}")

    return {
        "test_design": result,
        "erc_context": erc_context,
        "rag_cache": rag_cache,
    }
