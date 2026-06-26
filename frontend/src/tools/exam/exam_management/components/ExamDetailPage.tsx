import { useState, useEffect } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import {
  ArrowLeft,
  Save,
  Send,
  Archive,
  Loader2,
  Plus,
  Trash2,
  GripVertical,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Search,
  X,
  Users,
  Bot,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"

import useAuth from "@/hooks/useAuth"
import { cn } from "@/lib/utils"
import { AIAssistantPanel } from "../../ai_assistant/components/AIAssistantPanel"

import {
  getExam,
  updateExam,
  publishExam,
  validateExam,
  archiveExam,
  getPaper,
  savePaper,
  listParticipants,
  addParticipantsByCenters,
  addParticipantsByDepartments,
  addParticipantsByUsers,
  removeParticipant,
  searchUsers,
  getCenters,
  getDepartmentsOnly,
  getExamStatistics,
  getParticipantsByStatus,
} from "../api"
import { apiDatetimeToLocal, datetimeLocalToApi } from "../datetime"
import type { WecomUser, WecomDepartment } from "../api"
import type { Exam, ExamUpdate, QuestionCreate } from "../types"
import { TrainerSearchSelect } from "./TrainerSearchSelect"
import { listExamCategories } from "../../category_management/api"

// ─── Helpers ────────────────────────────────────────────────────────────────

const EXAM_TOTAL_SCORE = 100

function fmtDate(s: string | null): string {
  if (!s) return "—"
  return new Date(s).toLocaleString("zh-CN", { hour12: false })
}

// ─── Exam Settings Tab ──────────────────────────────────────────────────────

function ExamSettingsTab({ exam }: { exam: Exam }) {
  const queryClient = useQueryClient()
  const [form, setForm] = useState<ExamUpdate>({
    name: exam.name,
    trainer_ids: exam.trainer_ids ?? [],
    category_id: exam.category_id ?? null,
    start_at: apiDatetimeToLocal(exam.start_at),
    end_at: apiDatetimeToLocal(exam.end_at),
    duration_minutes: exam.duration_minutes,
    attempt_limit_type: exam.attempt_limit_type,
    attempt_limit_count: exam.attempt_limit_count ?? undefined,
    pass_score: exam.pass_score,
    submit_rule: exam.submit_rule,
    show_answer: exam.show_answer,
    random_question_order: exam.random_question_order,
    random_option_order: exam.random_option_order,
  })

  const categoriesQuery = useQuery({
    queryKey: ["examCategories"],
    queryFn: listExamCategories,
  })

  const categories = categoriesQuery.data?.data ?? []

  const updateMutation = useMutation({
    mutationFn: (data: ExamUpdate) => updateExam(exam.id, data),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["exam", exam.id] }),
  })

  const isDraft = exam.status === "DRAFT"

  function handleSave() {
    const data: ExamUpdate = {
      ...form,
      start_at: datetimeLocalToApi(form.start_at),
      end_at: datetimeLocalToApi(form.end_at),
    }
    updateMutation.mutate(data)
  }

  return (
    <div className="flex flex-col gap-6 max-w-2xl mx-auto">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">基本信息</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <div className="grid gap-2">
            <Label>考试名称</Label>
            <Input
              value={form.name ?? ""}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                setForm({ ...form, name: e.target.value })
              }
              disabled={!isDraft}
            />
          </div>
          <div className="grid gap-2">
            <Label>试卷分类</Label>
            <Select
              value={form.category_id?.toString() ?? "none"}
              onValueChange={(v: string) =>
                setForm({ ...form, category_id: v === "none" ? null : Number(v) })
              }
              disabled={!isDraft}
            >
              <SelectTrigger>
                <SelectValue placeholder="选择分类（可选）" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">无分类</SelectItem>
                {categories.map((cat) => (
                  <SelectItem key={cat.id} value={cat.id.toString()}>
                    {cat.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="grid gap-2">
            <Label>培训讲师（可选）</Label>
            <TrainerSearchSelect
              selectedTrainerIds={form.trainer_ids ?? []}
              selectedTrainers={exam.trainers ?? []}
              onSelectionChange={(ids) => setForm({ ...form, trainer_ids: ids })}
              disabled={!isDraft}
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="grid gap-2">
              <Label>开始时间</Label>
              <Input
                type="datetime-local"
                value={form.start_at ?? ""}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setForm({ ...form, start_at: e.target.value })
                }
                disabled={!isDraft}
              />
            </div>
            <div className="grid gap-2">
              <Label>结束时间</Label>
              <Input
                type="datetime-local"
                value={form.end_at ?? ""}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setForm({ ...form, end_at: e.target.value })
                }
                disabled={!isDraft}
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="grid gap-2">
              <Label>考试时长（分钟）</Label>
              <Input
                type="number"
                value={form.duration_minutes ?? ""}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setForm({ ...form, duration_minutes: Number(e.target.value) })
                }
                disabled={!isDraft}
              />
            </div>
            <div className="grid gap-2">
              <Label>及格分数</Label>
              <Input
                type="number"
                value={form.pass_score ?? ""}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setForm({ ...form, pass_score: Number(e.target.value) })
                }
                disabled={!isDraft}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">考试规则</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="grid gap-2">
              <Label>考试次数</Label>
              <Select
                value={form.attempt_limit_type ?? "UNLIMITED"}
                onValueChange={(v: string) =>
                  setForm({
                    ...form,
                    attempt_limit_type: v as "UNLIMITED" | "LIMITED",
                  })
                }
                disabled={!isDraft}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="UNLIMITED">不限制</SelectItem>
                  <SelectItem value="LIMITED">限制次数</SelectItem>
                </SelectContent>
              </Select>
            </div>
            {form.attempt_limit_type === "LIMITED" && (
              <div className="grid gap-2">
                <Label>最大次数</Label>
                <Input
                  type="number"
                  value={form.attempt_limit_count ?? ""}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                    setForm({
                      ...form,
                      attempt_limit_count: Number(e.target.value),
                    })
                  }
                  disabled={!isDraft}
                />
              </div>
            )}
          </div>
          <div className="grid gap-2">
            <Label>交卷要求</Label>
            <Select
              value={form.submit_rule ?? "ALL_REQUIRED"}
              onValueChange={(v: string) =>
                setForm({ ...form, submit_rule: v as "ALL_REQUIRED" | "ANY" })
              }
              disabled={!isDraft}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ALL_REQUIRED">全部题目必须作答</SelectItem>
                <SelectItem value="ANY">不限制</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="flex items-center justify-between">
            <div>
              <Label>提交后展示正确答案</Label>
              <p className="text-sm text-muted-foreground">
                学员提交试卷后是否可以查看正确答案
              </p>
            </div>
            <Checkbox
              checked={form.show_answer ?? false}
              onCheckedChange={(v: boolean) =>
                setForm({ ...form, show_answer: v })
              }
              disabled={!isDraft}
            />
          </div>
          <div className="flex items-center justify-between">
            <div>
              <Label>随机题目顺序</Label>
              <p className="text-sm text-muted-foreground">
                每位学员看到的题目顺序不同
              </p>
            </div>
            <Checkbox
              checked={form.random_question_order ?? false}
              onCheckedChange={(v: boolean) =>
                setForm({ ...form, random_question_order: v })
              }
              disabled={!isDraft}
            />
          </div>
          <div className="flex items-center justify-between">
            <div>
              <Label>随机选项顺序</Label>
              <p className="text-sm text-muted-foreground">
                每道题的选项顺序随机打乱
              </p>
            </div>
            <Checkbox
              checked={form.random_option_order ?? false}
              onCheckedChange={(v: boolean) =>
                setForm({ ...form, random_option_order: v })
              }
              disabled={!isDraft}
            />
          </div>
        </CardContent>
      </Card>

      {isDraft && (
        <div className="flex gap-3">
          <Button onClick={handleSave} disabled={updateMutation.isPending}>
            {updateMutation.isPending ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Save className="mr-2 h-4 w-4" />
            )}
            保存
          </Button>
          {updateMutation.isSuccess && (
            <span className="text-sm text-green-600 self-center">已保存</span>
          )}
        </div>
      )}
    </div>
  )
}

