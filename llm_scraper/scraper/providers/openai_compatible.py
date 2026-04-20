import httpx

from scraper.core.entities.config import ProviderConfig
from scraper.providers.base import BaseProvider


class OpenAICompatibleProvider(BaseProvider):
    """
    Generic provider for any API that follows the OpenAI chat completions format.
    Works with: Fireworks, LM Studio, Ollama, Together AI, etc.
    """

    def __init__(self, config: ProviderConfig):
        if not config.endpoint:
            raise ValueError(
                "OpenAICompatibleProvider requires an endpoint in ProviderConfig."
            )
        super().__init__(config)
        self.endpoint = config.endpoint

    def invoke(self, user_prompt: str, system_prompt: str) -> str:
        with httpx.Client() as client:
            return self._request(client, user_prompt, system_prompt)

    async def ainvoke(self, user_prompt: str, system_prompt: str) -> str:
        async with httpx.AsyncClient() as client:
            return await self._arequest(client, user_prompt, system_prompt)

    def _build_payload(self, user_prompt: str, system_prompt: str) -> dict:
        return {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
        }

    def _parse_response(self, data: dict) -> str:
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            raise ValueError(f"Unexpected response format: {data}") from e

    def _build_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _request(
        self, client: httpx.Client, user_prompt: str, system_prompt: str
    ) -> str:
        response = client.post(
            self.endpoint,
            headers=self._build_headers(),
            json=self._build_payload(user_prompt, system_prompt),
            timeout=60.0,
        )
        if response.status_code != 200:
            raise ValueError(f"Provider error {response.status_code}: {response.text}")
        return self._parse_response(response.json())

    async def _arequest(
        self, client: httpx.AsyncClient, user_prompt: str, system_prompt: str
    ) -> str:
        response = await client.post(
            self.endpoint,
            headers=self._build_headers(),
            json=self._build_payload(user_prompt, system_prompt),
            timeout=60.0,
        )
        if response.status_code != 200:
            raise ValueError(f"Provider error {response.status_code}: {response.text}")
        return self._parse_response(response.json())
