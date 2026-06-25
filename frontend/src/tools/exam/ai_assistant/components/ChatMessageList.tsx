import { Bot, User } from "lucide-react"

import { ToolCallCard } from "./ToolCallCard"
import type { ChatMessage } from "../types"

interface ChatMessageListProps {
  messages: ChatMessage[]
}

export function ChatMessageList({ messages }: ChatMessageListProps) {
  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {messages.length === 0 && (
        <div className="text-center text-sm text-muted-foreground py-8">
          我是 AI 组卷助手，可以帮你出题、改题、查题。
          <br />
          试试说：「添加一道单选题，问 Python 的创始人是谁」。
        </div>
      )}
      {messages.map((msg, idx) => (
        <div key={idx} className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : ""}`}>
          <div
            className={`h-8 w-8 shrink-0 rounded-full flex items-center justify-center ${
              msg.role === "user"
                ? "bg-primary text-primary-foreground"
                : "bg-muted text-muted-foreground"
            }`}
          >
            {msg.role === "user" ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
          </div>
          <div className={`flex flex-col gap-2 max-w-[80%] ${msg.role === "user" ? "items-end" : "items-start"}`}>
            {msg.content && (
              <div
                className={`rounded-lg px-4 py-2 text-sm ${
                  msg.role === "user"
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted"
                }`}
              >
                {msg.content}
              </div>
            )}
            {msg.tool_calls?.map((tc) => (
              <div key={tc.id} className="w-full">
                <ToolCallCard toolCall={tc} />
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
