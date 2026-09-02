"""
Judge Module
------------
Used in Multi-Model Comparison Mode.

Receives the original prompt and all model responses,
then picks the best response and explains why.
"""

import json

from app.providers.factory import get_provider


JUDGE_PROMPT = """
You are an impartial judge evaluating AI responses.

Original user prompt:
{original_prompt}

Model responses:
{responses_text}

Pick the BEST response based on:

1. Accuracy
2. Completeness
3. Clarity
4. Relevance
5. How well it follows the original user's instructions

Do not prefer a response simply because it comes from
a particular provider or model.

Respond ONLY with valid JSON:

{{
  "selected_model_id": "model_id",
  "selected_provider": "provider_name",
  "selected_response": "the full winning response text",
  "reasoning": "2-3 sentences explaining why this response is best"
}}
"""


async def judge(
    original_prompt: str,
    responses: list[dict]
) -> dict:
    """
    Compare multiple model responses and pick the best.

    Args:
        original_prompt:
            The user's original question.

        responses:
            List of dictionaries containing:

            {
                "model_id": "...",
                "provider": "...",
                "content": "..."
            }

    Returns:
        {
            "selected_model_id": "...",
            "selected_provider": "...",
            "selected_response": "...",
            "reasoning": "..."
        }
    """

    if not responses:
        return {
            "selected_model_id": None,
            "selected_provider": None,
            "selected_response": "",
            "reasoning": "No responses were available for comparison."
        }

    # --------------------------------------------------
    # JUDGE MODEL
    # --------------------------------------------------

    # The judge itself is independent of the candidate models.
    # Currently using OpenRouter as the judge provider.
    provider = get_provider("openrouter")

    # --------------------------------------------------
    # FORMAT RESPONSES
    # --------------------------------------------------

    responses_text = ""

    for i, response in enumerate(
        responses,
        start=1
    ):

        responses_text += (
            f"\n--- Response {i} ---\n"
            f"Model ID: {response['model_id']}\n"
            f"Provider: {response['provider']}\n"
            f"Response:\n{response['content']}\n"
        )

    # --------------------------------------------------
    # BUILD JUDGE PROMPT
    # --------------------------------------------------

    full_prompt = JUDGE_PROMPT.format(
        original_prompt=original_prompt,
        responses_text=responses_text
    )

    # --------------------------------------------------
    # CALL JUDGE MODEL
    # --------------------------------------------------

    try:

        raw = await provider.generate(
            full_prompt
        )

        text = raw.strip()

        # Remove markdown JSON fences if the model
        # accidentally returns them.
        if text.startswith("```"):

            lines = text.splitlines()

            if lines and lines[0].startswith("```"):
                lines = lines[1:]

            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            text = "\n".join(lines).strip()

        data = json.loads(text)

        # --------------------------------------------------
        # VALIDATE WINNER
        # --------------------------------------------------

        selected_model_id = data.get(
            "selected_model_id"
        )

        selected_provider = data.get(
            "selected_provider"
        )

        selected_response = data.get(
            "selected_response"
        )

        reasoning = data.get(
            "reasoning",
            "Selected based on overall response quality."
        )

        # Make sure the judge actually selected
        # one of the candidate models.
        valid_model_ids = {
            response["model_id"]
            for response in responses
        }

        if selected_model_id not in valid_model_ids:

            return {
                "selected_model_id": responses[0]["model_id"],
                "selected_provider": responses[0]["provider"],
                "selected_response": responses[0]["content"],
                "reasoning": (
                    "Judge returned an invalid model selection; "
                    "defaulting to the first successful response."
                )
            }

        return {
            "selected_model_id": selected_model_id,
            "selected_provider": selected_provider,
            "selected_response": selected_response,
            "reasoning": reasoning
        }

    except (
        json.JSONDecodeError,
        KeyError,
        IndexError,
        TypeError
    ):

        # --------------------------------------------------
        # FALLBACK
        # --------------------------------------------------

        return {
            "selected_model_id": responses[0]["model_id"],
            "selected_provider": responses[0]["provider"],
            "selected_response": responses[0]["content"],
            "reasoning": (
                "Unable to parse judge response; "
                "defaulting to the first successful model."
            )
        }