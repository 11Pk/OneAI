# """
# Orchestrator Module
# -------------------
# Main workflow coordinator. Ties together Planner, Classifier, Router,
# Enhancer, and Providers.

# Flow:
# 1. Plan (decompose or not)
# 2. For each task: classify -> route -> enhance -> generate
# 3. Run all tasks in parallel with asyncio.gather()
# 4. Combine responses into final answer
# """

# import asyncio
# import uuid

# from sqlalchemy.ext.asyncio import AsyncSession

# from app.models.db_models import Conversation, Message, Response, Task
# from app.modules.classifier import classify
# from app.modules.enhancer import enhance
# from app.modules.planner import plan
# from app.modules.router import route
# from app.providers.factory import get_all_providers, get_provider
# from app.schemas.api import ChatResponse, CompareResponseItem, TaskDetail


# async def _process_single_task(
#     task_prompt: str,
#     task_index: int,
# ) -> TaskDetail:
#     """
#     Process one task through the full pipeline:
#     classify -> route -> enhance -> generate
#     """
#     # Step 1: Classify the task
#     category = await classify(task_prompt)

#     # Step 2: Route to the right provider
#     provider_name = route(category)

#     # Step 3: Enhance the prompt
#     enhanced = await enhance(task_prompt, category)

#     # Step 4: Generate response from the routed provider
#     provider = get_provider(provider_name)
#     response_text = await provider.generate(enhanced)

#     return TaskDetail(
#         task_index=task_index,
#         category=category,
#         provider=provider_name,
#         original_prompt=task_prompt,
#         enhanced_prompt=enhanced,
#         response=response_text,
#     )


# def _combine_responses(tasks: list[TaskDetail], decomposed: bool) -> str:
#     """
#     Merge multiple task responses into one final message for the user.
#     """
#     if not decomposed or len(tasks) == 1:
#         return tasks[0].response

#     parts = []
#     for t in tasks:
#         parts.append(f"### Task {t.task_index + 1} ({t.category})\n\n{t.response}")
#     return "\n\n---\n\n".join(parts)


# async def orchestrate(
#     db: AsyncSession,
#     prompt: str,
#     conversation_id: uuid.UUID | None,
#     compare_mode: bool,
#     user_id: uuid.UUID,
# ) -> ChatResponse:
#     """
#     Main entry point for processing a user prompt.

#     Handles both normal mode and multi-model comparison mode.
#     Saves everything to the database.
#     """
#     # Create or get conversation
#     if conversation_id is None:
#         conv = Conversation(
#             user_id=user_id,
#             title=prompt[:80] + ("..." if len(prompt) > 80 else ""),
#         )
#         db.add(conv)
#         await db.flush()
#         conversation_id = conv.id
#     else:
#         conv = await db.get(Conversation, conversation_id)

#     # Save user message
#     user_msg = Message(
#         conversation_id=conversation_id,
#         role="user",
#         content=prompt,
#         compare_mode=compare_mode,
#     )
#     db.add(user_msg)
#     await db.flush()

#     # --- COMPARE MODE: send to all providers in parallel ---
#     if compare_mode:
#         providers = get_all_providers()

#         async def call_provider(p):
#             try:
#                 content = await p.generate(prompt)
#                 return CompareResponseItem(
#                     provider=p.name,
#                     model=getattr(p, "model", None),
#                     content=content,
#                 )
#             except Exception as e:
#                 return CompareResponseItem(
#                     provider=p.name,
#                     model=getattr(p, "model", None),
#                     content=f"Error: {str(e)}",
#                 )

#         compare_responses = await asyncio.gather(
#             *[call_provider(p) for p in providers]
#         )

#         # Save a placeholder assistant message (user picks best later)
#         assistant_content = "Compare mode: review responses below and click 'Choose Best Response'."
#         assistant_msg = Message(
#             conversation_id=conversation_id,
#             role="assistant",
#             content=assistant_content,
#             compare_mode=True,
#         )
#         db.add(assistant_msg)
#         await db.flush()

#         # Save task and responses to DB
#         task_record = Task(
#             message_id=user_msg.id,
#             task_index=0,
#             original_prompt=prompt,
#             category="general",
#             provider="all",
#             status="completed",
#         )
#         db.add(task_record)
#         await db.flush()

#         for cr in compare_responses:
#             db.add(Response(
#                 task_id=task_record.id,
#                 provider=cr.provider,
#                 model=cr.model,
#                 content=cr.content,
#             ))

