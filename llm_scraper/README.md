# LLM Scraper

A flexible and extensible web scraping library powered by Large Language Models. Instead of relying on fixed CSS selectors or XPath rules, LLM Scraper uses natural language queries to extract structured data from any web page, adapting automatically to structural changes.

## Features

- **Natural language queries** — describe what you want to extract in plain English or Spanish
- **Model-agnostic** — works with Gemini, Fireworks AI, LM Studio, Ollama, or any OpenAI-compatible endpoint
- **Agentic pipeline** — built on LangGraph with explicit state: clean → chunk → extract → merge → validate → refine
- **Adaptive HTML cleaning** — multi-level cleaning that reduces token usage while preserving relevant content
- **Markdown conversion** — converts HTML to Markdown before LLM ingestion using `trafilatura` or `markdownify`
- **Semantic chunking** — splits large pages by DOM structure instead of arbitrary character windows
- **Self-consistency** — generates multiple independent extractions and keeps results that appear in the majority
- **Refinement loop** — validator agent provides feedback to the extractor on failed attempts
- **Observability** — full pipeline tracing with LangSmith

## Installation

Requires Python 3.11+

```bash
git clone https://github.com/wwJCarlosPG/LLM-Scraper.git
cd llm_scraper
pip install poetry
poetry install
```

## Configuration

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

```bash
# .env

# Gemini (required for default examples)
GEMINI_API_KEY=your_gemini_api_key_here

# Fireworks AI (optional)
FIREWORKS_API_KEY=your_fireworks_api_key_here

# Anthropic (optional)
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# LangSmith (optional - for tracing)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=your_langsmith_api_key_here
LANGCHAIN_PROJECT=llm-scraper
```

## Quick start

```python
import asyncio
from dotenv import load_dotenv
from scraper.pipeline.runner import run
from scraper.core.entities.config import PipelineConfig, ProviderConfig

load_dotenv()

async def main():
    result = await run(
        query="Extract all news headlines from the page.",
        output_format={"headline": "news headline text"},
        config=PipelineConfig(
            provider=ProviderConfig(
                provider="gemini",
                model_name="gemini-2.0-flash",
                env_alias="GEMINI_API_KEY"
            )
        ),
        html_url="https://www.bbc.com"
    )

    for item in result.scraped_data:
        print(item)

asyncio.run(main())
```

## Pipeline

```
html / url
    │
    ▼
┌─────────┐     ┌─────────┐     ┌───────────┐     ┌────────┐
│ cleaner │────▶│ chunker │────▶│ extractor │────▶│ merger │
└─────────┘     └─────────┘     └───────────┘     └────────┘
                                      ▲                 │
                                      │                 ▼
                                   refine          ┌──────────┐
                                      │            │ validator│
                                      └────────────└──────────┘
                                                        │
                                                        ▼
                                                    is_valid?
                                                   yes → end
```

1. **cleaner** — removes noise tags, unnecessary attributes and whitespace. Optionally converts to Markdown.
2. **chunker** — splits the content into semantic blocks if it exceeds the context window.
3. **extractor** — sends each chunk to the LLM with the user query and extracts structured data.
4. **merger** — combines partial responses from all chunks and deduplicates results.
5. **validator** — verifies the extracted data against the query. If invalid, sends feedback back to the extractor.

## Configuration options

```python
PipelineConfig(
    provider=ProviderConfig(...),

    # Context
    context_length=32000,       # max chars sent to the LLM

    # Prompting strategy
    cot=True,                   # chain-of-thought reasoning
    self_consistency=False,     # generate N extractions, keep majority
    self_consistency_samples=3, # number of samples (2-5)

    # Pipeline control
    refinement=True,            # enable validator feedback loop
    max_retries=3,              # max refinement iterations

    # HTML processing
    use_markdown_conversion=False,          # convert HTML to Markdown
    markdown_converter="trafilatura",       # or "markdownify"

    # LLM settings
    temperature=0.5,
    max_tokens=10000,
)
```

## Supported providers

| Provider | `provider` value | Notes |
|---|---|---|
| Google Gemini | `gemini` | Recommended for best results |
| Fireworks AI | `openai_compatible` | Set `endpoint` to Fireworks URL |
| LM Studio | `openai_compatible` | Set `endpoint` to localhost |
| Ollama | `openai_compatible` | Set `endpoint` to Ollama URL |
| Any OpenAI-compatible API | `openai_compatible` | Works with any `/v1/chat/completions` endpoint |

## Examples

```bash
poetry run python examples/basic_extraction.py
```

## Observability

If `LANGCHAIN_TRACING_V2=true` is set, every pipeline run is traced in LangSmith including each node's input/output, LLM calls with full prompts and responses, token usage and latency per step.

## Project structure

```
scraper/
├── core/
│   ├── entities/       # PipelineState, ScrapedResponse, PipelineConfig
│   ├── ports/          # Abstract interfaces: LLMPort, CleanerPort, StoragePort
│   └── constants.py
├── pipeline/
│   ├── graph.py        # LangGraph state graph
│   ├── runner.py       # Public entry point
│   ├── nodes/          # cleaner, chunker, extractor, validator, merger
│   └── prompts/        # System and user prompts
├── providers/          # LLM provider implementations
└── adapters/           # HTML cleaners, markdown converter, storage
```

## License

MIT
