import warnings
from typing import Literal

from pydantic import BaseModel, Field, model_validator

ProviderName = Literal[
    "gemini", "openai", "anthropic", "fireworks", "openai_compatible"
]
EmbeddingProviderName = Literal["local", "openai"]
DomainType = Literal["web", "ecommerce", "news", "documentation"]


class ProviderConfig(BaseModel):
    provider: ProviderName
    model_name: str
    api_key: str | None = None
    endpoint: str | None = None
    env_alias: str | None = None
    max_tokens: int = Field(default=15000, ge=100)
    temperature: float = Field(default=0.1, ge=0.0, le=1.0)
    # none: return raw text, json_object: parse response as JSON object, json_schema: validate response against a JSON schema
    json_mode: Literal["none", "json_object", "json_schema"] = "json_object"


class EmbeddingConfig(BaseModel):
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    max_tokens: int = Field(default=256, ge=64)
    provider: EmbeddingProviderName = "local"
    api_key: str | None = None
    env_alias: str | None = None

    def resolve_api_key(self) -> str | None:
        if self.api_key:
            return self.api_key
        if self.env_alias:
            import os

            return os.getenv(self.env_alias)
        return None


class PipelineConfig(BaseModel):
    extractor_provider: ProviderConfig
    validator_provider: ProviderConfig | None = (
        None  # Optional separate provider for validation (can be same as extractor)
    )
    hyde_provider: ProviderConfig | None = (
        None  # Optional separate provider for HyDE (can be same as extractor)
    )
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    max_retries: int = Field(default=1, ge=0, le=10)
    context_length: int = Field(default=32000, ge=1000)
    top_k_chunks: int = Field(default=5, ge=1)

    # Prompting strategy
    cot: bool = True
    self_consistency: bool = False
    self_consistency_samples: int = Field(default=3, ge=2, le=5)

    # Pipeline control
    refinement: bool = True

    # HTML processing
    use_markdown_conversion: bool = True
    markdown_converter: Literal["trafilatura", "markdownify"] = "trafilatura"
    # Domain for HyDE ranking (optional, can improve relevance)
    domain: DomainType = "web"

    @model_validator(mode="after")
    def warn_expensive_config(self) -> "PipelineConfig":
        if self.self_consistency and self.refinement:
            warnings.warn(
                "Both self_consistency and refinement are enabled. "
                f"This will run up to {self.self_consistency_samples * self.max_retries} "
                "LLM calls per extraction. Consider disabling one of them.",
                UserWarning,
                stacklevel=2,
            )
        return self
