"""
Planner Module
--------------
Decides whether a user prompt should be split into multiple subtasks.

Uses an LLM with a simple prompt. Returns:
- needs_decomposition: True/False
- subtasks: list of task strings (empty if no decomposition)
"""

import json

from app.providers.factory import get_provider


PLANNER_PROMPT = """You are a task planner. Analyze the user prompt and decide if it should be broken into separate subtasks.

Rules:
- Simple questions or single requests: NO decomposition (one task)
- Complex requests with multiple distinct parts: YES decomposition
- Examples needing decomposition: "Write a blog post AND create a Python script for data analysis"
- Examples NOT needing decomposition: "What is machine learning?", "Write a hello world in Python"

Respond ONLY with valid JSON in this exact format:
{{"needs_decomposition": true/false, "subtasks": ["task1", "task2"]}}

If needs_decomposition is false, subtasks should contain only the original prompt as one item.

User prompt:
{prompt}
"""


async def plan(prompt: str) -> tuple[bool, list[str]]:
    """
    Analyze prompt and return (needs_decomposition, list_of_subtasks).

    Uses OpenRouter as the planner LLM (could use any provider).
    Falls back to single-task mode if LLM fails.
    """
    provider = get_provider("openrouter")
    full_prompt = PLANNER_PROMPT.format(prompt=prompt)

    try:
        raw = await provider.generate(full_prompt)
        # Extract JSON from response (handle markdown code blocks)
        text = raw.strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        data = json.loads(text.strip())

        needs_decomposition = bool(data.get("needs_decomposition", False))
        subtasks = data.get("subtasks", [prompt])

        if not subtasks:
            subtasks = [prompt]

        return needs_decomposition, subtasks

    except (json.JSONDecodeError, KeyError, IndexError):
        # If parsing fails, treat as single task
        return False, [prompt]
