import {
  Sparkles,
  ShieldCheck,
  FileText,
} from "lucide-react";

interface Props {
  title: string;
  documentId: string;
}

export default function ChatHeader({
  title,
  documentId,
}: Props) {
  return (
    <header className="chat-header">
      <div className="header-left">
        <div className="header-title-row">
          <span className="header-sparkle">
            <Sparkles size={19} />
          </span>

          <div>
            <h2>{title}</h2>
            <p>Ask questions and explore your documents</p>
          </div>
        </div>
      </div>

      <div className="header-status">
        <div className="status-pill">
          <span className="status-dot" />
          AI Ready
        </div>

        <div className="document-status">
          <FileText size={15} />

          <span>
            {documentId
              ? `${documentId.slice(0, 8)}...`
              : "No document selected"}
          </span>
        </div>

        <ShieldCheck size={18} className="security-icon" />
      </div>
    </header>
  );
}