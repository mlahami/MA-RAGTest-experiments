import json
import os
import re
import shutil
import subprocess

from backend.config.settings import BASE_DIR, CONTRACTS_DIR, OUTPUT_DIR


def _extract_main_contract_name(contract_code: str) -> str:
    """
    Extrait le nom du contrat principal depuis le code Solidity.

    Stratégie :
      1. Ignore les interfaces (interface Xxx) et les contrats abstraits (abstract contract Xxx).
      2. Parmi les contrats concrets restants, prend le DERNIER — il s'agit généralement
         du contrat principal qui hérite/compose les autres.
      3. Fallback sur le premier match brut si aucun contrat concret n'est trouvé.
    """
    if not contract_code:
        return "GeneratedContract"

    # Retire les commentaires pour éviter les faux positifs
    code = re.sub(r"/\*.*?\*/", "", contract_code, flags=re.DOTALL)
    code = re.sub(r"//.*$", "", code, flags=re.MULTILINE)

    # Contrats concrets uniquement (ni interface, ni abstract)
    concrete = re.findall(
        r"(?<!abstract\s)(?<!interface\s)\bcontract\s+(\w+)",
        code,
    )
    # Filtre plus explicite : exclure les lignes précédées de abstract ou interface
    concrete_filtered = []
    for m in re.finditer(r"\b(abstract\s+contract|interface|contract)\s+(\w+)", code):
        keyword = m.group(1).strip()
        name    = m.group(2)
        if keyword == "contract":          # contrat concret
            concrete_filtered.append(name)

    if concrete_filtered:
        return concrete_filtered[-1]       # dernier contrat concret = contrat principal

    # Fallback : premier match brut
    fallback = re.search(r"\bcontract\s+(\w+)", code)
    return fallback.group(1) if fallback else "GeneratedContract"


def _ensure_contract_file(contract_code: str, source_filename: str | None = None) -> str:
    """
    Écrit le contrat dans CONTRACTS_DIR et retourne son chemin absolu.

    Si ``source_filename`` est fourni (ex: "SimpleSwap.sol"), il est utilisé
    directement comme nom de fichier — ce qui garantit la cohérence entre le
    fichier écrit et le nom attendu par Hardhat.
    Sinon, le nom est extrait du code Solidity via _extract_main_contract_name.
    """
    CONTRACTS_DIR.mkdir(parents=True, exist_ok=True)

    if source_filename:
        # Utilise le nom du fichier source original (sans chemin)
        contract_name = re.sub(r"\.sol$", "", source_filename, flags=re.IGNORECASE)
    else:
        contract_name = _extract_main_contract_name(contract_code)

    contract_path = CONTRACTS_DIR / f"{contract_name}.sol"
    contract_path.write_text(contract_code or "", encoding="utf-8")
    return str(contract_path)


def _read_relative_imports(sol_file_path: str) -> list[str]:
    """Extrait les chemins d'import relatifs d'un fichier Solidity."""
    with open(sol_file_path, "r", encoding="utf-8") as f:
        content = f.read()
    imports = re.findall(r'import\s+\{[^}]+\}\s+from\s+"([^"]+)";', content)
    return [p for p in imports if p.startswith(".")]


def _copy_contract_tree(contract_path: str, contracts_root: str, dest_dir: str) -> None:
    """Copie le contrat et ses imports relatifs en préservant l'arborescence."""
    visited: set[str] = set()

    def _copy(src: str) -> None:
        src = os.path.normpath(src)
        if src in visited:
            return
        visited.add(src)

        rel  = os.path.relpath(src, contracts_root)
        dest = os.path.join(dest_dir, rel)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copyfile(src, dest)

        for imp in _read_relative_imports(src):
            child = os.path.normpath(os.path.join(os.path.dirname(src), imp))
            if os.path.exists(child) and child.endswith(".sol"):
                _copy(child)

    _copy(contract_path)


def _prepare_single_contract_sources(contract_path: str) -> str:
    """
    Crée .coverage_contracts/ avec uniquement le contrat ciblé et ses imports.
    Cela évite que hardhat coverage compile TOUS les contrats du projet.
    """
    temp_dir = str(BASE_DIR / ".coverage_contracts")
    if os.path.isdir(temp_dir):
        shutil.rmtree(temp_dir, ignore_errors=True)
    os.makedirs(temp_dir)

    contracts_root = str(CONTRACTS_DIR.resolve())
    abs_path       = os.path.abspath(contract_path)

    if abs_path.startswith(contracts_root + os.sep):
        _copy_contract_tree(abs_path, contracts_root, temp_dir)
    else:
        shutil.copyfile(contract_path, os.path.join(temp_dir, os.path.basename(contract_path)))

    return temp_dir


def _clean_hardhat_build_artifacts() -> None:
    """Supprime artifacts/ et cache/ pour forcer une recompilation propre."""
    for folder in ("artifacts", "cache"):
        path = BASE_DIR / folder
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)


# ---------------------------------------------------------------------------
# Helpers : exécution
# ---------------------------------------------------------------------------

