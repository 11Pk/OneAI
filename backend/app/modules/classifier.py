"""
Task Classifier Module
----------------------
Categorizes each task into one of: coding, research, writing, analysis, general.

Uses an LLM with a simple classification prompt.
"""

import json

from app.providers.factory import get_provider

# Valid categories the router understands
CATEGORIES = ["coding", "research", "writing", "analysis", "general"]

CLASSIFIER_PROMPT = """Classify the following task into exactly ONE category.

Categories:
- coding: programming, debugging, code review, algorithms, software development
- research: finding information, facts, explanations, learning topics
- writing: essays, emails, creative writing, content creation
- analysis: data analysis, comparisons, evaluations, reasoning
- general: anything that doesn't fit above

Respond ONLY with valid JSON:
{{"category": "coding"}}

Task:
{task}
"""


async def classify(task: str) -> str:
    """
    Return the category string for a task.
    Defaults to 'general' if classification fails.
    """
    provider = get_provider("openrouter")
    full_prompt = CLASSIFIER_PROMPT.format(task=task)

    try:
        raw = await provider.generate(full_prompt)
        text = raw.strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        data = json.loads(text.strip())
        category = data.get("category", "general").lower()

        if category not in CATEGORIES:
            return "general"
        return category

    except (json.JSONDecodeError, KeyError):
        return "general"
