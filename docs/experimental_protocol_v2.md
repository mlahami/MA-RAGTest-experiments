# Experimental protocol v2 — proposal after the ASE 2026 rejection

This note captures the revised experimental design agreed on after the ASE 2026
review (paper #1991, rejected at the Early Rejection stage, all three reviews
negative). It replaces the "naive RAG vs advanced RAG" axis (old Config 2) used
in the first submission with a "multi-agent vs single-agent" axis, which more
directly answers the reviewers' call for a component-level ablation study.

It is a planning document, written before any code change. The configuration
logic for anything beyond the current Config 1 (advanced RAG + multi-agent +
refinement loop) lives in the students' repository
(`https://github.com/TriguiMohamedYassine/MA-RAGTes`), not yet cloned locally
at the time this note was written. Once cloned, check what is already
implemented there (single-agent baseline, LLM-only baseline, loop toggle)
against the design below before writing new code.

## Why the old design changed

The first submission used 5 configurations built around two axes: retrieval
sophistication (advanced RAG / naive RAG / no RAG) and refinement (with /
without loop), all inside a fixed multi-agent architecture. Reviewer feedback
relevant to this choice:

- Reviewer A: unclear whether RAG is enabled in Config 3, unclear whether
  Config 4 is "Config 1 minus RAG" — the configs were not cleanly isolating
  one variable each.
- Reviewer B (Q1): the no-RAG configuration (Config 4) sometimes *outperforms*
  RAG-based configurations (e.g. SupplyChain: Config 4 100% pass rate vs
  Config 1 66.67%) — the benefit of RAG itself, not just retrieval
  sophistication, was not convincingly shown.
- Reviewer C: "An ablation study should be provided, isolating the
  contribution of each agent and separately assessing the advantages of the
  Refinement Loop and RAG." The novelty concern from Reviewers A and C is
  that feedback-driven iterative multi-agent pipelines are common; the paper
  did not show that agent decomposition itself buys anything over a simpler
  iterative baseline.

Dropping the naive-vs-advanced RAG comparison and adding a multi-agent-vs-
single-agent axis addresses both the "unclear isolation" complaint and the
novelty complaint more directly than the original design did.

## Design: three binary axes, five core configurations

| # | Config | Architecture | RAG | Refinement loop | Purpose |
|---|--------|-------------|-----|------------------|---------|
| 1 | **Full (MA-RAGTest)** | Multi-agent | Advanced | Yes | Complete proposed system (old Config 1) |
| 2 | Full − RAG | Multi-agent | None (LLM-only prompts) | Yes | Isolates the contribution of RAG inside the multi-agent pipeline |
| 3 | Full − Loop | Multi-agent | Advanced | No | Isolates the contribution of the refinement loop |
| 4 | RAG, single-agent | Single agent | Advanced | No | Isolates the contribution of multi-agent decomposition |
| 5 | LLM-only baseline | Single agent | None | No | Absolute floor baseline |

Numbering note (2026-09-09): configs 2 and 3 were swapped relative to the
first draft of this table so that each config's number matches the folder
that already implements it (`MA-RAGTes-exp-config2` → Config 2, Full − RAG;
`MA-RAGTes-exp-config3` → Config 3, Full − Loop), avoiding a repo rename.
`MA-RAGTes-exp-config2` no longer runs naive single-query retrieval; its
Test Designer now performs no retrieval at all (Config 2 definition above).

Design rule: each configuration removes exactly one dimension relative to the
full system (config 1), so each pairwise comparison is interpretable on its
own — this was explicitly missing in the first submission.

### Conditional Config 6 (stretch goal, only if 1–5 are fully run)

| # | Config | Architecture | RAG | Refinement loop | Purpose |
|---|--------|-------------|-----|------------------|---------|
| 6 | Single-agent + self-correction loop | Single agent | Advanced | Yes (generic retry: feed raw execution error back to the same LLM call, same iteration budget as config 1) | Tests whether specialized agent decomposition (Designer/Generator/Analyzer/Evaluator) outperforms a generic "retry until tests pass" loop, not just whether *some* loop helps |

