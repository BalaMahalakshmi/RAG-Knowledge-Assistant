import { FileText, ExternalLink } from "lucide-react";
import type { Source } from "../types/chat";

interface Props {
  sources: Source[];
}

export default function SourceCard({ sources }: Props) {
  if (!sources || sources.length === 0) {
    return null;
  }

  return (
    <div className="sources-section">
      <div className="sources-heading">
        <span className="source-icon">
          <FileText size={15} />
        </span>

        <span>Referenced sources</span>
        <span className="source-count">{sources.length}</span>
      </div>

      <div className="source-list">
        {sources.map((source, index) => (
          <div
            className="source-card"
            key={`${source.chunk_id || index}-${index}`}
          >
            <div className="source-file-icon">
              <FileText size={19} />
            </div>

            <div className="source-info">
              <strong>
                {source.filename || "Uploaded document"}
              </strong>

              <span>
                {source.source_label || `Source ${index + 1}`}
                {" · "}
                Page {source.page_number ?? "Unknown"}
              </span>
            </div>

            <ExternalLink
              size={15}
              className="source-external-icon"
            />
          </div>
        ))}
      </div>
    </div>
  );
}