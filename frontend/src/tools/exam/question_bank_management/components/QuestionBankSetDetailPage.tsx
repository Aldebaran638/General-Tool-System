import { useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useNavigate, useParams } from "@tanstack/react-router"
import {
  ArrowLeft,
  CheckCircle2,
  Loader2,
  Pencil,
  Plus,
  Trash2,
  XCircle,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

import { getSet, createQuestion, updateQuestion, deleteQuestion } from "../api"
import type {
  QuestionBankQuestion,
  QuestionBankQuestionCreate,
} from "../types"

const QUESTION_TYPES: {
  value: QuestionBankQuestionCreate["question_type"]
  label: string
}[] = [
  { value: "SINGLE_CHOICE", label: "单选题" },
  { value: "MULTIPLE_CHOICE", label: "多选题" },
  { value: "TRUE_FALSE", label: "判断题" },
]

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

function emptyQuestion(): QuestionBankQuestionCreate {
  return {
    question_type: "SINGLE_CHOICE",
    stem: "",
    score: 1,
    difficulty: "MEDIUM",
    sort_no: 1,
    analysis: "",
    options: defaultOptions("SINGLE_CHOICE"),
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

  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingQuestion, setEditingQuestion] = useState<QuestionBankQuestion | null>(null)
  const [form, setForm] = useState<QuestionBankQuestionCreate>(emptyQuestion())
  const [deleteTarget, setDeleteTarget] = useState<QuestionBankQuestion | null>(null)

  const setQuery = useQuery({
    queryKey: ["questionBankSet", setId],
    queryFn: () => getSet(setId),
  })

  const createMutation = useMutation({
    mutationFn: (data: QuestionBankQuestionCreate) => createQuestion(setId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["questionBankSet", setId] })
      closeDialog()
    },
  })

  const updateMutation = useMutation({
    mutationFn: (data: QuestionBankQuestionCreate) => {
      if (!editingQuestion) throw new Error("No question selected")
      return updateQuestion(setId, editingQuestion.id, data)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["questionBankSet", setId] })
      closeDialog()
    },
  })

  const deleteMutation = useMutation({
    mutationFn: ({ setId: sid, questionId }: { setId: string; questionId: string }) =>
      deleteQuestion(sid, questionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["questionBankSet", setId] })
      setDeleteTarget(null)
    },
  })

  const set_ = setQuery.data?.set
  const questions = setQuery.data?.questions ?? []

  function openCreate() {
    setEditingQuestion(null)
    setForm({
      ...emptyQuestion(),
      sort_no: questions.length + 1,
    })
    setDialogOpen(true)
  }

  function openEdit(q: QuestionBankQuestion) {
    setEditingQuestion(q)
    setForm(toCreateForm(q))
    setDialogOpen(true)
  }

  function closeDialog() {
    setDialogOpen(false)
    setEditingQuestion(null)
    setForm(emptyQuestion())
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!form.stem.trim()) return
    if (form.options.length === 0) return
    if (editingQuestion) {
      updateMutation.mutate(form)
    } else {
      createMutation.mutate(form)
    }
  }

  function updateOption(
    idx: number,
    patch: Partial<QuestionBankQuestionCreate["options"][number]>,
  ) {
    setForm({
      ...form,
      options: form.options.map((o, i) => (i === idx ? { ...o, ...patch } : o)),
    })
  }

  function addOption() {
    const nextKey = String.fromCharCode(65 + form.options.length)
    setForm({
      ...form,
      options: [
        ...form.options,
        {
          option_key: nextKey,
          option_text: "",
          is_correct: false,
          sort_no: form.options.length + 1,
        },
      ],
    })
  }

  function removeOption(idx: number) {
    const opts = form.options.filter((_, i) => i !== idx)
    setForm({
      ...form,
      options: opts.map((o, i) => ({
        ...o,
        option_key: String.fromCharCode(65 + i),
        sort_no: i + 1,
      })),
    })
  }

  function toggleCorrect(idx: number) {
    if (
      form.question_type === "SINGLE_CHOICE" ||
      form.question_type === "TRUE_FALSE"
    ) {
      setForm({
        ...form,
        options: form.options.map((o, i) => ({
          ...o,
          is_correct: i === idx,
        })),
      })
    } else {
      updateOption(idx, { is_correct: !form.options[idx].is_correct })
    }
  }

  function changeType(type: QuestionBankQuestionCreate["question_type"]) {
    setForm({
      ...form,
      question_type: type,
      options: defaultOptions(type),
    })
  }

  const isMutating = createMutation.isPending || updateMutation.isPending

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
              {set_.description || "暂无描述"} · 共 {questions.length} 题
            </p>
          </div>
        </div>
        <Button onClick={openCreate}>
          <Plus className="mr-2 h-4 w-4" />
          添加题目
        </Button>
      </div>

      {questions.length === 0 && (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            暂无题目，点击"添加题目"创建第一道题
          </CardContent>
        </Card>
      )}

      {questions.map((q) => (
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
              <span className="text-sm text-muted-foreground">第 {q.sort_no} 题 · {q.score} 分</span>
            </div>
            <div className="flex items-center gap-1">
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={() => openEdit(q)}
              >
                <Pencil className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 text-red-500"
                onClick={() => setDeleteTarget(q)}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <p className="text-sm font-medium">{q.stem}</p>
            <div className="grid gap-2">
              {q.options.map((opt) => (
                <div key={opt.id} className="flex items-center gap-2 text-sm">
                  <span
                    className={`inline-flex h-6 w-6 items-center justify-center rounded text-xs font-medium ${
                      opt.is_correct
                        ? "bg-green-600 text-white"
                        : "bg-muted text-muted-foreground"
                    }`}
                  >
                    {opt.option_key}
                  </span>
                  <span>{opt.option_text}</span>
                </div>
              ))}
            </div>
            {q.analysis && (
              <div className="text-sm text-muted-foreground">
                <span className="font-medium">解析：</span> {q.analysis}
              </div>
            )}
          </CardContent>
        </Card>
      ))}

      {/* Add/Edit dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {editingQuestion ? "编辑题目" : "添加题目"}
            </DialogTitle>
            <DialogDescription>
              {editingQuestion
                ? "修改题目内容、选项和正确答案。"
                : "在题库中新增一道题目。"}
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="flex flex-col gap-5">
            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label htmlFor="q-type">题型</Label>
                <Select
                  value={form.question_type}
                  onValueChange={(v) =>
                    changeType(v as QuestionBankQuestionCreate["question_type"])
                  }
                >
                  <SelectTrigger id="q-type">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {QUESTION_TYPES.map((t) => (
                      <SelectItem key={t.value} value={t.value}>
                        {t.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="grid gap-2">
                <Label htmlFor="q-score">分值</Label>
                <Input
                  id="q-score"
                  type="number"
                  min={0}
                  step={0.5}
                  value={form.score}
                  onChange={(e) =>
                    setForm({ ...form, score: Number(e.target.value) })
                  }
                  required
                />
              </div>
            </div>

            <div className="grid gap-2">
              <Label htmlFor="q-stem">题干</Label>
              <Textarea
                id="q-stem"
                value={form.stem}
                onChange={(e) => setForm({ ...form, stem: e.target.value })}
                placeholder="请输入题目内容"
                rows={3}
                required
              />
            </div>

            <div className="grid gap-2">
              <Label>选项</Label>
              <div className="flex flex-col gap-2">
                {form.options.map((opt, idx) => (
                  <div key={idx} className="flex items-center gap-2">
                    <Button
                      type="button"
                      variant={opt.is_correct ? "default" : "outline"}
                      size="sm"
                      className={`w-8 h-8 ${opt.is_correct ? "bg-green-600 hover:bg-green-700" : ""}`}
                      onClick={() => toggleCorrect(idx)}
                    >
                      {opt.is_correct ? (
                        <CheckCircle2 className="h-4 w-4" />
                      ) : (
                        opt.option_key
                      )}
                    </Button>
                    <Input
                      value={opt.option_key}
                      onChange={(e) =>
                        updateOption(idx, { option_key: e.target.value })
                      }
                      placeholder="选项键"
                      className="w-20"
                      disabled={form.question_type === "TRUE_FALSE"}
                    />
                    <Input
                      value={opt.option_text}
                      onChange={(e) =>
                        updateOption(idx, { option_text: e.target.value })
                      }
                      placeholder={
                        form.question_type === "TRUE_FALSE"
                          ? opt.option_text
                          : `选项 ${opt.option_key}`
                      }
                      className="flex-1"
                      disabled={form.question_type === "TRUE_FALSE"}
                    />
                    <Input
                      type="number"
                      value={opt.sort_no ?? 0}
                      onChange={(e) =>
                        updateOption(idx, { sort_no: Number(e.target.value) })
                      }
                      placeholder="排序"
                      className="w-20"
                    />
                    {form.question_type !== "TRUE_FALSE" && form.options.length > 2 && (
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 text-red-400"
                        onClick={() => removeOption(idx)}
                      >
                        <XCircle className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                ))}
              </div>
              {form.question_type !== "TRUE_FALSE" && form.options.length < 10 && (
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  className="w-fit"
                  onClick={addOption}
                >
                  <Plus className="mr-1 h-3 w-3" />
                  添加选项
                </Button>
              )}
            </div>

            <div className="grid gap-2">
              <Label htmlFor="q-analysis">解析（可选）</Label>
              <Textarea
                id="q-analysis"
                value={form.analysis ?? ""}
                onChange={(e) => setForm({ ...form, analysis: e.target.value })}
                placeholder="请输入答案解析"
                rows={2}
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="q-sort">排序号</Label>
              <Input
                id="q-sort"
                type="number"
                value={form.sort_no}
                onChange={(e) => setForm({ ...form, sort_no: Number(e.target.value) })}
              />
            </div>

            {(createMutation.isError || updateMutation.isError) && (
              <p className="text-sm text-red-600">
                {(
                  (createMutation.error ?? updateMutation.error) as Error
                )?.message}
              </p>
            )}

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={closeDialog}
              >
                取消
              </Button>
              <Button type="submit" disabled={isMutating}>
                {isMutating && (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                )}
                保存
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

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
                deleteMutation.mutate({ setId, questionId: deleteTarget.id })
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
