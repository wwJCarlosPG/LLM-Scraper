import logging

import httpx
from langsmith import traceable

from scraper.core.entities.config import ProviderConfig
from scraper.core.entities.token_usage import TokenUsage
from scraper.providers.base import BaseProvider

logger = logging.getLogger(__name__)


class GeminiProvider(BaseProvider):
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.endpoint = f"{self.BASE_URL}/{self.model_name}:generateContent"

    @traceable(name="GeminiProvider.invoke", run_type="llm")
    def invoke(self, user_prompt: str, system_prompt: str) -> tuple[str, TokenUsage]:
        with httpx.Client() as client:
            return self._request(client, user_prompt, system_prompt)

    @traceable(name="GeminiProvider.ainvoke", run_type="llm")
    async def ainvoke(
        self, user_prompt: str, system_prompt: str
    ) -> tuple[str, TokenUsage]:
        async with httpx.AsyncClient() as client:
            return await self._arequest(client, user_prompt, system_prompt)

    def _build_payload(self, user_prompt: str, system_prompt: str) -> dict:
        return {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "maxOutputTokens": self.max_tokens,
                "temperature": self.temperature,
            },
        }

    def _parse_response(self, data: dict) -> tuple[str, TokenUsage]:
        try:
            text = data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as e:
            raise ValueError(f"Unexpected Gemini response format: {data}") from e
        meta = data.get("usageMetadata", {})
        usage = TokenUsage(
            input_tokens=meta.get("promptTokenCount", 0),
            output_tokens=meta.get("candidatesTokenCount", 0),
        )
        return text, usage

    def _request(
        self, client: httpx.Client, user_prompt: str, system_prompt: str
    ) -> tuple[str, TokenUsage]:
        response = client.post(
            self.endpoint,
            params={"key": self.api_key},
            json=self._build_payload(user_prompt, system_prompt),
            timeout=60.0,
        )
        if response.status_code != 200:
            raise ValueError(f"Gemini error {response.status_code}: {response.text}")
        return self._parse_response(response.json())

    async def _arequest(
        self, client: httpx.AsyncClient, user_prompt: str, system_prompt: str
    ) -> tuple[str, TokenUsage]:
        response = await client.post(
            self.endpoint,
            params={"key": self.api_key},
            json=self._build_payload(user_prompt, system_prompt),
            timeout=60.0,
        )
        if response.status_code != 200:
            raise ValueError(f"Gemini error {response.status_code}: {response.text}")
        return self._parse_response(response.json())
