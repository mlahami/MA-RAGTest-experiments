# RAG configuration details for Config 1 and Config 2

This note documents the retrieval configuration currently used in the stabilized MA-RAGTest experimental setup.

## Knowledge-base sources

The local knowledge base is stored under:

`data/`

The current implementation uses three Chroma collection names:

| Collection | Intended role | Current source |
| --- | --- | --- |
| `erc_standards` | ERC/EIP standard knowledge for test design | Markdown files from `data/ERCs/` |
| `langchain` | Solidity contracts and JavaScript/Hardhat test examples for generation | Text files from `data/data_rag/contracts/` and `data/data_rag/tests/` |
| `swc_vulnerabilities` | Security vulnerability knowledge for test design | Markdown files from `data/swc/raw/SWC-registry/entries/docs/SWC-*.md` |

Observed local source counts:

| Source folder | Number of files |
| --- | ---: |
| `data/ERCs/*.md` | 574 |
| `data/data_rag/contracts/*` | 446 |
| `data/data_rag/tests/*` | 194 |

Observed Chroma embedding counts:

| Chroma collection | Indexed chunks |
| --- | ---: |
| `erc_standards` | 7,587 |
| `langchain` | 2,766 |
| `swc_vulnerabilities` | 267 |

The SWC collection is built by:

`backend/rag/ingest_swc.py`

The source is the SWC Registry markdown corpus. The registry itself states that it is no longer actively maintained and may be incomplete. For the experiments, it is used as a structured and reproducible vulnerability taxonomy, not as an up-to-date exhaustive security standard.

## Embedding model

Both Config 1 and Config 2 use:

`langchain_mistralai.MistralAIEmbeddings`

No explicit embedding model name is set in the code. Therefore, the implementation uses the default embedding model configured by LangChain's `MistralAIEmbeddings` class, commonly Mistral's embedding endpoint/default model.

For the paper, it is safer to write:

> We used `MistralAIEmbeddings` through LangChain with its default Mistral embedding configuration.

If an exact embedding model name is required for publication, the code should be modified to set it explicitly.

## Vector database

Both configurations use ChromaDB:

`langchain_chroma.Chroma`

The persisted vector database is stored in:

`data/vector_db/`

## Chunking strategy

### ERC standards collection: `erc_standards`

The ERC/EIP markdown documents are indexed by:

`backend/rag/ingest_erc.py`

Chunking method:

`MarkdownHeaderTextSplitter`

Headers used:

- `#`
- `##`
- `###`

This means ERC documents are split according to their Markdown structure rather than fixed-size character windows.

Metadata added to each chunk:

- `erc_number`;
- `source = ethereum_ercs`;
- `filename`;
- Markdown header metadata such as `Header 1`, `Header 2`, `Header 3` when available.

### Generator collection: `langchain`

The contract/test-example corpus is indexed by:

`backend/rag/ingest.py`

Chunking method:

`RecursiveCharacterTextSplitter`

Parameters:

- `chunk_size = 1500`
- `chunk_overlap = 200`
- separators:
  - `contract `
  - `describe(`
  - `function `
  - `interface `
  - blank line
  - newline

This chunking is adapted to Solidity contracts and JavaScript/Hardhat tests because it tries to split at contract, test-suite, function, interface, and paragraph boundaries.

### SWC vulnerability collection: `swc_vulnerabilities`

The SWC vulnerability corpus is indexed by:

`backend/rag/ingest_swc.py`

Source files:

`data/swc/raw/SWC-registry/entries/docs/SWC-*.md`

Chunking method:

custom deterministic Markdown-aware splitter.

Parameters:

- `chunk_size = 1200`
- `chunk_overlap = 150`
- preferred split boundaries:
  - `##`
  - `#`
  - `###`
  - blank line
  - newline
  - code fence
  - whitespace

Metadata added to each chunk:

- `source = swc_registry`;
- `filename`;
- `swc_id`;
- `title`;
- `chunk_index`.

## Config 1: Advanced RAG

Implementation:

`backend/rag/advanced_rag.py`

Config 1 uses an advanced retrieval pipeline.

### Pre-retrieval

Before querying ChromaDB, Config 1 performs:

1. ERC detection using regular expressions over the Solidity contract.
2. HyDE-style hypothetical document generation using the LLM.
3. Multi-query expansion.

The generated queries include:

- a contract-code excerpt;
- ERC-specific queries such as required functions, required events, security requirements, and revert conditions;
- function-specific security-best-practice queries for up to five detected Solidity functions;
- the LLM-generated hypothetical specification.

### Retrieval settings

Retrieval method:

`Chroma.similarity_search`

Retrieval is performed for each generated query.

Parameter:

- `k_per_query = 3`