#         return ChatResponse(
#             conversation_id=conversation_id,
#             message_id=assistant_msg.id,
#             user_message=prompt,
#             assistant_message=assistant_content,
#             compare_mode=True,
#             compare_responses=list(compare_responses),
#             decomposed=False,
#         )

#     # --- NORMAL MODE: plan, decompose, process in parallel ---
#     decomposed, subtasks = await plan(prompt)

#     # Process all subtasks in parallel using asyncio.gather
#     task_coroutines = [
#         _process_single_task(subtask, idx)
#         for idx, subtask in enumerate(subtasks)
#     ]
#     completed_tasks: list[TaskDetail] = await asyncio.gather(*task_coroutines)

#     # Combine into final response
#     final_response = _combine_responses(completed_tasks, decomposed)

#     # Save assistant message
#     assistant_msg = Message(
#         conversation_id=conversation_id,
#         role="assistant",
#         content=final_response,
#         compare_mode=False,
#     )
#     db.add(assistant_msg)
#     await db.flush()

#     # Save task records to database
#     for td in completed_tasks:
#         task_record = Task(
#             message_id=user_msg.id,
#             task_index=td.task_index,
#             original_prompt=td.original_prompt,
#             enhanced_prompt=td.enhanced_prompt,
#             category=td.category,
#             provider=td.provider,
#             status="completed",
#         )
#         db.add(task_record)
#         await db.flush()

#         db.add(Response(
#             task_id=task_record.id,
#             provider=td.provider,
#             content=td.response,
#         ))

#     return ChatResponse(
#         conversation_id=conversation_id,
#         message_id=assistant_msg.id,
#         user_message=prompt,
#         assistant_message=final_response,
#         compare_mode=False,
#         tasks=completed_tasks,
#         decomposed=decomposed,
#     )

"""
Orchestrator Module
-------------------
Main OneAI orchestration pipeline.

Flow:

User Prompt
    ↓
Planner
    ↓
Subtasks
    ↓
Embedding Classifier
    ↓
Top model / Top 3 models
    ↓
Generation
    ↓
Judge (compare mode only)
    ↓
Final Response
"""

import asyncio
import json
from pathlib import Path

from app.modules.planner import plan
from app.modules.classifier import get_top_models
from app.modules.judge import judge
from app.providers.factory import get_provider


PROJECT_ROOT = Path(__file__).resolve().parents[3]

REGISTRY_PATH = (
    PROJECT_ROOT
    / "models"
    / "model_registery.json"
)


def load_model_registry():
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)["models"]


MODELS = load_model_registry()


def get_model_metadata(model_id: str):
    """
    Find model metadata from the model registry.
    """
    for model in MODELS:
        if model["id"] == model_id:
            return model

    return None


async def generate_with_model(
    prompt: str,
    model_id: str
):
    """
    Generate a response using the exact model selected
    by the embedding classifier.
    """

    model_metadata = get_model_metadata(model_id)

    if not model_metadata:
        raise ValueError(
            f"Model '{model_id}' not found in model_registery.json"
        )

    provider_name = model_metadata["provider"]

    provider = get_provider(provider_name)

    # The registry may contain an API-specific model name.
    # For example:
    #
    # internal id:
    #     groq-oss-120b
    #
    # API model:
    #     openai/gpt-oss-120b

    api_model = (
        model_metadata.get("api_model")
        or model_metadata.get("model")
        or model_id
    )

    response = await provider.generate(
        prompt,
        model=api_model
    )

    return {
        "model_id": model_id,
        "provider": provider_name,
        "content": response
    }


