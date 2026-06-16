"use client";

/**
 * LoadingIndicator - animated dots while waiting for AI response.
 */

export default function LoadingIndicator({ text = "Thinking" }: { text?: string }) {
  return (
    <div className="flex items-center gap-2 text-gray-500 text-sm message-animate">
      <div className="flex gap-1">
        <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
        <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
        <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
      </div>
      <span>{text}</span>
    </div>
  );
}
