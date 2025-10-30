import { useCallback, useEffect, useRef, useState } from "react";

import { AnalysisView } from "@/components/AnalysisView";
import { ChatInterface } from "@/components/ChatInterface";
import { SettingsPanel } from "@/components/SettingsPanel";
import { useSettings } from "@/hooks/useSettings";
import { requestAnalysis, requestConversation } from "@/services/agentApi";
import type { AnalysisResult, ChatMessage } from "@/types";

type View = "chat" | "analysis";

const generateId = () =>
  typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(16).slice(2)}`;

const INITIAL_MESSAGE: ChatMessage = {
  id: generateId(),
  sender: "ai",
  text: "Вітаю! Я ваш AI-агент. Можу аналізувати кожне повідомлення та вести діалог. Запитайте щось або скористайтеся голосовим введенням.",
  analysis: undefined,
};

export default function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([INITIAL_MESSAGE]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [view, setView] = useState<View>("chat");
  const { settings, saveSettings, resetSettings } = useSettings();
  const pendingAnalysis = useRef(new Set<string>());

  useEffect(() => {
    return () => {
      pendingAnalysis.current.clear();
    };
  }, []);

  const lastMessage = messages.at(-1);

  useEffect(() => {
    if (!lastMessage) {
      return;
    }
    if (lastMessage.sender !== "ai") {
      return;
    }
    if (lastMessage.analysis) {
      return;
    }
    if (pendingAnalysis.current.has(lastMessage.id)) {
      return;
    }

    const controller = new AbortController();
    pendingAnalysis.current.add(lastMessage.id);

    void (async () => {
      try {
        const analysisResponse = await requestAnalysis(lastMessage, settings, controller.signal);
        updateMessageAnalysis(lastMessage.id, analysisResponse.analysis);
      } catch (error) {
        console.error("AI message analysis failed", error);
        updateMessageAnalysis(lastMessage.id, {
          error: "Analysis failed",
          details: error instanceof Error ? error.message : "Unknown error",
        });
      } finally {
        pendingAnalysis.current.delete(lastMessage.id);
      }
    })();

    return () => {
      controller.abort();
    };
  }, [lastMessage, settings]);

  const updateMessageAnalysis = useCallback((messageId: string, analysis: AnalysisResult) => {
    setMessages(previous =>
      previous.map(message => (message.id === messageId ? { ...message, analysis } : message)),
    );
  }, []);

  const handleSendMessage = useCallback(
    async (text: string) => {
      if (isLoading) {
        return;
      }

      setIsLoading(true);

      const userMessage: ChatMessage = {
        id: generateId(),
        sender: "user",
        text,
      };

      let conversationSnapshot: ChatMessage[] = [];

      setMessages(previous => {
        const next = [...previous, userMessage];
        conversationSnapshot = next;
        return next;
      });

      let userAnalysis: AnalysisResult | undefined;

      try {
        const analysisResponse = await requestAnalysis(userMessage, settings);
        userAnalysis = analysisResponse.analysis;
        updateMessageAnalysis(userMessage.id, userAnalysis);
      } catch (error) {
        console.error("User message analysis failed", error);
        userAnalysis = {
          error: "Analysis failed",
          details: error instanceof Error ? error.message : "Unknown error",
        };
        updateMessageAnalysis(userMessage.id, userAnalysis);
      }

      try {
        const historyForConversation = conversationSnapshot.map(message =>
          message.id === userMessage.id ? { ...message, analysis: userAnalysis } : message,
        );

        const conversationResponse = await requestConversation(historyForConversation, settings);
        const aiMessage: ChatMessage = {
          id: generateId(),
          sender: "ai",
          text: conversationResponse.message ?? "Вибачте, відповідь недоступна.",
        };

        setMessages(previous => [...previous, aiMessage]);
      } catch (error) {
        console.error("Conversation request failed", error);
        const aiMessage: ChatMessage = {
          id: generateId(),
          sender: "ai",
          text:
            "Вибачте, сталася помилка під час генерації відповіді. Перевірте бекенд або ключі доступу та спробуйте ще раз.",
        };
        setMessages(previous => [...previous, aiMessage]);
      } finally {
        setIsLoading(false);
      }
    },
    [isLoading, settings, updateMessageAnalysis],
  );

  return (
    <div className="app-shell">
      {view === "chat" ? (
        <ChatInterface
          messages={messages}
          isLoading={isLoading}
          onSendMessage={handleSendMessage}
          onOpenAnalysis={() => setView("analysis")}
          onOpenSettings={() => setIsSettingsOpen(true)}
        />
      ) : (
        <AnalysisView messages={messages} onClose={() => setView("chat")} />
      )}

      <SettingsPanel
        isOpen={isSettingsOpen}
        settings={settings}
        onClose={() => setIsSettingsOpen(false)}
        onSave={saveSettings}
        onReset={resetSettings}
      />
    </div>
  );
}
