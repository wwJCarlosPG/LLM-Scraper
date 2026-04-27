# Chunking Strategy Research

## Objective
Validate the semantic chunking implementation and determine the optimal 
chunking strategy for different page types.

## Test Setup
- Chunk size: 8,000 chars
- Overlap: 200 chars
- Pages tested: news article (BBC), e-commerce (books.toscrape.com)

## Strategies evaluated

### 1. SemanticChunker (HTMLSemanticPreservingSplitter)
Splits HTML by semantic sections using header tags as boundaries.

| Page type | Result |
|---|---|
| News article (BBC) | 31 chunks, majority < 200 chars. Headers present in navigation, sidebars and related articles generate useless chunks filled with noise. |
| E-commerce (books.toscrape.com) | 2 chunks of 579 and 1,237 chars. Discards most content because products are in `<article>` and `<li>` without headers. |

**Verdict: not suitable for real-world pages.** Pages with complex navigation and sidebars generate too much noise. Pages without headers discard most content.

---

### 2. Markdown conversion with trafilatura
Extracts the main content of the page and converts it to Markdown, 
ignoring navigation, sidebars and footers.

| Page type | Result |
|---|---|
| News article (BBC) | 10,994 chars → 2 clean chunks with article content only. Overlap verified ✓ |
| E-commerce (books.toscrape.com) | 375 chars. trafilatura finds no main article and returns almost nothing. |

**Verdict: excellent for articles and blogs, not suitable for e-commerce.**

---

### 3. Markdown conversion with markdownify
Converts the full HTML to Markdown preserving all content structure.

| Page type | Result |
|---|---|
| News article (BBC) | Similar to trafilatura but includes navigation noise. |
| E-commerce (books.toscrape.com) | 10,728 chars → 2 chunks with products, prices and navigation. Overlap verified ✓ |

**Verdict: best for e-commerce and structured listings.**

---

## Conclusions

### Recommended strategy by page type

| Page type | Recommended strategy | Config |
|---|---|---|
| News articles / blogs | trafilatura | `use_markdown_conversion=True`, `markdown_converter="trafilatura"` |
| E-commerce / product listings | markdownify | `use_markdown_conversion=True`, `markdown_converter="markdownify"` |
| Unknown / fallback | markdownify | `use_markdown_conversion=True`, `markdown_converter="markdownify"` |

### Key decisions

**`use_markdown_conversion=True` is now the default** in `PipelineConfig`. 
Markdown conversion consistently produces smaller, cleaner content than 
raw HTML cleaning, reducing token usage and improving extraction quality.

**SemanticChunker is kept in the codebase** but not used as the default 
strategy. It may be useful for pages with clean, well-structured HTML 
like technical documentation.

**Overlap works correctly** with `MarkdownTextSplitter`. Verified that 
content from the end of chunk N appears at the start of chunk N+1.

### Known limitations

- trafilatura cannot extract content from pages without a clear main article 
  (e-commerce, listings, dashboards).
- markdownify includes navigation and footer content which adds noise. 
  The LLM handles this well but it increases token usage.
- The optimal strategy depends on the page type, which the user must 
  configure manually via `markdown_converter`. A future improvement would 
  be an agent that detects the page type and selects the strategy 
  automatically (see Tarea 8 in backlog).

## Pending research

### Issue 7: Research optimal chunking strategies
The current default values (chunk_size, overlap) were not systematically 
validated. A dedicated research task is needed to:

- Test combinations of chunk sizes (4,000 / 8,000 / 16,000 chars)
- Test combinations of overlap sizes (0 / 200 / 500 chars)
- Evaluate alternative chunking strategies not covered in this research:
  - `HTMLHeaderTextSplitter` for documentation-style pages
  - `RecursiveCharacterTextSplitter` directly on cleaned HTML
  - Custom chunker based on DOM repetition patterns (e.g. detect 
    repeating `<article>` or `<li>` blocks as product/item units)
- Measure impact on extraction quality using a labeled dataset
- Update default values in `PipelineConfig` based on findings

See backlog for full task description.