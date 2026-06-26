"""
api.py
------
Serveur FastAPI exposant le pipeline SolidTest via HTTP.
À placer à la RACINE du projet (même niveau que main.py).

Démarrage :
    uvicorn api:app --reload --port 8000

Endpoints :
    POST /api/run              → lance le pipeline
    GET  /api/run/{run_id}     → statut + résultat d'un run
    GET  /api/history          → tous les runs terminés
    GET  /api/results/{run_id} → test_report + coverage_report détaillés
    DELETE /api/history        → vider l'historique
"""

import sys
import uuid
import asyncio
import json
import sqlite3
import threading
import shutil
from pathlib import Path
from datetime import datetime

# Permet d'importer backend/ depuis le projet racine
_ROOT = Path(__file__).parent.parent.resolve()  # Navigate to project root
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.workflows.orchestrator import build_graph
from backend.config.settings import OUTPUT_DIR, CONTRACTS_DIR
from backend.utils.llm import reset_llm_stats, get_llm_stats

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="SolidTest API",
    description="API pour le pipeline de génération automatique de tests Solidity",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def _on_startup() -> None:
    _init_db()
    _load_runs_from_db()

# ---------------------------------------------------------------------------
# Stockage en mémoire des runs
# ---------------------------------------------------------------------------

runs: dict[str, dict] = {}

# Hint de progression pour refléter l'etape en cours dans l'UI
# meme quand un noeud long (ex: executor) est toujours en execution.
_NEXT_NODE_HINT: dict[str, str] = {
    "test_designer": "generator_normal",
    "generator_normal": "executor",
    "executor": "analyzer",
    "analyzer": "evaluator",
    "increment": "corrector",
    "corrector": "executor",
}

# ---------------------------------------------------------------------------
# Persistance SQLite des runs
# ---------------------------------------------------------------------------

_OLD_DB_PATH = _ROOT / "outputs" / "runs.sqlite3"
_DB_PATH = _ROOT / "data" / "runs.sqlite3"
_DB_LOCK = threading.Lock()


def _db_connect() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _json_dumps(value) -> str:
    return json.dumps(value if value is not None else None, ensure_ascii=False)


def _json_loads(value: str | None):
    if not value:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return None


def _init_db() -> None:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Migration one-shot: preserve runs if an old DB exists in outputs/.
    if not _DB_PATH.exists() and _OLD_DB_PATH.exists():
        shutil.copy2(_OLD_DB_PATH, _DB_PATH)

    with _DB_LOCK, _db_connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                contract_name TEXT,
                started_at TEXT,
                finished_at TEXT,
                current_node TEXT,
                iterations INTEGER DEFAULT 0,
                summary TEXT,
                error TEXT,
                test_report TEXT,
                coverage_report TEXT,
                analyzer_report TEXT,
                test_code TEXT,
                test_design TEXT,
                llm_stats TEXT,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def _persist_run(run: dict) -> None:
    with _DB_LOCK, _db_connect() as conn:
        conn.execute(
            """
            INSERT INTO runs (
                run_id, status, contract_name, started_at, finished_at, current_node,
                iterations, summary, error, test_report, coverage_report, analyzer_report,
                test_code, test_design, llm_stats, updated_at
            ) VALUES (
                :run_id, :status, :contract_name, :started_at, :finished_at, :current_node,
                :iterations, :summary, :error, :test_report, :coverage_report, :analyzer_report,
                :test_code, :test_design, :llm_stats, :updated_at
            )
            ON CONFLICT(run_id) DO UPDATE SET
                status=excluded.status,
                contract_name=excluded.contract_name,
                started_at=excluded.started_at,
                finished_at=excluded.finished_at,
                current_node=excluded.current_node,
                iterations=excluded.iterations,
                summary=excluded.summary,
                error=excluded.error,
                test_report=excluded.test_report,
                coverage_report=excluded.coverage_report,
                analyzer_report=excluded.analyzer_report,
                test_code=excluded.test_code,
                test_design=excluded.test_design,
                llm_stats=excluded.llm_stats,
                updated_at=excluded.updated_at
            """,
            {
                "run_id": run.get("run_id"),
                "status": run.get("status", "running"),
                "contract_name": run.get("contract_name", "UnknownContract"),
                "started_at": run.get("started_at"),
                "finished_at": run.get("finished_at"),
                "current_node": run.get("current_node"),
                "iterations": int(run.get("iterations", 0) or 0),
                "summary": _json_dumps(run.get("summary")),
                "error": run.get("error"),
                "test_report": _json_dumps(run.get("test_report")),
                "coverage_report": _json_dumps(run.get("coverage_report")),
                "analyzer_report": _json_dumps(run.get("analyzer_report")),
                "test_code": run.get("test_code") or "",
                "test_design": _json_dumps(run.get("test_design")),
                "llm_stats": _json_dumps(run.get("llm_stats")),
                "updated_at": datetime.now().isoformat(),
            },
        )
        conn.commit()


