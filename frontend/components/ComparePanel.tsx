"use client";

/**
 * ComparePanel - shows all model responses side by side in compare mode.
 * Includes "Choose Best Response" button that calls the Judge.
 */

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import type { CompareResponseItem, JudgeResponse } from "@/lib/types";
import { judgeResponses } from "@/lib/api";
import LoadingIndicator from "./LoadingIndicator";

interface ComparePanelProps {
  messageId: string;
  originalPrompt: string;
  responses: CompareResponseItem[];
  onJudgeComplete: (result: JudgeResponse) => void;
  existingJudge?: JudgeResponse;
}

const PROVIDER_COLORS: Record<string, string> = {
  openrouter: "border-blue-400 bg-blue-50",
  gemini: "border-green-400 bg-green-50",
  groq: "border-orange-400 bg-orange-50",
};

export default function ComparePanel({
  messageId,
  originalPrompt,
  responses,
  onJudgeComplete,
  existingJudge,
}: ComparePanelProps) {
  const [isJudging, setIsJudging] = useState(false);
  const [judgeResult, setJudgeResult] = useState<JudgeResponse | undefined>(
    existingJudge
  );

  const handleChooseBest = async () => {
    setIsJudging(true);
    try {
      const result = await judgeResponses(messageId, originalPrompt, responses);
      setJudgeResult(result);
      onJudgeComplete(result);
    } catch (err) {
      console.error("Judge failed:", err);
    } finally {
      setIsJudging(false);
    }
  };

  // If judge already picked a winner, show that prominently
  if (judgeResult) {
    return (
      <div className="space-y-4 message-animate">
        <div className="p-4 border-2 border-purple-400 bg-purple-50 rounded-xl">
          <p className="text-xs font-semibold text-purple-600 mb-2">
            Best Response — {judgeResult.selected_provider}
          </p>
          <div className="prose prose-sm max-w-none">
            <ReactMarkdown>{judgeResult.selected_response}</ReactMarkdown>
          </div>
        </div>
        <div className="p-3 bg-gray-50 rounded-lg border border-gray-200">
          <p className="text-xs font-semibold text-gray-500 mb-1">Judge Reasoning</p>
          <p className="text-sm text-gray-700">{judgeResult.reasoning}</p>
        </div>

        {/* Still show all responses below for reference */}
        <details className="text-xs text-gray-400">
          <summary className="cursor-pointer hover:text-gray-600">
            View all {responses.length} responses
          </summary>
          <div className="grid gap-3 mt-2">
            {responses.map((r) => (
              <div
                key={r.provider}
                className={`p-3 rounded-lg border ${PROVIDER_COLORS[r.provider] || "border-gray-200"}`}
              >
                <p className="font-semibold text-xs mb-1 capitalize">{r.provider}</p>
                <div className="prose prose-sm max-w-none text-sm">
                  <ReactMarkdown>{r.content}</ReactMarkdown>
                </div>
              </div>
            ))}
          </div>
        </details>
      </div>
    );
  }

  return (
    <div className="space-y-4 message-animate">
      <p className="text-sm text-gray-500">
        Compare mode — review responses from each model:
      </p>

      <div className="grid gap-3 md:grid-cols-1 lg:grid-cols-1">
        {responses.map((r) => (
          <div
            key={r.provider}
            className={`p-4 rounded-xl border-2 ${PROVIDER_COLORS[r.provider] || "border-gray-200 bg-white"}`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold uppercase tracking-wide capitalize">
                {r.provider}
              </span>
              {r.model && (
                <span className="text-[10px] text-gray-400">{r.model}</span>
              )}
            </div>
            <div className="prose prose-sm max-w-none">
              <ReactMarkdown>{r.content}</ReactMarkdown>
            </div>
          </div>
        ))}
      </div>

      {isJudging ? (
        <LoadingIndicator text="Judge is evaluating responses..." />
      ) : (
        <button
          onClick={handleChooseBest}
          className="w-full py-2.5 bg-purple-600 text-white text-sm font-medium rounded-lg
                     hover:bg-purple-700 transition-colors"
        >
          Choose Best Response
        </button>
      )}
    </div>
  );
}
