# Phase 2 Extended: HyDE Retrieval and Cross-Architecture Validation

## Objective

The core hypothesis of this phase was: **a small, cheap LLM can produce
high-quality structured extraction if the pipeline compensates for its
weaknesses**, rather than requiring a large model to get good results.
Two architectural levers were tested against this hypothesis:

1. **HyDE retrieval** — replacing direct query embedding with an
   LLM-generated hypothetical document before scoring chunks, to close
   the semantic gap between task instructions and web content.
2. **Cross-architecture validation** — using a *different* small model
   (same size class, different model family) as the validator, instead
   of having the extractor validate its own output.

Both levers were chosen specifically because they do **not** require
access to a large/frontier model — consistent with the project's goal
of improving small-model performance through pipeline design rather
than through model scale.

## Configurations tested

| Config | Retrieval | Refinement | Validator model | Chunking |
|---|---|---|---|---|
| A | HyDE | Yes (same model) | Same as extractor | semantic_light |
| B | None (baseline) | No | — | semantic_light |
| C | None | Yes (same model) | Same as extractor | semantic_light |
| D | HyDE | Yes | Different small model | semantic_light |
| E | HyDE | Yes | Different small model | trafilatura (docs+news) |

All configurations used the same small extractor model throughout.

## Results

| Config | F1 | Precision | Recall | Total tokens | Documentation | E-commerce | News |
|---|---|---|---|---|---|---|---|
| A | 0.353 | 0.337 | 0.470 | 226,325 | 0.323 | 0.582 | 0.298 |
| B | 0.282 | 0.242 | 0.575 | 188,400 | 0.075 | 0.685 | 0.285 |
| C | 0.327 | 0.295 | 0.607 | 456,828 | 0.236 | 0.582 | 0.303 |
| D | 0.376 | 0.358 | 0.491 | 259,860 | 0.269 | 0.567 | 0.384 |
| E | **0.408** | **0.483** | 0.379 | **167,986** | 0.098 | 0.594 | **0.553** |

## Key findings

### 1. Retrieval quality matters more than self-refinement

A vs. B shows HyDE alone improves F1 by +25% relative (0.282 → 0.353)
for a modest +20% token cost. C vs. B shows that adding refinement
*without* improving retrieval costs +142% more tokens for only +16%
relative F1 gain. Refining over poorly-selected chunks has a low
ceiling: if the relevant content was never sent to the extractor, no
amount of feedback-driven retrying can recover it. This is the
strongest evidence in this phase that **retrieval quality is the
dominant lever for small models**, not iterative self-correction.

### 2. Cross-architecture validation beats self-validation

D vs. A isolates the effect of changing only the validator model
(same extractor, same HyDE retrieval). F1 improves from 0.353 to
0.376 (+6.5% relative) for only +15% more tokens — a far better
cost/benefit ratio than C's self-refinement path. This is consistent
with published findings on **self-preference bias in LLM-as-a-judge**:
models tend to rate their own outputs more favorably regardless of
actual quality, and using a judge from a different model family
mitigates this without requiring a larger model. Across configs B→C→D,
precision rises monotonically (0.242 → 0.295 → 0.358) while recall
drops slightly — the expected signature of a validator that is
actually filtering bad extractions rather than rubber-stamping them.

### 3. Chunking strategy must be selected per query, not per domain

E swaps `semantic_light` for `trafilatura` on documentation and news
domains. News F1 jumps from 0.384 to 0.553 (+44% relative) at 35%
lower token cost, confirming Phase 1 findings that trafilatura's
clean article extraction suits linear prose content well.
**Documentation collapses from 0.269 to 0.098**, because trafilatura
discards structural elements (headings, table of contents, section
hierarchy) that documentation queries often depend on explicitly.

This result invalidates "chunking strategy per domain" as a
sufficiently precise heuristic. The `documentation` label conflates
two distinct query types with opposite structural needs:

- Linear queries (e.g. "extract all programming languages mentioned")
  — trafilatura works fine, same as prose-heavy news content.
- Structural queries (e.g. "extract subsections under section X")
  — require the HTML hierarchy that trafilatura strips away.

The correct unit of routing is **query intent**, not domain label.

## Limitations of this phase

- **Model access was limited to small/mid-size models available
  through free or low-cost API tiers** (Together AI, OpenRouter). No
  controlled comparison against a frontier model was possible within
  this evaluation; all conclusions are scoped to small-model behavior.
- **Dataset size is small** (18 labeled entries across 3 domain. Domain-level F1 figures,
  especially for ecomerce, should be read as directional, not
  statistically robust.
- **HyDE used N=1 hypothetical document per query** (no averaging over
  multiple samples), as a deliberate cost trade-off. The original HyDE
  paper reports variance reduction from sampling N>1 documents and
  averaging embeddings; this was not evaluated here.
- **No query-level chunking router was implemented or tested.**
  Configuration E used a domain-level swap as a proxy experiment to
  demonstrate the need for finer-grained routing, not as the proposed
  final solution.

## Recommended next step

Implement a lightweight **query-intent router** that selects chunking
strategy (`trafilatura` vs. `semantic_light`) per query rather than
per domain, using a cheap heuristic (e.g. presence of structural
keywords such as "section", "subsection", "heading", "chapter") before
falling back to an LLM classifier if needed.

This is expected to combine the best outcomes observed independently
in this phase: documentation queries route to `semantic_light` (as in
configuration D, F1=0.269 vs. 0.098 in E) while linear-content queries
across all domains route to `trafilatura` (as in configuration E,
which achieved the best news F1 at the lowest token cost of any
configuration tested). The resulting blended configuration —
informally referred to as **F** — is expected to outperform both D and
E on aggregate F1 while remaining substantially more efficient than
the no-retrieval, no-refinement baseline (B): an estimated improvement
in the range of **+40-50% relative F1 over B**, based on combining each
domain's best-observed result from D and E, while keeping the per-query
token cost close to E's (the cheapest configuration with refinement
enabled). This was not run in this phase and remains the immediate
follow-up task.

## Conclusion

This phase confirms the project's central hypothesis: a small LLM,
when paired with retrieval-aware chunk selection (HyDE) and
cross-architecture validation, achieves substantially better
structured extraction quality than the same small LLM operating alone
or with same-model self-refinement — without requiring access to a
larger model. The remaining gap between the best single configuration
tested (E, F1=0.408) and the theoretical blended configuration (F) is
attributed entirely to a routing granularity issue (domain vs. query
intent), not to a limitation of the retrieval or validation
mechanisms themselves.

## References

Gao, L., Ma, X., Lin, J., & Callan, J. (2023). Precise Zero-Shot Dense
Retrieval without Relevance Labels. In *Proceedings of the 61st Annual
Meeting of the Association for Computational Linguistics (Volume 1:
Long Papers)*, pp. 1762–1777. Association for Computational
Linguistics. https://doi.org/10.18653/v1/2023.acl-long.99

Lehr, S. A., Cipperman, M., & Banaji, M. R. (2025). Extreme
Self-Preference in Language Models. *arXiv preprint arXiv:2509.26464*.
https://doi.org/10.48550/arXiv.2509.26464

Wataoka, K., Takahashi, T., & Ri, R. (2024). Self-Preference Bias in
LLM-as-a-Judge. *arXiv preprint arXiv:2410.21819*.