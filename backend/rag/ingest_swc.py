"""
ingest_swc.py
-------------
Index the SWC Registry markdown files into a dedicated ChromaDB collection.

The resulting collection is used by the test designer as the security
knowledge base:

    swc_vulnerabilities
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_mistralai import MistralAIEmbeddings


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.config.settings import DATA_DIR, VECTOR_DB_DIR, require_mistral_api_key


COLLECTION_NAME = "swc_vulnerabilities"
DEFAULT_SWC_DIR = DATA_DIR / "swc" / "raw" / "SWC-registry" / "entries" / "docs"


def _extract_title(markdown: str) -> str:
    """Extract the SWC title from the registry markdown format."""
    lines = markdown.splitlines()
    for index, line in enumerate(lines):
        if line.strip().lower() == "# title":
            for next_line in lines[index + 1 :]:
                title = next_line.strip()
                if title:
                    return title.lstrip("#").strip()

    for line in lines:
        match = re.match(r"^#\s+(.+)$", line.strip())
        if match and "please note" not in match.group(1).lower():
            return match.group(1).strip()

    return "Unknown SWC title"


def load_swc_documents(swc_dir: Path) -> list[Document]:
    """Load SWC markdown files and attach stable metadata."""
    if not swc_dir.exists():
        raise FileNotFoundError(f"SWC directory not found: {swc_dir}")

    documents: list[Document] = []
    for path in sorted(swc_dir.glob("SWC-*.md")):
        text = path.read_text(encoding="utf-8", errors="ignore")
        swc_id = path.stem.upper()
        title = _extract_title(text)
        documents.append(
            Document(
                page_content=text,
                metadata={
                    "source": "swc_registry",
                    "filename": path.name,
                    "swc_id": swc_id,
                    "title": title,
                },
            )
        )

    if not documents:
        raise RuntimeError(f"No SWC markdown files found in: {swc_dir}")

    return documents


def _split_text(text: str, chunk_size: int = 1200, chunk_overlap: int = 150) -> list[str]:
    """Split text into overlapping chunks without requiring extra dependencies."""
    if len(text) <= chunk_size:
        return [text]

    chunks: list[str] = []
    start = 0
    separators = ["\n## ", "\n# ", "\n### ", "\n\n", "\n", "```", " "]

    while start < len(text):
        max_end = min(start + chunk_size, len(text))
        end = max_end

        if max_end < len(text):
            window = text[start:max_end]
            split_at = -1
            for separator in separators:
                candidate = window.rfind(separator)
                if candidate > chunk_size // 2:
                    split_at = candidate + len(separator)
                    break
            if split_at > 0:
                end = start + split_at

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break
        start = max(0, end - chunk_overlap)

    return chunks


def split_documents(documents: list[Document]) -> list[Document]:
    """Split SWC documents into chunks suitable for retrieval."""
    chunks: list[Document] = []
    for doc in documents:
        for index, chunk in enumerate(_split_text(doc.page_content)):
            metadata = dict(doc.metadata)
            metadata["chunk_index"] = index
            chunks.append(Document(page_content=chunk, metadata=metadata))
    return chunks


def reset_collection_if_requested(collection_name: str, reset: bool) -> None:
    """Delete the target collection before indexing when --reset is used."""
    if not reset:
        return

    try:
        import chromadb

        client = chromadb.PersistentClient(path=str(VECTOR_DB_DIR))
        try:
            client.delete_collection(collection_name)
            print(f"[SWC Ingest] Deleted existing collection: {collection_name}")
        except Exception:
            print(f"[SWC Ingest] Collection did not exist yet: {collection_name}")
    except Exception as exc:
        print(f"[SWC Ingest] Could not reset collection; continuing: {exc}")


def index_swc_documents(swc_dir: Path, reset: bool = False) -> None:
    """Index SWC markdown documents into ChromaDB."""
    api_key = require_mistral_api_key()
    VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[SWC Ingest] Source directory: {swc_dir}")
    docs = load_swc_documents(swc_dir)
    chunks = split_documents(docs)
    print(f"[SWC Ingest] Loaded {len(docs)} SWC files.")
    print(f"[SWC Ingest] Created {len(chunks)} chunks.")

    reset_collection_if_requested(COLLECTION_NAME, reset=reset)

    embeddings = MistralAIEmbeddings(mistral_api_key=api_key)
    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(VECTOR_DB_DIR),
        collection_name=COLLECTION_NAME,
    )

    print(f"[SWC Ingest] Indexed collection: {COLLECTION_NAME}")
    print(f"[SWC Ingest] Persisted in: {VECTOR_DB_DIR}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Index SWC Registry markdown files into ChromaDB.")
    parser.add_argument(
        "--swc-dir",
        type=Path,
        default=DEFAULT_SWC_DIR,
        help="Directory containing SWC-*.md files.",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete the existing swc_vulnerabilities collection before indexing.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    index_swc_documents(args.swc_dir, reset=args.reset)
