import { useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useParams, useNavigate } from "@tanstack/react-router"
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
  Search,
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
  getExam,
  updateExam,
  publishExam,
  archiveExam,
  getPaper,
  savePaper,
  listParticipants,
  addParticipantsByCenters,
  addParticipantsByDepartments,
  addParticipantsByUsers,
  removeParticipant,
} from "../api"
import type {
  Exam,
  ExamUpdate,
  QuestionCreate,
} from "../types"

// ─── Helpers ────────────────────────────────────────────────────────────────

function fmtDate(s: string | null): string {
  if (!s) return "—"
  return new Date(s).toLocaleString("zh-CN", { hour12: false })
}

function toLocalDatetime(s: string): string {
  const d = new Date(s)
  const pad = (n: number) => String(n).padStart(2, "0")
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

// ─── Exam Settings Tab ──────────────────────────────────────────────────────

function ExamSettingsTab({ exam }: { exam: Exam }) {
  const queryClient = useQueryClient()
  const [form, setForm] = useState<ExamUpdate>({
    name: exam.name,
    description: exam.description ?? "",
    start_at: toLocalDatetime(exam.start_at),
    end_at: toLocalDatetime(exam.end_at),
    duration_minutes: exam.duration_minutes,
    attempt_limit_type: exam.attempt_limit_type,
    attempt_limit_count: exam.attempt_limit_count ?? undefined,
    pass_score: exam.pass_score,
    submit_rule: exam.submit_rule,
    show_answer: exam.show_answer,
    random_question_order: exam.random_question_order,
    random_option_order: exam.random_option_order,
  })

  const updateMutation = useMutation({
    mutationFn: (data: ExamUpdate) => updateExam(exam.id, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["exam", exam.id] }),
  })

  const isDraft = exam.status === "DRAFT"

  function handleSave() {
    const data: ExamUpdate = { ...form }
    if (data.start_at && !data.start_at.endsWith("Z")) data.start_at = data.start_at + ":00Z"
    if (data.end_at && !data.end_at.endsWith("Z")) data.end_at = data.end_at + ":00Z"
    updateMutation.mutate(data)
  }

  return (
    <div className="flex flex-col gap-6 max-w-2xl">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">基本信息</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <div className="grid gap-2">
            <Label>考试名称</Label>
            <Input
              value={form.name ?? ""}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setForm({ ...form, name: e.target.value })}
              disabled={!isDraft}
            />
          </div>
          <div className="grid gap-2">
            <Label>考试说明</Label>
            <textarea
              className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              value={form.description ?? ""}
              onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setForm({ ...form, description: e.target.value })}
              disabled={!isDraft}
              placeholder="给学员看的考试说明（可选）"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="grid gap-2">
              <Label>开始时间</Label>
              <Input
                type="datetime-local"
                value={form.start_at ?? ""}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setForm({ ...form, start_at: e.target.value })}
                disabled={!isDraft}
              />
            </div>
            <div className="grid gap-2">
              <Label>结束时间</Label>
              <Input
                type="datetime-local"
                value={form.end_at ?? ""}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setForm({ ...form, end_at: e.target.value })}
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
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setForm({ ...form, duration_minutes: Number(e.target.value) })}
                disabled={!isDraft}
              />
            </div>
            <div className="grid gap-2">
              <Label>及格分数</Label>
              <Input
                type="number"
                value={form.pass_score ?? ""}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setForm({ ...form, pass_score: Number(e.target.value) })}
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
                onValueChange={(v: string) => setForm({ ...form, attempt_limit_type: v as "UNLIMITED" | "LIMITED" })}
                disabled={!isDraft}
              >
                <SelectTrigger><SelectValue /></SelectTrigger>
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
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setForm({ ...form, attempt_limit_count: Number(e.target.value) })}
                  disabled={!isDraft}
                />
              </div>
            )}
          </div>
          <div className="grid gap-2">
            <Label>交卷要求</Label>
            <Select
              value={form.submit_rule ?? "ALL_REQUIRED"}
              onValueChange={(v: string) => setForm({ ...form, submit_rule: v as "ALL_REQUIRED" | "ANY" })}
              disabled={!isDraft}
            >
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="ALL_REQUIRED">全部题目必须作答</SelectItem>
                <SelectItem value="ANY">不限制</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="flex items-center justify-between">
            <div>
              <Label>提交后展示正确答案</Label>
              <p className="text-sm text-muted-foreground">学员提交试卷后是否可以查看正确答案</p>
            </div>
            <Checkbox
              checked={form.show_answer ?? false}
              onCheckedChange={(v: boolean) => setForm({ ...form, show_answer: v })}
              disabled={!isDraft}
            />
          </div>
          <div className="flex items-center justify-between">
            <div>
              <Label>随机题目顺序</Label>
              <p className="text-sm text-muted-foreground">每位学员看到的题目顺序不同</p>
            </div>
            <Checkbox
              checked={form.random_question_order ?? false}
              onCheckedChange={(v: boolean) => setForm({ ...form, random_question_order: v })}
              disabled={!isDraft}
            />
          </div>
          <div className="flex items-center justify-between">
            <div>
              <Label>随机选项顺序</Label>
              <p className="text-sm text-muted-foreground">每道题的选项顺序随机打乱</p>
            </div>
            <Checkbox
              checked={form.random_option_order ?? false}
              onCheckedChange={(v: boolean) => setForm({ ...form, random_option_order: v })}
              disabled={!isDraft}
            />
          </div>
        </CardContent>
      </Card>

      {isDraft && (
        <div className="flex gap-3">
          <Button onClick={handleSave} disabled={updateMutation.isPending}>
            {updateMutation.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
            保存
          </Button>
          {updateMutation.isSuccess && <span className="text-sm text-green-600 self-center">已保存</span>}
        </div>
      )}
    </div>
  )
}

