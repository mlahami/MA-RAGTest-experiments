"""
orchestrator.py (config_4)
---------------------------
Builds the LangGraph pipeline for Config 4: RAG, single-agent, no refinement
loop.

Flow:
    single_agent_rag -> executor -> END

No Test Designer / Analyzer / Evaluator / Corrector nodes: this isolates the
contribution of multi-agent decomposition (RQ3) relative to Config 1, while
keeping RAG retrieval on (unlike Config 5, the LLM-only baseline).
"""

from typing import TypedDict

from langgraph.graph import StateGraph, END

from backend.agents.single_agent_rag import single_agent_rag_node
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

    graph.add_node("single_agent_rag", single_agent_rag_node)
    graph.add_node("executor", executor_node)

    graph.set_entry_point("single_agent_rag")
    graph.add_edge("single_agent_rag", "executor")
    graph.add_edge("executor", END)

    return graph.compile()