Rationale for treating it as conditional: it is the strongest available
rebuttal to the "iterative feedback loops are not novel" criticism (Reviewer
A), but it is additional engineering (a new single-agent self-correction
mode) and additional compute on top of an already expensive matrix. Priority:
finish configs 1–5 with full repetitions on the full benchmark first; only
add config 6 if time/budget remains before the next submission deadline.

## Revised research questions

- **RQ1 (Completeness).** Coverage (statement, branch, function) across all
  configs, same benchmark and same contract set in every table/figure.
- **RQ2 (Role of retrieval).** Full vs Full−RAG (1 vs 2), and RAG-single-agent
  vs LLM-only baseline (4 vs 5). Reporting both pairs shows whether RAG's
  effect is consistent with and without multi-agent decomposition, which is a
  more robust claim than the old "advanced vs naive retrieval" comparison.
- **RQ3 (Role of multi-agent decomposition).** New RQ. Full vs
  RAG-single-agent (1 vs 4), Full−RAG vs LLM-only baseline (2 vs 5), and — if
  config 6 is run — Full vs single-agent-with-self-correction-loop (1 vs 6).
  This last comparison is the direct answer to the novelty critique.
- **RQ4 (Role of the refinement loop).** Full vs Full−Loop (1 vs 3).
- **RQ5 (Cost and efficiency).** Runtime, iterations, token usage across all
  configs actually run.

## Protocol fixes to apply regardless of which configs are run

These were raised independently by two or three reviewers and are cheap to
fix compared to rebuilding the config matrix:

1. **Repetitions and statistics.** Minimum 3 (ideally 5) repetitions per
   contract per config. Report mean ± standard deviation. Run a paired
   significance test (e.g. Wilcoxon signed-rank across contracts) between
   each ablation pair, with Holm correction for the multiple comparisons
   implied by RQ2–RQ4.
2. **Consistent benchmark across all tables.** Tables 2 and 3 in the
   rejected submission used contracts (Agreement, Splitter, SupplyChain) not
   listed in Table 1 (the benchmark table). Every table/figure in the next
   version must draw from the same declared contract set.
3. **Explicit thresholds in the text.** The Evaluator (Algorithm 2) already
   uses fixed values (90% statement coverage, or 85% statement + 80% branch
   coverage) to decide when to stop. Replace "e.g., 80%" in the methodology
   section with these exact values — no code change needed, just remove the
   hedge from the prose.
4. **Dedicated security metric.** The Analyzer (Algorithm 1) already tags
   security-oriented tests with `[SECURITY:<SWC-ID>]` and tracks their
   pass/fail status separately (`G` in the algorithm). Aggregate this per
   config into its own reported metric (e.g. SWC classes covered, security
   test pass rate) instead of only reporting generic coverage — this
   directly answers Reviewer C's point that the security claim in the title
   was not backed by a security-specific metric.
5. **Distinguish invalid failures from bug-revealing failures.** Reviewer C
   noted that a failing test is not necessarily a defect in the test suite —
   it can correctly reveal a contract bug. `run_experiment.py` already
   separates `invalid_failures_total` (syntax errors, undefined helpers,
   call errors — genuinely bad) from generic `tests_failed`. Use this
   existing split in the discussion instead of treating all failures as
   equally negative.
6. **Own prior work as an external baseline.** RAGUnitTest4SC (Sboui &
   Lahami, ENASE 2026) is architecturally close to config 4 (single-stage
   RAG, no multi-agent, no iterative loop) and is already published work from
   the same group. Re-running it under the same benchmark/metrics as a named
   "prior work" baseline answers Reviewer B's Q5 ("why no comparison with
   existing tools") at much lower cost than integrating a third-party tool
   such as AGSOLT. A third-party baseline can be mentioned as future work in
   Threats to Validity if time does not allow adding one now.

## Open items before implementation

- Clone `https://github.com/TriguiMohamedYassine/MA-RAGTes` and check what
  the students already implemented for the single-agent and LLM-only paths,
  and whether a loop toggle already exists, before writing new orchestration
  code.
- Confirm which benchmark contracts (from Table 1's set, or an updated set)
  will be used for the full 5-config (or 6-config) matrix, and freeze that
  list before any run starts, per fix #2 above.
- Decide the number of repetitions per contract per config given the
  observed per-run cost (500–900s wall time for config 1 alone in the first
  submission) and the available compute/API budget.
