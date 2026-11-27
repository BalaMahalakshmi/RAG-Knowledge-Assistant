import {
  BookOpen,
  BrainCircuit,
  FileSearch,
  MessageSquareText,
} from "lucide-react";

import type { Message } from "../types/chat";
import MessageBubble from "./MessageBubble";

interface Props {
  messages: Message[];
  loading: boolean;
  onSuggestion: (question: string) => void;
  hasDocument: boolean;
}

const suggestions = [
  {
    icon: BookOpen,
    title: "Summarize this document",
    description: "Get the key ideas and important points.",
    question: "Summarize the uploaded document.",
  },
  {
    icon: BrainCircuit,
    title: "Explain a concept",
    description: "Learn difficult topics in simple language.",
    question: "Explain the main concepts in this document in simple language.",
  },
  {
    icon: FileSearch,
    title: "Find important topics",
    description: "Discover the important information.",
    question: "What are the most important topics covered in this document?",
  },
  {
    icon: MessageSquareText,
    title: "Create study questions",
    description: "Prepare for exams with practice questions.",
    question: "Create five important study questions based on this document.",
  },
];

export default function ChatWindow({
  messages,
  loading,
  onSuggestion,
  hasDocument,
}: Props) {
  return (
    <div className="chat-scroll-area">
      {messages.length === 0 ? (
        <div className="welcome-screen">
          <div className="welcome-icon">
            <BrainCircuit size={35} />
            <span className="welcome-orbit" />
          </div>

          <div className="welcome-eyebrow">
            YOUR PERSONAL KNOWLEDGE SPACE
          </div>

          <h1>
            Knowledge begins
            <br />
            with a <span>question.</span>
          </h1>

          <p className="welcome-description">
            Explore your documents, understand complex ideas,
            and turn information into knowledge with your
            AI-powered study companion.
          </p>

          {!hasDocument && (
            <div className="document-required-note">
              Enter your uploaded PDF's document ID in the sidebar
              to get started.
            </div>
          )}

          <div className="suggestion-grid">
            {suggestions.map((suggestion) => {
              const Icon = suggestion.icon;

              return (
                <button
                  className="suggestion-card"
                  key={suggestion.title}
                  onClick={() =>
                    onSuggestion(suggestion.question)
                  }
                  disabled={!hasDocument || loading}
                >
                  <div className="suggestion-icon">
                    <Icon size={19} />
                  </div>

                  <strong>{suggestion.title}</strong>

                  <span>{suggestion.description}</span>
                </button>
              );
            })}
          </div>
        </div>
      ) : (
        <div className="messages-container">
          {messages.map((message, index) => (
            <MessageBubble
              key={message.id ?? `${message.role}-${index}`}
              message={message}
            />
          ))}

          {loading && (
            <div className="message-row assistant-row">
              <div className="avatar ai-avatar">
                <BrainCircuit size={19} />
              </div>

              <div className="typing-indicator">
                <span />
                <span />
                <span />
                <p>Neural AI is thinking...</p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}