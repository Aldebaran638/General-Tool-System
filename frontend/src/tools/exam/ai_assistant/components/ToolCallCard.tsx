import { CheckCircle2, Wrench } from "lucide-react"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import type { AIToolCall } from "../types"

const TOOL_LABELS: Record<AIToolCall["name"], string> = {
  create_question: "创建题目",
  edit_question: "编辑题目",
  delete_question: "删除题目",
  search_questions: "搜索题目",
  get_paper_summary: "试卷汇总",
  batch_create_questions: "批量创建题目",
}

interface ToolCallCardProps {
  toolCall: AIToolCall
}

export function ToolCallCard({ toolCall }: ToolCallCardProps) {
  return (
    <Card className="border-dashed bg-muted/40">
      <CardHeader className="py-3">
        <CardTitle className="text-sm flex items-center gap-2">
          <Wrench className="h-4 w-4 text-primary" />
          {TOOL_LABELS[toolCall.name] ?? toolCall.name}
          <CheckCircle2 className="h-4 w-4 text-green-600 ml-auto" />
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-0 pb-3">
        <pre className="text-xs text-muted-foreground overflow-x-auto">
          {JSON.stringify(toolCall.arguments, null, 2)}
        </pre>
      </CardContent>
    </Card>
  )
}
