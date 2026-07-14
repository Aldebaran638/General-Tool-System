import { useRef, useEffect, useState } from "react"

import { Bot, ChevronDown, Lightbulb } from "lucide-react"
import { CollapsibleToolBlock } from "./CollapsibleToolBlock"
import { MarkdownContent } from "./MarkdownContent"
import { ThinkingIndicator } from "./ThinkingIndicator"
import type { AIStatus, ChatMessage } from "../types"

function ReasoningBlock({ reasoning }: { reasoning: string }) {
  const [isExpanded, setIsExpanded] = useState(false)
  if (!reasoning.trim()) return null

  return (
    <div className="rounded-xl overflow-hidden border border-amber-200/50 bg-amber-50/40 dark:bg-amber-950/20">
      <button
        type="button"
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-3 py-2 flex items-center justify-between text-left"
      >
        <div className="flex items-center gap-2 text-[11px] font-medium text-amber-700 dark:text-amber-400">
          <Lightbulb className="w-3 h-3" />
          <span>思考过程</span>
        </div>
        <ChevronDown
          className={`w-3.5 h-3.5 text-amber-600/70 transition-transform duration-300 ${isExpanded ? "rotate-180" : ""
            }`}
        />
      </button>
      {isExpanded && (
        <div className="px-3 py-2 border-t border-amber-200/50 text-[11px] text-amber-900/80 dark:text-amber-300/80 leading-relaxed whitespace-pre-wrap font-mono">
          {reasoning}
        </div>
      )}
    </div>
  )
}

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

  const lastMsg = messages[messages.length - 1]
  const lastIsAssistant = lastMsg?.role === "assistant"

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

        const isLast = idx === messages.length - 1
        const showThinking = isLast && isLoading && !msg.content

        return (
          <div key={idx} className="flex gap-3 animate-fade-in-up">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
              <Bot className="h-4 w-4" />
            </div>
            <div className="flex-1 min-w-0 space-y-1">
              <div className="text-xs font-medium text-muted-foreground">
                AI 组卷助手
              </div>

              {msg.reasoning && msg.reasoning.trim().length > 0 && (
                <ReasoningBlock reasoning={msg.reasoning} />
              )}

              {showThinking && (
                <div className="inline-flex items-center gap-2 rounded-2xl rounded-tl-none border bg-muted/40 px-4 py-3 text-sm text-muted-foreground shadow-sm">
                  <span>{status === "tool-calling" ? "正在调用工具" : "正在思考"}</span>
                  <span className="flex gap-0.5">
                    <span className="h-1.5 w-1.5 rounded-full bg-current animate-bounce [animation-delay:-0.2s]" />
                    <span className="h-1.5 w-1.5 rounded-full bg-current animate-bounce [animation-delay:-0.1s]" />
                    <span className="h-1.5 w-1.5 rounded-full bg-current animate-bounce" />
                  </span>
                </div>
              )}

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

      {isLoading && !lastIsAssistant && (
        <ThinkingIndicator status={status} />
      )}

      <div ref={endRef} />
    </div>
  )
}
