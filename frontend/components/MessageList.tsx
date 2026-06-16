"use client";

/**
 * MessageList - displays the chat conversation.
 * Renders user/assistant messages, compare panels, and task details.
 */

import ReactMarkdown from "react-markdown";
import type { ChatMessage } from "@/lib/types";
import ComparePanel from "./ComparePanel";
import LoadingIndicator from "./LoadingIndicator";

interface MessageListProps {
  messages: ChatMessage[];
  isLoading: boolean;
  onJudgeComplete: (messageId: string, result: import("@/lib/types").JudgeResponse) => void;
}

export default function MessageList({
  messages,
  isLoading,
  onJudgeComplete,
}: MessageListProps) {
  if (messages.length === 0 && !isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center max-w-md px-4">
          <h2 className="text-2xl font-semibold text-gray-800 mb-2">
            OneAI Orchestration
          </h2>
          <p className="text-gray-500 text-sm">
            Enter a prompt and the system will intelligently route it to the
            best AI model. Enable comparison mode to see responses from all
            models side by side.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto chat-scroll">
      <div className="max-w-3xl mx-auto px-4 py-6 space-y-6">
        {messages.map((msg, idx) => {
          const isUser = msg.role === "user";
          // Find the user prompt before a compare-mode assistant message
          const prevUserMsg = !isUser ? messages[idx - 1] : null;

          return (
            <div key={msg.id} className="message-animate">
              {isUser ? (
                /* User message - right aligned bubble */
                <div className="flex justify-end">
                  <div className="bg-gray-900 text-white px-4 py-3 rounded-2xl rounded-br-md max-w-[85%] text-sm">
                    {msg.content}
                  </div>
                </div>
              ) : msg.compareMode && msg.compareResponses ? (
                /* Compare mode - show all model responses */
                <ComparePanel
                  messageId={msg.id}
                  originalPrompt={prevUserMsg?.content || ""}
                  responses={msg.compareResponses}
                  onJudgeComplete={(result) => onJudgeComplete(msg.id, result)}
                  existingJudge={msg.judgeResult}
                />
              ) : (
                /* Normal assistant response */
                <div className="space-y-3">
                  <div className="prose prose-sm max-w-none text-gray-800">
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                  </div>

                  {/* Show task breakdown if prompt was decomposed */}
                  {msg.decomposed && msg.tasks && msg.tasks.length > 1 && (
                    <details className="text-xs">
                      <summary className="cursor-pointer text-gray-400 hover:text-gray-600">
                        View {msg.tasks.length} subtasks
                      </summary>
                      <div className="mt-2 space-y-2">
                        {msg.tasks.map((t) => (
                          <div
                            key={t.task_index}
                            className="p-2 bg-gray-50 rounded border border-gray-100"
                          >
                            <p className="font-medium text-gray-600">
                              Task {t.task_index + 1}: {t.category} → {t.provider}
                            </p>
                            <p className="text-gray-500 mt-1 truncate">
                              {t.original_prompt}
                            </p>
                          </div>
                        ))}
                      </div>
                    </details>
                  )}
                </div>
              )}
            </div>
          );
        })}

        {isLoading && (
          <div className="py-4">
            <LoadingIndicator text="Orchestrating AI response..." />
          </div>
        )}
      </div>
    </div>
  );
}
