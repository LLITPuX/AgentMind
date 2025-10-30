import type {
  AgentSettings,
  AnalysisResponse,
  ChatMessage,
  ChatMessagePayload,
  ConversationResponse,
} from "@/types";

const DEFAULT_BASE_URL = "http://localhost:8000";

const baseUrl = (() => {
  const configured = import.meta.env.VITE_API_BASE_URL;
  if (typeof configured === "string" && configured.trim().length > 0) {
    return configured.replace(/\/$/, "");
  }
  return DEFAULT_BASE_URL;
})();

function buildUrl(path: string): string {
  if (path.startsWith("http://") || path.startsWith("https://")) {
    return path;
  }
  return `${baseUrl}${path.startsWith("/") ? path : `/${path}`}`;
}

async function postJson<TResponse>(path: string, body: unknown, signal?: AbortSignal): Promise<TResponse> {
  const response = await fetch(buildUrl(path), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify(body),
    signal,
  });

  if (!response.ok) {
    const text = await response.text().catch(() => "");
    throw new Error(`Request to ${path} failed with status ${response.status}: ${text}`);
  }

  return (await response.json()) as TResponse;
}

export async function requestAnalysis(
  message: ChatMessage,
  settings: AgentSettings,
  signal?: AbortSignal,
): Promise<AnalysisResponse> {
  const payload = {
    message: mapToPayload(message),
    settings,
  };

  return postJson<AnalysisResponse>('/api/analysis', payload, signal);
}

export async function requestConversation(
  history: ChatMessage[],
  settings: AgentSettings,
  signal?: AbortSignal,
): Promise<ConversationResponse> {
  const payload = {
    messages: history.map(mapToPayload),
    settings,
  };

  return postJson<ConversationResponse>('/api/chat', payload, signal);
}

export async function getBackendHealth(signal?: AbortSignal): Promise<boolean> {
  try {
    const response = await fetch(buildUrl('/health/ready'), {
      method: 'GET',
      signal,
    });
    if (!response.ok) {
      return false;
    }
    const body = (await response.json()) as { status?: string };
    return body.status === 'ok';
  } catch (error) {
    console.warn('Backend health check failed', error);
    return false;
  }
}

function mapToPayload(message: ChatMessage): ChatMessagePayload {
  return {
    id: message.id,
    text: message.text,
    sender: message.sender,
  };
}


