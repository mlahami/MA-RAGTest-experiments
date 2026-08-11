"""
advanced_rag.py
---------------
Advanced RAG pipeline combining:
- ERC standard detection with regular expressions
- HyDE query transformation
- Multi-query retrieval
- Hybrid search over ChromaDB
- LLM-based re-ranking
- Contextual compression
"""

import json
import re
from typing import Any

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage
from langchain_mistralai import ChatMistralAI, MistralAIEmbeddings

from backend.config.settings import VECTOR_DB_DIR, require_mistral_api_key


def _strip_markdown_fences(text: str) -> str:
    """Remove ```json / ``` fences that the LLM may add."""
    cleaned = text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return cleaned.strip()


# Detection rule: the contract IMPLEMENTS the standard, not merely consumes it.
# We look for inheritance/declaration such as "contract X is ERC20/IERC20".
# This avoids false positives from interface declarations or calls like
# IERC20(token).transfer(...), which indicate a consumer contract.
_ERC_PATTERNS: dict[str, list[str]] = {
    "ERC20": [
        r"is\s+(?:[\w,\s]*\s)?(?:ERC20|IERC20)\b",
        r"contract\s+\w+[^{]*\bERC20\b",
    ],
    "ERC721": [
        r"is\s+(?:[\w,\s]*\s)?(?:ERC721|IERC721)\b",
        r"contract\s+\w+[^{]*\bERC721\b",
    ],
    "ERC1155": [
        r"is\s+(?:[\w,\s]*\s)?(?:ERC1155|IERC1155)\b",
        r"contract\s+\w+[^{]*\bERC1155\b",
    ],
    "ERC777": [
        r"is\s+(?:[\w,\s]*\s)?(?:ERC777|IERC777)\b",
        r"contract\s+\w+[^{]*\bERC777\b",
    ],
    "ERC4626": [
        r"is\s+(?:[\w,\s]*\s)?(?:ERC4626|IERC4626)\b",
        r"contract\s+\w+[^{]*\bERC4626\b",
    ],
}


