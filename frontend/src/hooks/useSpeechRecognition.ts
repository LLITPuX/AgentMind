import { useCallback, useEffect, useRef, useState } from "react";

type SpeechRecognitionWithStart = SpeechRecognition & {
  start: () => void;
  stop: () => void;
};

const isBrowser = typeof window !== "undefined";

const SpeechRecognitionConstructor: typeof SpeechRecognition | undefined = isBrowser
  ? (window.SpeechRecognition ?? (window as typeof window & { webkitSpeechRecognition?: typeof SpeechRecognition })
      .webkitSpeechRecognition)
  : undefined;

export function useSpeechRecognition(onResult: (text: string) => void) {
  const [isListening, setIsListening] = useState(false);
  const recognitionRef = useRef<SpeechRecognitionWithStart | null>(null);

  useEffect(() => {
    if (!SpeechRecognitionConstructor) {
      return () => undefined;
    }

    const recognition = new SpeechRecognitionConstructor();
    recognition.lang = "uk-UA";
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onstart = () => setIsListening(true);
    recognition.onend = () => setIsListening(false);
    recognition.onerror = event => {
      console.error("Speech recognition error", event.error);
      setIsListening(false);
    };

    recognition.onresult = event => {
      const transcript = event.results?.[0]?.[0]?.transcript;
      if (typeof transcript === "string") {
        onResult(transcript);
      }
    };

    recognitionRef.current = recognition as SpeechRecognitionWithStart;

    return () => {
      recognition.stop();
      recognitionRef.current = null;
    };
  }, [onResult]);

  const toggleListening = useCallback(() => {
    const recognition = recognitionRef.current;
    if (!recognition) {
      return;
    }

    if (isListening) {
      recognition.stop();
    } else {
      recognition.start();
    }
  }, [isListening]);

  return {
    isListening,
    isSupported: Boolean(SpeechRecognitionConstructor),
    toggleListening,
  } as const;
}