def _load_runs_from_db() -> None:
    with _DB_LOCK, _db_connect() as conn:
        rows = conn.execute("SELECT * FROM runs ORDER BY started_at DESC").fetchall()

    for row in rows:
        run = {
            "run_id": row["run_id"],
            "status": row["status"],
            "contract_name": row["contract_name"],
            "started_at": row["started_at"],
            "finished_at": row["finished_at"],
            "current_node": row["current_node"],
            "iterations": int(row["iterations"] or 0),
            "summary": _json_loads(row["summary"]),
            "error": row["error"],
            "test_report": _json_loads(row["test_report"]),
            "coverage_report": _json_loads(row["coverage_report"]),
            "analyzer_report": _json_loads(row["analyzer_report"]),
            "test_code": row["test_code"] or "",
            "test_design": _json_loads(row["test_design"]),
            "llm_stats": _json_loads(row["llm_stats"]),
        }
        runs[run["run_id"]] = run


def _clear_runs_db() -> None:
    with _DB_LOCK, _db_connect() as conn:
        conn.execute("DELETE FROM runs")
        conn.commit()

# ---------------------------------------------------------------------------
# Modèles Pydantic
# ---------------------------------------------------------------------------

class RunRequest(BaseModel):
    contract_code: str
    contract_name: str = ""
    user_story: str = ""

class RunResponse(BaseModel):
    run_id: str
    status: str
    message: str

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_summary(state: dict) -> dict:
    """Extrait un résumé propre depuis le state final du pipeline."""
    summary  = state.get("execution_summary", {}) or {}
    coverage = summary.get("coverage", {}) or {}
    analyzer = state.get("analyzer_report", {}) or {}

    return {
        "total":    int(summary.get("total",  0) or 0),
        "passed":   int(summary.get("passed", 0) or 0),
        "failed":   int(summary.get("failed", 0) or 0),
        "coverage": {
            "statements": float(coverage.get("statements", 0) or 0),
            "branches":   float(coverage.get("branches",   0) or 0),
            "functions":  float(coverage.get("functions",  0) or 0),
        },
        "evaluation_decision": state.get("evaluation_decision", ""),
        "evaluation_reason":   state.get("evaluation_reason",   ""),
        "iterations":          int(state.get("iterations", 0) or 0),
        "failures_count":      len(analyzer.get("failures", []) or []),
        "detected_ercs":       (state.get("rag_cache", {}) or {}).get("detected_ercs", []),
    }


def _safe_test_report(state: dict) -> dict:
    """Retourne le test_report nettoyé."""
    report = state.get("test_report", {}) or {}
    stats  = report.get("stats", {}) or {}
    return {
        "stats": {
            "passes":   stats.get("passes",   0),
            "failures": stats.get("failures", 0),
            "tests":    stats.get("tests",    0),
        },
        "results": report.get("results", []),
    }


def _safe_coverage_report(state: dict) -> dict:
    """Retourne le coverage_report (peut être volumineux — tronqué à 50 fichiers)."""
    report = state.get("coverage_report", {}) or {}
    if "total" in report:
        return report
    # coverage-final.json : on limite le nombre de clés
    return dict(list(report.items())[:50])


def _safe_analyzer_report(state: dict) -> dict:
    """Retourne l'analyzer_report nettoyé."""
    report = state.get("analyzer_report", {}) or {}
    return {
        "failures":         report.get("failures", []),
        "missing_coverage": report.get("missing_coverage", {}),
        "suggestions":      report.get("suggestions", []),
    }

# ---------------------------------------------------------------------------
# Tâche de fond : exécution du pipeline
# ---------------------------------------------------------------------------

async def execute_pipeline(run_id: str, req: RunRequest) -> None:
    """Exécute le pipeline LangGraph dans un thread séparé (non-bloquant)."""
    loop = asyncio.get_event_loop()

    def _run_sync():
        reset_llm_stats()
        graph = build_graph()
        final_state: dict = {}

        for chunk in graph.stream({
            "contract_code":   req.contract_code,
            "source_filename": (req.contract_name + ".sol") if req.contract_name else "",
            "user_story":      req.user_story,
            "iterations":      0,
        }):
            # chunk = { node_name: {...state updates...} }
            for node_name, node_state in chunk.items():
                final_state.update(node_state)
                # Mise à jour du statut en temps réel
                runs[run_id]["current_node"] = node_name
                runs[run_id]["iterations"]   = int(final_state.get("iterations", 0) or 0)
                _persist_run(runs[run_id])

                # Indique l'etape suivante pour synchroniser l'UI
                # pendant l'execution des noeuds potentiellement longs.
                hinted_next = _NEXT_NODE_HINT.get(node_name)
                if hinted_next and runs[run_id].get("status") == "running":
                    runs[run_id]["current_node"] = hinted_next
                    _persist_run(runs[run_id])

        return final_state

    try:
        final_state = await loop.run_in_executor(None, _run_sync)
        llm_stats   = get_llm_stats()

        runs[run_id].update({
            "status":          "done",
            "finished_at":     datetime.now().isoformat(),
            "current_node":    "finished",
            "summary":         _safe_summary(final_state),
            "test_report":     _safe_test_report(final_state),
            "coverage_report": _safe_coverage_report(final_state),
            "analyzer_report": _safe_analyzer_report(final_state),
            "test_code":       final_state.get("test_code", ""),
            "test_design":     final_state.get("test_design", {}),
            "llm_stats":       llm_stats,
            "error":           None,
        })
        _persist_run(runs[run_id])

    except Exception as exc:
        runs[run_id].update({
            "status":      "error",
            "finished_at": datetime.now().isoformat(),
            "current_node": "error",
            "error":        str(exc),
            "summary":      None,
        })
        _persist_run(runs[run_id])
        print(f"[API] Pipeline erreur ({run_id}): {exc}")

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/")
async def root():
    return {
        "name":    "SolidTest API",
        "version": "1.0.0",
        "status":  "running",
        "endpoints": [
            "POST /api/run",
            "GET  /api/run/{run_id}",
            "GET  /api/history",
            "GET  /api/results/{run_id}",
            "DELETE /api/history",
        ],
    }


