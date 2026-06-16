/**
 * TypeScript types matching the backend API schemas.
 */

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  compare_mode: boolean;
  created_at: string;
}

export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages: Message[];
}

export interface CompareResponseItem {
  provider: string;
  model: string | null;
  content: string;
}

export interface TaskDetail {
  task_index: number;
  category: string;
  provider: string;
  original_prompt: string;
  enhanced_prompt: string | null;
  response: string;
}

export interface ChatResponse {
  conversation_id: string;
  message_id: string;
  user_message: string;
  assistant_message: string;
  compare_mode: boolean;
  compare_responses: CompareResponseItem[] | null;
  tasks: TaskDetail[] | null;
  decomposed: boolean;
}

export interface JudgeResponse {
  selected_provider: string;
  selected_response: string;
  reasoning: string;
}

/** Local UI state for a chat message (includes compare data) */
export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  compareMode?: boolean;
  compareResponses?: CompareResponseItem[];
  tasks?: TaskDetail[];
  decomposed?: boolean;
  judgeResult?: JudgeResponse;
}
