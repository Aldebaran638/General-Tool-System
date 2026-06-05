/**
 * Question Bank Preview Page — online preview of exam paper
 */

import { useQuery } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import {
  AlertCircle,
  ArrowLeft,
  BookOpen,
  CheckCircle2,
  Download,
  Loader2,
} from "lucide-react"
import { toast } from "sonner"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import type { QuestionPublic } from "../api"
import { downloadQuestionBank, getQuestionBankDetail } from "../api"

function QuestionTypeBadge({ type }: { type: string }) {
  switch (type) {
    case "SINGLE_CHOICE":
      return <Badge variant="outline">单选</Badge>
    case "MULTIPLE_CHOICE":
      return <Badge variant="outline">多选</Badge>
    case "TRUE_FALSE":
      return <Badge variant="outline">判断</Badge>
    default:
      return <Badge variant="outline">{type}</Badge>
  }
}

function QuestionCard({
  question,
  index,
}: {
  question: QuestionPublic
  index: number
}) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <Badge variant="secondary" className="font-mono">
            {index + 1}
          </Badge>
          <QuestionTypeBadge type={question.question_type} />
          <span className="text-sm text-muted-foreground">
            {question.score} 分
          </span>
        </div>
      </CardHeader>
      <CardContent>
        <p className="mb-4 text-base leading-relaxed">{question.stem}</p>
        <div className="flex flex-col gap-2">
          {question.options.map((opt) => (
            <div
              key={opt.id}
              className={`flex items-center gap-3 rounded-md px-3 py-2.5 transition-colors ${
                opt.is_correct
                  ? "bg-green-50 border border-green-200 dark:bg-green-950/30 dark:border-green-800"
                  : "bg-muted/50"
              }`}
            >
              <span className="font-medium text-sm w-6 text-center">
                {opt.option_key}.
              </span>
              <span className="flex-1">{opt.option_text}</span>
              {opt.is_correct && (
                <Badge
                  variant="default"
                  className="ml-auto bg-green-600 hover:bg-green-700 flex-shrink-0"
                >
                  <CheckCircle2 className="mr-1 h-3 w-3" />
                  正确答案
                </Badge>
              )}
            </div>
          ))}
        </div>
        {question.analysis && (
          <div className="mt-4 p-3 bg-muted rounded-md">
            <p className="text-sm text-muted-foreground">
              <span className="font-medium">解析：</span>
              {question.analysis}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

export function QuestionBankPreviewPage() {
  const examId = window.location.pathname.split("/").filter(Boolean).pop() ?? ""
  const navigate = useNavigate()

  const detailQuery = useQuery({
    queryKey: ["questionBankDetail", examId],
    queryFn: () => getQuestionBankDetail(examId),
    enabled: Boolean(examId),
  })

  const detail = detailQuery.data

  function handleBack() {
    window.history.back()
  }

  async function handleDownload() {
    try {
      await downloadQuestionBank(examId)
    } catch (error) {
      toast.error("下载失败", {
        description: error instanceof Error ? error.message : "请稍后重试",
      })
    }
  }

  // Loading state
  if (detailQuery.isLoading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          <p className="text-muted-foreground">加载试卷中...</p>
        </div>
      </div>
    )
  }

  // Error state
  if (detailQuery.isError) {
    return (
      <div className="flex flex-col items-center justify-center py-24 gap-4">
        <div className="rounded-full bg-destructive/10 p-4">
          <AlertCircle className="h-12 w-12 text-destructive" />
        </div>
        <h3 className="text-lg font-semibold">加载失败</h3>
        <p className="text-muted-foreground text-center max-w-sm">
          {detailQuery.error?.message || "无法加载试卷内容，请稍后重试"}
        </p>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleBack}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            返回列表
          </Button>
          <Button variant="outline" onClick={() => detailQuery.refetch()}>
            重试
          </Button>
        </div>
      </div>
    )
  }

  // Not found
  if (!detail) {
    return (
      <div className="flex flex-col items-center justify-center py-24 gap-4">
        <div className="rounded-full bg-muted p-5">
          <BookOpen className="h-14 w-14 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-semibold">试卷不存在或未生成</h3>
        <p className="text-muted-foreground text-center max-w-sm">
          请检查试卷是否已生成，或联系管理员
        </p>
        <Button variant="outline" onClick={handleBack}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          返回列表
        </Button>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={handleBack}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">
              {detail.exam_name}
            </h1>
            <p className="text-muted-foreground">
              {detail.question_count} 题 · 总分 {detail.total_score}
            </p>
          </div>
        </div>
        <Button onClick={handleDownload}>
          <Download className="mr-2 h-4 w-4" />
          下载 docx
        </Button>
      </div>

      {/* Questions */}
      <div className="flex flex-col gap-4">
        {detail.questions
          .sort((a, b) => a.sort_no - b.sort_no)
          .map((q, idx) => (
            <QuestionCard key={q.id} question={q} index={idx} />
          ))}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between rounded-lg border bg-card px-4 py-3">
        <span className="text-sm text-muted-foreground">
          共 {detail.question_count} 题，总分 {detail.total_score}
        </span>
        <Button variant="outline" onClick={handleBack}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          返回列表
        </Button>
      </div>
    </div>
  )
}
