"""
orchestrator.py (config_5)
---------------------------
Builds the LangGraph pipeline for Config 5: LLM-only baseline (single-agent,
no RAG, no refinement loop) — the absolute floor baseline.

Flow:
    single_agent_llm_only -> executor -> END

No Test Designer / Analyzer / Evaluator / Corrector nodes, and no RAG
retrieval: this is Config 4 (RAG, single-agent, no loop) with the RAG axis
also removed.
"""

from typing import TypedDict

from langgraph.graph import StateGraph, END

from backend.agents.single_agent_llm_only import single_agent_llm_only_node
from backend.agents.executor import executor_node


class PipelineState(TypedDict, total=False):
    contract_code:     str
    user_story:        str
    source_filename:   str
    experiment_config: str
    test_code:         str
    test_report:       dict
    coverage_report:   dict
    execution_summary: dict


def build_graph() -> StateGraph:
    graph = StateGraph(PipelineState)

    graph.add_node("single_agent_llm_only", single_agent_llm_only_node)
    graph.add_node("executor", executor_node)

    graph.set_entry_point("single_agent_llm_only")
    graph.add_edge("single_agent_llm_only", "executor")
    graph.add_edge("executor", END)

    return graph.compile()
