import { useCallback, useEffect, useState } from "react";

import type { AgentSettings } from "@/types";
import { DEFAULT_SETTINGS } from "@/utils/defaultSettings";

const STORAGE_KEY = "agentmind.settings";

function readPersistedSettings(): AgentSettings {
  if (typeof window === "undefined") {
    return DEFAULT_SETTINGS;
  }

  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return DEFAULT_SETTINGS;
    }

    const parsed = JSON.parse(raw) as Partial<AgentSettings>;
    if (typeof parsed.systemPrompt === "string" && typeof parsed.jsonSchema === "string") {
      return {
        systemPrompt: parsed.systemPrompt,
        jsonSchema: parsed.jsonSchema,
      };
    }

    return DEFAULT_SETTINGS;
  } catch (error) {
    console.error("Failed to parse persisted settings", error);
    window.localStorage.removeItem(STORAGE_KEY);
    return DEFAULT_SETTINGS;
  }
}

export function useSettings() {
  const [settings, setSettings] = useState<AgentSettings>(() => readPersistedSettings());

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
    } catch (error) {
      console.error("Failed to persist settings", error);
    }
  }, [settings]);

  const saveSettings = useCallback((nextSettings: AgentSettings) => {
    try {
      JSON.parse(nextSettings.jsonSchema);
      setSettings(nextSettings);
    } catch (error) {
      console.error("Invalid JSON schema", error);
      throw new Error("JSON schema is invalid. Please fix it before saving.");
    }
  }, []);

  const resetSettings = useCallback(() => {
    setSettings(DEFAULT_SETTINGS);
  }, []);

  return { settings, saveSettings, resetSettings } as const;
}