The raw retrieved documents from all queries are deduplicated using a hash of the beginning of the document content.

Because multiple queries are used, the total number of raw retrieved documents may be greater than 3. The final number depends on the number of generated sub-queries and deduplication.

### Top-k after reranking

After retrieval and deduplication, Config 1 keeps:

- `top_k = 5`

### Reranking method

Config 1 uses LLM-based reranking.

The reranker sends up to the first 15 candidate documents to the LLM and asks it to score each document from 0 to 10 according to relevance:

- direct standard behavior;
- security or test conditions;
- testing best practices;
- indirect relevance;
- no relevance.

The system then sorts candidates by LLM score and keeps the top 5 documents.

If reranking fails, the implementation falls back to the original candidate order and keeps the first 5 candidates.

### Filtering strategy

Config 1 applies several forms of filtering:

1. Structural ERC detection before retrieval.

   The system attempts to detect whether the contract implements ERC20, ERC721, ERC1155, ERC777, or ERC4626.

2. Query-based narrowing.

   Retrieval queries are adapted to the detected ERC standard and function names.

3. Deduplication.

   Retrieved documents are deduplicated using a hash of the first 200 characters of each document.

4. LLM-based relevance filtering through reranking.

   Low-relevance documents are indirectly filtered out because only the top 5 ranked documents are retained.

There is currently no explicit Chroma metadata filter such as `where={...}` in the retrieval call.

### Post-retrieval processing

Config 1 performs LLM-based contextual compression after reranking.

The selected documents are passed to the LLM, which extracts and organizes only information useful for test generation:

1. required functions;
2. required events;
3. revert conditions;
4. security requirements.

The compressed context is then injected into the downstream test-design or test-generation prompts.

## Config 2: Naive RAG

Implementation:

`backend/rag/naive_rag.py`

Config 2 is designed as a simpler baseline.

### Pre-retrieval

Config 2 only performs simple ERC detection using regular expressions.

It does not perform:

- HyDE;
- LLM-based hypothetical document generation;
- multi-query expansion;
- query decomposition.

### Retrieval settings

Retrieval method:

`Chroma.similarity_search`

Parameter:

- `k = 5`

The query is:

- the detected ERC label(s), if any ERC is detected;
- otherwise, the first 1,200 characters of the Solidity contract code.

### Reranking method

Config 2 does not use reranking.

The documents returned by Chroma similarity search are used in their original retrieval order.

### Filtering strategy

Config 2 uses minimal filtering:

1. Simple ERC regex detection.
2. Direct top-5 similarity search.
3. Empty-content documents are discarded.

There is no:

- LLM-based reranking;
- metadata filtering;
- contextual compression;
- multi-query deduplication.

### Post-retrieval processing

Config 2 does not perform LLM-based post-retrieval processing.

It simply concatenates the retrieved snippets and passes the raw retrieved context to the downstream agent.

If ChromaDB is unavailable or no documents are retrieved, Config 2 falls back to local `contracts/*.specs.md` files and selects up to 5 files, prioritizing files whose names match the detected ERC standards when possible.

## Summary comparison

| Aspect | Config 1: Advanced RAG | Config 2: Naive RAG |
| --- | --- | --- |
| Vector DB | ChromaDB | ChromaDB |
| Embeddings | MistralAIEmbeddings | MistralAIEmbeddings |
| KB collections | `erc_standards`, `swc_vulnerabilities`, `langchain` | same collections |
| ERC detection | yes, structural regex | yes, simple regex |
| HyDE | yes | no |
| Multi-query retrieval | yes | no |
| Retrieval method | Chroma similarity search | Chroma similarity search |
| Retrieval k | `k_per_query = 3` | `k = 5` |
| Final top-k | 5 after reranking | 5 direct results |
| Deduplication | yes | no |
| Reranking | LLM-based scoring | no |
| Post-retrieval compression | LLM-based contextual compression | no |
| Metadata filter | no explicit Chroma metadata filter | no explicit Chroma metadata filter |
| Context injected downstream | compressed/organized context | raw concatenated snippets |

## Suggested paper wording

> Both configurations use the same ChromaDB-backed knowledge base and the same Mistral embedding interface through LangChain. The difference lies in the retrieval pipeline. Config 1 applies an advanced RAG strategy with ERC detection, HyDE-style query enrichment, multi-query retrieval, deduplication, LLM-based reranking, and LLM-based contextual compression. Config 2 uses a naive single-query retrieval baseline, where the detected ERC label or a contract-code excerpt is used directly for top-5 Chroma similarity search, without reranking or post-retrieval compression. This design allows us to isolate the impact of advanced retrieval mechanisms while keeping the remaining multi-agent testing pipeline constant.
