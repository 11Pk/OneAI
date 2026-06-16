"""
API Routes
----------
All HTTP endpoints for the OneAI platform.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import get_db
from app.models.db_models import Conversation, JudgeResult, Message
from app.modules.judge import judge
from app.modules.orchestrator import orchestrate
from app.schemas.api import (
    ChatRequest,
    ChatResponse,
    ConversationOut,
    JudgeRequest,
    JudgeResponse,
    MessageOut,
)

router = APIRouter()


@router.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "ok", "service": "OneAI Orchestration Platform"}


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """
    Main chat endpoint. User sends a prompt, system orchestrates AI processing.

    - Creates new conversation if conversation_id is null
    - Runs planner, classifier, router, enhancer pipeline
    - Returns combined response (or compare mode responses)
    """
    user_id = uuid.UUID(settings.default_user_id)

    result = await orchestrate(
        db=db,
        prompt=request.prompt,
        conversation_id=request.conversation_id,
        compare_mode=request.compare_mode,
        user_id=user_id,
    )
    return result


@router.post("/judge", response_model=JudgeResponse)
async def judge_responses(request: JudgeRequest, db: AsyncSession = Depends(get_db)):
    """
    Compare mode: user clicks 'Choose Best Response'.
    Sends all responses to the Judge LLM to pick the winner.
    """
    responses_dict = [
        {"provider": r.provider, "content": r.content}
        for r in request.responses
    ]

    result = await judge(request.original_prompt, responses_dict)

    # Save judge result to database
    judge_record = JudgeResult(
        message_id=request.message_id,
        selected_provider=result["selected_provider"],
        selected_response=result["selected_response"],
        reasoning=result["reasoning"],
    )
    db.add(judge_record)

    # Update the assistant message with the winning response
    msg = await db.get(Message, request.message_id)
    if msg:
        msg.content = f"**Best Response ({result['selected_provider']})**\n\n{result['selected_response']}\n\n---\n**Judge Reasoning:** {result['reasoning']}"

    return JudgeResponse(
        selected_provider=result["selected_provider"],
        selected_response=result["selected_response"],
        reasoning=result["reasoning"],
    )


@router.get("/conversations", response_model=list[ConversationOut])
async def list_conversations(db: AsyncSession = Depends(get_db)):
    """Get all conversations for the default user (sidebar history)."""
    user_id = uuid.UUID(settings.default_user_id)

    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(Conversation.updated_at.desc())
    )
    conversations = result.scalars().all()

    return [
        ConversationOut(
            id=c.id,
            title=c.title,
            created_at=c.created_at,
            updated_at=c.updated_at,
            messages=[],
        )
        for c in conversations
    ]


@router.get("/conversations/{conversation_id}", response_model=ConversationOut)
async def get_conversation(conversation_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get one conversation with all its messages."""
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.id == conversation_id)
    )
    conv = result.scalar_one_or_none()

    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return ConversationOut(
        id=conv.id,
        title=conv.title,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        messages=[
            MessageOut(
                id=m.id,
                role=m.role,
                content=m.content,
                compare_mode=m.compare_mode,
                created_at=m.created_at,
            )
            for m in conv.messages
        ],
    )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Delete a conversation and all its messages."""
    conv = await db.get(Conversation, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await db.delete(conv)
    return {"status": "deleted"}
