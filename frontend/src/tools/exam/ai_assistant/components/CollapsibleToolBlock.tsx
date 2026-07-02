import { useState } from "react"
import { ChevronDown, Sparkles } from "lucide-react"

import type { AIToolCall } from "../types"

const nameMap: Record<string, string> = {
  create_question: "创建题目",
  batch_create_questions: "批量创建题目",
  edit_question: "编辑题目",
  delete_question: "删除题目",
  search_questions: "搜索题目",
  get_paper_summary: "获取试卷摘要",
}

interface CollapsibleToolBlockProps {
  toolCall: AIToolCall
  result?: string
}

export function CollapsibleToolBlock({ toolCall, result }: CollapsibleToolBlockProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const summary = nameMap[toolCall.name] || toolCall.name

  return (
    <div className="w-full px-2 md:px-4 transition-all duration-300">
      <div className="rounded-xl overflow-hidden border bg-muted/40 hover:border-muted-foreground/20">
        <button
          type="button"
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full px-4 py-2.5 flex items-center justify-between cursor-pointer select-none text-left"
        >
          <div className="flex items-center gap-2 text-[11px] leading-tight">
            <div className="p-1 rounded-md bg-primary/10 border border-primary/20 text-primary">
              <Sparkles className="w-3 h-3" />
            </div>
            <div className="flex items-center gap-1.5 flex-wrap">
              <span className="font-semibold font-mono text-primary">
                {toolCall.name}
              </span>
              <span className="text-muted-foreground">·</span>
              <span className="text-muted-foreground">{summary}</span>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0 pl-2">
            <span className="text-[9px] px-1.5 py-0.5 rounded font-mono bg-emerald-500/10 text-emerald-500 border border-emerald-500/20">
              SUCCESS
            </span>
            <ChevronDown
              className={`w-3.5 h-3.5 text-muted-foreground transition-transform duration-300 ${
                isExpanded ? "rotate-180" : ""
              }`}
            />
          </div>
        </button>

        {isExpanded && (
          <div className="px-4 py-3 border-t font-mono text-[10px] space-y-2.5 leading-relaxed bg-muted/60">
            <div>
              <span className="text-[9px] text-muted-foreground block mb-1 uppercase tracking-wider font-bold">
                Arguments:
              </span>
              <pre className="p-2 rounded-lg text-left overflow-x-auto whitespace-pre-wrap bg-black/5 dark:bg-white/5">
                {JSON.stringify(toolCall.arguments, null, 2)}
              </pre>
            </div>
            {result && (
              <div>
                <span className="text-[9px] text-muted-foreground block mb-1 uppercase tracking-wider font-bold">
                  Response:
                </span>
                <pre className="p-2 rounded-lg text-left overflow-x-auto whitespace-pre-wrap bg-black/5 dark:bg-white/5">
                  {result}
                </pre>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
