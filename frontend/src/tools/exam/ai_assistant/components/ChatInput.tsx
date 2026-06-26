import { useId, useRef, useState } from "react"
import { Loader2, Paperclip, Send, X } from "lucide-react"

import { Button } from "@/components/ui/button"

interface ChatInputProps {
  onSend: (message: string, files: File[]) => void
  onCancel?: () => void
  disabled?: boolean
  placeholder?: string
  files?: File[]
  onFilesChange?: (files: File[]) => void
  accept?: string
}

export function ChatInput({
  onSend,
  onCancel,
  disabled = false,
  placeholder = "输入消息...",
  files = [],
  onFilesChange,
  accept,
}: ChatInputProps) {
  const [text, setText] = useState("")
  const fileInputRef = useRef<HTMLInputElement>(null)
  const inputId = useId()

  function handleSend() {
    const trimmed = text.trim()
    if ((!trimmed && files.length === 0) || disabled) return
    onSend(trimmed, files)
    setText("")
    onFilesChange?.([])
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  function handleFileSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const selected = e.target.files
    if (!selected || selected.length === 0) return
    const newFiles = [...files, ...Array.from(selected)]
    onFilesChange?.(newFiles)
    e.target.value = ""
  }

  function removeFile(index: number) {
    onFilesChange?.(files.filter((_, i) => i !== index))
  }

  return (
    <div className="p-4 border-t bg-background flex flex-col gap-2">
      {files.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {files.map((file, idx) => (
            <div
              key={`${file.name}-${idx}`}
              className="flex items-center gap-1.5 text-xs bg-muted px-2 py-1 rounded-md border"
            >
              <span className="truncate max-w-[150px]">{file.name}</span>
              <button
                type="button"
                onClick={() => removeFile(idx)}
                className="text-muted-foreground hover:text-foreground"
                disabled={disabled}
              >
                <X className="h-3 w-3" />
              </button>
            </div>
          ))}
        </div>
      )}

      <div className="flex items-end gap-2 rounded-2xl border bg-muted/50 p-2 transition-all focus-within:ring-1 focus-within:ring-ring focus-within:bg-muted">
        <input
          id={inputId}
          ref={fileInputRef}
          type="file"
          multiple
          className="hidden"
          accept={accept}
          onChange={handleFileSelect}
          disabled={disabled}
        />
        <Button
          asChild
          variant="ghost"
          size="icon"
          disabled={disabled}
          className="shrink-0 h-9 w-9 cursor-pointer rounded-full"
          title="上传文件"
        >
          <label htmlFor={inputId} className="flex items-center justify-center">
            <Paperclip className="h-4 w-4" />
          </label>
        </Button>

        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          rows={1}
          className="flex min-h-[36px] max-h-[120px] w-full bg-transparent px-2 py-2 text-sm ring-0 border-0 placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-0 disabled:cursor-not-allowed disabled:opacity-50 resize-none"
        />
        <Button
          size="icon"
          onClick={disabled ? onCancel : handleSend}
          disabled={disabled ? !onCancel : !text.trim() && files.length === 0}
          className="shrink-0 h-9 w-9 rounded-full"
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
    </div>
  )
}
