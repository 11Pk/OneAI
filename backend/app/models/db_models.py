"""
SQLAlchemy database models matching schema.sql tables.
Each class maps to one database table.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), default="User")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    conversations: Mapped[list["Conversation"]] = relationship(back_populates="user")


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(500), default="New Chat")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship(back_populates="conversations")
    messages: Mapped[list["Message"]] = relationship(back_populates="conversation", order_by="Message.created_at")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # 'user' or 'assistant'
    content: Mapped[str] = mapped_column(Text, nullable=False)
    compare_mode: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")
    tasks: Mapped[list["Task"]] = relationship(back_populates="message")
    judge_results: Mapped[list["JudgeResult"]] = relationship(back_populates="message")


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("messages.id"), nullable=False)
    task_index: Mapped[int] = mapped_column(Integer, default=0)
    original_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    enhanced_prompt: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(50), default="general")
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    message: Mapped["Message"] = relationship(back_populates="tasks")
    responses: Mapped[list["Response"]] = relationship(back_populates="task")


class Response(Base):
    __tablename__ = "responses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str | None] = mapped_column(String(100))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    task: Mapped["Task"] = relationship(back_populates="responses")


class JudgeResult(Base):
    __tablename__ = "judge_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("messages.id"), nullable=False)
    selected_provider: Mapped[str] = mapped_column(String(50), nullable=False)
    selected_response: Mapped[str] = mapped_column(Text, nullable=False)
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    message: Mapped["Message"] = relationship(back_populates="judge_results")



# The PostgreSQL Schema looks like the following:
# -- Enable UUID generation (optional if app generates UUIDs)
# CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

# -- =========================
# -- USERS
# -- =========================

# CREATE TABLE users (
#     id UUID PRIMARY KEY,
#     email VARCHAR(255) UNIQUE NOT NULL,
#     name VARCHAR(255) DEFAULT 'User',
#     created_at TIMESTAMPTZ DEFAULT NOW()
# );

# -- =========================
# -- CONVERSATIONS
# -- =========================

# CREATE TABLE conversations (
#     id UUID PRIMARY KEY,
#     user_id UUID NOT NULL,
#     title VARCHAR(500) DEFAULT 'New Chat',
#     created_at TIMESTAMPTZ DEFAULT NOW(),
#     updated_at TIMESTAMPTZ DEFAULT NOW(),

#     CONSTRAINT fk_conversation_user
#         FOREIGN KEY (user_id)
#         REFERENCES users(id)
# );

# -- =========================
# -- MESSAGES
# -- =========================

# CREATE TABLE messages (
#     id UUID PRIMARY KEY,
#     conversation_id UUID NOT NULL,
#     role VARCHAR(20) NOT NULL,
#     content TEXT NOT NULL,
#     compare_mode BOOLEAN DEFAULT FALSE,
#     created_at TIMESTAMPTZ DEFAULT NOW(),

#     CONSTRAINT fk_message_conversation
#         FOREIGN KEY (conversation_id)
#         REFERENCES conversations(id)
# );

# -- =========================
# -- TASKS
# -- =========================

# CREATE TABLE tasks (
#     id UUID PRIMARY KEY,
#     message_id UUID NOT NULL,
#     task_index INTEGER DEFAULT 0,
#     original_prompt TEXT NOT NULL,
#     enhanced_prompt TEXT,
#     category VARCHAR(50) DEFAULT 'general',
#     provider VARCHAR(50) NOT NULL,
#     status VARCHAR(20) DEFAULT 'pending',
#     created_at TIMESTAMPTZ DEFAULT NOW(),

#     CONSTRAINT fk_task_message
#         FOREIGN KEY (message_id)
#         REFERENCES messages(id)
# );

# -- =========================
# -- RESPONSES
# -- =========================

# CREATE TABLE responses (
#     id UUID PRIMARY KEY,
#     task_id UUID NOT NULL,
#     provider VARCHAR(50) NOT NULL,
#     model VARCHAR(100),
#     content TEXT NOT NULL,
#     created_at TIMESTAMPTZ DEFAULT NOW(),

#     CONSTRAINT fk_response_task
#         FOREIGN KEY (task_id)
#         REFERENCES tasks(id)
# );

# -- =========================
# -- JUDGE RESULTS
# -- =========================

# CREATE TABLE judge_results (
#     id UUID PRIMARY KEY,
#     message_id UUID NOT NULL,
#     selected_provider VARCHAR(50) NOT NULL,
#     selected_response TEXT NOT NULL,
#     reasoning TEXT NOT NULL,
#     created_at TIMESTAMPTZ DEFAULT NOW(),

#     CONSTRAINT fk_judge_message
#         FOREIGN KEY (message_id)
#         REFERENCES messages(id)
# );