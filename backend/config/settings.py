"""
config.py
---------
Centralise toutes les constantes et variables d'environnement du projet.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Chemins principaux
# ---------------------------------------------------------------------------

BASE_DIR: Path = Path(__file__).parent.parent.parent.resolve()  # Navigate up from backend/config/

CONTRACTS_DIR: Path = BASE_DIR / "contracts"
OUTPUT_DIR:    Path = BASE_DIR / "outputs"
DATA_DIR:      Path = BASE_DIR / "data"
VECTOR_DB_DIR: Path = DATA_DIR / "vector_db"

# ---------------------------------------------------------------------------
# Paramètres de l'application
# ---------------------------------------------------------------------------

DEFAULT_CONTRACT_NAME: str = "Adoption"
MAX_RETRIES: int = 7

# ---------------------------------------------------------------------------
# Clés API
# ---------------------------------------------------------------------------

MISTRAL_API_KEY: str = os.getenv("MISTRAL_API_KEY", "")


def require_mistral_api_key() -> str:
    """Retourne la clé Mistral ou lève une erreur explicite si absente."""
    if not MISTRAL_API_KEY:
        raise EnvironmentError(
            "La variable d'environnement MISTRAL_API_KEY est manquante. "
            "Ajoutez-la dans votre fichier .env ou dans l'environnement système."
        )
    return MISTRAL_API_KEY
