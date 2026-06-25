import { Bot } from "lucide-react"

export function ThinkingIndicator() {
  return (
    <div className="flex flex-col items-center gap-2 py-2">
      {/* Pulsing robot with halo */}
      <div className="relative flex h-10 w-10 items-center justify-center">
        <span className="absolute inset-0 rounded-full bg-primary/20 animate-ping" />
        <span className="absolute inset-1 rounded-full bg-primary/10 animate-pulse" />
        <Bot className="relative h-5 w-5 text-primary animate-pulse" />
      </div>

      {/* Staggered bouncing dots */}
      <div className="flex items-center gap-1">
        <span
          className="h-1.5 w-1.5 rounded-full bg-muted-foreground/70 animate-bounce"
          style={{ animationDelay: "0ms" }}
        />
        <span
          className="h-1.5 w-1.5 rounded-full bg-muted-foreground/70 animate-bounce"
          style={{ animationDelay: "120ms" }}
        />
        <span
          className="h-1.5 w-1.5 rounded-full bg-muted-foreground/70 animate-bounce"
          style={{ animationDelay: "240ms" }}
        />
      </div>

      <span className="text-xs text-muted-foreground">思考中…</span>
    </div>
  )
}
