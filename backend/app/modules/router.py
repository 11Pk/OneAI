"""
Router Module
-------------
Maps task categories to AI providers using simple rule-based logic.

Rules (as specified):
- Coding    -> Groq
- Research  -> Gemini
- Writing   -> OpenRouter
- Analysis  -> OpenRouter
- General   -> OpenRouter
"""

# Simple lookup table - easy to modify
CATEGORY_TO_PROVIDER = {
    "coding": "groq",
    "research": "gemini",
    "writing": "openrouter",
    "analysis": "openrouter",
    "general": "openrouter",
}


def route(category: str) -> str:
    """
    Return the provider name for a given category.
    No AI call needed - just a dictionary lookup.
    """
    return CATEGORY_TO_PROVIDER.get(category.lower(), "openrouter")
