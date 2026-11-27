
import { useCallback, useEffect, useState } from "react";

import {
  AlertCircle,
  RefreshCw,
} from "lucide-react";

import Sidebar from "./components/Sidebar";
import ChatHeader from "./components/ChatHeader";
import ChatWindow from "./components/ChatWindow";
import ChatInput from "./components/ChatInput";

import { chatApi } from "./services/api";

import type {
  Conversation,
  Message,
} from "./types/chat";

function App() {
  const [documentId, setDocumentId] = useState("");

  const [conversations, setConversations] =
    useState<Conversation[]>([]);

  const [activeConversationId, setActiveConversationId] =
    useState<string | null>(null);

  const [messages, setMessages] = useState<Message[]>([]);

  const [loading, setLoading] = useState(false);

  const [error, setError] = useState("");

  const [collapsed, setCollapsed] = useState(false);

  const [loadingHistory, setLoadingHistory] = useState(false);

  const hasValidDocumentId =
    /^[a-f0-9]{32}$/.test(documentId.trim());

  const refreshConversations = useCallback(async () => {
    if (!hasValidDocumentId) {
      setConversations([]);
      return;
    }

    try {
      const response = await chatApi.getConversations(
        documentId.trim()
      );

      setConversations(response.conversations);
    } catch (err) {
      console.error("Unable to load conversations:", err);
      setError("Unable to load conversation history.");
    }
  }, [documentId, hasValidDocumentId]);

  useEffect(() => {
    setActiveConversationId(null);
    setMessages([]);
    setError("");

    if (hasValidDocumentId) {
      void refreshConversations();
    } else {
      setConversations([]);
    }
  }, [documentId, hasValidDocumentId, refreshConversations]);

  const handleNewChat = () => {
    setActiveConversationId(null);
    setMessages([]);
    setError("");
  };

  const handleSelectConversation = async (
    conversationId: string
  ) => {
    if (loading || loadingHistory) return;

    setLoadingHistory(true);
    setError("");

    try {
      const response = await chatApi.getConversationHistory(
        conversationId
      );

      if (
        !response.conversation ||
        response.conversation.document_id !== documentId.trim()
      ) {
        throw new Error(
          "This conversation belongs to another document or could not be loaded."
        );
      }

      setActiveConversationId(conversationId);
      setMessages(response.messages);
    } catch (err) {
      console.error("Unable to load conversation:", err);
      setError("Unable to load this conversation.");
    } finally {
      setLoadingHistory(false);
    }
  };

  const handleDeleteConversation = async (
    conversationId: string
  ) => {
    if (loading) return;

    const confirmed = window.confirm(
      "Delete this conversation and its message history?"
    );

    if (!confirmed) return;

    try {
      await chatApi.deleteConversation(conversationId);

      if (activeConversationId === conversationId) {
        setActiveConversationId(null);
        setMessages([]);
      }

      await refreshConversations();
    } catch (err) {
      console.error("Unable to delete conversation:", err);
      setError("Unable to delete this conversation.");
    }
  };

  const handleSendMessage = async (question: string) => {
    if (!hasValidDocumentId || loading) return;

    setLoading(true);
    setError("");

    const optimisticMessage: Message = {
      role: "user",
      content: question,
      created_at: new Date().toISOString(),
    };

    setMessages((previous) => [
      ...previous,
      optimisticMessage,
    ]);

    try {
      const response = await chatApi.askQuestion({
        document_id: documentId.trim(),
        question,
        top_k: 3,
        ...(activeConversationId
          ? { conversation_id: activeConversationId }
          : {}),
      });

      setActiveConversationId(response.conversation_id);

      const assistantMessage: Message = {
        id: response.assistant_message_id,
        role: "assistant",
        content: response.answer,
        sources: response.sources,
        created_at: new Date().toISOString(),
      };

      setMessages((previous) => [
        ...previous,
        assistantMessage,
      ]);

      await refreshConversations();
    } catch (err: any) {
      console.error("Chat request failed:", err);

      const detail =
        err.response?.data?.detail ||
        "Something went wrong. Please try again.";

      setError(detail);

      // Remove the optimistic user message if
      // the server did not accept the request.
      setMessages((previous) =>
        previous.filter(
          (message) => message !== optimisticMessage
        )
      );
    } finally {
      setLoading(false);
    }
  };

  const handleDocumentChange = (value: string) => {
    setDocumentId(value);
  };

  return (
    <div className="app-shell">
      <Sidebar
        documentId={documentId}
        setDocumentId={handleDocumentChange}
        conversations={conversations}
        activeConversationId={activeConversationId}
        onNewChat={handleNewChat}
        onSelectConversation={handleSelectConversation}
        onDeleteConversation={handleDeleteConversation}
        collapsed={collapsed}
        onToggle={() => setCollapsed((value) => !value)}
      />

      <main className="main-workspace">
        <ChatHeader
          title={
            activeConversationId
              ? conversations.find(
                (item) => item.id === activeConversationId
              )?.title || "Document conversation"
              : "Your AI study companion"
          }
          documentId={documentId}
        />

        {error && (
          <div className="error-banner">
            <AlertCircle size={17} />
            <span>{error}</span>

            <button onClick={() => setError("")}>
              Dismiss
            </button>
          </div>
        )}

        {loadingHistory && (
          <div className="history-loading">
            <RefreshCw size={16} className="spin" />
            Loading conversation...
          </div>
        )}

        <ChatWindow
          messages={messages}
          loading={loading}
          onSuggestion={handleSendMessage}
          hasDocument={hasValidDocumentId}
        />

        <ChatInput
          onSend={handleSendMessage}
          loading={loading || loadingHistory}
          disabled={!hasValidDocumentId}
        />
      </main>
    </div>
  );
}

export default App;
