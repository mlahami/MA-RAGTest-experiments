"""
main.py
-------
Point d'entrée du pipeline de génération automatique de tests pour smart contracts.

Usage :
    python main.py

Nettoyage au démarrage :
    Tous les dossiers et fichiers générés par le pipeline précédent sont supprimés
    avant chaque exécution : outputs/, coverage/, mochawesome-report/, artifacts/,
    cache/, test/generated_test.js et .coverage_contracts/.
"""

import argparse
import shutil
import sys
from pathlib import Path

# Permet l'exécution directe depuis backend/ avec accès au projet racine
_ROOT = Path(__file__).parent.parent.resolve()
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from backend.workflows.orchestrator import build_graph
from backend.utils.llm import get_llm_stats, reset_llm_stats
from backend.config.settings import CONTRACTS_DIR, OUTPUT_DIR, DEFAULT_CONTRACT_NAME, BASE_DIR


# ---------------------------------------------------------------------------
# Nettoyage des artefacts du pipeline précédent
# ---------------------------------------------------------------------------

# Dossiers entiers à supprimer puis recréer vides
_DIRS_TO_CLEAN: list[Path] = [
    OUTPUT_DIR,                          # outputs/
    BASE_DIR / "coverage",               # rapport solidity-coverage
    BASE_DIR / "mochawesome-report",     # rapport JSON des tests Mocha
    BASE_DIR / "artifacts",              # compilation Hardhat
    BASE_DIR / "cache",                  # cache Hardhat
    BASE_DIR / ".coverage_contracts",    # dossier temporaire de coverage
    BASE_DIR / ".nyc_output",    
    BASE_DIR / "tests" ,      
]

# Fichiers isolés à supprimer
_FILES_TO_CLEAN: list[Path] = [
    BASE_DIR / "tests" / "generated_test.js",
    BASE_DIR / "coverage.json",
]


def clean_pipeline_artifacts() -> None:
    """
    Supprime tous les fichiers et dossiers générés par le pipeline précédent.
    Recrée OUTPUT_DIR vide pour accueillir les nouveaux artefacts.
    """
    print("[Main] 🧹 Nettoyage des artefacts précédents…")

    for folder in _DIRS_TO_CLEAN:
        if folder.exists():
            shutil.rmtree(folder, ignore_errors=True)
            print(f"[Main]   ✓ Supprimé : {folder.relative_to(BASE_DIR)}/")

    for file_path in _FILES_TO_CLEAN:
        if file_path.exists():
            try:
                file_path.unlink()
                print(f"[Main]   ✓ Supprimé : {file_path.relative_to(BASE_DIR)}")
            except OSError as exc:
                print(f"[Main]   ⚠️  Impossible de supprimer {file_path} : {exc}")

    # Recrée OUTPUT_DIR vide
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("[Main] ✅ Nettoyage terminé.\n")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_contract(contract_name: str | None = None) -> tuple[str, Path]:
    """
    Charge le code source Solidity du contrat.

    Cherche d'abord ``<contract_name>.sol`` dans CONTRACTS_DIR,
    puis prend le premier fichier .sol disponible si aucun nom n'est précisé.

    Returns:
        Tuple (code_source, chemin_du_fichier)

    Raises:
        FileNotFoundError: Si aucun contrat n'est trouvé.
    """
    if contract_name:
        path = CONTRACTS_DIR / f"{contract_name}.sol"
        if not path.exists():
            raise FileNotFoundError(
                f"Contrat introuvable : '{path}'\n"
                f"Placez votre fichier .sol dans '{CONTRACTS_DIR}'."
            )
    else:
        candidates = sorted(CONTRACTS_DIR.glob("*.sol"))
        if not candidates:
            raise FileNotFoundError(
                f"Aucun fichier .sol trouvé dans '{CONTRACTS_DIR}'."
            )
        path = candidates[0]

    return path.read_text(encoding="utf-8"), path


def load_user_story(contract_name: str) -> str:
    """
    Charge les spécifications utilisateur depuis plusieurs chemins candidats.

    Ordre de priorité :
    1) <contract_name>.specs.md
    2) user_story.specs.md
    3) <contract_name>.txt
    4) user_story.txt
    """
    candidates = [
        CONTRACTS_DIR / f"{contract_name}.specs.md",
        CONTRACTS_DIR / "user_story.specs.md",
        CONTRACTS_DIR / f"{contract_name}.txt",
        CONTRACTS_DIR / "user_story.txt",
    ]

    for story_path in candidates:
        if story_path.exists():
            return story_path.read_text(encoding="utf-8")
    return ""


# ---------------------------------------------------------------------------
# Point d'entrée
# ---------------------------------------------------------------------------

def main() -> None:
    # --- Traitement des arguments en ligne de commande ---
    parser = argparse.ArgumentParser(
        description="Exécute le pipeline de génération de tests pour un contrat Solidity."
    )
    parser.add_argument(
        "--contract",
        type=str,
        default=DEFAULT_CONTRACT_NAME,
        help=f"Nom du contrat à tester (sans l'extension .sol). Défaut: {DEFAULT_CONTRACT_NAME}"
    )
    args = parser.parse_args()
    contract_name = args.contract

    reset_llm_stats()

    # Nettoyage complet des artefacts du pipeline précédent
    clean_pipeline_artifacts()

    CONTRACTS_DIR.mkdir(parents=True, exist_ok=True)

    # --- Chargement du contrat ---
    try:
        contract_code, contract_path = load_contract(contract_name)
        user_story = load_user_story(contract_name)
        print(f"[Main] Contrat chargé : {contract_path}")
        if user_story:
            print(f"[Main] User story chargée ({len(user_story)} caractères).")
    except FileNotFoundError as exc:
        print(f"[Main] ❌ {exc}")
        sys.exit(1)

    # --- Construction du graphe LangGraph ---
    print("[Main] Construction du graphe LangGraph…")
    app = build_graph()

    # --- Exécution du pipeline ---
    initial_state = {
        "contract_code":   contract_code,
        "user_story":      user_story,
        "source_filename": contract_path.name, 
        "iterations":      0,
    }

    print("[Main] Démarrage du pipeline…\n")
    for chunk in app.stream(initial_state):
        for node_name in chunk:
            print(f"[Main] ✅ Nœud terminé : {node_name}")

    # --- Résumé ---
    stats = get_llm_stats()
    print(
        f"\n[Main] Résumé LLM — appels : {stats['calls']}, "
        f"durée totale : {stats['total_time_seconds']:.2f}s"
    )


if __name__ == "__main__":
    main()
