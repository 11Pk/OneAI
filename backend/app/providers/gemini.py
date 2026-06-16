"""
Google Gemini provider.
Used for Research tasks.
"""

import httpx

from app.config import settings
from app.providers.base import BaseProvider


class GeminiProvider(BaseProvider):
    name = "gemini"

    def __init__(self):
        self.api_key = settings.gemini_api_key
        self.model = settings.gemini_model

    async def generate(self, prompt: str) -> str:
        """Call Google Gemini generateContent API."""
        if not self.api_key:
            return "[Gemini] API key not configured. Set GEMINI_API_KEY in .env"

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent?key={self.api_key}"
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
