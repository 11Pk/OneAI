"use client";

/**
 * Main Chat Page - the heart of the OneAI frontend.
 *
 * Manages:
 * - Sidebar with conversation history
 * - Message list (chat area)
 * - Input box with compare mode toggle
 * - API calls to backend orchestrator
 */

import { useCallback, useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";
import MessageList from "@/components/MessageList";
import ChatInput from "@/components/ChatInput";
import {
  sendChat,
  getConversations,
  getConversation,
  deleteConversation,
} from "@/lib/api";
import type { ChatMessage, Conversation, JudgeResponse } from "@/lib/types";

export default function Home() {
  // --- State ---
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [compareMode, setCompareMode] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // --- Load conversation list on mount ---
  const loadConversations = useCallback(async () => {
    try {
      const convs = await getConversations();
      setConversations(convs);
    } catch (err) {
      console.error("Failed to load conversations:", err);
    }
  }, []);

  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  // --- Load messages when selecting a conversation ---
  const selectConversation = async (id: string) => {
    try {
      const conv = await getConversation(id);
      setActiveConversationId(id);
      setMessages(
        conv.messages.map((m) => ({
          id: m.id,
          role: m.role as "user" | "assistant",
          content: m.content,
          compareMode: m.compare_mode,
        }))
      );
    } catch (err) {
      console.error("Failed to load conversation:", err);
    }
  };

  // --- Start a new chat ---
  const handleNewChat = () => {
    setActiveConversationId(null);
    setMessages([]);
    setInput("");
    setSidebarOpen(false);
  };

  // --- Delete a conversation ---
  const handleDelete = async (id: string) => {
    try {
      await deleteConversation(id);
      if (activeConversationId === id) handleNewChat();
      loadConversations();
    } catch (err) {
      console.error("Failed to delete:", err);
    }
  };

  // --- Send a message ---
  const handleSend = async () => {
    const prompt = input.trim();
    if (!prompt || isLoading) return;

    // Add user message to UI immediately
    const userMsg: ChatMessage = {
      id: `temp-${Date.now()}`,
      role: "user",
      content: prompt,
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await sendChat(prompt, activeConversationId, compareMode);

      // Update conversation ID if new
      if (!activeConversationId) {
        setActiveConversationId(response.conversation_id);
      }

      // Build assistant message
      const assistantMsg: ChatMessage = {
        id: response.message_id,
        role: "assistant",
        content: response.assistant_message,
        compareMode: response.compare_mode,
        compareResponses: response.compare_responses || undefined,
        tasks: response.tasks || undefined,
        decomposed: response.decomposed,
      };

      setMessages((prev) => [...prev, assistantMsg]);
      loadConversations(); // Refresh sidebar titles
    } catch (err) {
      const errorMsg: ChatMessage = {
        id: `err-${Date.now()}`,
        role: "assistant",
        content: `Error: ${err instanceof Error ? err.message : "Something went wrong"}`,
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  // --- Handle judge result ---
  const handleJudgeComplete = (messageId: string, result: JudgeResponse) => {
    setMessages((prev) =>
      prev.map((m) =>
        m.id === messageId ? { ...m, judgeResult: result } : m
      )
    );
  };

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <Sidebar
        conversations={conversations}
        activeId={activeConversationId}
        isOpen={sidebarOpen}
        onSelect={selectConversation}
        onNewChat={handleNewChat}
        onDelete={handleDelete}
        onClose={() => setSidebarOpen(false)}
      />

      {/* Main chat area */}
      <main className="flex-1 flex flex-col min-w-0">
        {/* Top bar */}
        <header className="flex items-center gap-3 px-4 py-3 border-b border-gray-200">
          <button
            onClick={() => setSidebarOpen(true)}
            className="md:hidden p-1 text-gray-500 hover:text-gray-800"
          >
            ☰
          </button>
          <h1 className="text-sm font-semibold text-gray-700 truncate">
            {activeConversationId
              ? conversations.find((c) => c.id === activeConversationId)?.title ||
                "Chat"
              : "OneAI"}
          </h1>
        </header>

        {/* Messages */}
        <MessageList
          messages={messages}
          isLoading={isLoading}
          onJudgeComplete={handleJudgeComplete}
        />

        {/* Input */}
        <ChatInput
          value={input}
          onChange={setInput}
          onSend={handleSend}
          compareMode={compareMode}
          onCompareModeChange={setCompareMode}
          isLoading={isLoading}
        />
      </main>
    </div>
  );
}