// ─── Paper Editor Tab ───────────────────────────────────────────────────────

function PaperEditorTab({
  exam,
  questions,
  setQuestions,
}: {
  exam: Exam
  questions: QuestionCreate[]
  setQuestions: React.Dispatch<React.SetStateAction<QuestionCreate[]>>
}) {
  const queryClient = useQueryClient()

  const saveMutation = useMutation({
    mutationFn: () => savePaper(exam.id, { questions }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["paper", exam.id] })
      queryClient.invalidateQueries({ queryKey: ["exam", exam.id] })
    },
  })

  const isDraft = exam.status === "DRAFT"
  const totalScore = questions.reduce((sum, q) => sum + q.score, 0)
  const scoreDelta = EXAM_TOTAL_SCORE - totalScore
  const isTotalScoreValid = Math.abs(scoreDelta) < 0.001

  function addQuestion(type: QuestionCreate["question_type"]) {
    const sortNo = questions.length + 1
    const defaultOptions =
      type === "TRUE_FALSE"
        ? [
            {
              option_key: "A",
              option_text: "正确",
              is_correct: true,
              sort_no: 1,
            },
            {
              option_key: "B",
              option_text: "错误",
              is_correct: false,
              sort_no: 2,
            },
          ]
        : type === "MULTIPLE_CHOICE"
          ? [
              {
                option_key: "A",
                option_text: "",
                is_correct: true,
                sort_no: 1,
              },
              {
                option_key: "B",
                option_text: "",
                is_correct: true,
                sort_no: 2,
              },
            ]
          : [
              {
                option_key: "A",
                option_text: "",
                is_correct: true,
                sort_no: 1,
              },
              {
                option_key: "B",
                option_text: "",
                is_correct: false,
                sort_no: 2,
              },
            ]
    setQuestions([
      ...questions,
      {
        question_type: type,
        stem: "",
        score: 10,
        sort_no: sortNo,
        options: defaultOptions,
      },
    ])
  }

  function updateQuestion(idx: number, patch: Partial<QuestionCreate>) {
    setQuestions(questions.map((q, i) => (i === idx ? { ...q, ...patch } : q)))
  }

  function deleteQuestion(idx: number) {
    setQuestions(
      questions
        .filter((_, i) => i !== idx)
        .map((q, i) => ({ ...q, sort_no: i + 1 })),
    )
  }

  function moveQuestion(idx: number, dir: -1 | 1) {
    const newIdx = idx + dir
    if (newIdx < 0 || newIdx >= questions.length) return
    const arr = [...questions]
    ;[arr[idx], arr[newIdx]] = [arr[newIdx], arr[idx]]
    setQuestions(arr.map((q, i) => ({ ...q, sort_no: i + 1 })))
  }

  function updateOption(
    qIdx: number,
    oIdx: number,
    patch: Partial<{ option_text: string; is_correct: boolean }>,
  ) {
    updateQuestion(qIdx, {
      options: questions[qIdx].options.map((o, i) =>
        i === oIdx ? { ...o, ...patch } : o,
      ),
    })
  }

  function addOption(qIdx: number) {
    const opts = questions[qIdx].options
    const key = String.fromCharCode(65 + opts.length)
    updateQuestion(qIdx, {
      options: [
        ...opts,
        {
          option_key: key,
          option_text: "",
          is_correct: false,
          sort_no: opts.length + 1,
        },
      ],
    })
  }

  function removeOption(qIdx: number, oIdx: number) {
    const opts = questions[qIdx].options.filter((_, i) => i !== oIdx)
    updateQuestion(qIdx, {
      options: opts.map((o, i) => ({
        ...o,
        option_key: String.fromCharCode(65 + i),
        sort_no: i + 1,
      })),
    })
  }

  function setCorrectOption(qIdx: number, oIdx: number) {
    const q = questions[qIdx]
    if (
      q.question_type === "SINGLE_CHOICE" ||
      q.question_type === "TRUE_FALSE"
    ) {
      updateQuestion(qIdx, {
        options: q.options.map((o, i) => ({ ...o, is_correct: i === oIdx })),
      })
    } else {
      updateOption(qIdx, oIdx, { is_correct: !q.options[oIdx].is_correct })
    }
  }

  return (
    <div className="flex flex-col gap-6">
      {/* Toolbar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div className="flex gap-2 flex-wrap">
          <Button
            variant="outline"
            size="sm"
            onClick={() => addQuestion("SINGLE_CHOICE")}
            disabled={!isDraft}
          >
            <Plus className="mr-1 h-3 w-3" />
            单选题
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => addQuestion("MULTIPLE_CHOICE")}
            disabled={!isDraft}
          >
            <Plus className="mr-1 h-3 w-3" />
            多选题
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => addQuestion("TRUE_FALSE")}
            disabled={!isDraft}
          >
            <Plus className="mr-1 h-3 w-3" />
            判断题
          </Button>
        </div>
        <div className="flex items-center gap-x-4 gap-y-2 text-sm text-muted-foreground flex-wrap">
          <span>共 {questions.length} 题</span>
          <span className={isTotalScoreValid ? "text-emerald-600" : "text-amber-600"}>
            总分 {totalScore} / {EXAM_TOTAL_SCORE}
          </span>
          {!isTotalScoreValid && (
            <span className="inline-flex items-center gap-1 text-amber-600">
              <AlertCircle className="h-3.5 w-3.5" />
              {scoreDelta > 0
                ? `还差 ${scoreDelta} 分`
                : `超出 ${Math.abs(scoreDelta)} 分`}
            </span>
          )}
          {isDraft && (
            <Button
              size="sm"
              onClick={() => saveMutation.mutate()}
              disabled={saveMutation.isPending}
            >
              {saveMutation.isPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Save className="mr-2 h-4 w-4" />
              )}
              保存试卷
            </Button>
          )}
        </div>
      </div>

      {saveMutation.isSuccess && (
        <p className="text-sm text-green-600">试卷已保存</p>
      )}
      {saveMutation.isError && (
        <p className="text-sm text-red-600">
          {(saveMutation.error as Error).message}
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
        <Card key={qIdx}>
          <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-3">
            <div className="flex items-center gap-3">
              {isDraft && (
                <div className="flex flex-col gap-1">
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6"
                    onClick={() => moveQuestion(qIdx, -1)}
                    disabled={qIdx === 0}
                  >
                    <GripVertical className="h-3 w-3 rotate-180" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6"
                    onClick={() => moveQuestion(qIdx, 1)}
                    disabled={qIdx === questions.length - 1}
                  >
                    <GripVertical className="h-3 w-3" />
                  </Button>
                </div>
              )}
              <div>
                <Badge variant="outline" className="mr-2">
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
            </div>
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-1 text-sm">
                <Label className="text-xs">分值</Label>
                <Input
                  type="number"
                  className="w-16 h-7 text-sm"
                  value={q.score}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                    updateQuestion(qIdx, { score: Number(e.target.value) })
                  }
                  disabled={!isDraft}
                />
              </div>
              {isDraft && (
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7 text-red-500"
                  onClick={() => deleteQuestion(qIdx)}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <div className="grid gap-2">
              <Label>题干</Label>
              <textarea
                className="flex min-h-[60px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                value={q.stem}
                onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) =>
                  updateQuestion(qIdx, { stem: e.target.value })
                }
                disabled={!isDraft}
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
                    disabled={!isDraft}
                  >
                    {opt.is_correct ? (
                      <CheckCircle2 className="h-4 w-4" />
                    ) : (
                      opt.option_key
                    )}
                  </Button>
                  <Input
                    value={opt.option_text}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                      updateOption(qIdx, oIdx, { option_text: e.target.value })
                    }
                    disabled={!isDraft || q.question_type === "TRUE_FALSE"}
                    placeholder={
                      q.question_type === "TRUE_FALSE"
                        ? opt.option_text
                        : `选项 ${opt.option_key}`
                    }
                    className="flex-1"
                  />
                  {isDraft &&
                    q.question_type !== "TRUE_FALSE" &&
                    q.options.length > 2 && (
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
              {isDraft &&
                q.question_type !== "TRUE_FALSE" &&
                q.options.length < 10 && (
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
            {isDraft && (
              <div className="grid gap-2">
                <Label>答案解析（可选）</Label>
                <textarea
                  className="flex min-h-[60px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  value={q.analysis ?? ""}
                  onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) =>
                    updateQuestion(qIdx, { analysis: e.target.value })
                  }
                  placeholder="提交后展示给学员的解析"
                />
              </div>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  )
}

// ─── User Search Select Component ────────────────────────────────────────────

interface UserSearchSelectProps {
  selectedUsers: WecomUser[]
  onSelectionChange: (users: WecomUser[]) => void
  disabled?: boolean
}

function UserSearchSelect({
  selectedUsers,
  onSelectionChange,
  disabled,
}: UserSearchSelectProps) {
  const [searchQuery, setSearchQuery] = useState("")

  const searchQuery_ = useQuery({
    queryKey: ["userSearch", searchQuery],
    queryFn: () => searchUsers({ q: searchQuery || undefined, limit: 100 }),
  })

  const users = searchQuery_?.data?.data ?? []
  const isLoading = searchQuery_?.isLoading ?? false

  const selectedUserids = new Set(selectedUsers.map((u) => u.userid))

  function handleToggle(user: WecomUser) {
    if (selectedUserids.has(user.userid)) {
      onSelectionChange(selectedUsers.filter((u) => u.userid !== user.userid))
    } else {
      onSelectionChange([...selectedUsers, user])
    }
  }

  function handleRemove(userid: string) {
    onSelectionChange(selectedUsers.filter((u) => u.userid !== userid))
  }

  return (
    <div className="flex flex-col gap-2">
      {/* Search */}
      <div className="relative">
        <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="输入姓名或 userid 搜索..."
          value={searchQuery}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
            setSearchQuery(e.target.value)
          }
          className="pl-8"
          disabled={disabled}
        />
        {searchQuery && (
          <Button
            variant="ghost"
            size="icon"
            className="absolute right-1 top-1 h-7 w-7"
            onClick={() => setSearchQuery("")}
          >
            <X className="h-4 w-4" />
          </Button>
        )}
      </div>

      {/* Selected tags — fixed min-height to prevent layout shift */}
      <div className="min-h-[40px] flex flex-wrap gap-1.5 content-start">
        {selectedUsers.map((user) => (
          <Badge
            key={user.userid}
            variant="secondary"
            className="pr-1 text-xs max-w-[200px]"
          >
            <span className="mr-1 truncate">{user.name}</span>
            {!disabled && (
              <Button
                variant="ghost"
                size="icon"
                className="h-3.5 w-3.5 ml-0.5 hover:bg-destructive/20 shrink-0"
                onClick={() => handleRemove(user.userid)}
              >
                <X className="h-2.5 w-2.5" />
              </Button>
            )}
          </Badge>
        ))}
      </div>

      {/* User list — fixed height for stable layout */}
      <div className="rounded-md border bg-card h-[240px] overflow-y-auto">
        {isLoading && (
          <div className="flex items-center justify-center h-full text-sm text-muted-foreground">
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            加载中...
          </div>
        )}
        {!isLoading && users.length === 0 && (
          <div className="flex items-center justify-center h-full text-sm text-muted-foreground">
            {searchQuery ? "未找到匹配的用户" : "请输入关键词搜索"}
          </div>
        )}
        {!isLoading &&
          users.map((user) => {
            const isSelected = selectedUserids.has(user.userid)
            return (
              <div
                key={user.userid}
                className={`flex items-center gap-2 px-3 h-10 text-sm hover:bg-muted/50 cursor-pointer border-b border-border/50 last:border-b-0 ${
                  isSelected ? "bg-muted/30" : ""
                }`}
                onClick={() => !disabled && handleToggle(user)}
              >
                <Checkbox
                  checked={isSelected}
                  disabled={disabled}
                  onCheckedChange={() => handleToggle(user)}
                  className="shrink-0"
                />
                <div className="flex flex-col flex-1 min-w-0">
                  <span className="truncate">{user.name}</span>
                </div>
                <span className="text-xs text-muted-foreground shrink-0">
                  {user.userid}
                </span>
              </div>
            )
          })}
      </div>
    </div>
  )
}