class AdvancedRAG:
    """Retrieve ERC/security context before test generation."""

    def __init__(
        self,
        collection_name: str = "erc_standards",
        *,
        compress_context: bool = True,
    ) -> None:
        self._collection_name = collection_name
        self._compress_context_enabled = compress_context
        api_key = require_mistral_api_key()
        self._embeddings = MistralAIEmbeddings(mistral_api_key=api_key)
        self._vector_db = Chroma(
            persist_directory=str(VECTOR_DB_DIR),
            embedding_function=self._embeddings,
            collection_name=collection_name,
        )
        self._llm = ChatMistralAI(
            model="mistral-large-latest",
            temperature=0,
            mistral_api_key=api_key,
        )

    def _detect_erc_standards(self, contract_code: str) -> list[str]:
        """Detect ERC standards implemented by the contract."""
        detected: list[str] = []
        for standard, patterns in _ERC_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, contract_code, re.IGNORECASE):
                    detected.append(standard)
                    break

        label = ", ".join(detected) if detected else "none; generic Solidity contract"
        print(f"[RAG] Detected ERC standards: {label}")
        return detected

    def _generate_hypothetical_document(
        self, contract_code: str, detected_ercs: list[str]
    ) -> str:
        """
        Generate a hypothetical technical specification to improve semantic
        retrieval against the vector database.
        """
        standards_label = ", ".join(detected_ercs) if detected_ercs else "generic Solidity contract"

        prompt = (
            f"Detected standards: {standards_label}\n\n"
            f"Contract code excerpt:\n{contract_code[:2000]}\n\n"
            "Generate a hypothetical technical specification in English (200-300 words) covering:\n"
            "1. Required functions and expected behavior\n"
            "2. Required events\n"
            "3. Revert conditions\n\n"
            "Return only the specification text."
        )

        response = self._llm.invoke([HumanMessage(content=prompt)])
        print("[HyDE] Hypothetical document generated.")
        return response.content

    def _generate_sub_queries(
        self, contract_code: str, detected_ercs: list[str]
    ) -> list[str]:
        """Generate targeted retrieval queries to improve recall."""
        queries: list[str] = [contract_code[:1500]]

        for erc in detected_ercs:
            queries.append(f"{erc} standard specification required functions")
            queries.append(f"{erc} required events and emit conditions")
            queries.append(f"{erc} security requirements and revert conditions")

        function_names = re.findall(r"function\s+(\w+)\s*\(", contract_code)
        for func in function_names[:5]:
            queries.append(f"Solidity {func} function security best practices")

        print(f"[Multi-Query] Generated {len(queries)} sub-queries.")
        return queries

    def _hybrid_search(
        self, queries: list[str], k_per_query: int = 3
    ) -> list[Document]:
        """Run similarity search for each query and deduplicate results."""
        results: list[Document] = []
        seen_hashes: set[int] = set()

        for query in queries:
            try:
                docs = self._vector_db.similarity_search(query, k=k_per_query)
                for doc in docs:
                    content_hash = hash(doc.page_content[:200])
                    if content_hash not in seen_hashes:
                        seen_hashes.add(content_hash)
                        results.append(doc)
            except Exception as exc:
                print(f"[Hybrid Search] Query skipped: {exc}")

        print(f"[Hybrid Search] Retrieved {len(results)} unique documents.")
        return results

    def _rerank_documents(
        self,
        documents: list[Document],
        detected_ercs: list[str],
        top_k: int = 5,
    ) -> list[Document]:
        """Rank documents by relevance using an LLM scoring prompt."""
        if len(documents) <= top_k:
            return documents

        candidates = documents[:15]
        summaries = "\n".join(
            f"[DOC {i}] Source: {doc.metadata.get('filename', 'unknown')}\n"
            f"Content: {doc.page_content[:300].replace(chr(10), ' ')}..."
            for i, doc in enumerate(candidates)
        )

        standards_label = ", ".join(detected_ercs) if detected_ercs else "generic Solidity contract"
        rerank_prompt = (
            f"The contract implements: {standards_label}\n\n"
            "Scoring criteria (0-10):\n"
            "  10 - Directly specifies required behavior for the standard\n"
            "   8 - Contains relevant security or test conditions\n"
            "   6 - Contains useful testing best practices\n"
            "   4 - Indirectly related\n"
            "   0 - Not relevant\n\n"
            f"Documents:\n{summaries}\n\n"
            'Return JSON only: {"scores": [<score_0>, <score_1>, ...]}'
        )

        try:
            response = self._llm.invoke([HumanMessage(content=rerank_prompt)])
            cleaned = _strip_markdown_fences(response.content)
            scores: list[float] = json.loads(cleaned).get("scores", [])

            padded_scores = scores + [0.0] * (len(candidates) - len(scores))
            ranked = sorted(zip(candidates, padded_scores), key=lambda item: item[1], reverse=True)

            print(f"[Re-ranking] Selected top {top_k} documents.")
            return [doc for doc, _ in ranked[:top_k]]

        except Exception as exc:
            print(f"[Re-ranking] Failed; preserving original order: {exc}")
            return candidates[:top_k]

    def _compress_context(
        self, documents: list[Document], detected_ercs: list[str]
    ) -> str:
        """Extract only the information useful for test generation."""
        if not documents:
            return "No relevant standard context was found in the knowledge base."

        raw_context = "\n\n".join(
            f"--- SOURCE ---\n{doc.page_content}" for doc in documents
        )
        standards_label = ", ".join(detected_ercs) if detected_ercs else "generic Solidity contract"

        prompt = (
            f"Detected standards: {standards_label}\n\n"
            f"Raw context:\n{raw_context[:6000]}\n\n"
            "Extract and organize ONLY the information useful for smart-contract test generation:\n"
            "1. REQUIRED FUNCTIONS\n"
            "2. REQUIRED EVENTS\n"
            "3. REVERT CONDITIONS\n"
            "4. SECURITY REQUIREMENTS\n\n"
            "Return the compressed context in English."
        )

        try:
            response = self._llm.invoke([HumanMessage(content=prompt)])
            print("[Compression] Context compressed.")
            return response.content
        except Exception as exc:
            print(f"[Compression] Failed: {exc}")
            return raw_context[:4000]

    def _format_raw_context(self, documents: list[Document]) -> str:
        """Return top-ranked documents without LLM contextual compression."""
        if not documents:
            return "No relevant standard context was found in the knowledge base."

        raw_context = "\n\n".join(
            f"--- SOURCE: {doc.metadata.get('filename', 'unknown')} ---\n{doc.page_content}"
            for doc in documents
        )
        print("[Compression] Skipped; using raw top-ranked context.")
        return raw_context[:6000]

    def retrieve(self, contract_code: str) -> dict[str, Any]:
        """
        Execute the full RAG pipeline and return:
        - context: compressed context ready for prompt injection
        - detected_ercs: detected ERC standards
        - metadata: retrieval statistics
        """
        print("\n" + "=" * 60)
        print(f"[ADVANCED RAG] Starting pipeline (collection: {self._collection_name})")
        print("=" * 60)

        detected_ercs = self._detect_erc_standards(contract_code)
        hyde_doc = self._generate_hypothetical_document(contract_code, detected_ercs)
        queries = self._generate_sub_queries(contract_code, detected_ercs) + [hyde_doc]
        raw_docs = self._hybrid_search(queries, k_per_query=3)
        ranked_docs = self._rerank_documents(raw_docs, detected_ercs, top_k=5)
        context = (
            self._compress_context(ranked_docs, detected_ercs)
            if self._compress_context_enabled
            else self._format_raw_context(ranked_docs)
        )

        print(f"[ADVANCED RAG] Pipeline complete (collection: {self._collection_name})")
        print("=" * 60 + "\n")

        return {
            "context": context,
            "detected_ercs": detected_ercs,
            "metadata": {
                "total_docs_retrieved": len(raw_docs),
                "docs_after_rerank": len(ranked_docs),
                "compression_enabled": self._compress_context_enabled,
            },
        }
