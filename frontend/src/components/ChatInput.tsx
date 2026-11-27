import {
  Send,
  Sparkles,
  LoaderCircle,
} from "lucide-react";

import { useState } from "react";

interface Props {
  onSend: (message: string) => void;
  loading: boolean;
  disabled?: boolean;
}

export default function ChatInput({
  onSend,
  loading,
  disabled = false,
}: Props) {
  const [message, setMessage] = useState("");

  const submitMessage = () => {
    const trimmed = message.trim();

    if (!trimmed || loading || disabled) {
      return;
    }

    onSend(trimmed);
    setMessage("");
  };

  return (
    <div className="composer-area">
      <div className="composer">
        <textarea
          value={message}
          onChange={(event) =>
            setMessage(event.target.value.slice(0, 2000))
          }
          onKeyDown={(event) => {
            if (
              event.key === "Enter" &&
              !event.shiftKey &&
              !event.nativeEvent.isComposing
            ) {
              event.preventDefault();
              submitMessage();
            }
          }}
          placeholder={
            disabled
              ? "Enter a valid document ID to begin..."
              : "Ask anything about your document..."
          }
          rows={2}
          disabled={loading || disabled}
        />

        <button
          className="send-button"
          onClick={submitMessage}
          disabled={
            loading ||
            disabled ||
            !message.trim()
          }
          title="Send message"
        >
          {loading ? (
            <LoaderCircle size={19} className="spin" />
          ) : (
            <Send size={19} />
          )}
        </button>
      </div>

      <div className="composer-footer">
        <span>
          <Sparkles size={13} />
          Powered by Groq + Retrieval Augmented Generation
        </span>

        <span>{message.length}/2000</span>
      </div>
    </div>
  );
}