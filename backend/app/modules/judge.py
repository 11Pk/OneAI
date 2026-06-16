"""
Judge Module
------------
Used in Multi-Model Comparison Mode.

Receives the original prompt and all model responses,
then picks the best one and explains why.
"""

import json

from app.providers.factory import get_provider

JUDGE_PROMPT = """You are an impartial judge evaluating AI responses.

Original user prompt:
{original_prompt}

Model responses:
{responses_text}

Pick the BEST response based on: accuracy, completeness, clarity, and relevance.

Respond ONLY with valid JSON:
{{
  "selected_provider": "provider_name",
  "selected_response": "the full winning response text",
  "reasoning": "2-3 sentences explaining why this response is best"
}}
"""


async def judge(original_prompt: str, responses: list[dict]) -> dict:
    """
    Compare multiple responses and pick the best.

    Args:
        original_prompt: The user's original question
        responses: List of dicts with keys: provider, content

    Returns:
        Dict with selected_provider, selected_response, reasoning
    """
    provider = get_provider("openrouter")

    # Format all responses for the judge prompt
    responses_text = ""
    for i, r in enumerate(responses, 1):
        responses_text += f"\n--- Response {i} ({r['provider']}) ---\n{r['content']}\n"

    full_prompt = JUDGE_PROMPT.format(
        original_prompt=original_prompt,
        responses_text=responses_text,
    )

    try:
        raw = await provider.generate(full_prompt)
        text = raw.strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        data = json.loads(text.strip())
        return {
            "selected_provider": data.get("selected_provider", responses[0]["provider"]),
            "selected_response": data.get("selected_response", responses[0]["content"]),
            "reasoning": data.get("reasoning", "Selected based on overall quality."),
        }
    except (json.JSONDecodeError, KeyError, IndexError):
        # Fallback: pick first response
        return {
            "selected_provider": responses[0]["provider"],
            "selected_response": responses[0]["content"],
            "reasoning": "Unable to parse judge response; defaulting to first model.",
        }
