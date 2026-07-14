import { useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useNavigate, useParams } from "@tanstack/react-router"
import {
  ArrowLeft,
  CheckCircle2,
  Loader2,
  Plus,
  Trash2,
  XCircle,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Card,
  CardContent,
  CardHeader,
} from "@/components/ui/card"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"

import { getSet, createQuestion, updateQuestion, deleteQuestion } from "../api"
import type {
  QuestionBankQuestion,
  QuestionBankQuestionCreate,
} from "../types"

function defaultOptions(
  type: QuestionBankQuestionCreate["question_type"],
): QuestionBankQuestionCreate["options"] {
  if (type === "TRUE_FALSE") {
    return [
      { option_key: "A", option_text: "正确", is_correct: true, sort_no: 1 },
      { option_key: "B", option_text: "错误", is_correct: false, sort_no: 2 },
    ]
  }
  if (type === "MULTIPLE_CHOICE") {
    return [
      { option_key: "A", option_text: "", is_correct: true, sort_no: 1 },
      { option_key: "B", option_text: "", is_correct: true, sort_no: 2 },
    ]
  }
  return [
    { option_key: "A", option_text: "", is_correct: true, sort_no: 1 },
    { option_key: "B", option_text: "", is_correct: false, sort_no: 2 },
  ]
}

function emptyQuestion(type: QuestionBankQuestionCreate["question_type"] = "SINGLE_CHOICE", sortNo: number = 1): QuestionBankQuestionCreate {
  return {
    question_type: type,
    stem: "",
    score: 10,
    difficulty: "MEDIUM",
    sort_no: sortNo,
    analysis: "",
    options: defaultOptions(type),
  }
}

function toCreateForm(q: QuestionBankQuestion): QuestionBankQuestionCreate {
  return {
    question_type: q.question_type,
    stem: q.stem,
    score: q.score,
    difficulty: q.difficulty,
    sort_no: q.sort_no,
    analysis: q.analysis ?? "",
    options: q.options.map((o) => ({
      option_key: o.option_key,
      option_text: o.option_text,
      is_correct: o.is_correct,
      sort_no: o.sort_no,
    })),
  }
}

