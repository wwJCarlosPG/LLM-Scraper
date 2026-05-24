# Chunking Strategy Research

> **Scope notice:** All results were obtained on a restricted dataset of 24 labeled pages
> across 3 domains (news, ecommerce, documentation) with 27 queries total. 3 entries
> failed due to site access restrictions (reuters.com). Conclusions should be treated as
> directional signals, not statistically definitive benchmarks.

---

## Setup

| Parameter | Value |
|---|---|
| Chunk sizes tested | small_8k (1,600 chars), medium_32k (6,400 chars) |
| Top-k range | k = 1 to 15 |
| Overlap ratio | 10% of chunk size |
| Embedding model | text-embedding-ada-002 (OpenAI) |
| Similarity threshold | 0.75 |
| Dataset | 24 valid entries across news (9), ecommerce (9), documentation (6) |

### Metrics

- **coverage_ratio[k]**: fraction of expected items whose best matching chunk appears in top-k with similarity ≥ threshold. 1.0 = all expected items covered.
- **hard_coverage[k]**: percentage of entries where ≥80% of expected items are covered at top-k.
- **scorer_improvement**: average rank change for expected items after relevance scoring (positive = scorer helped).
- **false_positive_ratio[k]**: fraction of top-k chunks that do not contain relevant content.

---

## Chunking strategies evaluated

| Strategy | Description |
|---|---|
| `trafilatura` | Main content extraction via trafilatura → MarkdownTextSplitter |
| `markdownify` | Full HTML to Markdown conversion → MarkdownTextSplitter |
| `semantic_light` | HTMLSemanticPreservingSplitter on lightly cleaned HTML (noise tags only removed) |
| `recursive_light` | RecursiveCharacterTextSplitter on lightly cleaned HTML |

---

## Global results — small_8k (1,600 chars)

### Coverage ratio (avg % of expected items in top-k)

| Strategy | k=1 | k=5 | k=8 | k=10 | k=13 | k=15 |
|---|---|---|---|---|---|---|
| `trafilatura` | 32% | 71% | **85%** | 85% | 86% | 86% |
| `semantic_light` | 8% | 39% | 48% | 62% | **80%** | 81% |
| `markdownify` | 4% | 28% | 38% | 42% | 45% | 52% |
| `recursive_light` | 3% | 19% | 25% | 29% | 32% | 39% |

Minimum k for ≥80% average coverage:
- `trafilatura`: k=8 (85%)
- `semantic_light`: k=14 (80%)
- `markdownify`: never reaches 80% (max 52%)
- `recursive_light`: never reaches 80% (max 39%)

---

## Global results — medium_32k (6,400 chars)

### Coverage ratio (avg % of expected items in top-k)

| Strategy | k=1 | k=2 | k=5 | k=10 | k=12 | k=15 |
|---|---|---|---|---|---|---|
| `trafilatura` | 59% | **80%** | 81% | 81% | 81% | 81% |
| `semantic_light` | 2% | 21% | 50% | 74% | **80%** | 82% |
| `markdownify` | 12% | 21% | 54% | 60% | 63% | 64% |
| `recursive_light` | 6% | 16% | 38% | 57% | 63% | 66% |

Minimum k for ≥80% average coverage:
- `trafilatura`: k=5 (81%), effective from k=2 (80%)
- `semantic_light`: k=13 (80%)
- `markdownify`: never reaches 80% (max 64%)
- `recursive_light`: never reaches 80% (max 66%)

---

## Results by domain — medium_32k

### News (9 entries)

| Strategy | k=2 | k=5 | k=10 | k=15 |
|---|---|---|---|---|
| `trafilatura` | **84%** | 84% | 84% | 84% |
| `recursive_light` | 18% | 31% | 52% | 58% |
| `markdownify` | 14% | 30% | 42% | 54% |
| `semantic_light` | 4% | 9% | 56% | 57% |

`trafilatura` reaches 84% at k=2 and stays flat. The relevant content is naturally in the first few chunks because trafilatura extracts only the main article body. No other strategy comes close for this domain on the tested pages.

`semantic_light` shows a steep jump at k=10 (56%) and plateaus at 57%, suggesting most relevant content sits at chunk ranks 8-10. News articles with complex HTML structure (e.g. BBC) confuse the semantic splitter, producing many small low-ranked chunks before the main content.

### E-commerce (9 entries)

| Strategy | k=2 | k=5 | k=10 | k=15 |
|---|---|---|---|---|
| `trafilatura` | **97%** | 97% | 97% | 97% |
| `semantic_light` | 34% | **97%** | 97% | 97% |
| `markdownify` | 18% | 89% | 89% | 89% |
| `recursive_light` | 9% | 53% | 72% | 84% |

Both `trafilatura` and `semantic_light` reach 97% coverage. `trafilatura` gets there at k=2 while `semantic_light` needs k=5. Both are strong options for e-commerce pages. `recursive_light` never reaches 97% within k=15.

### Documentation (6 entries)

| Strategy | k=5 | k=10 | k=12 | k=14 | k=15 |
|---|---|---|---|---|---|
| `semantic_light` | 39% | 67% | 90% | **99%** | 99% |
| `trafilatura` | 50% | 52% | 52% | 52% | 52% |
| `recursive_light` | 26% | 40% | 48% | 51% | 52% |
| `markdownify` | 36% | 42% | 42% | 42% | 42% |