@app.post("/api/run", response_model=RunResponse)
async def start_run(req: RunRequest, background_tasks: BackgroundTasks):
    """
    Lance le pipeline SolidTest sur le contrat fourni.
    Retourne immédiatement un run_id pour suivre l'avancement.
    """
    if not req.contract_code.strip():
        raise HTTPException(status_code=400, detail="contract_code ne peut pas être vide.")

    run_id = str(uuid.uuid4())
    runs[run_id] = {
        "run_id":        run_id,
        "status":        "running",
        "contract_name": req.contract_name or "UnknownContract",
        "started_at":    datetime.now().isoformat(),
        "finished_at":   None,
        "current_node":  "starting",
        "iterations":    0,
        "summary":       None,
        "error":         None,
    }
    _persist_run(runs[run_id])

    background_tasks.add_task(execute_pipeline, run_id, req)

    return RunResponse(
        run_id=run_id,
        status="running",
        message=f"Pipeline démarré. Suivez l'avancement via GET /api/run/{run_id}",
    )


@app.get("/api/run/{run_id}")
async def get_run_status(run_id: str):
    """
    Retourne le statut et le résumé d'un run.
    Statuts possibles : running | done | error

    Polling recommandé toutes les 3 secondes depuis le frontend.
    """
    if run_id not in runs:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' introuvable.")

    run = runs[run_id]
    # En mode "running", ne retourner que les infos légères (pas les rapports)
    if run["status"] == "running":
        return {
            "run_id":       run_id,
            "status":       "running",
            "contract_name": run.get("contract_name"),
            "started_at":   run.get("started_at"),
            "current_node": run.get("current_node"),
            "iterations":   run.get("iterations", 0),
        }

    return run


@app.get("/api/results/{run_id}")
async def get_run_results(run_id: str):
    """
    Retourne les résultats détaillés d'un run terminé :
    test_report, coverage_report, analyzer_report, test_code.
    """
    if run_id not in runs:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' introuvable.")

    run = runs[run_id]
    if run["status"] == "running":
        raise HTTPException(status_code=202, detail="Pipeline encore en cours d'exécution.")
    if run["status"] == "error":
        raise HTTPException(status_code=500, detail=run.get("error", "Erreur inconnue."))

    return {
        "run_id":          run_id,
        "contract_name":   run.get("contract_name"),
        "summary":         run.get("summary"),
        "test_report":     run.get("test_report"),
        "coverage_report": run.get("coverage_report"),
        "analyzer_report": run.get("analyzer_report"),
        "test_code":       run.get("test_code"),
        "test_design":     run.get("test_design"),
        "llm_stats":       run.get("llm_stats"),
    }


@app.get("/api/history")
async def get_history():
    """
    Retourne la liste de tous les runs (terminés et en cours),
    triés du plus récent au plus ancien.
    """
    all_runs = []
    for run in runs.values():
        all_runs.append({
            "run_id":        run["run_id"],
            "status":        run["status"],
            "contract_name": run.get("contract_name"),
            "started_at":    run.get("started_at"),
            "finished_at":   run.get("finished_at"),
            "current_node":  run.get("current_node"),
            "iterations":    run.get("iterations", 0),
            "summary":       run.get("summary"),
            "error":         run.get("error"),
        })
    # Tri par date décroissante
    all_runs.sort(key=lambda r: r.get("started_at") or "", reverse=True)
    return all_runs


@app.delete("/api/history")
async def clear_history():
    """Vide l'historique des runs en mémoire (ne supprime pas les fichiers outputs/)."""
    count = len(runs)
    runs.clear()
    _clear_runs_db()
    return {"deleted": count, "message": "Historique vidé."}


@app.get("/api/health")
async def health():
    """Endpoint de santé pour vérifier que l'API tourne."""
    return {
        "status":    "ok",
        "runs_total":   len(runs),
        "runs_active":  sum(1 for r in runs.values() if r["status"] == "running"),
        "runs_done":    sum(1 for r in runs.values() if r["status"] == "done"),
        "runs_error":   sum(1 for r in runs.values() if r["status"] == "error"),
    }

