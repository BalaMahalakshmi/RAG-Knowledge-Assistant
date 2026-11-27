import {
  Bot,
  UserRound,
  Copy,
  Check,
} from "lucide-react";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import type { Message } from "../types/chat";
import SourceCard from "./SourceCard";

interface Props {
  message: Message;
}

export default function MessageBubble({ message }: Props) {
  const isAssistant = message.role === "assistant";

  const [copied, setCopied] = useState(false);

  const copyMessage = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);

      window.setTimeout(() => {
        setCopied(false);
      }, 2000);
    } catch {
      console.error("Unable to copy message.");
    }
  };

  return (
    <div
      className={`message-row ${
        isAssistant ? "assistant-row" : "user-row"
      }`}
    >
      <div className={`avatar ${isAssistant ? "ai-avatar" : "user-avatar"}`}>
        {isAssistant ? (
          <Bot size={19} />
        ) : (
          <UserRound size={19} />
        )}
      </div>

      <div className="message-content">
        <div className="message-meta">
          <strong>
            {isAssistant ? "Neural AI" : "You"}
          </strong>

          {message.created_at && (
            <span>
              {new Date(message.created_at).toLocaleTimeString(
                [],
                {
                  hour: "2-digit",
                  minute: "2-digit",
                }
              )}
            </span>
          )}
        </div>

        <div className={`message-bubble ${
          isAssistant ? "ai-bubble" : "user-bubble"
        }`}>
          {isAssistant ? (
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content}
            </ReactMarkdown>
          ) : (
            <p>{message.content}</p>
          )}
        </div>

        {isAssistant && (
          <>
            <SourceCard sources={message.sources || []} />

            <button
              className="copy-message-button"
              onClick={copyMessage}
              type="button"
            >
              {copied ? <Check size={14} /> : <Copy size={14} />}
              {copied ? "Copied" : "Copy answer"}
            </button>
          </>
        )}
      </div>
    </div>
  );
}