// ─── Department Checkbox List ───────────────────────────────────────────────

interface DepartmentCheckboxListProps {
  selectedDepartments: WecomDepartment[]
  onSelectionChange: (departments: WecomDepartment[]) => void
  fetchDepartments: (params: { q?: string; limit?: number }) => Promise<{
    data: WecomDepartment[]
    count: number
  }>
  disabled?: boolean
  placeholder?: string
  label?: string
}

function DepartmentCheckboxList({
  selectedDepartments,
  onSelectionChange,
  fetchDepartments,
  disabled,
  placeholder = "搜索...",
  label,
}: DepartmentCheckboxListProps) {
  const [searchQuery, setSearchQuery] = useState("")
  const query = useQuery({
    queryKey: ["department-checkbox-list", label, searchQuery],
    queryFn: () => fetchDepartments({ q: searchQuery || undefined, limit: 100 }),
  })

  const allDepartments = query.data?.data ?? []
  const selectedIds = new Set(selectedDepartments.map((d) => d.id))

  function toggleDepartment(dept: WecomDepartment) {
    if (selectedIds.has(dept.id)) {
      onSelectionChange(selectedDepartments.filter((d) => d.id !== dept.id))
    } else {
      onSelectionChange([...selectedDepartments, dept])
    }
  }

  function removeDepartment(id: number) {
    onSelectionChange(selectedDepartments.filter((d) => d.id !== id))
  }

  return (
    <div className="flex flex-col gap-2">
      {/* Search */}
      <div className="relative">
        <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder={placeholder}
          value={searchQuery}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
            setSearchQuery(e.target.value)
          }
          className="pl-8"
          disabled={disabled}
        />
        {searchQuery && (
          <Button
            variant="ghost"
            size="icon"
            className="absolute right-1 top-1 h-7 w-7"
            onClick={() => setSearchQuery("")}
          >
            <X className="h-4 w-4" />
          </Button>
        )}
      </div>

      {/* Selected tags — fixed min-height to prevent layout shift */}
      <div className="min-h-[40px] flex flex-wrap gap-1.5 content-start">
        {selectedDepartments.map((dept) => (
          <Badge
            key={dept.id}
            variant="secondary"
            className="pr-1 text-xs max-w-[200px]"
          >
            <span className="mr-1 truncate">{dept.name}</span>
            {!disabled && (
              <Button
                variant="ghost"
                size="icon"
                className="h-3.5 w-3.5 ml-0.5 hover:bg-destructive/20 shrink-0"
                onClick={() => removeDepartment(dept.id)}
              >
                <X className="h-2.5 w-2.5" />
              </Button>
            )}
          </Badge>
        ))}
      </div>

      {/* Checkbox list — fixed height for stable layout */}
      <div className="rounded-md border bg-card h-[240px] overflow-y-auto">
        {query.isLoading && (
          <div className="flex items-center justify-center h-full text-sm text-muted-foreground">
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            加载中...
          </div>
        )}
        {!query.isLoading && allDepartments.length === 0 && (
          <div className="flex items-center justify-center h-full text-sm text-muted-foreground">
            {searchQuery ? "未找到匹配的部门" : "暂无数据"}
          </div>
        )}
        {!query.isLoading &&
          allDepartments.map((dept) => {
            const isSelected = selectedIds.has(dept.id)
            return (
              <div
                key={dept.id}
                className={`flex items-center gap-2 px-3 h-10 text-sm hover:bg-muted/50 cursor-pointer border-b border-border/50 last:border-b-0 ${
                  isSelected ? "bg-muted/30" : ""
                }`}
                onClick={() => !disabled && toggleDepartment(dept)}
              >
                <Checkbox
                  checked={isSelected}
                  disabled={disabled}
                  onCheckedChange={() => toggleDepartment(dept)}
                  className="shrink-0"
                />
                <span className="flex-1 truncate">{dept.name}</span>
                <span className="text-xs text-muted-foreground shrink-0">
                  ID: {dept.id}
                </span>
              </div>
            )
          })}
      </div>
    </div>
  )
}

