import { useState } from "react"
import { useMutation } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import { ArrowLeft, Loader2 } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

import { createExam } from "../api"
import type { ExamCreate } from "../types"

export function NewExamPage() {
  const navigate = useNavigate()
  const [form, setForm] = useState<ExamCreate>({
    name: "",
    description: "",
    start_at: "",
    end_at: "",
    duration_minutes: 60,
    attempt_limit_type: "UNLIMITED",
    pass_score: 60,
    submit_rule: "ALL_REQUIRED",
    show_answer: false,
    random_question_order: false,
    random_option_order: false,
  })

  const createMutation = useMutation({
    mutationFn: (data: ExamCreate) => {
      const payload = { ...data }
      if (payload.start_at && !payload.start_at.endsWith("Z")) payload.start_at = payload.start_at + ":00Z"
      if (payload.end_at && !payload.end_at.endsWith("Z")) payload.end_at = payload.end_at + ":00Z"
      return createExam(payload)
    },
    onSuccess: (exam) => navigate({ to: `/exams/${exam.id}` }),
  })

  function handleCreate() {
    if (!form.name.trim()) return
    if (!form.start_at || !form.end_at) return
    createMutation.mutate(form)
  }

  return (
    <div className="flex flex-col gap-6 max-w-2xl">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" onClick={() => navigate({ to: "/exams" })}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">新建考试</h1>
          <p className="text-muted-foreground">创建一场新的考试</p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">基本信息</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <div className="grid gap-2">
            <Label>考试名称 *</Label>
            <Input
              placeholder="例如：化妆品出口欧美合规培训"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
            />
          </div>
          <div className="grid gap-2">
            <Label>考试说明</Label>
            <Textarea
              placeholder="给学员看的考试说明（可选）"
              value={form.description ?? ""}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              rows={3}
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="grid gap-2">
              <Label>开始时间 *</Label>
              <Input
                type="datetime-local"
                value={form.start_at}
                onChange={(e) => setForm({ ...form, start_at: e.target.value })}
              />
            </div>
            <div className="grid gap-2">
              <Label>结束时间 *</Label>
              <Input
                type="datetime-local"
                value={form.end_at}
                onChange={(e) => setForm({ ...form, end_at: e.target.value })}
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="grid gap-2">
              <Label>考试时长（分钟）*</Label>
              <Input
                type="number"
                value={form.duration_minutes}
                onChange={(e) => setForm({ ...form, duration_minutes: Number(e.target.value) })}
              />
            </div>
            <div className="grid gap-2">
              <Label>及格分数 *</Label>
              <Input
                type="number"
                value={form.pass_score}
                onChange={(e) => setForm({ ...form, pass_score: Number(e.target.value) })}
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
                value={form.attempt_limit_type}
                onValueChange={(v) => setForm({ ...form, attempt_limit_type: v as "UNLIMITED" | "LIMITED" })}
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
                  onChange={(e) => setForm({ ...form, attempt_limit_count: Number(e.target.value) })}
                />
              </div>
            )}
          </div>
          <div className="grid gap-2">
            <Label>交卷要求</Label>
            <Select
              value={form.submit_rule}
              onValueChange={(v) => setForm({ ...form, submit_rule: v as "ALL_REQUIRED" | "ANY" })}
            >
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="ALL_REQUIRED">全部题目必须作答</SelectItem>
                <SelectItem value="ANY">不限制</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {createMutation.isError && (
        <p className="text-sm text-red-600">{(createMutation.error as Error).message}</p>
      )}

      <div className="flex gap-3">
        <Button onClick={handleCreate} disabled={createMutation.isPending || !form.name.trim()}>
          {createMutation.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
          创建考试
        </Button>
        <Button variant="outline" onClick={() => navigate({ to: "/exams" })}>
          取消
        </Button>
      </div>
    </div>
  )
}
