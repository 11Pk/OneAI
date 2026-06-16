"""
Base class for all AI providers.
Every provider must implement the generate() method.
"""

from abc import ABC, abstractmethod


class BaseProvider(ABC):
    """Abstract base - all AI providers inherit from this."""

    name: str = "base"

    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """
        Send a prompt to the AI model and return the text response.
        Must be implemented by each provider subclass.
        """
        pass
