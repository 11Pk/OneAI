from abc import ABC, abstractmethod


class BaseProvider(ABC):
    """Abstract base - all AI providers inherit from this."""

    name: str = "base"

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        model: str | None = None
    ) -> str:
        """
        Send a prompt to the AI model and return the text response.

        model:
            Specific model ID selected by OneAI classifier.
            If None, provider uses its configured default model.
        """
        pass