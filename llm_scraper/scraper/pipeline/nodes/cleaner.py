from scraper.adapters.html.cleaner import DefaultHTMLCleaner
from scraper.adapters.html.markdown_converter import MarkdownConverter
from scraper.core.entities.state import PipelineState

cleaner = DefaultHTMLCleaner()
converter = MarkdownConverter()


async def cleaner_node(state: PipelineState) -> dict:
    html = state["html"]
    html_url = state["html_url"]
    config = state["config"]

    # fetch HTML from URL if not provided directly
    if html is None and html_url is not None:
        html = cleaner.fetch(html_url)
    elif html is None and html_url is None:
        raise ValueError("Either html or html_url must be provided in PipelineState.")

    # convert to markdown if configured
    if config.use_markdown_conversion:
        cleaned = converter.convert(html, strategy=config.markdown_converter)
    else:
        cleaned = cleaner.clean(html, config.context_length)

    return {"cleaned_html": cleaned, "html": html}
