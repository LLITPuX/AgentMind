import { useEffect, useRef } from "react";

import type { ChatMessage } from "@/types";
import { AnalysisIcon, SettingsIcon } from "./Icons";
import { InputBar } from "./InputBar";
import { Message } from "./Message";

interface ChatInterfaceProps {
  messages: ChatMessage[];
  isLoading: boolean;
  onSendMessage: (text: string) => void;
  onOpenSettings: () => void;
  onOpenAnalysis: () => void;
}

export function ChatInterface({
  messages,
  isLoading,
  onSendMessage,
  onOpenAnalysis,
  onOpenSettings,
}: ChatInterfaceProps) {
  const endRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="chat-shell">
      <header className="chat-header">
        <h1 className="chat-title">AgentMind Assistant</h1>
        <div className="chat-actions">
          <button type="button" className="icon-button" onClick={onOpenAnalysis} aria-label="Open analysis view">
            <AnalysisIcon width={22} height={22} />
          </button>
          <button type="button" className="icon-button" onClick={onOpenSettings} aria-label="Open settings">
            <SettingsIcon width={22} height={22} />
          </button>
        </div>
      </header>

      <main className="chat-body">
        {messages.map(message => (
          <Message key={message.id} message={message} />
        ))}

        {isLoading ? (
          <div className="loader">
            <span className="loader__dot" />
            <span className="loader__dot" />
            <span className="loader__dot" />
          </div>
        ) : null}

        <div ref={endRef} />
      </main>

      <footer className="chat-footer">
        <InputBar isLoading={isLoading} onSendMessage={onSendMessage} />
      </footer>
    </div>
  );
}



