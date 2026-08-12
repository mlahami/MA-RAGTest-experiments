"""
orchestrator.py
---------------
Construit et retourne le graphe LangGraph du pipeline de génération de tests.

Config 3 (no-loop ablation) : passe unique, sans boucle de correction.
Réutilise les mêmes nœuds agents que la config stable (Config 1) ; seul le
routage après l'Évaluateur change pour toujours s'arrêter après la première
évaluation, au lieu de renvoyer vers un correcteur.
"""

from typing import TypedDict

from langgraph.graph import StateGraph, END

from backend.agents.test_designer  import test_designer_node
from backend.agents.generator      import generator_normal_node
from backend.agents.executor       import executor_node
from backend.agents.analyzer       import analyzer_node
from backend.agents.evaluator      import evaluator_node


# ---------------------------------------------------------------------------
# Définition du state partagé
# ---------------------------------------------------------------------------

class PipelineState(TypedDict, total=False):
    contract_code:       str
    user_story:          str
    source_filename:     str   # nom du fichier .sol original (ex: "SimpleSwap.sol")
    experiment_config:   str
    erc_context:         str
    test_design:         dict
    test_code:           str
    rag_cache:           dict
    test_report:         dict
    coverage_report:     dict
    execution_summary:   dict
    analyzer_report:     dict
    evaluation_decision: str
    evaluation_reason:   str
    iterations:          int


# ---------------------------------------------------------------------------
# Helpers : diagnostic de fin de pipeline
# ---------------------------------------------------------------------------

def _suspected_contract_logic_failures(state: PipelineState) -> list[dict]:
    """
    Retourne la liste des échecs pouvant indiquer un problème logique du contrat.
    Heuristique prudente : on exclut les erreurs d'appel API évidentes côté tests.
    """
    analyzer = state.get("analyzer_report", {}) or {}
    failures = analyzer.get("failures", []) if isinstance(analyzer, dict) else []
    if not isinstance(failures, list):
        return []

    suspected: list[dict] = []
    for item in failures:
        if not isinstance(item, dict):
            continue
        f_type = str(item.get("type", "")).upper()
        reason = str(item.get("reason", "")).lower()

        # Exclut les erreurs typiquement côté test (pas logique contrat).
        test_side_signals = [
            "cannot mix bigint",
            "unsafe",
            "is not a function",
            "expected undefined to deeply equal",
            "assertion_data_shape",
        ]
        if any(sig in reason for sig in test_side_signals) or f_type in {"ASSERTION_DATA_SHAPE", "CALL_ERROR", "OTHER"}:
            continue

        if f_type in {"REVERT_MISMATCH", "ASSERTION_MISMATCH"}:
            suspected.append(item)
            continue

        # Fallback pour anciens rapports sans champ "type"
        has_assertion_signal = "assertionerror" in reason or "expected " in reason
        has_revert_signal = "revert" in reason or "reverted" in reason
        has_call_signal = "is not a function" in reason
        if (has_assertion_signal or has_revert_signal) and not has_call_signal:
            suspected.append(item)

    return suspected


def _print_contract_logic_warning_if_needed(state: PipelineState, stop_reason: str) -> None:
    """
    Affiche un message de fin si des échecs persistants suggèrent une faute logique
    dans le contrat. Ne modifie jamais le contrat — diagnostic uniquement.
    """
    summary = state.get("execution_summary", {}) or {}
    failed = int(summary.get("failed", 0) or 0)
    if failed <= 0:
        return

    suspected = _suspected_contract_logic_failures(state)
    if not suspected:
        return

    print("[DIAGNOSTIC] ⚠️  Anomalie potentielle de logique métier dans le contrat détectée.")
    print("[DIAGNOSTIC] Le pipeline corrige uniquement les tests et ne modifie jamais le contrat Solidity.")
    print(f"[DIAGNOSTIC] Contexte d'arrêt : {stop_reason}")
    print(f"[DIAGNOSTIC] Échecs suspects : {len(suspected)}/{failed}")

    for idx, failure in enumerate(suspected[:3], start=1):
        test_name = str(failure.get("test", "<test inconnu>"))
        reason = str(failure.get("reason", "raison indisponible"))
        print(f"[DIAGNOSTIC] {idx}. {test_name}")
        print(f"[DIAGNOSTIC]    ↳ {reason}")

    print("[DIAGNOSTIC] Action recommandée : revue manuelle des règles métier dans le contrat.")


