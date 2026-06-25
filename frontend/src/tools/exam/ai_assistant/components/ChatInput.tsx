import { useState } from "react"
import { Loader2, Send, X } from "lucide-react"

import { Button } from "@/components/ui/button"

interface ChatInputProps {
  onSend: (message: string) => void
  onCancel?: () => void
  disabled?: boolean
  placeholder?: string
}

export function ChatInput({
  onSend,
  onCancel,
  disabled = false,
  placeholder = "输入消息...",
}: ChatInputProps) {
  const [text, setText] = useState("")

  function handleSend() {
    const trimmed = text.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setText("")
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="p-4 border-t flex gap-2 items-end">
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled}
        className="flex min-h-[60px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 resize-none"
      />
      <Button
        size="icon"
        onClick={disabled ? onCancel : handleSend}
        disabled={disabled ? !onCancel : !text.trim()}
        className="shrink-0 h-10 w-10"
      >
        {disabled ? (
          onCancel ? (
            <X className="h-4 w-4" />
          ) : (
            <Loader2 className="h-4 w-4 animate-spin" />
          )
        ) : (
          <Send className="h-4 w-4" />
        )}
      </Button>
    </div>
  )
}
