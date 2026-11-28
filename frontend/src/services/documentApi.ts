
import api from "./api";

export interface DocumentUploadResponse {
  success: boolean;
  message: string;
  document_id: string;
  filename: string;
  total_pages: number;
  total_characters: number;
  pages: {
    page_number: number;
    character_count: number;
    preview: string;
  }[];
}

export interface DocumentProcessingResponse {
  success: boolean;
  message: string;
  document_id: string;
  total_chunks?: number;
  total_vectors?: number;
  stored_vectors?: number;
  collection_name?: string;
}

export const documentApi = {
  async upload(file: File): Promise<DocumentUploadResponse> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await api.post<DocumentUploadResponse>(
      "/api/v1/documents/upload",
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      }
    );

    return response.data;
  },

  async chunk(
    documentId: string
  ): Promise<DocumentProcessingResponse> {
    const response = await api.post<DocumentProcessingResponse>(
      `/api/v1/documents/${documentId}/chunk`
    );

    return response.data;
  },

  async embed(
    documentId: string
  ): Promise<DocumentProcessingResponse> {
    const response = await api.post<DocumentProcessingResponse>(
      `/api/v1/documents/${documentId}/embed`
    );

    return response.data;
  },

  async store(
    documentId: string
  ): Promise<DocumentProcessingResponse> {
    const response = await api.post<DocumentProcessingResponse>(
      `/api/v1/documents/${documentId}/store`
    );

    return response.data;
  },
};