The most important domain finding. `semantic_light` reaches **99% coverage at k=14** while `trafilatura` plateaus at **52% regardless of k**. Trafilatura discards navigation and structural elements that in documentation pages include the table of contents and section headers needed for extraction. `semantic_light` preserves the full HTML structure using semantic section boundaries as chunk delimiters, making it the only viable strategy for structured documentation on this dataset.

---

## Key findings

### 1. No single strategy works across all domains

The optimal chunking strategy depends on the page type:

| Domain | Best strategy | Optimal k (medium_32k) | Max coverage |
|---|---|---|---|
| News | `trafilatura` | k=2 | 84% |
| E-commerce | `trafilatura` or `semantic_light` | k=2–5 | 97% |
| Documentation | `semantic_light` | k=12–14 | 99% |

This strongly motivates automatic page-type detection (see Pending Research, Task 8).

### 2. Chunk size matters significantly

`medium_32k` (6,400 chars) consistently outperforms `small_8k` (1,600 chars) for the same strategy and k. With `trafilatura`, the minimum k for ≥80% coverage drops from k=8 to k=2 when moving from small to medium chunks. Larger chunks group related content together, reducing the number of chunks needed to cover the expected items.

### 3. Chunking is not always necessary

The pipeline should determine whether to chunk at all based on context length. If the total content length fits within the model's context window, sending the full document in a single call is both cheaper and safer (no risk of losing context through chunking). Chunking only makes sense when the content exceeds the model's context window.

The chunk size should be derived from the available context:
```python
chunk_size = context_length // top_k_chunks
```

### 4. The relevance scorer has negligible impact

| Strategy | avg improvement (medium_32k) | better | same | worse |
|---|---|---|---|---|
| `trafilatura` | +0.00 | 0 | 367 | 0 |
| `semantic_light` | +0.76 | 27 | 331 | 5 |
| `markdownify` | +1.26 | 18 | 274 | 0 |
| `recursive_light` | +4.30 | 104 | 67 | 85 |

For `trafilatura` the scorer makes no difference. For `recursive_light` it actively worsens ranking in 85 cases. The root cause is semantic mismatch: the scorer compares a task instruction query ("Extract all product names") against document chunks. This is an asymmetric retrieval problem — the query describes a task, not content, so embedding similarity does not reliably identify relevant chunks.

False positive ratios at k=3 remain high (28–42%) across all strategies, confirming the scorer is not discriminating effectively.

### 5. markdownify and recursive_light are not viable as primary strategies

Neither strategy reaches 80% coverage in any tested configuration. `markdownify` generates excessive noise from HTML-to-Markdown conversion, and `recursive_light` splits content without respecting semantic boundaries. Both may serve as fallbacks for specific edge cases but should not be default strategies.

### 6. Documentation requires significantly higher k

Unlike news and e-commerce where coverage saturates at k=2–5, documentation requires k=12–14 with `semantic_light` to exceed 80% coverage. Documentation pages distribute relevant content (section titles, code examples, definitions) throughout the entire document, and no small top-k window can capture all of it.

---

## Configuration recommendations

### Recommended PipelineConfig by domain

```python
# News and general web content
PipelineConfig(
    use_markdown_conversion=True,
    markdown_converter="trafilatura",
    context_length=32000,
    top_k_chunks=5
)

# E-commerce
PipelineConfig(
    use_markdown_conversion=True,
    markdown_converter="trafilatura",
    context_length=32000,
    top_k_chunks=5
)

# Technical documentation
PipelineConfig(
    use_markdown_conversion=False,  # semantic_light uses light_clean directly
    context_length=32000,
    top_k_chunks=15
)
```

---

## Limitations of this benchmark

**Restricted dataset.** 24 valid entries across 3 domains is insufficient for statistically robust conclusions. Results should be interpreted as directional signals. A production benchmark would require 200+ pages across more diverse sources.

**Single source bias.** News entries are predominantly BBC articles. E-commerce entries use practice/sandbox sites. Documentation entries use Python docs and LangChain docs only. Results may not generalise to other sources.

**Query quality.** Queries were manually designed to be specific to each page but remain relatively simple. More complex multi-step or inferential queries would likely produce lower coverage scores across the board.

**No ground truth for retrieval quality.** `coverage_ratio` measures whether the embedding-matched chunk for each expected item is in top-k. It does not directly measure extraction quality. A chunk can be in top-k but the LLM may still fail to extract the correct information from it.

**Single embedding model.** All evaluations used `text-embedding-ada-002`. Results may differ with asymmetric retrieval models (E5, BGE) trained specifically for query-document pairs, or with HyDE query transformation.

**Reuters.com blocked.** 3 news entries failed due to HTTP 401. News domain results are based on 6 BBC articles and 3 dev.to articles only.

---

## Pending research

| Description task |
|---|
| Page-type detection agent to automatically select chunking strategy per domain |
| Playwright support for JavaScript-rendered pages |
| Late Chunking (arxiv:2409.04701): embed the full document first, then pool token embeddings into chunks, preserving cross-chunk context |
| DOM-based RAG (HtmlRAG arxiv:2411.02959): use DOM nodes directly as retrieval units instead of text chunks |
| HyDE (Hypothetical Document Embeddings): use the LLM to generate a hypothetical ideal chunk and embed that as the query, replacing task-instruction embeddings with content-style embeddings |
| Evaluate asymmetric retrieval models (E5-base, BGE) with query/passage prefixes |