// ─── Paper Editor Tab ───────────────────────────────────────────────────────

function PaperEditorTab({ exam }: { exam: Exam }) {
  const queryClient = useQueryClient()
  const [questions, setQuestions] = useState<QuestionCreate[]>([])
  const [loaded, setLoaded] = useState(false)

  const paperQuery = useQuery({
    queryKey: ["paper", exam.id],
    queryFn: () => getPaper(exam.id),
    enabled: !loaded,
  })

  // Load existing paper data
  if (paperQuery.data && !loaded) {
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
      }))
    )
    setLoaded(true)
  }

  const saveMutation = useMutation({
    mutationFn: () => savePaper(exam.id, { questions }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["paper", exam.id] })
      queryClient.invalidateQueries({ queryKey: ["exam", exam.id] })
    },
  })

  const isDraft = exam.status === "DRAFT"
  const totalScore = questions.reduce((sum, q) => sum + q.score, 0)

  function addQuestion(type: QuestionCreate["question_type"]) {
    const sortNo = questions.length + 1
    const defaultOptions =
      type === "TRUE_FALSE"
        ? [
            { option_key: "A", option_text: "正确", is_correct: true, sort_no: 1 },
            { option_key: "B", option_text: "错误", is_correct: false, sort_no: 2 },
          ]
        : [
            { option_key: "A", option_text: "", is_correct: true, sort_no: 1 },
            { option_key: "B", option_text: "", is_correct: false, sort_no: 2 },
          ]
    setQuestions([
      ...questions,
      { question_type: type, stem: "", score: 10, sort_no: sortNo, options: defaultOptions },
    ])
  }

  function updateQuestion(idx: number, patch: Partial<QuestionCreate>) {
    setQuestions(questions.map((q, i) => (i === idx ? { ...q, ...patch } : q)))
  }

  function deleteQuestion(idx: number) {
    setQuestions(questions.filter((_, i) => i !== idx).map((q, i) => ({ ...q, sort_no: i + 1 })))
  }

  function moveQuestion(idx: number, dir: -1 | 1) {
    const newIdx = idx + dir
    if (newIdx < 0 || newIdx >= questions.length) return
    const arr = [...questions]
    ;[arr[idx], arr[newIdx]] = [arr[newIdx], arr[idx]]
    setQuestions(arr.map((q, i) => ({ ...q, sort_no: i + 1 })))
  }

  function updateOption(qIdx: number, oIdx: number, patch: Partial<{ option_text: string; is_correct: boolean }>) {
    updateQuestion(qIdx, {
      options: questions[qIdx].options.map((o, i) => (i === oIdx ? { ...o, ...patch } : o)),
    })
  }

  function addOption(qIdx: number) {
    const opts = questions[qIdx].options
    const key = String.fromCharCode(65 + opts.length)
    updateQuestion(qIdx, {
      options: [...opts, { option_key: key, option_text: "", is_correct: false, sort_no: opts.length + 1 }],
    })
  }

  function removeOption(qIdx: number, oIdx: number) {
    const opts = questions[qIdx].options.filter((_, i) => i !== oIdx)
    updateQuestion(qIdx, {
      options: opts.map((o, i) => ({ ...o, option_key: String.fromCharCode(65 + i), sort_no: i + 1 })),
    })
  }

  function setCorrectOption(qIdx: number, oIdx: number) {
    const q = questions[qIdx]
    if (q.question_type === "SINGLE_CHOICE" || q.question_type === "TRUE_FALSE") {
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
      <div className="flex items-center justify-between">
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => addQuestion("SINGLE_CHOICE")} disabled={!isDraft}>
            <Plus className="mr-1 h-3 w-3" />单选题
          </Button>
          <Button variant="outline" size="sm" onClick={() => addQuestion("MULTIPLE_CHOICE")} disabled={!isDraft}>
            <Plus className="mr-1 h-3 w-3" />多选题
          </Button>
          <Button variant="outline" size="sm" onClick={() => addQuestion("TRUE_FALSE")} disabled={!isDraft}>
            <Plus className="mr-1 h-3 w-3" />判断题
          </Button>
        </div>
        <div className="flex items-center gap-4 text-sm text-muted-foreground">
          <span>共 {questions.length} 题</span>
          <span>总分 {totalScore}</span>
          {isDraft && (
            <Button size="sm" onClick={() => saveMutation.mutate()} disabled={saveMutation.isPending}>
              {saveMutation.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
              保存试卷
            </Button>
          )}
        </div>
      </div>

      {saveMutation.isSuccess && (
        <p className="text-sm text-green-600">试卷已保存</p>
      )}
      {saveMutation.isError && (
        <p className="text-sm text-red-600">{(saveMutation.error as Error).message}</p>
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
                  <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => moveQuestion(qIdx, -1)} disabled={qIdx === 0}>
                    <GripVertical className="h-3 w-3 rotate-180" />
                  </Button>
                  <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => moveQuestion(qIdx, 1)} disabled={qIdx === questions.length - 1}>
                    <GripVertical className="h-3 w-3" />
                  </Button>
                </div>
              )}
              <div>
                <Badge variant="outline" className="mr-2">
                  {q.question_type === "SINGLE_CHOICE" ? "单选" : q.question_type === "MULTIPLE_CHOICE" ? "多选" : "判断"}
                </Badge>
                <span className="text-sm text-muted-foreground">第 {q.sort_no} 题</span>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-1 text-sm">
                <Label className="text-xs">分值</Label>
                <Input
                  type="number"
                  className="w-16 h-7 text-sm"
                  value={q.score}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateQuestion(qIdx, { score: Number(e.target.value) })}
                  disabled={!isDraft}
                />
              </div>
              {isDraft && (
                <Button variant="ghost" size="icon" className="h-7 w-7 text-red-500" onClick={() => deleteQuestion(qIdx)}>
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
                onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => updateQuestion(qIdx, { stem: e.target.value })}
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
                    {opt.is_correct ? <CheckCircle2 className="h-4 w-4" /> : opt.option_key}
                  </Button>
                  <Input
                    value={opt.option_text}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateOption(qIdx, oIdx, { option_text: e.target.value })}
                    disabled={!isDraft || q.question_type === "TRUE_FALSE"}
                    placeholder={q.question_type === "TRUE_FALSE" ? opt.option_text : `选项 ${opt.option_key}`}
                    className="flex-1"
                  />
                  {isDraft && q.question_type !== "TRUE_FALSE" && q.options.length > 2 && (
                    <Button variant="ghost" size="icon" className="h-8 w-8 text-red-400" onClick={() => removeOption(qIdx, oIdx)}>
                      <XCircle className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              ))}
              {isDraft && q.question_type !== "TRUE_FALSE" && q.options.length < 10 && (
                <Button variant="outline" size="sm" className="w-fit" onClick={() => addOption(qIdx)}>
                  <Plus className="mr-1 h-3 w-3" />添加选项
                </Button>
              )}
            </div>
            {isDraft && (
              <div className="grid gap-2">
                <Label>答案解析（可选）</Label>
                <textarea
                  className="flex min-h-[60px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  value={q.analysis ?? ""}
                  onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => updateQuestion(qIdx, { analysis: e.target.value })}
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

// ─── Participants Tab ───────────────────────────────────────────────────────

function ParticipantsTab({ exam }: { exam: Exam }) {
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState("")
  const [addMode, setAddMode] = useState<"centers" | "departments" | "users" | null>(null)
  const [addInput, setAddInput] = useState("")

  const participantsQuery = useQuery({
    queryKey: ["participants", exam.id, page, search],
    queryFn: () => listParticipants(exam.id, { page, q: search || undefined }),
  })

  const addByCentersMutation = useMutation({
    mutationFn: (ids: number[]) => addParticipantsByCenters(exam.id, ids),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["participants", exam.id] })
      setAddMode(null)
      setAddInput("")
    },
  })

  const addByDeptsMutation = useMutation({
    mutationFn: (ids: number[]) => addParticipantsByDepartments(exam.id, ids),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["participants", exam.id] })
      setAddMode(null)
      setAddInput("")
    },
  })

  const addByUsersMutation = useMutation({
    mutationFn: (userids: string[]) => addParticipantsByUsers(exam.id, userids),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["participants", exam.id] })
      setAddMode(null)
      setAddInput("")
    },
  })

  const removeMutation = useMutation({
    mutationFn: (userid: string) => removeParticipant(exam.id, userid),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["participants", exam.id] }),
  })

  const participants = participantsQuery.data?.data ?? []
  const total = participantsQuery.data?.count ?? 0
  const pageSize = 20
  const totalPages = Math.max(1, Math.ceil(total / pageSize))

  function handleAdd() {
    const ids = addInput.split(",").map((s) => s.trim()).filter(Boolean)
    if (ids.length === 0) return

    if (addMode === "centers") {
      addByCentersMutation.mutate(ids.map(Number))
    } else if (addMode === "departments") {
      addByDeptsMutation.mutate(ids.map(Number))
    } else if (addMode === "users") {
      addByUsersMutation.mutate(ids)
    }
  }

  const isMutating = addByCentersMutation.isPending || addByDeptsMutation.isPending || addByUsersMutation.isPending

  return (
    <div className="flex flex-col gap-4">
      {/* Add participants */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">添加学员</CardTitle>
          <CardDescription>
            按中心、部门或特定人员添加。输入 ID 用逗号分隔。
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <div className="flex gap-2">
            <Button variant={addMode === "centers" ? "default" : "outline"} size="sm" onClick={() => setAddMode("centers")}>
              按中心
            </Button>
            <Button variant={addMode === "departments" ? "default" : "outline"} size="sm" onClick={() => setAddMode("departments")}>
              按部门
            </Button>
            <Button variant={addMode === "users" ? "default" : "outline"} size="sm" onClick={() => setAddMode("users")}>
              按人员
            </Button>
          </div>
          {addMode && (
            <div className="flex gap-2">
              <Input
                placeholder={
                  addMode === "users"
                    ? "输入 userid，逗号分隔"
                    : `输入${addMode === "centers" ? "中心" : "部门"} ID，逗号分隔`
                }
                value={addInput}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setAddInput(e.target.value)}
              />
              <Button onClick={handleAdd} disabled={isMutating}>
                {isMutating ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                添加
              </Button>
            </div>
          )}
          {addByCentersMutation.isSuccess && <p className="text-sm text-green-600">已添加 {addByCentersMutation.data.added} 人</p>}
          {addByDeptsMutation.isSuccess && <p className="text-sm text-green-600">已添加 {addByDeptsMutation.data.added} 人</p>}
          {addByUsersMutation.isSuccess && <p className="text-sm text-green-600">已添加 {addByUsersMutation.data.added} 人</p>}
        </CardContent>
      </Card>

      {/* Search */}
      <div className="relative max-w-sm">
        <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="搜索姓名或 userid…"
          value={search}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) => { setSearch(e.target.value); setPage(1) }}
          className="pl-8"
        />
      </div>

      {/* Table */}
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Userid</TableHead>
              <TableHead>姓名</TableHead>
              <TableHead>中心</TableHead>
              <TableHead>部门</TableHead>
              <TableHead>添加时间</TableHead>
              <TableHead className="w-12"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {participantsQuery.isLoading && (
              <TableRow><TableCell colSpan={6} className="text-center text-muted-foreground">加载中…</TableCell></TableRow>
            )}
            {!participantsQuery.isLoading && participants.length === 0 && (
              <TableRow><TableCell colSpan={6} className="text-center text-muted-foreground">暂无学员</TableCell></TableRow>
            )}
            {participants.map((p) => (
              <TableRow key={p.id}>
                <TableCell className="font-mono text-sm">{p.userid}</TableCell>
                <TableCell className="font-medium">{p.name_snapshot ?? "—"}</TableCell>
                <TableCell className="text-sm">{p.center_snapshot ?? "—"}</TableCell>
                <TableCell className="text-sm">{p.department_snapshot ?? "—"}</TableCell>
                <TableCell className="text-sm">{fmtDate(p.created_at)}</TableCell>
                <TableCell>
                  {exam.status === "DRAFT" && (
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
          <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage(page - 1)}>上一页</Button>
          <span className="text-muted-foreground">第 {page} / {totalPages} 页，共 {total} 条</span>
          <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage(page + 1)}>下一页</Button>
        </div>
      )}
    </div>
  )
}

