# Multi-Agent RAG Configurations Repository

This repository contains multiple configurations of a **Multi-Agent Test Generation pipeline combined with Retrieval-Augmented Generation (RAG)**.
Each configuration is implemented in a **separate branch** to ensure clarity, modularity, and ease of experimentation.

---

## Repository Structure

* Each branch represents a **specific configuration**
* The `main` branch contains this documentation only
* This design avoids code conflicts and keeps each configuration **independent and readable**

---

## Available Configurations

### Config 1: Full Multi-Agent + Advanced RAG

* Multi-agent pipeline (Test Designer + Test Generator)
* Advanced retrieval strategy:
  * Domain-aware filtering
  * Security pattern integration
  * Re-ranking
* Includes refinement/feedback loop

---

### Config 2: Full Multi-Agent + Naive RAG

* Same architecture as Config 1
* Uses a simpler retrieval strategy:
  * Top-k similarity search
* No advanced filtering or ranking

---

### Config 3: Multi-Agent without Refinement Loop

* Multi-agent system enabled
* Retrieval enabled (similar to Config 1/2)
* No refinement or feedback loop
* Single-pass generation

---

### Config 4: Multi-Agent without RAG

* Multi-agent pipeline enabled
* No retrieval (LLM-only)
* No refinement loop
* Baseline for comparison

---

### Config 5: Single-Agent Baseline (LLM-only)

* Single LLM agent
* No RAG
* No feedback loop
* Simplest configuration

---

## Purpose

This repository is designed for:

* Comparing different RAG strategies
* Evaluating multi-agent vs single-agent systems
* Measuring the impact of refinement loops
* Benchmarking LLM-based test generation pipelines

---

## Dataset (Important)

The dataset used for the Retrieval-Augmented Generation (RAG) pipeline is **not included** in this repository due to its size.

You must download it manually from the following link:

👉 [Google Drive Dataset Link](#)

### Instructions

1. Download the dataset from the link above
2. Extract the files (if compressed)
3. Place the `data` folder in the root directory of the project
```
project-root/
└── data/
```

> ⚠️ Without the dataset, RAG-based configurations (Config 1, 2, and 3) will not function correctly.

---

## Usage

To explore a configuration:
```bash
git checkout <branch-name>
```

Example:
```bash
git checkout config-1
```
