import React from "react"

function parseInlineMarkdown(text: string): React.ReactNode[] {
  if (!text) return []
  const regex = /(\*\*.*?\*\*|`.*?`)/g
  const segments = text.split(regex)

  return segments.map((seg, idx) => {
    if (seg.startsWith("**") && seg.endsWith("**")) {
      return (
        <strong key={idx} className="font-bold text-foreground">
          {seg.slice(2, -2)}
        </strong>
      )
    }
    if (seg.startsWith("`") && seg.endsWith("`")) {
      return (
        <code
          key={idx}
          className="font-mono text-xs bg-muted px-1.5 py-0.5 rounded border"
        >
          {seg.slice(1, -1)}
        </code>
      )
    }
    return <span key={idx}>{seg}</span>
  })
}

interface MarkdownContentProps {
  text: string
  className?: string
}

export function MarkdownContent({ text, className = "" }: MarkdownContentProps) {
  if (!text) return null
  const lines = text.split("\n")

  return (
    <div className={`space-y-2 ${className}`}>
      {lines.map((line, lineIdx) => {
        if (line.startsWith("### ")) {
          return (
            <h3 key={lineIdx} className="text-base font-bold text-primary mt-3 mb-1">
              {parseInlineMarkdown(line.slice(4))}
            </h3>
          )
        }
        if (line.startsWith("## ")) {
          return (
            <h2
              key={lineIdx}
              className="text-lg font-bold text-primary mt-4 mb-2 border-b pb-1"
            >
              {parseInlineMarkdown(line.slice(3))}
            </h2>
          )
        }
        if (line.startsWith("# ")) {
          return (
            <h1 key={lineIdx} className="text-xl font-bold text-primary mt-5 mb-2">
              {parseInlineMarkdown(line.slice(2))}
            </h1>
          )
        }

        const numberedMatch = line.match(/^(\d+)\.\s(.*)/)
        if (numberedMatch) {
          return (
            <div key={lineIdx} className="flex gap-2.5 ml-2 items-start">
              <span className="font-mono text-primary font-bold shrink-0">
                {numberedMatch[1]}.
              </span>
              <span className="text-foreground/90">
                {parseInlineMarkdown(numberedMatch[2])}
              </span>
            </div>
          )
        }

        const bulletMatch = line.match(/^([*\-])\s(.*)/)
        if (bulletMatch) {
          return (
            <div key={lineIdx} className="flex gap-2.5 ml-3 items-start">
              <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-primary shrink-0" />
              <span className="text-foreground/90">
                {parseInlineMarkdown(bulletMatch[2])}
              </span>
            </div>
          )
        }

        if (line.trim() === "") {
          return <div key={lineIdx} className="h-2" />
        }

        return (
          <p key={lineIdx} className="text-foreground/90 leading-relaxed">
            {parseInlineMarkdown(line)}
          </p>
        )
      })}
    </div>
  )
}
