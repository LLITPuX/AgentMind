import type { AgentSettings } from "@/types";

export const DEFAULT_SYSTEM_PROMPT_BASE = `Ви — високоінтелектуальний агент-аналітик. Ваше завдання — проаналізувати ОДНУ подію-повідомлення з розмови та класифікувати її.
Повідомлення матиме префікс, що вказує на відправника ('User:' або 'AI:').

- Ваш результат ПОВИНЕН бути валідним JSON-об'єктом, що суворо відповідає наданій схемі.
- Не додавайте жодного зайвого тексту чи пояснень поза структурою JSON.
- Аналізуйте ЛИШЕ надане повідомлення. Не робіть висновків на основі попередньої історії розмови.`;

export const DEFAULT_SYSTEM_PROMPT_FIELDS = `- eventType: Тип події.
- messageContent: Копія тексту повідомлення, що аналізується.
- detectedIntent: Основний намір або мета цього конкретного повідомлення.
- entities: Список ключових сутностей (люди, місця, поняття), згаданих у цьому повідомленні.
- sentiment: Тональність (сентимент) повідомлення.`;

export const DEFAULT_SYSTEM_PROMPT = `${DEFAULT_SYSTEM_PROMPT_BASE}

${DEFAULT_SYSTEM_PROMPT_FIELDS}`;

const DEFAULT_SCHEMA = {
  type: "object",
  properties: {
    eventType: {
      type: "string",
      description: "Тип події.",
      enum: ["USER_MESSAGE", "AI_RESPONSE"],
    },
    messageContent: {
      type: "string",
      description: "Копія тексту повідомлення, що аналізується.",
    },
    detectedIntent: {
      type: "string",
      description: "Основний намір або мета цього конкретного повідомлення.",
    },
    entities: {
      type: "array",
      description: "Список ключових сутностей (люди, місця, поняття), згаданих у цьому повідомленні.",
      items: {
        type: "string",
      },
    },
    sentiment: {
      type: "string",
      description: "Тональність (сентимент) повідомлення.",
      enum: ["positive", "negative", "neutral"],
    },
  },
  required: ["eventType", "messageContent", "detectedIntent", "entities", "sentiment"],
} as const;

export const DEFAULT_JSON_SCHEMA_STRING = JSON.stringify(DEFAULT_SCHEMA, null, 2);

export const DEFAULT_SETTINGS: AgentSettings = {
  systemPrompt: DEFAULT_SYSTEM_PROMPT,
  jsonSchema: DEFAULT_JSON_SCHEMA_STRING,
};



