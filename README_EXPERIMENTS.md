# MA-RAGTest Experiments

This repository is an experimental fork of the original MA-RAGTest student implementation.

The original repository is kept as `student-origin` and should remain untouched. This fork is
intended to host the reproducibility code for the journal experiments, including:

- experiment runners;
- configuration-specific prompts and pipeline variants;
- Solidity benchmark contracts;
- scripts for collecting generated-test metrics, pass rates, coverage, and runtime.

Generated artifacts such as `outputs/`, `coverage/`, `artifacts/`, temporary Hardhat tests, and
local API keys are intentionally excluded from Git.

Current stabilized branch:

- `experiment/config-1-stable`: configuration 1 stabilization and 14-contract pilot execution.