// ─── Participants Tab ───────────────────────────────────────────────────────

function ParticipantsTab({ exam }: { exam: Exam }) {
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState("")
  const [addMode, setAddMode] = useState<
    "centers" | "departments" | "users" | null
  >(null)
  const [selectedCenters, setSelectedCenters] = useState<WecomDepartment[]>([])
  const [selectedDepartments, setSelectedDepartments] = useState<WecomDepartment[]>([])
  const [selectedUsers, setSelectedUsers] = useState<WecomUser[]>([])

  const participantsQuery = useQuery({
    queryKey: ["participants", exam.id, page, search],
    queryFn: () => listParticipants(exam.id, { page, q: search || undefined }),
  })

  const addByCentersMutation = useMutation({
    mutationFn: (ids: number[]) => addParticipantsByCenters(exam.id, ids),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["participants", exam.id] })
      setAddMode(null)
      setSelectedCenters([])
    },
  })

  const addByDeptsMutation = useMutation({
    mutationFn: (ids: number[]) => addParticipantsByDepartments(exam.id, ids),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["participants", exam.id] })
      setAddMode(null)
      setSelectedDepartments([])
    },
  })

  const addByUsersMutation = useMutation({
    mutationFn: (userids: string[]) => addParticipantsByUsers(exam.id, userids),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["participants", exam.id] })
      setAddMode(null)
      setSelectedUsers([])
    },
  })

  const removeMutation = useMutation({
    mutationFn: (userid: string) => removeParticipant(exam.id, userid),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["participants", exam.id] }),
  })

  const participants = participantsQuery.data?.data ?? []
  const total = participantsQuery.data?.count ?? 0
  const pageSize = 20
  const totalPages = Math.max(1, Math.ceil(total / pageSize))

  function handleAdd() {
    if (addMode === "centers") {
      if (selectedCenters.length === 0) return
      addByCentersMutation.mutate(selectedCenters.map((d) => d.id))
    } else if (addMode === "departments") {
      if (selectedDepartments.length === 0) return
      addByDeptsMutation.mutate(selectedDepartments.map((d) => d.id))
    } else if (addMode === "users") {
      if (selectedUsers.length === 0) return
      addByUsersMutation.mutate(selectedUsers.map((u) => u.userid))
    }
  }

  const isMutating =
    addByCentersMutation.isPending ||
    addByDeptsMutation.isPending ||
    addByUsersMutation.isPending
  const isDraft = exam.status === "DRAFT"

  return (
    <div className="flex flex-col gap-4">
      {/* Add participants */}
      {isDraft && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">添加学员</CardTitle>
            <CardDescription>按中心、部门或搜索选择人员添加。</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            <div className="flex gap-2">
              <Button
                variant={addMode === "centers" ? "default" : "outline"}
                size="sm"
                onClick={() => setAddMode("centers")}
              >
                按中心
              </Button>
              <Button
                variant={addMode === "departments" ? "default" : "outline"}
                size="sm"
                onClick={() => setAddMode("departments")}
              >
                按部门
              </Button>
              <Button
                variant={addMode === "users" ? "default" : "outline"}
                size="sm"
                onClick={() => setAddMode("users")}
              >
                按人员
              </Button>
            </div>
            {addMode === "centers" && (
              <div className="flex flex-col gap-3">
                <DepartmentCheckboxList
                  selectedDepartments={selectedCenters}
                  onSelectionChange={setSelectedCenters}
                  fetchDepartments={getCenters}
                  disabled={isMutating}
                  placeholder="搜索中心名称..."
                  label="centers"
                />
                {selectedCenters.length > 0 && (
                  <div className="flex items-center gap-2">
                    <Button onClick={handleAdd} disabled={isMutating}>
                      {isMutating ? (
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      ) : null}
                      添加 {selectedCenters.length} 个中心
                    </Button>
                    <span className="text-sm text-muted-foreground">
                      已选择 {selectedCenters.length} 个中心
                    </span>
                  </div>
                )}
              </div>
            )}
            {addMode === "departments" && (
              <div className="flex flex-col gap-3">
                <DepartmentCheckboxList
                  selectedDepartments={selectedDepartments}
                  onSelectionChange={setSelectedDepartments}
                  fetchDepartments={getDepartmentsOnly}
                  disabled={isMutating}
                  placeholder="搜索部门名称..."
                  label="departments"
                />
                {selectedDepartments.length > 0 && (
                  <div className="flex items-center gap-2">
                    <Button onClick={handleAdd} disabled={isMutating}>
                      {isMutating ? (
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      ) : null}
                      添加 {selectedDepartments.length} 个部门
                    </Button>
                    <span className="text-sm text-muted-foreground">
                      已选择 {selectedDepartments.length} 个部门
                    </span>
                  </div>
                )}
              </div>
            )}
            {addMode === "users" && (
              <div className="flex flex-col gap-3">
                <UserSearchSelect
                  selectedUsers={selectedUsers}
                  onSelectionChange={setSelectedUsers}
                  disabled={isMutating}
                />
                {selectedUsers.length > 0 && (
                  <div className="flex items-center gap-2">
                    <Button onClick={handleAdd} disabled={isMutating}>
                      {isMutating ? (
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      ) : null}
                      添加 {selectedUsers.length} 人
                    </Button>
                    <span className="text-sm text-muted-foreground">
                      已选择 {selectedUsers.length} 人
                    </span>
                  </div>
                )}
              </div>
            )}
            {addByCentersMutation.isSuccess && (
              <p className="text-sm text-green-600">
                已添加 {addByCentersMutation.data.added} 人
              </p>
            )}
            {addByDeptsMutation.isSuccess && (
              <p className="text-sm text-green-600">
                已添加 {addByDeptsMutation.data.added} 人
              </p>
            )}
            {addByUsersMutation.isSuccess && (
              <p className="text-sm text-green-600">
                已添加 {addByUsersMutation.data.added} 人
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Search */}
      <div className="relative max-w-sm">
        <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="搜索姓名…"
          value={search}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
            setSearch(e.target.value)
            setPage(1)
          }}
          className="pl-8"
        />
      </div>

      {/* Table */}
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>姓名</TableHead>
              <TableHead>中心</TableHead>
              <TableHead>部门</TableHead>
              <TableHead>添加时间</TableHead>
              <TableHead className="w-12"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {participantsQuery.isLoading && (
              <TableRow>
                <TableCell
                  colSpan={5}
                  className="text-center text-muted-foreground"
                >
                  加载中…
                </TableCell>
              </TableRow>
            )}
            {!participantsQuery.isLoading && participants.length === 0 && (
              <TableRow>
                <TableCell
                  colSpan={5}
                  className="text-center text-muted-foreground"
                >
                  暂无学员
                </TableCell>
              </TableRow>
            )}
            {participants.map((p) => (
              <TableRow key={p.id}>
                <TableCell className="font-medium">
                  {p.name_snapshot ?? "—"}
                </TableCell>
                <TableCell className="text-sm">
                  {p.center_snapshot ?? "—"}
                </TableCell>
                <TableCell className="text-sm">
                  {p.department_snapshot ?? "—"}
                </TableCell>
                <TableCell className="text-sm">
                  {fmtDate(p.created_at)}
                </TableCell>
                <TableCell>
                  {isDraft && (
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7 text-red-400"
                      onClick={() => removeMutation.mutate(p.userid)}
                      disabled={removeMutation.isPending}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-end gap-2 text-sm">
          <Button
            variant="outline"
            size="sm"
            disabled={page <= 1}
            onClick={() => setPage(page - 1)}
          >
            上一页
          </Button>
          <span className="text-muted-foreground">
            第 {page} / {totalPages} 页，共 {total} 条
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={page >= totalPages}
            onClick={() => setPage(page + 1)}
          >
            下一页
          </Button>
        </div>
      )}
    </div>
  )
}

// ─── Exam Statistics Tab ────────────────────────────────────────────────────

function ParticipantDetailDialog({
  examId,
  status,
  statusLabel,
  open,
  onOpenChange,
}: {
  examId: string
  status: string
  statusLabel: string
  open: boolean
  onOpenChange: (open: boolean) => void
}) {
  const query = useQuery({
    queryKey: ["participantsByStatus", examId, status],
    queryFn: () => getParticipantsByStatus(examId, status),
    enabled: open,
  })

  const participants = query.data?.data ?? []

  function getStatusBadge(s: string) {
    switch (s) {
      case "COMPLETED":
        return <Badge variant="success">已完成</Badge>
      case "NOT_COMPLETED":
        return <Badge variant="warning">未通过</Badge>
      case "IN_PROGRESS":
        return <Badge variant="info">进行中</Badge>
      case "NOT_STARTED":
        return <Badge variant="secondary">未开始</Badge>
      default:
        return <Badge variant="outline">{s}</Badge>
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{statusLabel} — 共 {participants.length} 人</DialogTitle>
          <DialogDescription>考试 ID: {examId}</DialogDescription>
        </DialogHeader>
        {query.isLoading && (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        )}
        {query.isError && (
          <div className="text-center py-8 text-red-500">
            加载失败: {query.error instanceof Error ? query.error.message : "未知错误"}
          </div>
        )}
        {!query.isLoading && !query.isError && (
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>姓名</TableHead>
                  <TableHead>中心</TableHead>
                  <TableHead>部门</TableHead>
                  <TableHead>分数</TableHead>
                  <TableHead>状态</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {participants.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center text-muted-foreground py-8">
                      暂无人员
                    </TableCell>
                  </TableRow>
                )}
                {participants.map((p) => (
                  <TableRow key={p.id}>
                    <TableCell className="font-medium">
                      {p.name_snapshot ?? "—"}
                    </TableCell>
                    <TableCell className="text-sm">{p.center_snapshot ?? "—"}</TableCell>
                    <TableCell className="text-sm">{p.department_snapshot ?? "—"}</TableCell>
                    <TableCell>
                      {p.final_score !== null ? (
                        <span className={p.final_passed ? "text-green-600 font-medium" : "text-red-600 font-medium"}>
                          {p.final_score}
                        </span>
                      ) : (
                        "—"
                      )}
                    </TableCell>
                    <TableCell>{getStatusBadge(p.completion_status)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}

function ExamStatisticsTab({ exam }: { exam: Exam }) {
  const statsQuery = useQuery({
    queryKey: ["examStatistics", exam.id],
    queryFn: () => getExamStatistics(exam.id),
  })

  const [dialogStatus, setDialogStatus] = useState<string | null>(null)
  const [dialogLabel, setDialogLabel] = useState("")

  const stats = statsQuery.data

  if (statsQuery.isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (!stats) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        暂无统计数据
      </div>
    )
  }

  function openDialog(status: string, label: string) {
    setDialogStatus(status)
    setDialogLabel(label)
  }

  function closeDialog() {
    setDialogStatus(null)
    setDialogLabel("")
  }

  return (
    <div className="flex flex-col gap-6">
      {/* 数据卡片 — 可点击查看人员名单 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card
          className="cursor-pointer hover:shadow-md transition-all hover:bg-accent/30"
          onClick={() => openDialog("ALL", "参考人员总数")}
        >
          <CardHeader className="pb-2">
            <CardDescription className="flex items-center gap-1">
              <Users className="h-3.5 w-3.5" />
              参考人员总数
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total_participants}</div>
          </CardContent>
        </Card>
        <Card
          className="cursor-pointer hover:shadow-md transition-all hover:bg-green-50 dark:hover:bg-green-950/20"
          onClick={() => openDialog("COMPLETED", "及格人数")}
        >
          <CardHeader className="pb-2">
            <CardDescription className="flex items-center gap-1 text-green-600">
              <CheckCircle2 className="h-3.5 w-3.5" />
              及格人数
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{stats.passed_count}</div>
          </CardContent>
        </Card>
        <Card
          className="cursor-pointer hover:shadow-md transition-all hover:bg-red-50 dark:hover:bg-red-950/20"
          onClick={() => openDialog("NOT_COMPLETED", "未通过人数")}
        >
          <CardHeader className="pb-2">
            <CardDescription className="flex items-center gap-1 text-red-600">
              <XCircle className="h-3.5 w-3.5" />
              未通过人数
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{stats.failed_count}</div>
          </CardContent>
        </Card>
        <Card
          className="cursor-pointer hover:shadow-md transition-all hover:bg-amber-50 dark:hover:bg-amber-950/20"
          onClick={() => openDialog("NOT_STARTED", "未考试人数")}
        >
          <CardHeader className="pb-2">
            <CardDescription className="flex items-center gap-1 text-amber-600">
              <AlertCircle className="h-3.5 w-3.5" />
              未考试人数
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-amber-600">{stats.not_started_count}</div>
          </CardContent>
        </Card>
      </div>

      {/* 及格率 + 平均分 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>及格率</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{stats.pass_rate}%</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>平均分</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.avg_score ?? "—"}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>最高分</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.max_score ?? "—"}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>最低分</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.min_score ?? "—"}</div>
          </CardContent>
        </Card>
      </div>

      {/* 分数分布 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">分数分布</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {stats.score_distribution.map((item) => (
              <div key={item.range_label} className="flex items-center gap-3">
                <div className="w-16 text-sm text-muted-foreground">{item.range_label}</div>
                <div className="flex-1 bg-muted rounded-full h-6 overflow-hidden">
                  <div
                    className="bg-primary h-full rounded-full transition-all"
                    style={{
                      width: `${stats.total_participants > 0 ? (item.count / stats.total_participants) * 100 : 0}%`,
                    }}
                  />
                </div>
                <div className="w-12 text-sm text-right">{item.count}人</div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* 状态统计 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">完成状态</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <div className="text-muted-foreground">已完成</div>
              <div className="text-lg font-medium">{stats.completed_count}</div>
            </div>
            <div>
              <div className="text-muted-foreground">进行中</div>
              <div className="text-lg font-medium">{stats.in_progress_count}</div>
            </div>
            <div>
              <div className="text-muted-foreground">未开始</div>
              <div className="text-lg font-medium">{stats.not_started_count}</div>
            </div>
            <div>
              <div className="text-muted-foreground">已完成考试</div>
              <div className="text-lg font-medium">{stats.passed_count + stats.failed_count}</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 人员详情弹窗 */}
      {dialogStatus && (
        <ParticipantDetailDialog
          examId={exam.id}
          status={dialogStatus}
          statusLabel={dialogLabel}
          open={true}
          onOpenChange={(open) => !open && closeDialog()}
        />
      )}
    </div>
  )
}

// ─── Main Detail Page ───────────────────────────────────────────────────────

export function ExamDetailPage() {
  const queryClient = useQueryClient()
  const examId = window.location.pathname.split("/").filter(Boolean).pop() ?? ""
  const { user: currentUser } = useAuth()

  const [questions, setQuestions] = useState<QuestionCreate[]>([])
  const [paperLoaded, setPaperLoaded] = useState(false)
  const [aiOpen, setAiOpen] = useState(false)

  const examQuery = useQuery({
    queryKey: ["exam", examId],
    queryFn: () => getExam(examId),
  })

  const paperQuery = useQuery({
    queryKey: ["paper", examId],
    queryFn: () => getPaper(examId),
    enabled: examQuery.isSuccess && !paperLoaded,
  })

  useEffect(() => {
    if (paperQuery.data && !paperLoaded) {
      setQuestions(
        paperQuery.data.questions.map((q) => ({
          question_type: q.question_type,
          stem: q.stem,
          score: q.score,
          sort_no: q.sort_no,
          analysis: q.analysis ?? undefined,
          options: q.options.map((o) => ({
            option_key: o.option_key,
            option_text: o.option_text,
            is_correct: o.is_correct,
            sort_no: o.sort_no,
          })),
        })),
      )
      setPaperLoaded(true)
    }
  }, [paperQuery.data, paperLoaded])

  const publishMutation = useMutation({
    mutationFn: async () => {
      const validation = await validateExam(examId)
      if (!validation.valid) {
        throw new Error(validation.errors.join("\n"))
      }
      return publishExam(examId)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["exam", examId] })
      queryClient.invalidateQueries({ queryKey: ["exams"] })
      toast.success("考试发布成功")
    },
    onError: (error: Error) => {
      toast.error("考试无法发布", {
        description: error.message,
      })
    },
  })

  const archiveMutation = useMutation({
    mutationFn: () => archiveExam(examId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["exam", examId] })
      queryClient.invalidateQueries({ queryKey: ["exams"] })
      toast.success("考试已归档")
    },
    onError: (error: Error) => {
      toast.error(error.message)
    },
  })

  const exam = examQuery.data

  if (examQuery.isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (!exam) {
    return (
      <div className="text-center py-12 text-muted-foreground">考试不存在</div>
    )
  }

  const showAIAssistant = currentUser?.is_superuser ?? false

  return (
    <div className="flex flex-col lg:flex-row lg:h-[calc(100vh-4rem)] lg:-mt-6 lg:-mt-8 lg:overflow-hidden lg:gap-4">
      <div className="flex-1 min-w-0 flex flex-col gap-6 p-6 md:p-8 lg:overflow-y-auto">
        {/* Header */}
        <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => window.history.back()}
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">{exam.name}</h1>
            <p className="text-muted-foreground">
              {exam.status === "DRAFT"
                ? "未发布"
                : exam.status === "PUBLISHED"
                  ? "已发布"
                  : "已归档"}
              {exam.published_at && ` · 发布于 ${fmtDate(exam.published_at)}`}
            </p>
            {exam.trainers && exam.trainers.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-1">
                <span className="text-sm text-muted-foreground">讲师：</span>
                {exam.trainers.map((t) => (
                  <Badge key={t.id} variant="secondary" className="text-xs">
                    {t.name}
                  </Badge>
                ))}
              </div>
            )}
          </div>
        </div>
        <div className="flex gap-2">
          {exam.status === "DRAFT" && (
            <Button
              onClick={() => publishMutation.mutate()}
              disabled={publishMutation.isPending}
            >
              {publishMutation.isPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Send className="mr-2 h-4 w-4" />
              )}
              发布考试
            </Button>
          )}
          {exam.status === "PUBLISHED" && (
            <Button
              variant="outline"
              onClick={() => archiveMutation.mutate()}
              disabled={archiveMutation.isPending}
            >
              {archiveMutation.isPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Archive className="mr-2 h-4 w-4" />
              )}
              归档
            </Button>
          )}
        </div>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="settings">
        <TabsList>
          <TabsTrigger value="settings">考试设置</TabsTrigger>
          <TabsTrigger value="paper">试卷编辑</TabsTrigger>
          <TabsTrigger value="participants">人员管理</TabsTrigger>
          <TabsTrigger value="statistics">考试统计</TabsTrigger>
        </TabsList>

        <TabsContent value="settings" className="mt-4">
          <ExamSettingsTab exam={exam} />
        </TabsContent>

        <TabsContent value="paper" className="mt-4">
          <PaperEditorTab
            exam={exam}
            questions={questions}
            setQuestions={setQuestions}
          />
        </TabsContent>

        <TabsContent value="participants" className="mt-4">
          <ParticipantsTab exam={exam} />
        </TabsContent>

        <TabsContent value="statistics" className="mt-4">
          <ExamStatisticsTab exam={exam} />
        </TabsContent>
      </Tabs>
      </div>

      {showAIAssistant && !aiOpen && (
        <button
          type="button"
          onClick={() => setAiOpen(true)}
          className="fixed right-4 bottom-4 z-30 flex items-center justify-center gap-2 p-3 text-sm text-muted-foreground bg-background/95 border rounded-full shadow-sm hover:bg-muted/60 hover:text-foreground transition-colors lg:right-0 lg:top-24 lg:bottom-auto lg:rounded-l-xl lg:rounded-r-none lg:px-3 lg:py-4 lg:flex-col"
        >
          <Bot className="h-5 w-5" />
          <span className="hidden lg:inline [writing-mode:vertical-rl]">AI 助手</span>
        </button>
      )}

      {showAIAssistant && aiOpen && (
        <aside
          className={cn(
            "shrink-0 flex flex-col transition-all duration-300 bg-background overflow-hidden",
            "fixed inset-0 top-16 z-30 lg:static lg:w-96 lg:h-full lg:border-l",
          )}
        >
          <AIAssistantPanel
            examId={examId}
            open={aiOpen}
            onOpenChange={setAiOpen}
            questions={questions}
            onQuestionsChange={setQuestions}
            className="h-full"
          />
        </aside>
      )}
    </div>
  )
}
