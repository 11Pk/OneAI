"""
Orchestrator Module
-------------------
Main workflow coordinator. Ties together Planner, Classifier, Router,
Enhancer, and Providers.

Flow:
1. Plan (decompose or not)
2. For each task: classify -> route -> enhance -> generate
3. Run all tasks in parallel with asyncio.gather()
4. Combine responses into final answer
"""

import asyncio
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db_models import Conversation, Message, Response, Task
from app.modules.classifier import classify
from app.modules.enhancer import enhance
from app.modules.planner import plan
from app.modules.router import route
from app.providers.factory import get_all_providers, get_provider
from app.schemas.api import ChatResponse, CompareResponseItem, TaskDetail


async def _process_single_task(
    task_prompt: str,
    task_index: int,
) -> TaskDetail:
    """
    Process one task through the full pipeline:
    classify -> route -> enhance -> generate
    """
    # Step 1: Classify the task
    category = await classify(task_prompt)

    # Step 2: Route to the right provider
    provider_name = route(category)

    # Step 3: Enhance the prompt
    enhanced = await enhance(task_prompt, category)

    # Step 4: Generate response from the routed provider
    provider = get_provider(provider_name)
    response_text = await provider.generate(enhanced)

    return TaskDetail(
        task_index=task_index,
        category=category,
        provider=provider_name,
        original_prompt=task_prompt,
        enhanced_prompt=enhanced,
        response=response_text,
    )


def _combine_responses(tasks: list[TaskDetail], decomposed: bool) -> str:
    """
    Merge multiple task responses into one final message for the user.
    """
    if not decomposed or len(tasks) == 1:
        return tasks[0].response

    parts = []
    for t in tasks:
        parts.append(f"### Task {t.task_index + 1} ({t.category})\n\n{t.response}")
    return "\n\n---\n\n".join(parts)


async def orchestrate(
    db: AsyncSession,
    prompt: str,
    conversation_id: uuid.UUID | None,
    compare_mode: bool,
    user_id: uuid.UUID,
) -> ChatResponse:
    """
    Main entry point for processing a user prompt.

    Handles both normal mode and multi-model comparison mode.
    Saves everything to the database.
    """
    # Create or get conversation
    if conversation_id is None:
        conv = Conversation(
            user_id=user_id,
            title=prompt[:80] + ("..." if len(prompt) > 80 else ""),
        )
        db.add(conv)
        await db.flush()
        conversation_id = conv.id
    else:
        conv = await db.get(Conversation, conversation_id)

    # Save user message
    user_msg = Message(
        conversation_id=conversation_id,
        role="user",
        content=prompt,
        compare_mode=compare_mode,
    )
    db.add(user_msg)
    await db.flush()

    # --- COMPARE MODE: send to all providers in parallel ---
    if compare_mode:
        providers = get_all_providers()

        async def call_provider(p):
            try:
                content = await p.generate(prompt)
                return CompareResponseItem(
                    provider=p.name,
                    model=getattr(p, "model", None),
                    content=content,
                )
            except Exception as e:
                return CompareResponseItem(
                    provider=p.name,
                    model=getattr(p, "model", None),
                    content=f"Error: {str(e)}",
                )

        compare_responses = await asyncio.gather(
            *[call_provider(p) for p in providers]
        )

        # Save a placeholder assistant message (user picks best later)
        assistant_content = "Compare mode: review responses below and click 'Choose Best Response'."
        assistant_msg = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=assistant_content,
            compare_mode=True,
        )
        db.add(assistant_msg)
        await db.flush()

        # Save task and responses to DB
        task_record = Task(
            message_id=user_msg.id,
            task_index=0,
            original_prompt=prompt,
            category="general",
            provider="all",
            status="completed",
        )
        db.add(task_record)
        await db.flush()

        for cr in compare_responses:
            db.add(Response(
                task_id=task_record.id,
                provider=cr.provider,
                model=cr.model,
                content=cr.content,
            ))

        return ChatResponse(
            conversation_id=conversation_id,
            message_id=assistant_msg.id,
            user_message=prompt,
            assistant_message=assistant_content,
            compare_mode=True,
            compare_responses=list(compare_responses),
            decomposed=False,
        )

    # --- NORMAL MODE: plan, decompose, process in parallel ---
    decomposed, subtasks = await plan(prompt)

    # Process all subtasks in parallel using asyncio.gather
    task_coroutines = [
        _process_single_task(subtask, idx)
        for idx, subtask in enumerate(subtasks)
    ]
    completed_tasks: list[TaskDetail] = await asyncio.gather(*task_coroutines)

    # Combine into final response
    final_response = _combine_responses(completed_tasks, decomposed)

    # Save assistant message
    assistant_msg = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=final_response,
        compare_mode=False,
    )
    db.add(assistant_msg)
    await db.flush()

    # Save task records to database
    for td in completed_tasks:
        task_record = Task(
            message_id=user_msg.id,
            task_index=td.task_index,
            original_prompt=td.original_prompt,
            enhanced_prompt=td.enhanced_prompt,
            category=td.category,
            provider=td.provider,
            status="completed",
        )
        db.add(task_record)
        await db.flush()

        db.add(Response(
            task_id=task_record.id,
            provider=td.provider,
            content=td.response,
        ))

    return ChatResponse(
        conversation_id=conversation_id,
        message_id=assistant_msg.id,
        user_message=prompt,
        assistant_message=final_response,
        compare_mode=False,
        tasks=completed_tasks,
        decomposed=decomposed,
    )