// ─── Main Detail Page ───────────────────────────────────────────────────────

export function ExamDetailPage() {
  const { examId } = useParams({ from: "/_layout/exams/$examId" })
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const examQuery = useQuery({
    queryKey: ["exam", examId],
    queryFn: () => getExam(examId),
  })

  const publishMutation = useMutation({
    mutationFn: () => publishExam(examId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["exam", examId] })
      queryClient.invalidateQueries({ queryKey: ["exams"] })
    },
  })

  const archiveMutation = useMutation({
    mutationFn: () => archiveExam(examId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["exam", examId] })
      queryClient.invalidateQueries({ queryKey: ["exams"] })
    },
  })

  const exam = examQuery.data

  if (examQuery.isLoading) {
    return <div className="flex items-center justify-center py-12"><Loader2 className="h-8 w-8 animate-spin text-muted-foreground" /></div>
  }

  if (!exam) {
    return <div className="text-center py-12 text-muted-foreground">考试不存在</div>
  }

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={() => navigate({ to: "/exams" })}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">{exam.name}</h1>
            <p className="text-muted-foreground">
              {exam.status === "DRAFT" ? "未发布" : exam.status === "PUBLISHED" ? "已发布" : "已归档"}
              {exam.published_at && ` · 发布于 ${fmtDate(exam.published_at)}`}
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          {exam.status === "DRAFT" && (
            <Button
              onClick={() => publishMutation.mutate()}
              disabled={publishMutation.isPending}
            >
              {publishMutation.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Send className="mr-2 h-4 w-4" />}
              发布考试
            </Button>
          )}
          {exam.status === "PUBLISHED" && (
            <Button variant="outline" onClick={() => archiveMutation.mutate()} disabled={archiveMutation.isPending}>
              {archiveMutation.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Archive className="mr-2 h-4 w-4" />}
              归档
            </Button>
          )}
        </div>
      </div>

      {publishMutation.isError && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-4 text-sm text-red-700">
            {(publishMutation.error as Error).message}
          </CardContent>
        </Card>
      )}

      {/* Tabs */}
      <Tabs defaultValue="settings">
        <TabsList>
          <TabsTrigger value="settings">考试设置</TabsTrigger>
          <TabsTrigger value="paper">试卷编辑</TabsTrigger>
          <TabsTrigger value="participants">人员管理</TabsTrigger>
        </TabsList>

        <TabsContent value="settings" className="mt-4">
          <ExamSettingsTab exam={exam} />
        </TabsContent>

        <TabsContent value="paper" className="mt-4">
          <PaperEditorTab exam={exam} />
        </TabsContent>

        <TabsContent value="participants" className="mt-4">
          <ParticipantsTab exam={exam} />
        </TabsContent>
      </Tabs>
    </div>
  )
}
