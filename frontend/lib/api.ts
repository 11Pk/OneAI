/**
 * API client - all HTTP calls to the FastAPI backend.
 */

import type {
  ChatResponse,
  Conversation,
  CompareResponseItem,
  JudgeResponse,
} from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/** Send a chat message and get orchestrated response */
export async function sendChat(
  prompt: string,
  conversationId: string | null,
  compareMode: boolean
): Promise<ChatResponse> {
  const res = await fetch(`${API_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      prompt,
      conversation_id: conversationId,
      compare_mode: compareMode,
    }),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || "Chat request failed");
  }
  return res.json();
}

/** Ask judge to pick best response in compare mode */
export async function judgeResponses(
  messageId: string,
  originalPrompt: string,
  responses: CompareResponseItem[]
): Promise<JudgeResponse> {
  const res = await fetch(`${API_URL}/api/judge`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message_id: messageId,
      original_prompt: originalPrompt,
      responses,
    }),
  });
  if (!res.ok) throw new Error("Judge request failed");
  return res.json();
}

/** Get all conversations for sidebar */
export async function getConversations(): Promise<Conversation[]> {
  const res = await fetch(`${API_URL}/api/conversations`);
  if (!res.ok) throw new Error("Failed to load conversations");
  return res.json();
}

/** Get one conversation with messages */
export async function getConversation(id: string): Promise<Conversation> {
  const res = await fetch(`${API_URL}/api/conversations/${id}`);
  if (!res.ok) throw new Error("Conversation not found");
  return res.json();
}

/** Delete a conversation */
export async function deleteConversation(id: string): Promise<void> {
  const res = await fetch(`${API_URL}/api/conversations/${id}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete conversation");
}
