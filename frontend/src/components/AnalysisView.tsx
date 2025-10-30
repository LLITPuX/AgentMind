import type { ChatMessage } from "@/types";
import { BotIcon, UserIcon } from "./Icons";

interface AnalysisViewProps {
  messages: ChatMessage[];
  onClose: () => void;
}

function AnalysisCard({ message }: { message: ChatMessage }) {
  const isUser = message.sender === "user";
  if (!message.analysis) {
    return null;
  }

  return (
    <article className="analysis-card" aria-label="Analysis result">
      <header className={`analysis-card__header${isUser ? " analysis-card__header--user" : ""}`}>
        <div className={`message__avatar ${isUser ? "message__avatar--user" : "message__avatar--ai"}`}>
          {isUser ? <UserIcon width={18} height={18} /> : <BotIcon width={18} height={18} />}
        </div>
        <div>
          <p className="message__text" style={{ margin: 0, fontWeight: 600, color: "var(--color-text-muted)" }}>
            Original message
          </p>
          <p className="message__text" style={{ marginTop: 4, fontStyle: "italic" }}>
            “{message.text}”
          </p>
        </div>
      </header>
      <div className="analysis-card__body">
        <p className="message__text" style={{ marginBottom: 8, color: "var(--color-text-muted)", fontWeight: 600 }}>
          Analysis
        </p>
        <pre className="analysis-card__json">{JSON.stringify(message.analysis, null, 2)}</pre>
      </div>
    </article>
  );
}

export function AnalysisView({ messages, onClose }: AnalysisViewProps) {
  const analyzedMessages = messages.filter(message => Boolean(message.analysis));

  return (
    <div className="analysis-shell">
      <header className="analysis-header">
        <h1 className="analysis-title">Analysis Results</h1>
        <button type="button" className="button-primary" onClick={onClose}>
          ← Back to chat
        </button>
      </header>

      <main className="analysis-body">
        {analyzedMessages.length === 0 ? (
          <div className="empty-state">
            <strong>No analyzed messages yet.</strong>
            <span>Send a prompt in the chat to see extraction results here.</span>
          </div>
        ) : (
          analyzedMessages.map(message => <AnalysisCard key={message.id} message={message} />)
        )}
      </main>
    </div>
  );
}



