"""
Groq provider - fast inference for coding tasks.
Used for Coding tasks.
"""

import httpx

from app.config import settings
from app.providers.base import BaseProvider


class GroqProvider(BaseProvider):
    name = "groq"

    def __init__(self):
        self.api_key = settings.groq_api_key
        self.model = settings.groq_model
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"

    async def generate(self, prompt: str) -> str:
        """Call Groq chat completions API (OpenAI-compatible)."""
        if not self.api_key:
            return "[Groq] API key not configured. Set GROQ_API_KEY in .env"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(self.base_url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