async def process_node(
    task_prompt: str,
    output_type: str,
    compare_mode: bool = False
):
    """
    Process a single planner node.

    Normal mode:
        Run only the #1 model.

    Compare mode:
        Run top 3 models in parallel,
        then pass their responses to judge.py.
    """

    # --------------------------------------------------
    # STEP 1: CLASSIFY
    # --------------------------------------------------

    top_models = get_top_models(
        task_prompt,
        output_type=output_type,
        k=3
    )

    if not top_models:
        return {
            "model_id": None,
            "provider": None,
            "content": "No suitable model found.",
            "candidates": []
        }

    # --------------------------------------------------
    # NORMAL MODE
    # --------------------------------------------------

    if not compare_mode:

        selected_model = top_models[0]

        result = await generate_with_model(
            task_prompt,
            selected_model["model_id"]
        )

        result["similarity_score"] = (
            selected_model.get("similarity_score")
        )

        result["candidates"] = [
            {
                "model_id": selected_model["model_id"],
                "provider": result["provider"],
                "similarity_score": selected_model.get(
                    "similarity_score"
                )
            }
        ]

        return result

    # --------------------------------------------------
    # COMPARE MODE
    # --------------------------------------------------

    generation_tasks = []

    for model in top_models:

        generation_tasks.append(
            generate_with_model(
                task_prompt,
                model["model_id"]
            )
        )

    generated_results = await asyncio.gather(
        *generation_tasks,
        return_exceptions=True
    )

    # Keep only successful generations.
    valid_responses = []

    for result in generated_results:

        if isinstance(result, Exception):
            continue

        valid_responses.append({
            "provider": result["provider"],
            "content": result["content"],
            "model_id": result["model_id"]
        })

    if not valid_responses:
        return {
            "model_id": None,
            "provider": None,
            "content": "All selected models failed to generate a response.",
            "candidates": []
        }

    # --------------------------------------------------
    # JUDGE
    # --------------------------------------------------

    judged_result = await judge(
        original_prompt=task_prompt,
        responses=valid_responses
    )

    # Find model ID corresponding to winning provider/response.
    winning_model_id = None

    for response in valid_responses:

        if (
            response["provider"]
            == judged_result["selected_provider"]
            and response["content"]
            == judged_result["selected_response"]
        ):
            winning_model_id = response["model_id"]
            break

    return {
        "model_id": winning_model_id,
        "provider": judged_result["selected_provider"],
        "content": judged_result["selected_response"],
        "reasoning": judged_result["reasoning"],
        "candidates": valid_responses
    }


async def orchestrate(
    prompt: str,
    compare_mode: bool = False
):
    """
    Main OneAI orchestration function.
    """

    # --------------------------------------------------
    # STEP 1: PLANNER
    # --------------------------------------------------

    plan_result = await plan(prompt)

    needs_decomposition = plan_result[
        "needs_decomposition"
    ]

    nodes = plan_result["nodes"]

    # --------------------------------------------------
    # SIMPLE TASK
    # --------------------------------------------------

    if not needs_decomposition:

        node = nodes[0]

        return await process_node(
            task_prompt=node["task"],
            output_type=node["output_type"],
            compare_mode=compare_mode
        )

    # --------------------------------------------------
    # COMPLEX TASK
    # --------------------------------------------------

    completed = {}

    remaining = nodes.copy()

    while remaining:

        ready_nodes = []

        # Find nodes whose dependencies are completed.
        for node in remaining:

            dependencies = node.get(
                "depends_on",
                []
            )

            if all(
                dependency in completed
                for dependency in dependencies
            ):
                ready_nodes.append(node)

        if not ready_nodes:
            raise RuntimeError(
                "Planner produced an invalid dependency graph."
            )

        generation_tasks = []

        for node in ready_nodes:

            task_prompt = node["task"]

            dependencies = node.get(
                "depends_on",
                []
            )

            # --------------------------------------------------
            # ADD DEPENDENCY RESULTS
            # --------------------------------------------------

            if dependencies:

                dependency_context = "\n\n".join(
                    [
                        (
                            f"Result from {dependency}:\n"
                            f"{completed[dependency]['content']}"
                        )
                        for dependency in dependencies
                    ]
                )

                task_prompt = (
                    f"{task_prompt}\n\n"
                    f"Results from previous tasks:\n"
                    f"{dependency_context}"
                )

            generation_tasks.append(
                process_node(
                    task_prompt=task_prompt,
                    output_type=node["output_type"],
                    compare_mode=compare_mode
                )
            )

        # Independent nodes execute in parallel.
        results = await asyncio.gather(
            *generation_tasks
        )

        for node, result in zip(
            ready_nodes,
            results
        ):

            completed[node["id"]] = result

            remaining.remove(node)

    # --------------------------------------------------
    # FINAL RESPONSE
    # --------------------------------------------------

    ordered_results = []

    for node in nodes:

        node_id = node["id"]

        if node_id in completed:
            ordered_results.append(
                completed[node_id]
            )

    # One final result.
    if len(ordered_results) == 1:
        return ordered_results[0]

    # Multiple task results.
    combined_response = "\n\n".join(
        [
            result["content"]
            for result in ordered_results
            if result.get("content")
        ]
    )

    return {
        "model_id": "multiple",
        "provider": "multiple",
        "content": combined_response,
        "tasks": ordered_results
    }