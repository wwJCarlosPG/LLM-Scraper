from logging import getLogger

from scraper.adapters.html.cleaner import DefaultHTMLCleaner
from scraper.adapters.html.markdown_converter import MarkdownConverter
from scraper.core.entities.state import PipelineState

cleaner = DefaultHTMLCleaner()
converter = MarkdownConverter()
logger = getLogger(__name__)


async def cleaner_node(state: PipelineState) -> dict:
    html = state["html"]
    html_url = state["html_url"]
    config = state["config"]

    # fetch HTML from URL if not provided directly
    if html is None and html_url is not None:
        logger.info(f"[cleaner] fetching HTML from {html_url}")
        html = cleaner.fetch(html_url)
    elif html is None and html_url is None:
        raise ValueError("Either html or html_url must be provided in PipelineState.")

    # convert to markdown if configured
    if config.use_markdown_conversion:
        logger.info(
            f"[cleaner] converting to markdown with {config.markdown_converter}"
        )
        cleaned = converter.convert(html, strategy=config.markdown_converter)
    else:
        cleaned = cleaner.light_clean(html, config.context_length)

    logger.info(f"[cleaner] cleaned HTML length: {len(cleaned)} chars")
    return {"cleaned_html": cleaned, "html": html}
