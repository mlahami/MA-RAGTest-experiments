"""
naive_rag.py
------------
Naive retrieval strategy for configuration 2.

This module intentionally avoids the advanced RAG steps used in configuration 1:
- no HyDE document generation;
- no multi-query expansion;
- no LLM-based re-ranking;
- no LLM-based contextual compression.

It performs one direct similarity search against the requested Chroma collection
and falls back to local contract specification files when the vector database is
not available.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from backend.config.settings import BASE_DIR, VECTOR_DB_DIR, MISTRAL_API_KEY


_ERC_PATTERNS: dict[str, list[str]] = {
    "ERC20": [
        r"\bfunction\s+transfer\s*\(",
        r"\bcontract\s+\w+[^{]*\b(?:ERC20|IERC20)\b",
        r"\b(?:ERC20|IERC20)\b",
    ],
    "ERC721": [
        r"\bfunction\s+ownerOf\s*\(",
        r"\bcontract\s+\w+[^{]*\b(?:ERC721|IERC721)\b",
        r"\b(?:ERC721|IERC721)\b",
    ],
    "ERC1155": [
        r"\bfunction\s+balanceOfBatch\s*\(",
        r"\bcontract\s+\w+[^{]*\b(?:ERC1155|IERC1155)\b",
        r"\b(?:ERC1155|IERC1155)\b",
    ],
    "ERC777": [
        r"\bfunction\s+send\s*\(",
        r"\bcontract\s+\w+[^{]*\b(?:ERC777|IERC777)\b",
        r"\b(?:ERC777|IERC777)\b",
    ],
    "ERC4626": [
        r"\bfunction\s+deposit\s*\(",
        r"\bcontract\s+\w+[^{]*\b(?:ERC4626|IERC4626)\b",
        r"\b(?:ERC4626|IERC4626)\b",
    ],
    "ERC6909": [
        r"\bfunction\s+transfer\s*\([^)]*uint256\s+id",
        r"\b(?:ERC6909|IERC6909)\b",
    ],
}


def _strip_comments(contract_code: str) -> str:
    code = re.sub(r"/\*.*?\*/", "", contract_code or "", flags=re.DOTALL)
    return re.sub(r"//.*$", "", code, flags=re.MULTILINE)


def _detect_erc_standards(contract_code: str) -> list[str]:
    """Detect likely ERC standards using simple regex patterns."""
    code = _strip_comments(contract_code)
    detected: list[str] = []
    for standard, patterns in _ERC_PATTERNS.items():
        if any(re.search(pattern, code, re.IGNORECASE) for pattern in patterns):
            detected.append(standard)

    label = ", ".join(detected) if detected else "none; generic Solidity contract"
    print(f"[Naive RAG] Detected ERC standards: {label}")
    return detected


class NaiveRAG:
    """Naive single-query retrieval used by configuration 2."""

    def __init__(self, collection_name: str = "erc_standards") -> None:
        self.collection_name = collection_name

    def _retrieve_from_vector_db(self, query: str, k: int = 5) -> list[str]:
        """Run a direct Chroma similarity search; return [] if unavailable."""
        try:
            if not MISTRAL_API_KEY or not VECTOR_DB_DIR.exists():
                return []

            from langchain_chroma import Chroma
            from langchain_mistralai import MistralAIEmbeddings

            embeddings = MistralAIEmbeddings(mistral_api_key=MISTRAL_API_KEY)
            vector_db = Chroma(
                persist_directory=str(VECTOR_DB_DIR),
                embedding_function=embeddings,
                collection_name=self.collection_name,
            )
            docs = vector_db.similarity_search(query, k=k)
            return [doc.page_content for doc in docs if getattr(doc, "page_content", "")]
        except Exception as exc:
            print(f"[Naive RAG] Vector DB unavailable; using local fallback when possible: {exc}")
            return []

    def _retrieve_from_local_specs(self, detected_ercs: list[str], k: int = 5) -> list[str]:
        """Fallback: read the most relevant local contract .specs.md files."""
        specs = sorted(Path(BASE_DIR / "contracts").rglob("*.specs.md"))
        if not specs:
            return []

        targets = [erc.lower() for erc in detected_ercs]
        selected: list[Path] = []

        if targets:
            for path in specs:
                name = path.name.lower()
                if any(target in name for target in targets):
                    selected.append(path)

        if not selected:
            selected = specs[:k]

        contexts: list[str] = []
        for path in selected[:k]:
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
                contexts.append(f"--- SOURCE: {path.name} ---\n{text[:2500]}")
            except OSError:
                continue
        return contexts

    def retrieve(self, contract_code: str) -> dict[str, Any]:
        detected_ercs = _detect_erc_standards(contract_code)

        query = " ".join(detected_ercs) if detected_ercs else (contract_code or "")[:1200]
        snippets = self._retrieve_from_vector_db(query=query, k=5)
        if not snippets:
            snippets = self._retrieve_from_local_specs(detected_ercs=detected_ercs, k=5)

        context = (
            "\n\n".join(snippets)
            if snippets
            else "No relevant standard context was found in the knowledge base."
        )

        print(f"[Naive RAG] Retrieved {len(snippets)} document(s) from collection '{self.collection_name}'.")
        return {
            "context": context,
            "detected_ercs": detected_ercs,
            "metadata": {
                "retrieval_strategy": "naive_single_query",
                "collection_name": self.collection_name,
                "docs_retrieved": len(snippets),
            },
        }