# ---------------------------------------------------------------------------
# Condition de routage après l'Évaluateur (passe unique)
# ---------------------------------------------------------------------------
def _route_after_evaluation(state: PipelineState) -> str:
    """
    Config 3 : pipeline en passe unique. On affiche le bilan final et le
    diagnostic éventuel, puis on s'arrête toujours après l'évaluation,
    quelle que soit la décision de l'Évaluateur.
    """
    _print_execution_summary(state)

    stop_reason = "⛔ Passe unique (boucle de correction désactivée pour Config 3)."
    print(f"\n[FIN DU PIPELINE] {stop_reason}")
    _print_contract_logic_warning_if_needed(state, stop_reason)
    print("Nombre total d'itérations parcourues : 0\n")
    return END


# ---------------------------------------------------------------------------
# Affichage du résumé d'exécution
# ---------------------------------------------------------------------------

def _print_execution_summary(state: PipelineState) -> None:
    """Affiche dans le terminal un résumé lisible des résultats Hardhat."""
    summary  = state.get("execution_summary", {})
    decision = state.get("evaluation_decision", "?")
    reason   = state.get("evaluation_reason", "")
    coverage = summary.get("coverage", {})

    total     = summary.get("total",  0)
    passed    = summary.get("passed", 0)
    failed    = summary.get("failed", 0)
    stmts     = coverage.get("statements", 0)
    branches  = coverage.get("branches",   0)
    functions = coverage.get("functions",  0)

    bar_ok  = "█" * passed
    bar_err = "░" * failed

    print("\n" + "─" * 50)
    print("  📊  RÉSULTATS D'EXÉCUTION")
    print("─" * 50)
    print(f"  Tests     : {bar_ok}{bar_err}  {passed} ✅  {failed} ❌  (total : {total})")
    print(f"  Coverage statements : {stmts:.1f} %")
    print(f"  Coverage branches   : {branches:.1f} %")
    print(f"  Coverage functions  : {functions:.1f} %")
    print(f"  Décision évaluateur : {'🔁 REGENERATE' if decision == 'regenerate' else '🛑 STOP'}")
    if reason:
        print(f"  Raison              : {reason}")
    print("─" * 50 + "\n")


# ---------------------------------------------------------------------------
# Construction du graphe
# ---------------------------------------------------------------------------

def build_graph() -> StateGraph:
    """
    Construit et compile le graphe LangGraph du pipeline en passe unique.

    Flux principal (pas de boucle de correction) :
        test_designer → generator_normal → executor → analyzer → evaluator → END
    """
    graph = StateGraph(PipelineState)

    # --- Nœuds ---
    graph.add_node("test_designer",    test_designer_node)
    graph.add_node("generator_normal", generator_normal_node)
    graph.add_node("executor",         executor_node)
    graph.add_node("analyzer",         analyzer_node)
    graph.add_node("evaluator",        evaluator_node)

    # --- Arêtes du flux principal ---
    graph.set_entry_point("test_designer")
    graph.add_edge("test_designer",    "generator_normal")
    graph.add_edge("generator_normal", "executor")
    graph.add_edge("executor",         "analyzer")
    graph.add_edge("analyzer",         "evaluator")

    # --- Routage depuis l'Évaluateur : toujours END (pas de correcteur) ---
    graph.add_conditional_edges(
        "evaluator",
        _route_after_evaluation,
        {END: END},
    )

    return graph.compile()
