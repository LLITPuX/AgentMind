import type { ChatMessage } from "@/types";
import { BotIcon, UserIcon } from "./Icons";

interface MessageProps {
  message: ChatMessage;
}

export function Message({ message }: MessageProps) {
  const isUser = message.sender === "user";

  return (
    <div className={`message${isUser ? " message--user" : ""}`}>
      <div className={`message__avatar ${isUser ? "message__avatar--user" : "message__avatar--ai"}`}>
        {isUser ? <UserIcon width={18} height={18} /> : <BotIcon width={18} height={18} />}
      </div>
      <div className="message__bubble">
        <p className="message__text">{message.text}</p>
      </div>
    </div>
  );
}


