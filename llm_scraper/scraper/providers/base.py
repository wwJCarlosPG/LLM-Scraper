import os

from scraper.core.entities.config import ProviderConfig
from scraper.core.ports.llm_port import LLMPort


class BaseProvider(LLMPort):
    def __init__(self, config: ProviderConfig):
        self.config = config
        self.api_key = self._resolve_api_key()
        self.model_name = config.model_name

    def _resolve_api_key(self) -> str:
        if self.config.api_key:
            return self.config.api_key
        if self.config.env_alias:
            key = os.getenv(self.config.env_alias)
            if key:
                return key
            raise ValueError(
                f"API key not found in environment variable '{self.config.env_alias}'"
            )
        raise ValueError(
            "Either api_key or env_alias must be provided in ProviderConfig."
        )
