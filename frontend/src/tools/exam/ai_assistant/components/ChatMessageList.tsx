import { useMemo, useRef, useEffect } from "react"

import { AetherSpectrum } from "./AetherSpectrum"
import { CollapsibleToolBlock } from "./CollapsibleToolBlock"
import { MarkdownContent } from "./MarkdownContent"
import type { ChatMessage } from "../types"

interface ChatMessageListProps {
  messages: ChatMessage[]
  isLoading?: boolean
}

export function ChatMessageList({ messages, isLoading = false }: ChatMessageListProps) {
  const endRef = useRef<HTMLDivElement>(null)

  const lastAiIndex = useMemo(() => {
    for (let i = messages.length - 1; i >= 0; i--) {
      if (messages[i].role === "assistant") return i
    }
    return -1
  }, [messages])

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
        <div className="text-center text-sm text-muted-foreground py-8">
          我是 AI 组卷助手，可以帮你出题、改题、查题。
          <br />
          试试说：「添加一道单选题，问 Python 的创始人是谁」。
        </div>
      )}

      {messages.map((msg, idx) => {
        const isLastAi = idx === lastAiIndex

        if (msg.role === "user") {
          return (
            <div key={idx} className="flex justify-end">
              <div className="bg-primary text-primary-foreground font-medium text-sm px-4 py-3 rounded-2xl rounded-tr-none max-w-[85%] shadow-sm leading-relaxed text-left">
                {msg.content}
              </div>
            </div>
          )
        }

        return (
          <div key={idx} className="space-y-1.5">
            <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">
              {msg.role === "tool" ? "外部扩展工具 (Tool Call)" : "AI 智能输出"}
            </div>

            <div className="pl-1 space-y-3 py-1">
              {msg.content && (
                <div className="text-sm leading-relaxed">
                  <MarkdownContent text={msg.content} />
                </div>
              )}

              {msg.tool_calls?.map((tc) => (
                <CollapsibleToolBlock key={tc.id} toolCall={tc} />
              ))}

              {isLastAi && !isLoading && (
                <div className="flex items-center gap-2 -ml-2 pt-1">
                  <AetherSpectrum state="idle" size={28} />
                  <span className="text-[10px] font-mono text-muted-foreground tracking-wider">
                    AETHER_IDLE
                  </span>
                </div>
              )}
            </div>
          </div>
        )
      })}

      {isLoading && (
        <div className="space-y-1.5">
          <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">
            AI 智能输出
          </div>
          <div className="pl-1 flex items-center gap-3 py-1">
            <AetherSpectrum state="thinking" size={28} />
            <span className="text-xs text-muted-foreground">AI 正在思考…</span>
          </div>
        </div>
      )}

      <div ref={endRef} />
    </div>
  )
}
