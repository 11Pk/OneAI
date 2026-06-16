"""
Pydantic schemas for API request/response validation.
These define the shape of JSON data going in and out of the API.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# --- Request schemas ---

class ChatRequest(BaseModel):
    """User sends a prompt to start or continue a chat."""
    prompt: str = Field(..., min_length=1, description="The user's message")
    conversation_id: UUID | None = Field(None, description="Existing conversation ID, or null for new chat")
    compare_mode: bool = Field(False, description="If true, send to all models and compare")


class JudgeRequest(BaseModel):
    """User asks the judge to pick the best response from compare mode."""
    message_id: UUID
    original_prompt: str
    responses: list["CompareResponseItem"]


class CompareResponseItem(BaseModel):
    """One model's response in compare mode."""
    provider: str
    model: str | None = None
    content: str


# --- Response schemas ---

class TaskDetail(BaseModel):
    """Details about one subtask that was processed."""
    task_index: int
    category: str
    provider: str
    original_prompt: str
    enhanced_prompt: str | None
    response: str


class ChatResponse(BaseModel):
    """Full response returned after orchestration completes."""
    conversation_id: UUID
    message_id: UUID
    user_message: str
    assistant_message: str
    compare_mode: bool
    # In compare mode, each provider's response is listed separately
    compare_responses: list[CompareResponseItem] | None = None
    # In normal mode, shows how the prompt was broken down
    tasks: list[TaskDetail] | None = None
    decomposed: bool = False


class MessageOut(BaseModel):
    id: UUID
    role: str
    content: str
    compare_mode: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationOut(BaseModel):
    id: UUID
    title: str
    created_at: datetime
    updated_at: datetime
    messages: list[MessageOut] = []

    class Config:
        from_attributes = True


class JudgeResponse(BaseModel):
    """Result after the judge picks the best response."""
    selected_provider: str
    selected_response: str
    reasoning: str