export function QuestionBankSetDetailPage() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const params = useParams({ from: "/_layout/question-bank-management/$setId" })
  const setId = params.setId

  const [deleteTarget, setDeleteTarget] = useState<QuestionBankQuestion | null>(null)

  const setQuery = useQuery({
    queryKey: ["questionBankSet", setId],
    queryFn: () => getSet(setId),
  })

  const createMutation = useMutation({
    mutationFn: (data: QuestionBankQuestionCreate) => createQuestion(setId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["questionBankSet", setId] })
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ questionId, data }: { questionId: string; data: QuestionBankQuestionCreate }) =>
      updateQuestion(setId, questionId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["questionBankSet", setId] })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: ({ questionId }: { questionId: string }) =>
      deleteQuestion(setId, questionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["questionBankSet", setId] })
      setDeleteTarget(null)
    },
  })

  const set_ = setQuery.data?.set
  const questions = setQuery.data?.questions ?? []

  function addQuestion(type: QuestionBankQuestionCreate["question_type"]) {
    const sortNo = questions.length + 1
    createMutation.mutate(emptyQuestion(type, sortNo))
  }

  function updateQuestionLocal(qIdx: number, patch: Partial<QuestionBankQuestionCreate>) {
    const q = questions[qIdx]
    const updated = { ...toCreateForm(q), ...patch }
    updateMutation.mutate({ questionId: q.id, data: updated })
  }

  function deleteQuestionLocal(qIdx: number) {
    const q = questions[qIdx]
    deleteMutation.mutate({ questionId: q.id })
  }

  function updateOption(qIdx: number, oIdx: number, patch: Partial<{ option_text: string; is_correct: boolean }>) {
    const q = questions[qIdx]
    const form = toCreateForm(q)
    const updatedOptions = form.options.map((o, i) => (i === oIdx ? { ...o, ...patch } : o))
    updateMutation.mutate({ questionId: q.id, data: { ...form, options: updatedOptions } })
  }

  function addOption(qIdx: number) {
    const q = questions[qIdx]
    const form = toCreateForm(q)
    const key = String.fromCharCode(65 + form.options.length)
    const updatedOptions = [
      ...form.options,
      { option_key: key, option_text: "", is_correct: false, sort_no: form.options.length + 1 },
    ]
    updateMutation.mutate({ questionId: q.id, data: { ...form, options: updatedOptions } })
  }

  function removeOption(qIdx: number, oIdx: number) {
    const q = questions[qIdx]
    const form = toCreateForm(q)
    const updatedOptions = form.options
      .filter((_, i) => i !== oIdx)
      .map((o, i) => ({ ...o, option_key: String.fromCharCode(65 + i), sort_no: i + 1 }))
    updateMutation.mutate({ questionId: q.id, data: { ...form, options: updatedOptions } })
  }

  function setCorrectOption(qIdx: number, oIdx: number) {
    const q = questions[qIdx]
    const form = toCreateForm(q)
    let updatedOptions
    if (q.question_type === "SINGLE_CHOICE" || q.question_type === "TRUE_FALSE") {
      updatedOptions = form.options.map((o, i) => ({ ...o, is_correct: i === oIdx }))
    } else {
      updatedOptions = form.options.map((o, i) => (i === oIdx ? { ...o, is_correct: !o.is_correct } : o))
    }
    updateMutation.mutate({ questionId: q.id, data: { ...form, options: updatedOptions } })
  }

  const totalScore = questions.reduce((sum, q) => sum + q.score, 0)

  if (setQuery.isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (!set_) {
    return (
      <div className="text-center py-12 text-muted-foreground">题库不存在</div>
    )
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={() => navigate({ to: "/question-bank-management" })}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">{set_.name}</h1>
            <p className="text-muted-foreground">
              {set_.description || "暂无描述"}
            </p>
          </div>
        </div>
      </div>

      {/* Toolbar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div className="flex gap-2 flex-wrap">
          <Button
            variant="outline"
            size="sm"
            onClick={() => addQuestion("SINGLE_CHOICE")}
          >
            <Plus className="mr-1 h-3 w-3" />
            单选题
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => addQuestion("MULTIPLE_CHOICE")}
          >
            <Plus className="mr-1 h-3 w-3" />
            多选题
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => addQuestion("TRUE_FALSE")}
          >
            <Plus className="mr-1 h-3 w-3" />
            判断题
          </Button>
        </div>
        <div className="flex items-center gap-x-4 gap-y-2 text-sm text-muted-foreground flex-wrap">
          <span>共 {questions.length} 题</span>
          <span>总分 {totalScore}</span>
        </div>
      </div>

      {createMutation.isError && (
        <p className="text-sm text-red-600">
          {(createMutation.error as Error).message}
        </p>
      )}

      {/* Questions */}
      {questions.length === 0 && (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            暂无题目，点击上方按钮添加
          </CardContent>
        </Card>
      )}

      {questions.map((q, qIdx) => (
        <Card key={q.id}>
          <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-3">
            <div className="flex items-center gap-3">
              <Badge variant="outline">
                {q.question_type === "SINGLE_CHOICE"
                  ? "单选"
                  : q.question_type === "MULTIPLE_CHOICE"
                    ? "多选"
                    : "判断"}
              </Badge>
              <span className="text-sm text-muted-foreground">
                第 {q.sort_no} 题
              </span>
            </div>
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-1 text-sm">
                <Label className="text-xs">分值</Label>
                <Input
                  type="number"
                  className="w-16 h-7 text-sm"
                  value={q.score}
                  onChange={(e) => updateQuestionLocal(qIdx, { score: Number(e.target.value) })}
                />
              </div>
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7 text-red-500"
                onClick={() => setDeleteTarget(q)}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <div className="grid gap-2">
              <Label>题干</Label>
              <textarea
                className="flex min-h-[60px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                value={q.stem}
                onChange={(e) => updateQuestionLocal(qIdx, { stem: e.target.value })}
                placeholder="请输入题目内容"
              />
            </div>
            <div className="grid gap-2">
              <Label>选项</Label>
              {q.options.map((opt, oIdx) => (
                <div key={oIdx} className="flex items-center gap-2">
                  <Button
                    variant={opt.is_correct ? "default" : "outline"}
                    size="sm"
                    className={`w-8 h-8 ${opt.is_correct ? "bg-green-600 hover:bg-green-700" : ""}`}
                    onClick={() => setCorrectOption(qIdx, oIdx)}
                  >
                    {opt.is_correct ? (
                      <CheckCircle2 className="h-4 w-4" />
                    ) : (
                      opt.option_key
                    )}
                  </Button>
                  <Input
                    value={opt.option_text}
                    onChange={(e) => updateOption(qIdx, oIdx, { option_text: e.target.value })}
                    disabled={q.question_type === "TRUE_FALSE"}
                    placeholder={
                      q.question_type === "TRUE_FALSE"
                        ? opt.option_text
                        : `选项 ${opt.option_key}`
                    }
                    className="flex-1"
                  />
                  {q.question_type !== "TRUE_FALSE" && q.options.length > 2 && (
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 text-red-400"
                      onClick={() => removeOption(qIdx, oIdx)}
                    >
                      <XCircle className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              ))}
              {q.question_type !== "TRUE_FALSE" && q.options.length < 10 && (
                <Button
                  variant="outline"
                  size="sm"
                  className="w-fit"
                  onClick={() => addOption(qIdx)}
                >
                  <Plus className="mr-1 h-3 w-3" />
                  添加选项
                </Button>
              )}
            </div>
            <div className="grid gap-2">
              <Label>答案解析（可选）</Label>
              <textarea
                className="flex min-h-[60px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                value={q.analysis ?? ""}
                onChange={(e) => updateQuestionLocal(qIdx, { analysis: e.target.value })}
                placeholder="提交后展示给学员的解析"
              />
            </div>
          </CardContent>
        </Card>
      ))}

      {/* Delete confirmation */}
      <Dialog open={!!deleteTarget} onOpenChange={() => setDeleteTarget(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>确认删除</DialogTitle>
            <DialogDescription>
              确定要删除这道题吗？此操作不可撤销。
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteTarget(null)}>
              取消
            </Button>
            <Button
              variant="destructive"
              onClick={() =>
                deleteTarget &&
                deleteMutation.mutate({ questionId: deleteTarget.id })
              }
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              删除
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
