"""
LangGraph agent responsible for designing the test strategy.

Config 2 (Full - RAG): no retrieval. The designer reasons from the contract
code and user story alone, with no ERC/SWC context injected into the prompt.
This isolates the contribution of RAG inside the multi-agent pipeline.
"""

import json

from langchain_core.output_parsers import JsonOutputParser

from backend.config.prompts import TEST_DESIGNER_PROMPT
from backend.utils.llm import get_llm, invoke_with_retry
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
    print("--- TEST DESIGNER (config_2, no RAG) ---")

    contract_code: str = state.get("contract_code", "")

    erc_context = "No RAG context: LLM-only ablation (Config 2, RAG disabled)."
    swc_context = "No RAG context: LLM-only ablation (Config 2, RAG disabled)."
    rag_cache = {
        "context": erc_context,
        "detected_ercs": [],
        "collection_name": None,
    }

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
