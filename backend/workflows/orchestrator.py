"""
orchestrator.py
---------------
Construit et retourne le graphe LangGraph du pipeline de génération de tests.

Ce module est le chef d'orchestre : il relie tous les nœuds agents et définit
les conditions de routage (stop / regenerate).
"""

from typing import TypedDict

from langgraph.graph import StateGraph, END

from backend.agents.test_designer  import test_designer_node
from backend.agents.generator      import generator_normal_node, generator_corrector_node
from backend.agents.executor       import executor_node
from backend.agents.analyzer       import analyzer_node
from backend.agents.evaluator      import evaluator_node
from backend.config.settings       import MAX_RETRIES


# ---------------------------------------------------------------------------
# Définition du state partagé
# ---------------------------------------------------------------------------

class PipelineState(TypedDict, total=False):
    contract_code:       str
    user_story:          str
    source_filename:     str   # nom du fichier .sol original (ex: "SimpleSwap.sol")
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
    prev_score:          float   # score de l'itération précédente pour détection de stagnation


# ---------------------------------------------------------------------------
# Helpers : calcul du score composite
# ---------------------------------------------------------------------------

def _compute_score(state: PipelineState) -> float:
    """
    Score composite = (tests passés × 10) + coverage statements.
    Utilisé pour détecter la stagnation entre deux itérations.
    """
    summary  = state.get("execution_summary", {})
    coverage = summary.get("coverage", {})
    return (
        summary.get("passed", 0) * 10
        + coverage.get("statements", 0)
    )


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
# Condition de routage après l'Évaluateur
# ---------------------------------------------------------------------------
def _route_after_evaluation(state: PipelineState) -> str:
    """
    Détermine si le pipeline doit continuer ou s'arrêter, 
    et affiche un bilan final unique et clair.
    """
    decision   = state.get("evaluation_decision", "stop")
    iterations = state.get("iterations", 0)

    # Affichage du tableau de bord des résultats (Tests + Coverage)
    _print_execution_summary(state)

    # --- Logique de détermination de l'arrêt ---
    stop_reason = None

    if iterations >= MAX_RETRIES:
        stop_reason = f"⛔ Limite de {MAX_RETRIES} itérations atteinte."
    
    elif decision == "regenerate" and iterations >= 2:
        curr_score = _compute_score(state)
        prev_score = state.get("prev_score", -1.0)
        if curr_score <= prev_score:
            stop_reason = f"⛔ Arrêt par stagnation (Score stable à {curr_score:.1f})."

    elif decision == "stop":
        stop_reason = "✅ Critères satisfaits ou arrêt structurel."

    # --- Sortie du graphe ---
    if stop_reason:
        print(f"\n[FIN DU PIPELINE] {stop_reason}")
        _print_contract_logic_warning_if_needed(state, stop_reason)
        print(f"Nombre total d'itérations parcourues : {iterations}\n")
        return END

    # Sinon, on continue vers l'incrémentation
    return "increment"


def _increment_iterations(state: PipelineState) -> dict:
    """
    Incrémente le compteur d'itérations et sauvegarde le score courant
    pour permettre la détection de stagnation à l'itération suivante.
    """
    new_count  = state.get("iterations", 0) + 1
    curr_score = _compute_score(state)
    print(
        f"[Orchestrator] 🔁 Itération {new_count}/{MAX_RETRIES} "
        f"— score={curr_score:.1f} — lancement de la correction…"
    )
    return {"iterations": new_count, "prev_score": curr_score}


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
    Construit et compile le graphe LangGraph du pipeline.

    Flux principal :
        test_designer → generator_normal → executor → analyzer → evaluator
                                ↑                                      |
                                └──────── corrector ←──── (regenerate) ┘
    """
    graph = StateGraph(PipelineState)

    # --- Nœuds ---
    graph.add_node("test_designer",    test_designer_node)
    graph.add_node("generator_normal", generator_normal_node)
    graph.add_node("executor",         executor_node)
    graph.add_node("analyzer",         analyzer_node)
    graph.add_node("evaluator",        evaluator_node)
    graph.add_node("increment",        _increment_iterations)
    graph.add_node("corrector",        generator_corrector_node)

    # --- Arêtes du flux principal ---
    graph.set_entry_point("test_designer")
    graph.add_edge("test_designer",    "generator_normal")
    graph.add_edge("generator_normal", "executor")
    graph.add_edge("executor",         "analyzer")
    graph.add_edge("analyzer",         "evaluator")

    # --- Routage conditionnel depuis l'Évaluateur ---
    graph.add_conditional_edges(
        "evaluator",
        _route_after_evaluation,
        {"increment": "increment", END: END},
    )

    # --- Boucle de correction ---
    graph.add_edge("increment", "corrector")
    graph.add_edge("corrector", "executor")

    return graph.compile()
