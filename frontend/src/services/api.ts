import axios from "axios";

import type {
  AskRequest,
  AskResponse,
  ConversationListResponse,
  HistoryResponse,
} from "../types/chat";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000,
  headers: {
    "Content-Type": "application/json",
  },
});

export const chatApi = {
  async askQuestion(payload: AskRequest): Promise<AskResponse> {
    const response = await api.post<AskResponse>(
      "/api/v1/chat/ask",
      payload
    );

    return response.data;
  },

  async getConversations(
    documentId: string
  ): Promise<ConversationListResponse> {
    const response = await api.get<ConversationListResponse>(
      "/api/v1/chat/conversations",
      {
        params: {
          document_id: documentId,
        },
      }
    );

    return response.data;
  },

  async getConversationHistory(
    conversationId: string
  ): Promise<HistoryResponse> {
    const response = await api.get<HistoryResponse>(
      `/api/v1/chat/conversations/${conversationId}`
    );

    return response.data;
  },

  async deleteConversation(
    conversationId: string
  ): Promise<void> {
    await api.delete(
      `/api/v1/chat/conversations/${conversationId}`
    );
  },
};

export default api;