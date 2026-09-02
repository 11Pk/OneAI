import httpx

from app.config import settings
from app.providers.base import BaseProvider


class OpenRouterProvider(BaseProvider):
    name = "openrouter"

    def __init__(self):
        self.api_key = settings.openrouter_api_key
        self.model = settings.openrouter_model
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

    async def generate(
        self,
        prompt: str,
        model: str | None = None
    ) -> str:

        if not self.api_key:
            return "[OpenRouter] API key not configured. Set OPENROUTER_API_KEY in .env"

        selected_model = model or self.model

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": selected_model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                self.base_url,
                headers=headers,
                json=payload
            )

            response.raise_for_status()

            data = response.json()

            return data["choices"][0]["message"]["content"]