"""
Factory to get provider instances by name.
"""

from app.providers.base import BaseProvider
from app.providers.gemini import GeminiProvider
from app.providers.groq import GroqProvider
from app.providers.openrouter import OpenRouterProvider

# Cache provider instances so we don't recreate them every time
_providers: dict[str, BaseProvider] = {}


def get_provider(name: str) -> BaseProvider:
    """Return a provider instance by name (openrouter, gemini, groq)."""
    if name not in _providers:
        if name == "openrouter":
            _providers[name] = OpenRouterProvider()
        elif name == "gemini":
            _providers[name] = GeminiProvider()
        elif name == "groq":
            _providers[name] = GroqProvider()
        else:
            # Default to openrouter for unknown providers
            _providers[name] = OpenRouterProvider()
    return _providers[name]


def get_all_providers() -> list[BaseProvider]:
    """Return all three providers (used in compare mode)."""
    return [
        get_provider("openrouter"),
        get_provider("gemini"),
        get_provider("groq"),
    ]
