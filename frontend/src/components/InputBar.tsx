import { FormEvent, useCallback, useState } from "react";

import { useSpeechRecognition } from "@/hooks/useSpeechRecognition";
import { MicIcon, MicOffIcon, SendIcon } from "./Icons";

interface InputBarProps {
  isLoading: boolean;
  onSendMessage: (text: string) => void;
}

export function InputBar({ isLoading, onSendMessage }: InputBarProps) {
  const [text, setText] = useState("");

  const handleSpeechResult = useCallback((transcript: string) => {
    setText(transcript);
  }, []);

  const { isListening, isSupported, toggleListening } = useSpeechRecognition(handleSpeechResult);

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmed = text.trim();
    if (!trimmed || isLoading) {
      return;
    }
    onSendMessage(trimmed);
    setText("");
  };

  return (
    <form className="input-bar" onSubmit={handleSubmit}>
      <div className="input-bar__field">
        <input
          className="input-bar__input"
          type="text"
          value={text}
          onChange={event => setText(event.target.value)}
          placeholder={isListening ? "Прослуховування..." : "Введіть ваш запит..."}
          disabled={isLoading || isListening}
          aria-label="User message"
        />
        {isSupported ? (
          <button
            type="button"
            className={`input-bar__voice-button${isListening ? " input-bar__voice-button--active" : ""}`}
            onClick={toggleListening}
            disabled={isLoading}
            aria-label={isListening ? "Stop listening" : "Start listening"}
          >
            {isListening ? <MicOffIcon width={18} height={18} /> : <MicIcon width={18} height={18} />}
          </button>
        ) : null}
      </div>
      <button type="submit" className="button-primary" disabled={isLoading || !text.trim()}>
        <SendIcon width={20} height={20} />
      </button>
    </form>
  );
}


