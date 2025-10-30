export type Sender = "user" | "ai";

export interface ChatMessage {
  id: string;
  text: string;
  sender: Sender;
  analysis?: AnalysisResult;
}

export interface AgentSettings {
  systemPrompt: string;
  jsonSchema: string;
}

export type AnalysisResult = Record<string, unknown>;

export interface ChatMessagePayload {
  id: string;
  text: string;
  sender: Sender;
}

export interface AnalysisResponse {
  messageId: string;
  analysis: AnalysisResult;
}

export interface ConversationResponse {
  message: string;
}


