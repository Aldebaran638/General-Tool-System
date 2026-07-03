import { Bot } from "lucide-react"

interface ThinkingIndicatorProps {
  status?: "thinking" | "tool-calling" | string | null
}

export function ThinkingIndicator({ status }: ThinkingIndicatorProps) {
  const label = status === "tool-calling" ? "正在调用工具" : "正在思考"

  return (
    <div className="flex gap-3 animate-fade-in-up">
      <div className="relative flex h-8 w-8 shrink-0 items-center justify-center">
        <span className="absolute inline-flex h-full w-full rounded-full bg-primary/30 animate-ping" />
        <span className="relative flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 text-primary ring-2 ring-primary/20 animate-pulse">
          <Bot className="h-4 w-4" />
        </span>
      </div>
      <div className="flex-1 min-w-0 space-y-2">
        <div className="text-xs font-medium text-muted-foreground">AI 组卷助手</div>
        <div className="inline-flex items-center gap-2 rounded-2xl rounded-tl-none border bg-muted/40 px-4 py-3 text-sm text-muted-foreground shadow-sm">
          <span>{label}</span>
          <span className="flex gap-0.5">
            <span className="h-1.5 w-1.5 rounded-full bg-current animate-bounce [animation-delay:-0.2s]" />
            <span className="h-1.5 w-1.5 rounded-full bg-current animate-bounce [animation-delay:-0.1s]" />
            <span className="h-1.5 w-1.5 rounded-full bg-current animate-bounce" />
          </span>
        </div>
      </div>
    </div>
  )
}
