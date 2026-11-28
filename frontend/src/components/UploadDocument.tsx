
import { useRef, useState } from "react";
import {
  UploadCloud,
  FileText,
  CheckCircle2,
  AlertCircle,
  LoaderCircle,
  X,
} from "lucide-react";

import { documentApi } from "../services/documentApi";
import type { DocumentUploadResponse } from "../services/documentApi";

interface Props {
  onDocumentReady: (document: DocumentUploadResponse) => void;
  disabled?: boolean;
}

type ProcessingStage =
  | "idle"
  | "uploading"
  | "chunking"
  | "embedding"
  | "storing"
  | "completed"
  | "error";

const MAX_FILE_SIZE = 10 * 1024 * 1024;

const stageLabels: Record<ProcessingStage, string> = {
  idle: "Choose a PDF document",
  uploading: "Uploading and extracting text...",
  chunking: "Creating document chunks...",
  embedding: "Generating embeddings...",
  storing: "Storing vectors in Qdrant...",
  completed: "Document is ready!",
  error: "Processing failed",
};

export default function UploadDocument({
  onDocumentReady,
  disabled = false,
}: Props) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [stage, setStage] = useState<ProcessingStage>("idle");
  const [error, setError] = useState("");

  const isProcessing = [
    "uploading",
    "chunking",
    "embedding",
    "storing",
  ].includes(stage);

  const resetUpload = () => {
    setSelectedFile(null);
    setStage("idle");
    setError("");

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleFileSelection = (file?: File) => {
    if (!file) return;

    setError("");
    setStage("idle");

    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setError("Only PDF files are supported.");
      return;
    }

    if (file.size === 0) {
      setError("The selected file is empty.");
      return;
    }

    if (file.size > MAX_FILE_SIZE) {
      setError("File size must not exceed 10 MB.");
      return;
    }

    setSelectedFile(file);
  };

  const handleUpload = async () => {
    if (!selectedFile || isProcessing || disabled) return;

    setError("");

    try {
      // STEP 1: Upload PDF and extract text.
      setStage("uploading");

      const uploadResult = await documentApi.upload(selectedFile);

      if (!uploadResult.success || !uploadResult.document_id) {
        throw new Error("Document upload failed.");
      }

      const documentId = uploadResult.document_id;

      // STEP 2: Create document chunks.
      setStage("chunking");

      await documentApi.chunk(documentId);

      // STEP 3: Generate embeddings.
      setStage("embedding");

      await documentApi.embed(documentId);

      // STEP 4: Store vectors in Qdrant.
      setStage("storing");

      await documentApi.store(documentId);

      // STEP 5: Mark document as ready.
      setStage("completed");

      onDocumentReady(uploadResult);

      setSelectedFile(null);

      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    } catch (err: unknown) {
      console.error("Document processing failed:", err);

      const axiosError = err as {
        response?: {
          data?: {
            detail?: string | { message?: string };
          };
        };
        message?: string;
      };

      const detail = axiosError.response?.data?.detail;

      const errorMessage =
        typeof detail === "string"
          ? detail
          : detail?.message ||
            axiosError.message ||
            "Unable to process the document.";

      setError(errorMessage);
      setStage("error");
    }
  };

  return (
    <section className="upload-document">
      <div className="upload-heading">
        <div className="upload-heading-icon">
          <UploadCloud size={19} />
        </div>

        <div>
          <h3>Upload Document</h3>
          <p>Add a PDF to your knowledge space</p>
        </div>
      </div>

      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,application/pdf"
        hidden
        disabled={isProcessing || disabled}
        onChange={(event) =>
          handleFileSelection(event.target.files?.[0])
        }
      />

      {!selectedFile ? (
        <button
          type="button"
          className="upload-dropzone"
          disabled={isProcessing || disabled}
          onClick={() => fileInputRef.current?.click()}
        >
          <UploadCloud size={25} />

          <strong>Choose PDF file</strong>

          <span>Click to browse your computer</span>

          <small>PDF only · Maximum 10 MB</small>
        </button>
      ) : (
        <div className="selected-document">
          <FileText size={21} />

          <div className="selected-document-info">
            <strong>{selectedFile.name}</strong>
            <span>
              {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
            </span>
          </div>

          {!isProcessing && (
            <button
              type="button"
              className="upload-reset-button"
              onClick={resetUpload}
              aria-label="Remove selected file"
            >
              <X size={17} />
            </button>
          )}
        </div>
      )}

      {selectedFile && stage !== "completed" && (
        <button
          type="button"
          className="upload-submit-button"
          onClick={handleUpload}
          disabled={isProcessing || disabled}
        >
          {isProcessing ? (
            <>
              <LoaderCircle size={17} className="spin" />
              Processing...
            </>
          ) : (
            <>
              <UploadCloud size={17} />
              Upload and process
            </>
          )}
        </button>
      )}

      {stage !== "idle" && (
        <div
          className={`upload-status ${
            stage === "error"
              ? "upload-status-error"
              : stage === "completed"
                ? "upload-status-success"
                : ""
          }`}
          aria-live="polite"
        >
          {isProcessing ? (
            <LoaderCircle size={16} className="spin" />
          ) : stage === "completed" ? (
            <CheckCircle2 size={16} />
          ) : stage === "error" ? (
            <AlertCircle size={16} />
          ) : null}

          <span>{stageLabels[stage]}</span>
        </div>
      )}

      {error && (
        <div className="upload-error-message" role="alert">
          <AlertCircle size={15} />
          <span>{error}</span>
        </div>
      )}

      <p className="upload-help-text">
        Your document will be processed and indexed before chat becomes available.
      </p>
    </section>
  );
}
