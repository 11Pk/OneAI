"use client";

/**
 * ChatInput - prompt input box at the bottom (like ChatGPT).
 * Includes compare mode toggle and send button.
 */

interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  compareMode: boolean;
  onCompareModeChange: (enabled: boolean) => void;
  isLoading: boolean;
}

export default function ChatInput({
  value,
  onChange,
  onSend,
  compareMode,
  onCompareModeChange,
  isLoading,
}: ChatInputProps) {
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!isLoading && value.trim()) onSend();
    }
  };

  return (
    <div className="border-t border-gray-200 bg-white p-4">
      <div className="max-w-3xl mx-auto">
        {/* Compare mode toggle */}
        <div className="flex items-center gap-2 mb-2">
          <label className="flex items-center gap-2 text-xs text-gray-500 cursor-pointer">
            <input
              type="checkbox"
              checked={compareMode}
              onChange={(e) => onCompareModeChange(e.target.checked)}
              className="rounded border-gray-300"
            />
            Multi-Model Comparison Mode
          </label>
          {compareMode && (
            <span className="text-xs text-blue-500">
              Sends to OpenRouter, Gemini & Groq
            </span>
          )}
        </div>

        {/* Input area */}
        <div className="flex items-end gap-2 bg-gray-50 border border-gray-300 rounded-xl p-2">
          <textarea
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Send a message..."
            rows={1}
            disabled={isLoading}
            className="flex-1 resize-none bg-transparent outline-none text-sm px-2 py-2
                       max-h-32 placeholder:text-gray-400 disabled:opacity-50"
          />
          <button
            onClick={onSend}
            disabled={isLoading || !value.trim()}
            className="px-4 py-2 bg-gray-900 text-white text-sm rounded-lg
                       hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed
                       transition-colors"
          >
            {isLoading ? "..." : "Send"}
          </button>
        </div>

        <p className="text-[10px] text-gray-400 text-center mt-2">
          OneAI orchestrates your prompt across multiple AI models intelligently.
        </p>
      </div>
    </div>
  );
}
