import { useMutation, useQuery } from "@tanstack/react-query"
import {
  CalendarDays,
  CheckCircle2,
  ClipboardList,
  Plus,
  RotateCcw,
  Send,
  Trash2,
} from "lucide-react"
import { useState } from "react"

import {
  type ReportType,
  type TaskSummaryInput,
  type WorkPlanInput,
  type WorkReportSubmissionResult,
  WorkReportsService,
  type WorkReviewInput,
} from "@/client"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { LoadingButton } from "@/components/ui/loading-button"
import { Textarea } from "@/components/ui/textarea"
import useAuth from "@/hooks/useAuth"
import useCustomToast from "@/hooks/useCustomToast"
import { cn } from "@/lib/utils"
import { handleError } from "@/utils"
import { FIELD_LABELS, SECTION_FIELDS, type SectionKey } from "./constants"

type PlanRow = WorkPlanInput & { _key: string }
type SummaryRow = TaskSummaryInput & { _key: string }
type ReviewRow = WorkReviewInput & { _key: string }
type FormErrors = Record<string, string>

const newKey = () => crypto.randomUUID()

const currentPeriod = (reportType: ReportType) => {
  const now = new Date()
  if (reportType === "monthly") {
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`
  }
  const date = new Date(
    Date.UTC(now.getFullYear(), now.getMonth(), now.getDate()),
  )
  const day = date.getUTCDay() || 7
  date.setUTCDate(date.getUTCDate() + 4 - day)
  const yearStart = new Date(Date.UTC(date.getUTCFullYear(), 0, 1))
  const week = Math.ceil(
    ((date.getTime() - yearStart.getTime()) / 86_400_000 + 1) / 7,
  )
  return `${date.getUTCFullYear()}-W${String(week).padStart(2, "0")}`
}

const WorkReportForm = () => {
  const { user } = useAuth()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const [reportType, setReportType] = useState<ReportType>("weekly")
  const [periodKey, setPeriodKey] = useState(currentPeriod("weekly"))
  const [title, setTitle] = useState("")
  const [remarks, setRemarks] = useState("")
  const [plans, setPlans] = useState<PlanRow[]>([])
  const [summaries, setSummaries] = useState<SummaryRow[]>([])
  const [reviews, setReviews] = useState<ReviewRow[]>([])
  const [errors, setErrors] = useState<FormErrors>({})
  const [result, setResult] = useState<WorkReportSubmissionResult | null>(null)
  const configQuery = useQuery({
    queryKey: ["work-report-field-config"],
    queryFn: WorkReportsService.readFieldConfig,
  })

  const isRequired = (section: SectionKey, field: string) =>
    configQuery.data?.data.find(
      (item) => item.section === section && item.field_key === field,
    )?.is_required ?? false

  const mutation = useMutation({
    mutationFn: WorkReportsService.createOrSupplementWorkReport,
    onSuccess: (data) => {
      setResult(data)
      showSuccessToast(
        data.submission_mode === "created"
          ? "工作汇报已提交"
          : "汇报内容已补充",
      )
      window.scrollTo({ top: 0, behavior: "smooth" })
    },
    onError: handleError.bind(showErrorToast),
  })

  const updatePlan = (key: string, patch: Partial<PlanRow>) =>
    setPlans((rows) =>
      rows.map((row) => (row._key === key ? { ...row, ...patch } : row)),
    )
  const updateSummary = (key: string, patch: Partial<SummaryRow>) =>
    setSummaries((rows) =>
      rows.map((row) => (row._key === key ? { ...row, ...patch } : row)),
    )
  const updateReview = (key: string, patch: Partial<ReviewRow>) =>
    setReviews((rows) =>
      rows.map((row) => (row._key === key ? { ...row, ...patch } : row)),
    )

  const validate = () => {
    const next: FormErrors = {}
    if (!title.trim()) next.title = "请填写汇报标题"
    if (!periodKey) next.period_key = "请选择汇报周期"
    validateRows("work_plan", plans, next, isRequired)
    validateRows("task_summary", summaries, next, isRequired)
    validateRows("work_review", reviews, next, isRequired)
    setErrors(next)
    return Object.keys(next).length === 0
  }

  const submit = () => {
    if (!validate()) return
    mutation.mutate({
      requestBody: {
        report_type: reportType,
        period_key: periodKey,
        title: title.trim(),
        remarks: remarks.trim() || null,
        work_plans: plans.map(({ _key, ...row }) => row),
        task_summaries: summaries.map(({ _key, ...row }) => row),
        work_reviews: reviews.map(({ _key, ...row }) => row),
      },
    })
  }

  const continueReporting = () => {
    setPlans([])
    setSummaries([])
    setReviews([])
    setErrors({})
    setResult(null)
  }

  if (result) {
    return <SubmissionResult result={result} onContinue={continueReporting} />
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="flex items-center gap-2 text-2xl font-semibold">
          <ClipboardList className="h-6 w-6 text-primary" />
          填写工作汇报
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          一次提交工作计划、任务总结和工作复盘；同周期再次提交会追加明细。
        </p>
      </div>

      {configQuery.isError ? (
        <Alert variant="destructive">
          <AlertTitle>无法加载字段配置</AlertTitle>
          <AlertDescription>请刷新页面后重试。</AlertDescription>
        </Alert>
      ) : null}
      {Object.keys(errors).length > 0 ? (
        <Alert variant="destructive">
          <AlertTitle>请检查表单</AlertTitle>
          <AlertDescription>
            带红色提示的字段需要补充后才能提交。
          </AlertDescription>
        </Alert>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle>工作汇报信息</CardTitle>
          <CardDescription>汇报人和提交时间由系统自动记录。</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-5 md:grid-cols-2">
          <Field label="汇报人" required>
            <Input
              value={user?.full_name || user?.email || "正在获取当前用户…"}
              disabled
              data-testid="work-report-reporter"
            />
          </Field>
          <Field label="汇报类型" required>
            <select
              className="border-input bg-background h-9 w-full rounded-md border px-3 text-sm"
              value={reportType}
              onChange={(event) => {
                const type = event.target.value as ReportType
                setReportType(type)
                setPeriodKey(currentPeriod(type))
              }}
            >
              <option value="weekly">周报</option>
              <option value="monthly">月报</option>
            </select>
          </Field>
          <Field
            label={reportType === "weekly" ? "汇报周" : "汇报月份"}
            required
          >
            <Input
              type={reportType === "weekly" ? "week" : "month"}
              value={periodKey}
              onChange={(event) => setPeriodKey(event.target.value)}
              aria-invalid={Boolean(errors.period_key)}
            />
            <ErrorText message={errors.period_key} />
          </Field>
          <Field label="汇报标题" required>
            <Input
              value={title}
              maxLength={255}
              onChange={(event) => setTitle(event.target.value)}
              aria-invalid={Boolean(errors.title)}
              placeholder="例如：研发一部第 31 周工作汇报"
            />
            <ErrorText message={errors.title} />
          </Field>
          <div className="md:col-span-2">
            <Field label="备注">
              <Textarea
                value={remarks}
                onChange={(event) => setRemarks(event.target.value)}
                placeholder="其他需要说明的信息"
              />
            </Field>
          </div>
        </CardContent>
      </Card>

      <EditableCard
        title="工作计划"
        description="填写下一阶段计划，可添加多行。"
        onAdd={() => setPlans((rows) => [...rows, { _key: newKey() }])}
      >
        <div className="overlay-scrollbar overflow-x-auto">
          <table className="w-full min-w-[1280px] border-collapse text-sm">
            <thead>
              <tr className="border-b text-left">
                {SECTION_FIELDS.work_plan.map((field) => (
                  <TableHead
                    key={field}
                    required={isRequired("work_plan", field)}
                  >
                    {FIELD_LABELS[field]}
                  </TableHead>
                ))}
                <TableHead className="w-14">操作</TableHead>
              </tr>
            </thead>
            <tbody>
              {plans.map((row) => (
                <tr key={row._key} className="border-b align-top last:border-0">
                  <TableCell
                    error={rowError(errors, "work_plan", row, "plan_content")}
                  >
                    <Textarea
                      className="h-20 min-h-20 resize-none"
                      value={row.plan_content ?? ""}
                      onChange={(event) =>
                        updatePlan(row._key, {
                          plan_content: event.target.value,
                        })
                      }
                      placeholder="计划内容"
                    />
                  </TableCell>
                  <TableCell
                    error={rowError(
                      errors,
                      "work_plan",
                      row,
                      "planned_completion_date",
                    )}
                  >
                    <Input
                      className="h-20!"
                      type="date"
                      value={row.planned_completion_date ?? ""}
                      onChange={(event) =>
                        updatePlan(row._key, {
                          planned_completion_date: event.target.value || null,
                        })
                      }
                    />
                  </TableCell>
                  <TableCell
                    error={rowError(
                      errors,
                      "work_plan",
                      row,
                      "expected_result",
                    )}
                  >
                    <Textarea
                      className="h-20 min-h-20 resize-none"
                      value={row.expected_result ?? ""}
                      onChange={(event) =>
                        updatePlan(row._key, {
                          expected_result: event.target.value,
                        })
                      }
                    />
                  </TableCell>
                  <TableCell
                    error={rowError(errors, "work_plan", row, "support_needed")}
                  >
                    <Textarea
                      className="h-20 min-h-20 resize-none"
                      value={row.support_needed ?? ""}
                      onChange={(event) =>
                        updatePlan(row._key, {
                          support_needed: event.target.value,
                        })
                      }
                    />
                  </TableCell>
                  <TableCell
                    error={rowError(errors, "work_plan", row, "remarks")}
                  >
                    <Textarea
                      className="h-20 min-h-20 resize-none"
                      value={row.remarks ?? ""}
                      onChange={(event) =>
                        updatePlan(row._key, { remarks: event.target.value })
                      }
                    />
                  </TableCell>
                  <DeleteCell
                    onDelete={() =>
                      setPlans((rows) =>
                        rows.filter((item) => item._key !== row._key),
                      )
                    }
                  />
                </tr>
              ))}
            </tbody>
          </table>
          {plans.length === 0 ? <EmptyRows /> : null}
        </div>
      </EditableCard>

      <EditableCard
        title="任务总结"
        description="进度低于 100% 时必须填写未完成原因。"
        onAdd={() =>
          setSummaries((rows) => [...rows, { _key: newKey(), progress: null }])
        }
      >
        <div className="overlay-scrollbar overflow-x-auto">
          <table className="w-full min-w-[1280px] border-collapse text-sm">
            <thead>
              <tr className="border-b text-left">
                {SECTION_FIELDS.task_summary.map((field) => (
                  <TableHead
                    key={field}
                    required={isRequired("task_summary", field)}
                  >
                    {FIELD_LABELS[field]}
                  </TableHead>
                ))}
                <TableHead className="w-14">操作</TableHead>
              </tr>
            </thead>
            <tbody>
              {summaries.map((row) => (
                <tr key={row._key} className="border-b align-top last:border-0">
                  <TableCell
                    error={rowError(errors, "task_summary", row, "work_goal")}
                  >
                    <Textarea
                      className="h-20 min-h-20 resize-none"
                      value={row.work_goal ?? ""}
                      onChange={(event) =>
                        updateSummary(row._key, {
                          work_goal: event.target.value,
                        })
                      }
                    />
                  </TableCell>
                  <TableCell
                    error={rowError(
                      errors,
                      "task_summary",
                      row,
                      "completion_date",
                    )}
                  >
                    <Input
                      className="h-20!"
                      type="date"
                      value={row.completion_date ?? ""}
                      onChange={(event) =>
                        updateSummary(row._key, {
                          completion_date: event.target.value || null,
                        })
                      }
                    />
                  </TableCell>
                  <TableCell
                    error={rowError(
                      errors,
                      "task_summary",
                      row,
                      "progress_description",
                    )}
                  >
                    <Textarea
                      className="h-20 min-h-20 resize-none"
                      value={row.progress_description ?? ""}
                      onChange={(event) =>
                        updateSummary(row._key, {
                          progress_description: event.target.value,
                        })
                      }
                    />
                  </TableCell>
                  <TableCell
                    error={rowError(errors, "task_summary", row, "progress")}
                  >
                    <div className="flex h-20 min-w-40 flex-col justify-center gap-2 rounded-md border border-input px-3">
                      <input
                        type="range"
                        min="0"
                        max="100"
                        step="5"
                        value={row.progress ?? 0}
                        onPointerDown={() =>
                          row.progress == null &&
                          updateSummary(row._key, { progress: 0 })
                        }
                        onChange={(event) =>
                          updateSummary(row._key, {
                            progress: Number(event.target.value),
                          })
                        }
                        className="w-full cursor-pointer accent-primary"
                        aria-label="当前进度"
                      />
                      <div className="flex items-center justify-between text-xs text-muted-foreground">
                        <span>
                          {row.progress == null ? "未设置" : `${row.progress}%`}
                        </span>
                        {row.progress != null ? (
                          <button
                            type="button"
                            className="hover:text-foreground"
                            onClick={() =>
                              updateSummary(row._key, { progress: null })
                            }
                          >
                            清空
                          </button>
                        ) : null}
                      </div>
                    </div>
                  </TableCell>
                  <TableCell
                    error={rowError(
                      errors,
                      "task_summary",
                      row,
                      "incomplete_reason",
                    )}
                  >
                    <Textarea
                      className="h-20 min-h-20 resize-none"
                      value={row.incomplete_reason ?? ""}
                      onChange={(event) =>
                        updateSummary(row._key, {
                          incomplete_reason: event.target.value,
                        })
                      }
                      placeholder={
                        row.progress != null && row.progress < 100
                          ? "当前进度未完成，必须填写"
                          : "未完成原因"
                      }
                    />
                  </TableCell>
                  <DeleteCell
                    onDelete={() =>
                      setSummaries((rows) =>
                        rows.filter((item) => item._key !== row._key),
                      )
                    }
                  />
                </tr>
              ))}
            </tbody>
          </table>
          {summaries.length === 0 ? <EmptyRows /> : null}
        </div>
      </EditableCard>

      <EditableCard
        title="工作复盘"
        description="总结值得保留或改进的方法。"
        onAdd={() => setReviews((rows) => [...rows, { _key: newKey() }])}
      >
        <div className="overlay-scrollbar overflow-x-auto">
          <table className="w-full min-w-[900px] border-collapse text-sm">
            <thead>
              <tr className="border-b text-left">
                {SECTION_FIELDS.work_review.map((field) => (
                  <TableHead
                    key={field}
                    required={isRequired("work_review", field)}
                  >
                    {FIELD_LABELS[field]}
                  </TableHead>
                ))}
                <TableHead className="w-14">操作</TableHead>
              </tr>
            </thead>
            <tbody>
              {reviews.map((row) => (
                <tr key={row._key} className="border-b align-top last:border-0">
                  <TableCell
                    error={rowError(
                      errors,
                      "work_review",
                      row,
                      "review_module",
                    )}
                  >
                    <Input
                      className="h-20!"
                      value={row.review_module ?? ""}
                      onChange={(event) =>
                        updateReview(row._key, {
                          review_module: event.target.value,
                        })
                      }
                      placeholder="例如：需求沟通"
                    />
                  </TableCell>
                  <TableCell
                    error={rowError(
                      errors,
                      "work_review",
                      row,
                      "review_content",
                    )}
                  >
                    <Textarea
                      className="h-20 min-h-20 resize-none"
                      value={row.review_content ?? ""}
                      onChange={(event) =>
                        updateReview(row._key, {
                          review_content: event.target.value,
                        })
                      }
                    />
                  </TableCell>
                  <DeleteCell
                    onDelete={() =>
                      setReviews((rows) =>
                        rows.filter((item) => item._key !== row._key),
                      )
                    }
                  />
                </tr>
              ))}
            </tbody>
          </table>
          {reviews.length === 0 ? <EmptyRows /> : null}
        </div>
      </EditableCard>

      <div className="flex justify-end border-t pt-6">
        <LoadingButton
          size="lg"
          loading={mutation.isPending}
          disabled={configQuery.isLoading || configQuery.isError || !user}
          onClick={submit}
        >
          <Send />
          提交工作汇报
        </LoadingButton>
      </div>
    </div>
  )
}

function validateRows(
  section: SectionKey,
  rows: Array<PlanRow | SummaryRow | ReviewRow>,
  errors: FormErrors,
  required: (section: SectionKey, field: string) => boolean,
) {
  for (const row of rows) {
    const fields = SECTION_FIELDS[section]
    const values = row as Record<string, unknown>
    if (!fields.some((field) => hasValue(values[field]))) {
      errors[`${section}.${row._key}.${fields[0]}`] = "已添加的行不能全部为空"
      continue
    }
    for (const field of fields) {
      if (required(section, field) && !hasValue(values[field])) {
        errors[`${section}.${row._key}.${field}`] = "此字段为必填项"
      }
    }
    if (
      section === "task_summary" &&
      typeof values.progress === "number" &&
      values.progress < 100 &&
      !hasValue(values.incomplete_reason)
    ) {
      errors[`${section}.${row._key}.incomplete_reason`] =
        "进度低于 100% 时必须填写原因"
    }
  }
}

const hasValue = (value: unknown) =>
  value !== null &&
  value !== undefined &&
  (typeof value !== "string" || value.trim().length > 0)

const rowError = (
  errors: FormErrors,
  section: SectionKey,
  row: { _key: string },
  field: string,
) => errors[`${section}.${row._key}.${field}`]

const Field = ({
  label,
  required,
  children,
}: {
  label: string
  required?: boolean
  children: React.ReactNode
}) => (
  <div className="space-y-2 text-sm font-medium">
    <span>
      {label}
      {required ? <span className="ml-1 text-destructive">*</span> : null}
    </span>
    {children}
  </div>
)

const EditableCard = ({
  title,
  description,
  onAdd,
  children,
}: {
  title: string
  description: string
  onAdd: () => void
  children: React.ReactNode
}) => (
  <Card>
    <CardHeader className="flex flex-row items-start justify-between gap-4">
      <div>
        <CardTitle>{title}</CardTitle>
        <CardDescription className="mt-1">{description}</CardDescription>
      </div>
      <Button type="button" variant="outline" size="sm" onClick={onAdd}>
        <Plus />
        添加一行
      </Button>
    </CardHeader>
    <CardContent>{children}</CardContent>
  </Card>
)

const TableHead = ({
  required,
  className,
  children,
}: {
  required?: boolean
  className?: string
  children: React.ReactNode
}) => (
  <th className={cn("min-w-44 px-2 py-3 font-medium", className)}>
    {children}
    {required ? <span className="ml-1 text-destructive">*</span> : null}
  </th>
)

const TableCell = ({
  error,
  children,
}: {
  error?: string
  children: React.ReactNode
}) => (
  <td
    className={cn(
      "px-2 py-3",
      error && "[&_input]:border-destructive [&_textarea]:border-destructive",
    )}
  >
    {children}
    <ErrorText message={error} />
  </td>
)

const DeleteCell = ({ onDelete }: { onDelete: () => void }) => (
  <td className="px-2 py-3">
    <Button
      type="button"
      variant="ghost"
      size="icon"
      onClick={onDelete}
      aria-label="删除此行"
    >
      <Trash2 className="text-destructive" />
    </Button>
  </td>
)

const ErrorText = ({ message }: { message?: string }) =>
  message ? (
    <span className="mt-1 block text-xs text-destructive">{message}</span>
  ) : null

const EmptyRows = () => (
  <div className="rounded-md border border-dashed py-8 text-center text-sm text-muted-foreground">
    暂无记录，点击“添加一行”开始填写。
  </div>
)

const SubmissionResult = ({
  result,
  onContinue,
}: {
  result: WorkReportSubmissionResult
  onContinue: () => void
}) => (
  <Card className="mx-auto max-w-3xl">
    <CardHeader className="text-center">
      <CheckCircle2 className="mx-auto h-12 w-12 text-emerald-500" />
      <CardTitle className="text-2xl">
        {result.submission_mode === "created"
          ? "工作汇报提交成功"
          : "工作汇报补充成功"}
      </CardTitle>
      <CardDescription>{result.title}</CardDescription>
    </CardHeader>
    <CardContent className="space-y-6">
      <div className="grid gap-4 rounded-lg bg-muted/50 p-4 sm:grid-cols-2">
        <ResultItem
          label="汇报人"
          value={result.reporter.name || result.reporter.email}
        />
        <ResultItem
          label="汇报类型"
          value={result.report_type === "weekly" ? "周报" : "月报"}
        />
        <ResultItem
          label="汇报周期"
          value={`${result.period_start} 至 ${result.period_end}`}
          icon={<CalendarDays />}
        />
        <ResultItem
          label="提交时间"
          value={new Date(result.submitted_at).toLocaleString()}
        />
      </div>
      <div className="grid grid-cols-3 gap-3 text-center">
        <Count label="工作计划" value={result.counts.work_plans} />
        <Count label="任务总结" value={result.counts.task_summaries} />
        <Count label="工作复盘" value={result.counts.work_reviews} />
      </div>
      <div className="flex justify-center">
        <Button onClick={onContinue}>
          <RotateCcw />
          继续补充本周期
        </Button>
      </div>
    </CardContent>
  </Card>
)

const ResultItem = ({
  label,
  value,
  icon,
}: {
  label: string
  value: string
  icon?: React.ReactNode
}) => (
  <div>
    <span className="flex items-center gap-1 text-xs text-muted-foreground">
      {icon}
      {label}
    </span>
    <p className="mt-1 font-medium">{value}</p>
  </div>
)

const Count = ({ label, value }: { label: string; value: number }) => (
  <div className="rounded-lg border p-4">
    <Badge variant="secondary" className="text-lg">
      {value}
    </Badge>
    <p className="mt-2 text-sm text-muted-foreground">{label}</p>
  </div>
)

export default WorkReportForm
