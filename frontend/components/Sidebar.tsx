"use client";

/**
 * Sidebar - conversation history and new chat button.
 * Collapsible on mobile.
 */

import type { Conversation } from "@/lib/types";

interface SidebarProps {
  conversations: Conversation[];
  activeId: string | null;
  isOpen: boolean;
  onSelect: (id: string) => void;
  onNewChat: () => void;
  onDelete: (id: string) => void;
  onClose: () => void;
}

export default function Sidebar({
  conversations,
  activeId,
  isOpen,
  onSelect,
  onNewChat,
  onDelete,
  onClose,
}: SidebarProps) {
  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/30 z-40 md:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={`
          fixed md:static inset-y-0 left-0 z-50
          w-64 bg-gray-50 border-r border-gray-200
          flex flex-col transition-transform duration-200
          ${isOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"}
        `}
      >
        {/* Header */}
        <div className="p-4 border-b border-gray-200">
          <button
            onClick={onNewChat}
            className="w-full px-4 py-2.5 bg-white border border-gray-300 rounded-lg
                       text-sm font-medium hover:bg-gray-100 transition-colors"
          >
            + New Chat
          </button>
        </div>

        {/* Conversation list */}
        <div className="flex-1 overflow-y-auto chat-scroll p-2">
          {conversations.length === 0 && (
            <p className="text-xs text-gray-400 text-center mt-4">
              No conversations yet
            </p>
          )}
          {conversations.map((conv) => (
            <div
              key={conv.id}
              className={`
                group flex items-center justify-between px-3 py-2 rounded-lg cursor-pointer
                text-sm truncate mb-1
                ${activeId === conv.id ? "bg-gray-200" : "hover:bg-gray-100"}
              `}
            >
              <span
                className="truncate flex-1"
                onClick={() => {
                  onSelect(conv.id);
                  onClose();
                }}
              >
                {conv.title}
              </span>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete(conv.id);
                }}
                className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500 ml-2 text-xs"
                title="Delete"
              >
                ✕
              </button>
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200">
          <p className="text-xs text-gray-400 text-center">OneAI v1.0</p>
        </div>
      </aside>
    </>
  );
}
