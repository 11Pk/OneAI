"""
Prompt Enhancer Module
----------------------
Improves the user's prompt before sending it to the target AI model.

Adds clarity, context, and structure so the model gives better answers.
"""

from app.providers.factory import get_provider

ENHANCER_PROMPT = """You are a prompt engineer. Improve the following task prompt to get a better AI response.

Guidelines:
- Keep the original intent
- Add clarity and structure if needed
- Do NOT answer the task - only rewrite the prompt
- Return ONLY the improved prompt, nothing else

Original prompt:
{prompt}

Category: {category}
"""


async def enhance(prompt: str, category: str) -> str:
    """
    Return an improved version of the prompt.
    Falls back to original prompt if enhancement fails.
    """
    provider = get_provider("openrouter")
    full_prompt = ENHANCER_PROMPT.format(prompt=prompt, category=category)

    try:
        enhanced = await provider.generate(full_prompt)
        result = enhanced.strip()
        # If empty or too short, use original
        if len(result) < 5:
            return prompt
        return result
    except Exception:
        return prompt
