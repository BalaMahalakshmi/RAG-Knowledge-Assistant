
export interface Source {
  source_id?: number;
  source_label?: string;
  filename: string;
  page_number: number;
  chunk_id?: string;
  score?: number;
  content?: string;
}

export interface Message {
  id?: string;
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  created_at?: string;
}

export interface Conversation {
  id: string;
  document_id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface AskRequest {
  document_id: string;
  question: string;
  top_k: number;
  conversation_id?: string;
}

export interface AskResponse {
  success: boolean;
  conversation_id: string;
  answer: string;
  sources: Source[];
  retrieved_chunks: number;
  retrieval_query?: string;
  assistant_message_id?: string;
}

export interface HistoryResponse {
  success: boolean;
  conversation: Conversation;
  total_messages: number;
  messages: Message[];
}

export interface ConversationListResponse {
  success: boolean;
  document_id: string;
  total_conversations: number;
  conversations: Conversation[];
}

export interface ApiError {
  detail?: string;
  message?: string;
}