def _run_cmd(
    command: list[str],
    env_extra: dict | None = None,
    timeout_seconds: float | None = None,
) -> subprocess.CompletedProcess:
    """Lance une commande dans BASE_DIR avec fusion d'environnement optionnelle."""
    merged_env = os.environ.copy()
    if env_extra:
        merged_env.update(env_extra)

    try:
        try:
            return subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                shell=False,
                cwd=str(BASE_DIR),
                env=merged_env,
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            return subprocess.CompletedProcess(
                args=command,
                returncode=124,
                stdout=exc.stdout or "",
                stderr=(exc.stderr or "") + f"\n[Executor] Timeout apres {timeout_seconds:.0f}s",
            )
    except FileNotFoundError:
        if os.name == "nt" and command and command[0] == "npx":
            try:
                return subprocess.run(
                    ["npx.cmd", *command[1:]],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    shell=False,
                    cwd=str(BASE_DIR),
                    env=merged_env,
                    timeout=timeout_seconds,
                )
            except subprocess.TimeoutExpired as exc:
                return subprocess.CompletedProcess(
                    args=["npx.cmd", *command[1:]],
                    returncode=124,
                    stdout=exc.stdout or "",
                    stderr=(exc.stderr or "") + f"\n[Executor] Timeout apres {timeout_seconds:.0f}s",
                )
        raise


def _summarize_hardhat_error(output: str) -> str:
    """Extrait le message d'erreur Hardhat le plus pertinent depuis la sortie brute."""
    if not output:
        return "Erreur Hardhat inconnue."
    for pattern in [
        r"Error\s+HH\d+:\s+.+",
        r"HardhatError:\s+HH\d+:\s+.+",
        r"HardhatPluginError:\s+.+",
        r"TypeError:\s+.+",
    ]:
        m = re.search(pattern, output)
        if m:
            return m.group(0).strip()
    first = next((l.strip() for l in output.splitlines() if l.strip()), "")
    return first or "Erreur Hardhat inconnue."


def _coverage_artifacts_exist() -> bool:
    return (
        (BASE_DIR / "coverage" / "coverage-summary.json").exists()
        or (BASE_DIR / "coverage" / "coverage-final.json").exists()
    )


def _parse_stdout_stats(stdout: str) -> dict:
    """Fallback : extrait les stats depuis la sortie texte de Hardhat."""
    passes   = 0
    failures = 0
    m = re.search(r"(\d+)\s+passing", stdout or "")
    if m:
        passes = int(m.group(1))
    m = re.search(r"(\d+)\s+failing", stdout or "")
    if m:
        failures = int(m.group(1))
    if passes > 0 or failures > 0:
        print(f"[Executor] Fallback stdout → {passes} ✅  {failures} ❌")
        return {"stats": {"passes": passes, "failures": failures, "tests": passes + failures}}
    return {}


# ---------------------------------------------------------------------------
# Helpers : lecture des rapports
# ---------------------------------------------------------------------------

def _load_json(path) -> dict:
    try:
        p = BASE_DIR / path if isinstance(path, str) else path
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as exc:
        print(f"[Executor] Lecture {path} échouée : {exc}")
    return {}


def _coverage_from_final_json(coverage_final: dict) -> dict:
    """
    Calcule les métriques de couverture depuis coverage-final.json
    quand coverage-summary.json est absent.
    """
    total_stmts = covered_stmts = 0
    total_funcs = covered_funcs = 0
    total_branches = covered_branches = 0

    for file_data in coverage_final.values():
        if not isinstance(file_data, dict):
            continue
        stmts = file_data.get("s", {})
        total_stmts   += len(stmts)
        covered_stmts += sum(1 for h in stmts.values() if h and h > 0)

        funcs = file_data.get("f", {})
        total_funcs   += len(funcs)
        covered_funcs += sum(1 for h in funcs.values() if h and h > 0)

        for hits in file_data.get("b", {}).values():
            if isinstance(hits, list):
                total_branches   += len(hits)
                covered_branches += sum(1 for h in hits if h and h > 0)

    def pct(cov, tot):
        return round((cov / tot) * 100, 2) if tot else 0

    # Utilise la clé "statements" pour rester cohérent avec le résumé d'exécution.
    return {
        "statements": pct(covered_stmts,   total_stmts),
        "functions":  pct(covered_funcs,   total_funcs),
        "branches":   pct(covered_branches, total_branches),
    }


def _build_cov_summary(coverage_report: dict) -> dict:
    if "total" in coverage_report:
        t = coverage_report["total"]
        return {
            # Utilise la clé "statements" au lieu de "lines".
            "statements": t.get("statements", t.get("lines", {})).get("pct", 0),
            "functions":  t.get("functions", {}).get("pct", 0),
            "branches":   t.get("branches",  {}).get("pct", 0),
        }
    elif coverage_report:
        return _coverage_from_final_json(coverage_report)
    return {"statements": 0, "functions": 0, "branches": 0}


