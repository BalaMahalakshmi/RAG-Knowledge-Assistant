import {
  BrainCircuit,
  Plus,
  MessageSquare,
  Trash2,
  FileText,
  PanelLeftClose,
  PanelLeftOpen,
} from "lucide-react";

import type { Conversation } from "../types/chat";

interface Props {
  documentId: string;
  setDocumentId: (value: string) => void;
  conversations: Conversation[];
  activeConversationId: string | null;
  onNewChat: () => void;
  onSelectConversation: (id: string) => void;
  onDeleteConversation: (id: string) => void;
  collapsed: boolean;
  onToggle: () => void;
}

export default function Sidebar({
  documentId,
  setDocumentId,
  conversations,
  activeConversationId,
  onNewChat,
  onSelectConversation,
  onDeleteConversation,
  collapsed,
  onToggle,
}: Props) {
  return (
    <aside className={`sidebar ${collapsed ? "sidebar-collapsed" : ""}`}>
      <div className="sidebar-brand">
        <div className="brand-symbol">
          <BrainCircuit size={25} />
        </div>

        {!collapsed && (
          <div className="brand-text">
            <strong>Neural Knowledge</strong>
            <span>AI DOCUMENT ASSISTANT</span>
          </div>
        )}

        <button
          className="sidebar-toggle"
          onClick={onToggle}
          title="Toggle sidebar"
        >
          {collapsed ? (
            <PanelLeftOpen size={18} />
          ) : (
            <PanelLeftClose size={18} />
          )}
        </button>
      </div>

      {!collapsed && (
        <>
          <div className="sidebar-document">
            <label>ACTIVE DOCUMENT ID</label>

            <div className="document-input-wrapper">
              <FileText size={16} />

              <input
                value={documentId}
                onChange={(event) =>
                  setDocumentId(event.target.value)
                }
                placeholder="Paste your document ID"
              />
            </div>

            <span className="document-hint">
              Use the ID returned by your PDF upload API.
            </span>
          </div>

          <button
            className="new-chat-button"
            onClick={onNewChat}
          >
            <Plus size={18} />
            New conversation
          </button>

          <div className="history-heading">
            <span>RECENT CONVERSATIONS</span>
            <span>{conversations.length}</span>
          </div>

          <div className="conversation-list">
            {conversations.length === 0 ? (
              <div className="empty-history">
                <MessageSquare size={22} />
                <p>No conversations yet</p>
              </div>
            ) : (
              conversations.map((conversation) => (
                <div
                  className={`conversation-item ${
                    activeConversationId === conversation.id
                      ? "conversation-active"
                      : ""
                  }`}
                  key={conversation.id}
                >
                  <button
                    className="conversation-select"
                    onClick={() =>
                      onSelectConversation(conversation.id)
                    }
                  >
                    <MessageSquare size={16} />

                    <span>{conversation.title}</span>
                  </button>

                  <button
                    className="delete-conversation"
                    onClick={() =>
                      onDeleteConversation(conversation.id)
                    }
                    title="Delete conversation"
                  >
                    <Trash2 size={15} />
                  </button>
                </div>
              ))
            )}
          </div>
        </>
      )}

      <div className="sidebar-footer">
        <div className="online-indicator" />

        {!collapsed && (
          <div>
            <strong>RAG Engine</strong>
            <span>Conversation workspace</span>
          </div>
        )}
      </div>
    </aside>
  );
}