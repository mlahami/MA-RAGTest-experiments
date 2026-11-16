# Technical notes on Config 1 and Config 2 orchestration

This note summarizes the technical role of the orchestrator and the LLM calls in the current MA-RAGTest experimental implementation. It can be reused later when revising the paper or preparing the experimental methodology section.

## Is there an orchestrator?

Yes. In the stabilized experimental version, the multi-agent workflow is coordinated by an orchestrator located in:

`backend/workflows/orchestrator.py`

The orchestrator is not itself a test-generation agent. Its role is to manage the execution flow between the different agents and to decide whether the workflow should stop or continue with another correction iteration.

## Role of the orchestrator

The orchestrator coordinates the complete pipeline:

```text
Test Designer
    -> Test Generator
        -> Test Executor
            -> Test Analyzer
                -> Test Evaluator
                    -> stop or correction loop
```

If the generated test suite is not satisfactory, the orchestrator starts a correction loop:

```text
Corrector Generator
    -> Test Executor
        -> Test Analyzer
            -> Test Evaluator
                -> stop or another correction iteration
```

More concretely, the orchestrator:

- initializes the shared workflow state;
- calls the agents in the correct order;
- stores intermediate results such as the test design, generated test code, execution results, analyzer report, and evaluator decision;
- manages the maximum number of correction attempts;
- decides whether the pipeline should stop or regenerate tests;
- detects stagnation when correction iterations no longer improve the result;
- keeps track of progress indicators such as passed tests and statement coverage.

Therefore, the orchestrator acts as the control layer of the multi-agent system.

## Does the orchestrator call an LLM?

No. In the current stabilized implementation, the orchestrator does not directly call an LLM.

Its role is deterministic: it manages the workflow, routes the state between agents, and decides whether to continue or stop according to the evaluator output and iteration limits.

The LLM calls happen inside specific agents and, depending on the configuration, inside the RAG component.

## Which components call the LLM?

The following components call the LLM:

1. Test Designer

   The Test Designer uses the LLM to analyze the Solidity contract and produce a structured test plan. This plan includes functional scenarios and security-oriented scenarios.

2. Test Generator

   The Test Generator uses the LLM to transform the test design into executable Hardhat/JavaScript tests.

3. Corrector Generator

   When the initial generated tests fail or need improvement, the Corrector Generator uses the LLM to revise the test suite using execution errors, analyzer feedback, and evaluator feedback.

4. Advanced RAG in Config 1

   In Config 1, the RAG component is not only a simple vector search. It uses LLM-based steps such as query enrichment, reranking, and context compression. Therefore, Config 1 may include additional LLM calls inside the retrieval process itself.

The following components do not call the LLM in the stabilized implementation:

- Orchestrator;
- Test Executor;
- Test Analyzer;
- Test Evaluator.

These components are deterministic.

## Difference between Config 1 and Config 2

The main difference between Config 1 and Config 2 is the retrieval strategy.

### Config 1: advanced RAG

Config 1 uses an advanced RAG pipeline. It includes:

- pre-retrieval processing;
- query enrichment;
- multiple query variants;
- retrieval from the vector database;
- post-retrieval processing;
- reranking;
- context compression.

This means that Config 1 tries to improve the quality and relevance of the retrieved security and smart-contract knowledge before passing it to the test-design and test-generation agents.

In the current implementation, Config 1 uses:

`backend/rag/advanced_rag.py`

### Config 2: naive RAG

Config 2 uses a simpler retrieval strategy. It performs a direct similarity search using the original query.

It does not use:

- HyDE;
- multi-query expansion;
- LLM-based reranking;
- LLM-based context compression;
- advanced post-retrieval filtering.

This makes Config 2 a useful baseline for evaluating whether the advanced retrieval mechanisms of Config 1 actually improve test quality.

In the current implementation, Config 2 uses:

`backend/rag/naive_rag.py`

## Why this distinction matters for the paper

This distinction is important experimentally because the objective is not only to evaluate whether MA-RAGTest can generate tests, but also whether advanced retrieval improves the generated tests compared with a simpler RAG baseline.

The comparison between Config 1 and Config 2 should therefore isolate the retrieval strategy as much as possible:

- same contracts;
- same experimental runner;
- same prompts, except when the retrieval context differs;
- same LLM provider and model;
- same number of repetitions;
- same evaluation metrics;
- same correction policy;
- same maximum number of correction iterations.

This helps reduce experimental bias. If Config 1 performs better than Config 2 under these controlled conditions, the improvement can be more reasonably attributed to the advanced RAG strategy rather than to unrelated implementation differences.

## Suggested wording for the paper

The following paragraph can be adapted for the methodology section:

> The MA-RAGTest workflow is coordinated by a deterministic orchestrator that manages the interaction between specialized agents. The orchestrator does not directly call the LLM; instead, it controls the execution order, maintains the shared workflow state, and decides whether to stop or trigger additional correction iterations. LLM calls are performed by the test design, test generation, and test correction agents. In Config 1, additional LLM calls may occur inside the advanced RAG module for query enrichment, reranking, and context compression. In Config 2, the RAG module is restricted to naive similarity-based retrieval, without pre-retrieval or post-retrieval LLM-based processing. This design allows us to compare the effect of advanced retrieval while keeping the remaining experimental pipeline constant.

