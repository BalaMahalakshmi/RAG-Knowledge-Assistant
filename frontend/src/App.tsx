import { useCallback, useState } from "react";

import { AlertCircle, RefreshCw } from "lucide-react";

import Sidebar from "./components/Sidebar";
import ChatHeader from "./components/ChatHeader";
import ChatWindow from "./components/ChatWindow";
import ChatInput from "./components/ChatInput";

import type { DocumentUploadResponse } from "./services/documentApi";
import { chatApi } from "./services/api";

import type { Conversation, Message } from "./types/chat";

interface ApiError {
  response?: {
    data?: {
      detail?: string | { message?: string };
      message?: string;
    };
  };
  message?: string;
}

function getErrorMessage(error: unknown, fallback: string): string {
  if (typeof error === "object" && error !== null) {
    const apiError = error as ApiError;
    const detail = apiError.response?.data?.detail;

    if (typeof detail === "string") {
      return detail;
    }

    if (detail && typeof detail === "object" && detail.message) {
      return detail.message;
    }

    const message = apiError.response?.data?.message;

    if (message) {
      return message;
    }

    if (apiError.message) {
      return apiError.message;
    }
  }

  return fallback;
}

function App() {
  // =========================================
  // DOCUMENT STATE
  // =========================================

  const [documentId, setDocumentId] = useState("");
  const [documentName, setDocumentName] = useState("");

  // =========================================
  // CONVERSATION STATE
  // =========================================

  const [conversations, setConversations] = useState<Conversation[]>([]);

  const [activeConversationId, setActiveConversationId] = useState<
    string | null
  >(null);

  const [messages, setMessages] = useState<Message[]>([]);

  // =========================================
  // LOADING AND ERROR STATE
  // =========================================

  const [loading, setLoading] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);

  const [error, setError] = useState("");

  // =========================================
  // SIDEBAR STATE
  // =========================================

  const [collapsed, setCollapsed] = useState(false);

  // =========================================
  // DOCUMENT VALIDATION
  // =========================================

  const hasValidDocumentId = /^[a-f0-9]{32}$/i.test(documentId.trim());

  // =========================================
  // REFRESH CONVERSATIONS
  // =========================================

  const refreshConversations = useCallback(async (targetDocumentId: string) => {
    if (!/^[a-f0-9]{32}$/i.test(targetDocumentId.trim())) {
      return;
    }

    try {
      const response = await chatApi.getConversations(targetDocumentId.trim());

      setConversations(response.conversations ?? []);
    } catch (err: unknown) {
      console.error("Unable to load conversations:", err);

      setError(getErrorMessage(err, "Unable to load conversation history."));
    }
  }, []);

  // =========================================
  // HANDLE NEW CONVERSATION
  // =========================================

  const handleNewChat = () => {
    setActiveConversationId(null);
    setMessages([]);
    setError("");
  };

  // =========================================
  // HANDLE SUCCESSFUL DOCUMENT UPLOAD
  // =========================================

  const handleDocumentUploaded = (document: DocumentUploadResponse) => {
    if (!document.document_id || !document.filename) {
      setError("The uploaded document response is incomplete.");
      return;
    }

    setDocumentId(document.document_id);
    setDocumentName(document.filename);

    setActiveConversationId(null);
    setMessages([]);
    setConversations([]);
    setError("");

    // Load conversations for the newly uploaded document.
    void refreshConversations(document.document_id);
  };

  // =========================================
  // LOAD EXISTING CONVERSATION
  // =========================================

  const handleSelectConversation = async (conversationId: string) => {
    if (loading || loadingHistory || !hasValidDocumentId) {
      return;
    }

    setLoadingHistory(true);
    setError("");

    try {
      const response = await chatApi.getConversationHistory(conversationId);

      if (
        !response.conversation ||
        response.conversation.document_id !== documentId.trim()
      ) {
        throw new Error(
          "This conversation belongs to another document or could not be loaded.",
        );
      }

      setActiveConversationId(conversationId);
      setMessages(response.messages ?? []);
    } catch (err: unknown) {
      console.error("Unable to load conversation:", err);

      setError(getErrorMessage(err, "Unable to load this conversation."));
    } finally {
      setLoadingHistory(false);
    }
  };

  // =========================================
  // DELETE CONVERSATION
  // =========================================

  const handleDeleteConversation = async (conversationId: string) => {
    if (loading || loadingHistory) {
      return;
    }

    const confirmed = window.confirm(
      "Delete this conversation and its message history?",
    );

    if (!confirmed) {
      return;
    }

    try {
      await chatApi.deleteConversation(conversationId);

      if (activeConversationId === conversationId) {
        setActiveConversationId(null);
        setMessages([]);
      }

      await refreshConversations(documentId);
    } catch (err: unknown) {
      console.error("Unable to delete conversation:", err);

      setError(getErrorMessage(err, "Unable to delete this conversation."));
    }
  };

  // =========================================
  // SEND MESSAGE TO RAG BACKEND
  // =========================================

  const handleSendMessage = async (question: string) => {
    if (!hasValidDocumentId || loading || loadingHistory || !question.trim()) {
      return;
    }

    setLoading(true);
    setError("");

    const optimisticMessage: Message = {
      role: "user",
      content: question.trim(),
      created_at: new Date().toISOString(),
    };

    // Immediately display the user's question.
    setMessages((previous) => [...previous, optimisticMessage]);

    try {
      const response = await chatApi.askQuestion({
        document_id: documentId.trim(),
        question: question.trim(),
        top_k: 3,
        ...(activeConversationId
          ? { conversation_id: activeConversationId }
          : {}),
      });

      if (!response.success || !response.answer) {
        throw new Error("The backend did not return a valid answer.");
      }

      // Save the conversation ID returned by the backend.
      setActiveConversationId(response.conversation_id);

      // Create the assistant message.
      const assistantMessage: Message = {
        id: response.assistant_message_id,
        role: "assistant",
        content: response.answer,
        sources: response.sources ?? [],
        created_at: new Date().toISOString(),
      };

      setMessages((previous) => [...previous, assistantMessage]);

      // Refresh the sidebar conversation list.
      await refreshConversations(documentId);
    } catch (err: unknown) {
      console.error("Chat request failed:", err);

      setError(getErrorMessage(err, "Something went wrong. Please try again."));

      // Remove the optimistic message if the request failed.
      setMessages((previous) =>
        previous.filter((message) => message !== optimisticMessage),
      );
    } finally {
      setLoading(false);
    }
  };

  // =========================================
  // APPLICATION UI
  // =========================================

  return (
    <div className="app-shell">
      {/* SIDEBAR */}
      <Sidebar
        documentId={documentId}
        documentName={documentName}
        onDocumentUploaded={handleDocumentUploaded}
        conversations={conversations}
        activeConversationId={activeConversationId}
        onNewChat={handleNewChat}
        onSelectConversation={handleSelectConversation}
        onDeleteConversation={handleDeleteConversation}
        collapsed={collapsed}
        onToggle={() => setCollapsed((value) => !value)}
      />

      {/* MAIN WORKSPACE */}
      <main className="main-workspace">
        {/* CHAT HEADER */}
        <ChatHeader
          title={
            activeConversationId
              ? conversations.find((item) => item.id === activeConversationId)
                  ?.title || "Document conversation"
              : "Your AI study companion"
          }
          documentId={documentId}
        />

        {/* ERROR MESSAGE */}
        {error && (
          <div className="error-banner" role="alert">
            <AlertCircle size={17} />

            <span>{error}</span>

            <button onClick={() => setError("")}>Dismiss</button>
          </div>
        )}

        {/* CONVERSATION HISTORY LOADING */}
        {loadingHistory && (
          <div className="history-loading">
            <RefreshCw size={16} className="spin" />
            Loading conversation...
          </div>
        )}

        {/* CHAT WINDOW */}
        <ChatWindow
          messages={messages}
          loading={loading}
          onSuggestion={handleSendMessage}
          hasDocument={hasValidDocumentId}
        />

        {/* CHAT INPUT */}
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
