import { useRef, useEffect } from "react"

import { Bot } from "lucide-react"
import { CollapsibleToolBlock } from "./CollapsibleToolBlock"
import { MarkdownContent } from "./MarkdownContent"
import type { AIStatus, ChatMessage } from "../types"

interface ChatMessageListProps {
  messages: ChatMessage[]
  isLoading?: boolean
  status?: AIStatus | null
}

export function ChatMessageList({
  messages,
  isLoading = false,
  status = null,
}: ChatMessageListProps) {
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, isLoading])

  return (
    <div
      className="flex-1 overflow-y-auto p-4 space-y-5
        [scrollbar-width:thin]
        [scrollbar-color:hsl(var(--muted-foreground)/0.3)_transparent]
        [&::-webkit-scrollbar]:w-1.5
        [&::-webkit-scrollbar-track]:bg-transparent
        [&::-webkit-scrollbar-thumb]:rounded-full
        [&::-webkit-scrollbar-thumb]:bg-muted-foreground/30"
    >
      {messages.length === 0 && !isLoading && (
        <div className="animate-fade-in-up text-center text-sm text-muted-foreground py-8">
          我是 AI 组卷助手，可以帮你出题、改题、查题。
          <br />
          试试说：「添加一道单选题，问 Python 的创始人是谁」。
        </div>
      )}

      {messages.map((msg, idx) => {
        if (msg.role === "user") {
          return (
            <div key={idx} className="flex justify-end animate-fade-in-up">
              <div className="bg-primary text-primary-foreground font-medium text-sm px-4 py-3 rounded-2xl rounded-tr-none max-w-[85%] shadow-sm leading-relaxed text-left">
                {msg.content}
              </div>
            </div>
          )
        }

        return (
          <div key={idx} className="flex gap-3 animate-fade-in-up">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
              <Bot className="h-4 w-4" />
            </div>
            <div className="flex-1 min-w-0 space-y-2">
              <div className="text-xs font-medium text-muted-foreground">
                AI 组卷助手
              </div>

              {msg.content && (
                <div className="rounded-2xl rounded-tl-none border bg-muted/40 px-4 py-3 text-sm leading-relaxed shadow-sm">
                  <MarkdownContent text={msg.content} />
                </div>
              )}

              {msg.tool_calls?.map((tc) => (
                <CollapsibleToolBlock key={tc.id} toolCall={tc} />
              ))}
            </div>
          </div>
        )
      })}

      {isLoading && (
        <div className="flex gap-3 animate-fade-in-up">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
            <Bot className="h-4 w-4 animate-pulse" />
          </div>
          <div className="flex-1 min-w-0 space-y-2">
            <div className="text-xs font-medium text-muted-foreground">
              AI 组卷助手
            </div>
            <div className="inline-flex items-center gap-2 rounded-2xl rounded-tl-none border bg-muted/40 px-4 py-3 text-sm text-muted-foreground shadow-sm">
              <span>
                {status === "tool-calling" ? "正在调用工具…" : "AI 正在思考…"}
              </span>
              <span className="flex gap-0.5">
                <span className="h-1 w-1 rounded-full bg-current animate-bounce [animation-delay:-0.2s]" />
                <span className="h-1 w-1 rounded-full bg-current animate-bounce [animation-delay:-0.1s]" />
                <span className="h-1 w-1 rounded-full bg-current animate-bounce" />
              </span>
            </div>
          </div>
        </div>
      )}

      <div ref={endRef} />
    </div>
  )
}
