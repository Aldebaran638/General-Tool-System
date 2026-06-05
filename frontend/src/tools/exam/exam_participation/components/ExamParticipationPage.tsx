/**
 * Exam Participation Page — for regular users to view and take exams
 */

import { useQuery } from "@tanstack/react-query"
import { Link as RouterLink, useNavigate } from "@tanstack/react-router"
import {
  AlertCircle,
  ArrowRight,
  BookOpen,
  Calendar,
  CheckCircle2,
  Clock,
  Download,
  Eye,
  FileText,
  History,
  Lock,
  RotateCcw,
  Star,
  Timer,
  Trophy,
  XCircle,
} from "lucide-react"
import { useState } from "react"
import { toast } from "sonner"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { downloadQuestionBank } from "@/tools/exam/question_bank/api"
import { fetchMyExams, type MyExam, type MyExamsResponse } from "../api"

function formatDate(s: string): string {
  return new Date(s).toLocaleString("zh-CN", { hour12: false })
}

function formatDateShort(s: string): string {
  return new Date(s).toLocaleDateString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  })
}

/** Returns true when the exam window has ended (by time or archival) */
function isExamDone(exam: MyExam): boolean {
  return exam.is_ended || exam.status === "ARCHIVED"
}

// ─── Status Badge ─────────────────────────────────────────────────────────────

function ExamStatusBadge({ exam }: { exam: MyExam }) {
  const now = new Date()
  const start = new Date(exam.start_at)
  const end = new Date(exam.end_at)

  if (exam.status === "ARCHIVED") {
    return (
      <Badge variant="secondary">
        <History className="mr-1 h-3 w-3" />
        已归档
      </Badge>
    )
  }

  if (exam.completion_status === "COMPLETED") {
    return (
      <Badge variant="success">
        <Trophy className="mr-1 h-3 w-3" />
        已完成
      </Badge>
    )
  }

  if (exam.completion_status === "NOT_COMPLETED" && exam.attempt_count > 0) {
    return (
      <Badge variant="warning">
        <XCircle className="mr-1 h-3 w-3" />
        未通过
      </Badge>
    )
  }

  if (now < start) {
    return (
      <Badge variant="info">
        <Timer className="mr-1 h-3 w-3" />
        未开始
      </Badge>
    )
  }
  if (now > end) {
    return (
      <Badge variant="outline" className="text-muted-foreground">
        已结束
      </Badge>
    )
  }
  return (
    <Badge variant="success">
      <CheckCircle2 className="mr-1 h-3 w-3" />
      进行中
    </Badge>
  )
}

// ─── Active Exam Card (for current / upcoming exams) ─────────────────────────

function ActiveExamCard({ exam }: { exam: MyExam }) {
  const navigate = useNavigate()
  const now = new Date()
  const start = new Date(exam.start_at)
  const end = new Date(exam.end_at)
  const canStart = now >= start && now <= end
  const isEnded = isExamDone(exam)

  async function handleDownload() {
    try {
      await downloadQuestionBank(exam.id)
    } catch (error) {
      toast.error("下载失败", {
        description: error instanceof Error ? error.message : "请稍后重试",
      })
    }
  }

  const getTimeInfo = () => {
    if (now < start) {
      const ms = start.getTime() - now.getTime()
      const days = Math.ceil(ms / (1000 * 60 * 60 * 24))
      if (days > 1) return `${days} 天后开始`
      const hours = Math.ceil(ms / (1000 * 60 * 60))
      return `${hours} 小时后开始`
    }
    if (now > end) return null
    const ms = end.getTime() - now.getTime()
    const hours = Math.floor(ms / (1000 * 60 * 60))
    if (hours > 24) return `${Math.floor(hours / 24)} 天剩余`
    return `${hours} 小时剩余`
  }

  const timeInfo = getTimeInfo()
  const isAttemptLimited =
    exam.attempt_limit_type === "LIMITED" && exam.attempt_limit_count !== null
  const remainingAttempts = isAttemptLimited
    ? Math.max((exam.attempt_limit_count ?? 0) - exam.attempt_count, 0)
    : null

  const canNavigateToExam = canStart && exam.can_attempt

  const actionContent = !exam.can_attempt ? (
    <><Lock className="mr-2 h-4 w-4" />已达考试次数上限</>
  ) : exam.passed ? (
    <><RotateCcw className="mr-2 h-4 w-4" />重新考试</>
  ) : exam.attempt_count > 0 ? (
    <><RotateCcw className="mr-2 h-4 w-4" />再次考试<ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-0.5" /></>
  ) : canStart ? (
    <>开始考试<ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-0.5" /></>
  ) : now < start ? (
    <><Timer className="mr-2 h-4 w-4" />考试尚未开始</>
  ) : (
    "考试已结束"
  )

  return (
    <Card className="group relative flex flex-col overflow-hidden transition-all duration-300 hover:shadow-lg hover:-translate-y-0.5">
      {/* top color bar */}
      <div className={`absolute top-0 left-0 right-0 h-1 ${
        canStart ? "bg-gradient-to-r from-emerald-500 to-primary"
          : now < start ? "bg-gradient-to-r from-blue-400 to-primary"
          : "bg-gradient-to-r from-muted to-muted-foreground/30"
      }`} />

      <CardHeader className="pb-3 pt-5">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <div className={`rounded-lg p-1.5 ${
                canStart ? "bg-emerald-500/10 text-emerald-600"
                  : now < start ? "bg-blue-500/10 text-blue-600"
                  : "bg-muted text-muted-foreground"
              }`}>
                <BookOpen className="h-4 w-4" />
              </div>
              <ExamStatusBadge exam={exam} />
            </div>
            <CardTitle className="text-base font-semibold line-clamp-2 leading-snug">
              {exam.name}
            </CardTitle>
          </div>
        </div>
      </CardHeader>

      <CardContent className="flex flex-1 flex-col pt-0 pb-4">
        <div className="space-y-2 mb-4 text-sm text-muted-foreground">
          <div className="flex items-center gap-2">
            <Calendar className="h-3.5 w-3.5 flex-shrink-0" />
            <span className="truncate">{formatDateShort(exam.start_at)} — {formatDateShort(exam.end_at)}</span>
          </div>
          <div className="flex items-center gap-2">
            <Clock className="h-3.5 w-3.5 flex-shrink-0" />
            <span>{exam.duration_minutes} 分钟</span>
            <span className="text-muted-foreground/50">·</span>
            <Trophy className="h-3.5 w-3.5 flex-shrink-0" />
            <span>及格 {exam.pass_score} 分</span>
          </div>
          <div className="flex items-center gap-2">
            <RotateCcw className="h-3.5 w-3.5 flex-shrink-0" />
            <span>
              {isAttemptLimited
                ? `${exam.attempt_count}/${exam.attempt_limit_count} 次 · 剩余 ${remainingAttempts} 次`
                : `已考 ${exam.attempt_count} 次 · 不限次数`}
            </span>
          </div>
          {exam.best_score !== null && (
            <div className="flex items-center gap-2">
              {exam.passed ? (
                <CheckCircle2 className="h-3.5 w-3.5 flex-shrink-0 text-emerald-500" />
              ) : (
                <XCircle className="h-3.5 w-3.5 flex-shrink-0 text-red-500" />
              )}
              <span className={exam.passed ? "text-emerald-600 font-medium" : "text-red-600 font-medium"}>
                最高 {exam.best_score} 分 {exam.passed ? "· 已通过" : "· 未通过"}
              </span>
            </div>
          )}
        </div>

        <div className="mt-auto space-y-2">
          {timeInfo && canStart && (
            <div className="flex items-center gap-2 rounded-lg bg-emerald-500/10 px-3 py-2 text-sm text-emerald-700 dark:text-emerald-400">
              <AlertCircle className="h-3.5 w-3.5 flex-shrink-0" />
              <span>{timeInfo}</span>
            </div>
          )}

          {canNavigateToExam ? (
            <Button asChild className="w-full group bg-gradient-to-r from-primary to-emerald-600 shadow-sm hover:shadow-md transition-all">
              <RouterLink to="/my-exams/$examId" params={{ examId: exam.id }} data-testid={`start-exam-${exam.id}`}>
                {actionContent}
              </RouterLink>
            </Button>
          ) : (
            <Button type="button" disabled className="w-full" variant="outline">
              {actionContent}
            </Button>
          )}

          {isEnded && (
            <div className="flex gap-2">
              <Button variant="outline" size="sm" className="flex-1" onClick={() => navigate({ to: `/question-bank/${exam.id}` })}>
                <Eye className="mr-1.5 h-3.5 w-3.5" />浏览试题
              </Button>
              <Button variant="outline" size="sm" className="flex-1" onClick={handleDownload}>
                <Download className="mr-1.5 h-3.5 w-3.5" />下载
              </Button>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

// ─── History Exam Card (compact row-style for past exams) ─────────────────────

function HistoryExamCard({ exam }: { exam: MyExam }) {
  const navigate = useNavigate()

  async function handleDownload() {
    try {
      await downloadQuestionBank(exam.id)
    } catch (error) {
      toast.error("下载失败", { description: error instanceof Error ? error.message : "请稍后重试" })
    }
  }

  const scoreColor = exam.passed
    ? "text-emerald-600 dark:text-emerald-400"
    : exam.best_score !== null
    ? "text-red-600 dark:text-red-400"
    : "text-muted-foreground"

  return (
    <Card className="group transition-all duration-200 hover:shadow-md hover:bg-accent/30">
      <CardContent className="p-4">
        <div className="flex items-start gap-4">
          {/* Score circle */}
          <div className={`relative flex-shrink-0 flex h-14 w-14 items-center justify-center rounded-full border-2 ${
            exam.passed ? "border-emerald-500 bg-emerald-500/10"
              : exam.best_score !== null ? "border-red-400 bg-red-400/10"
              : "border-muted bg-muted/40"
          }`}>
            {exam.best_score !== null ? (
              <span className={`text-lg font-bold ${scoreColor}`}>{exam.best_score}</span>
            ) : (
              <XCircle className="h-6 w-6 text-muted-foreground" />
            )}
            {exam.passed && (
              <div className="absolute -top-1 -right-1 rounded-full bg-emerald-500 p-0.5">
                <Star className="h-2.5 w-2.5 text-white fill-white" />
              </div>
            )}
          </div>

          {/* Info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2 mb-1.5">
              <h3 className="text-sm font-semibold line-clamp-1 flex-1">{exam.name}</h3>
              <ExamStatusBadge exam={exam} />
            </div>
            <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
              <span className="flex items-center gap-1">
                <Calendar className="h-3 w-3" />
                {formatDate(exam.end_at)} 结束
              </span>
              <span className="flex items-center gap-1">
                <RotateCcw className="h-3 w-3" />
                共考 {exam.attempt_count} 次
              </span>
              {exam.best_score !== null && (
                <span className={`flex items-center gap-1 font-medium ${scoreColor}`}>
                  {exam.passed ? <CheckCircle2 className="h-3 w-3" /> : <XCircle className="h-3 w-3" />}
                  最高 {exam.best_score} 分 / 及格 {exam.pass_score} 分
                </span>
              )}
              {exam.best_score === null && (
                <span className="text-muted-foreground/70">未参加</span>
              )}
            </div>
          </div>

          {/* Actions */}
          <div className="flex-shrink-0 flex items-center gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
            <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => navigate({ to: `/question-bank/${exam.id}` })} title="浏览试题">
              <Eye className="h-3.5 w-3.5" />
            </Button>
            <Button variant="ghost" size="icon" className="h-7 w-7" onClick={handleDownload} title="下载试题库">
              <Download className="h-3.5 w-3.5" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

// ─── Skeleton loaders ─────────────────────────────────────────────────────────

function ActiveCardSkeleton() {
  return (
    <Card className="overflow-hidden">
      <div className="h-1 bg-muted" />
      <CardHeader className="pb-3 pt-5">
        <div className="flex items-center gap-2 mb-2">
          <Skeleton className="h-7 w-7 rounded-lg" />
          <Skeleton className="h-5 w-16" />
        </div>
        <Skeleton className="h-5 w-4/5" />
      </CardHeader>
      <CardContent className="space-y-2 pt-0">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-9 w-full mt-4" />
      </CardContent>
    </Card>
  )
}

function HistoryCardSkeleton() {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center gap-4">
          <Skeleton className="h-14 w-14 rounded-full flex-shrink-0" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-4 w-2/3" />
            <Skeleton className="h-3 w-1/2" />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

// ─── Summary stats bar ────────────────────────────────────────────────────────

function StatsBar({ exams }: { exams: MyExam[] }) {
  const total = exams.length
  const passed = exams.filter((e) => e.passed).length
  const attempted = exams.filter((e) => e.attempt_count > 0).length
  const scores = exams.filter((e) => e.best_score !== null).map((e) => e.best_score as number)
  const avgScore = scores.length ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length) : null

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      {[
        { label: "参与考试", value: total, icon: FileText, color: "text-blue-600 bg-blue-500/10" },
        { label: "已通过", value: passed, icon: Trophy, color: "text-emerald-600 bg-emerald-500/10" },
        { label: "已参加", value: attempted, icon: RotateCcw, color: "text-purple-600 bg-purple-500/10" },
        { label: "平均分", value: avgScore ?? "—", icon: Star, color: "text-amber-600 bg-amber-500/10" },
      ].map(({ label, value, icon: Icon, color }) => (
        <div key={label} className="flex items-center gap-3 rounded-xl border bg-card px-4 py-3">
          <div className={`rounded-lg p-2 ${color}`}>
            <Icon className="h-4 w-4" />
          </div>
          <div>
            <p className="text-xs text-muted-foreground">{label}</p>
            <p className="text-xl font-bold">{value}</p>
          </div>
        </div>
      ))}
    </div>
  )
}

// ─── Main page ────────────────────────────────────────────────────────────────

export function ExamParticipationPage() {
  const [page] = useState(1)

  const examsQuery = useQuery<MyExamsResponse>({
    queryKey: ["my-exams", page],
    queryFn: () => fetchMyExams(page, 100), // load more since we split into tabs
  })

  const allExams = examsQuery.data?.data ?? []

  const activeExams = allExams.filter((e) => !isExamDone(e))
  const historyExams = allExams.filter((e) => isExamDone(e))

  const defaultTab = activeExams.length > 0 ? "active" : "history"

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="rounded-xl bg-primary/10 p-2.5">
          <FileText className="h-6 w-6 text-primary" />
        </div>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">我的考试</h1>
          <p className="text-muted-foreground text-sm">查看和参与分配给您的考试</p>
        </div>
      </div>

      {/* Stats bar — only when data is ready */}
      {!examsQuery.isLoading && allExams.length > 0 && (
        <StatsBar exams={allExams} />
      )}

      {/* Loading */}
      {examsQuery.isLoading && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-[72px] rounded-xl" />
            ))}
          </div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <ActiveCardSkeleton key={i} />
            ))}
          </div>
        </div>
      )}

      {/* Error */}
      {examsQuery.isError && (
        <Card className="border-destructive">
          <CardContent className="flex flex-col items-center justify-center py-16 gap-4">
            <div className="rounded-full bg-destructive/10 p-4">
              <AlertCircle className="h-10 w-10 text-destructive" />
            </div>
            <div className="text-center">
              <h3 className="font-semibold mb-1">加载失败</h3>
              <p className="text-sm text-muted-foreground">{examsQuery.error?.message || "无法加载考试列表"}</p>
            </div>
            <Button variant="outline" onClick={() => examsQuery.refetch()}>重试</Button>
          </CardContent>
        </Card>
      )}

      {/* Empty */}
      {!examsQuery.isLoading && !examsQuery.isError && allExams.length === 0 && (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-20 gap-4">
            <div className="relative">
              <div className="rounded-full bg-primary/10 p-5">
                <BookOpen className="h-14 w-14 text-primary" />
              </div>
              <div className="absolute -bottom-1 -right-1 rounded-full bg-emerald-500 p-1.5">
                <CheckCircle2 className="h-4 w-4 text-white" />
              </div>
            </div>
            <div className="text-center">
              <h3 className="font-semibold mb-1">暂无考试</h3>
              <p className="text-sm text-muted-foreground max-w-sm">您还没有被分配任何考试，请联系管理员</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tabs */}
      {!examsQuery.isLoading && !examsQuery.isError && allExams.length > 0 && (
        <Tabs defaultValue={defaultTab} className="w-full">
          <TabsList className="grid w-full max-w-xs grid-cols-2">
            <TabsTrigger value="active" className="gap-1.5">
              <BookOpen className="h-3.5 w-3.5" />
              当前考试
              {activeExams.length > 0 && (
                <span className="ml-0.5 rounded-full bg-primary/15 px-1.5 py-0.5 text-xs font-medium text-primary">
                  {activeExams.length}
                </span>
              )}
            </TabsTrigger>
            <TabsTrigger value="history" className="gap-1.5">
              <History className="h-3.5 w-3.5" />
              历史记录
              {historyExams.length > 0 && (
                <span className="ml-0.5 rounded-full bg-muted px-1.5 py-0.5 text-xs font-medium text-muted-foreground">
                  {historyExams.length}
                </span>
              )}
            </TabsTrigger>
          </TabsList>

          {/* Active tab */}
          <TabsContent value="active" className="mt-4">
            {activeExams.length === 0 ? (
              <Card className="border-dashed">
                <CardContent className="flex flex-col items-center justify-center py-12 gap-3 text-center">
                  <Timer className="h-10 w-10 text-muted-foreground/50" />
                  <div>
                    <p className="font-medium">没有进行中的考试</p>
                    <p className="text-sm text-muted-foreground">所有考试已结束或归档，请查看历史记录</p>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {activeExams.map((exam, idx) => (
                  <div key={exam.id} className="animate-fade-in-up" style={{ animationDelay: `${idx * 50}ms` }}>
                    <ActiveExamCard exam={exam} />
                  </div>
                ))}
              </div>
            )}
          </TabsContent>

          {/* History tab */}
          <TabsContent value="history" className="mt-4">
            {historyExams.length === 0 ? (
              <Card className="border-dashed">
                <CardContent className="flex flex-col items-center justify-center py-12 gap-3 text-center">
                  <History className="h-10 w-10 text-muted-foreground/50" />
                  <div>
                    <p className="font-medium">暂无历史记录</p>
                    <p className="text-sm text-muted-foreground">参加过的结束考试会显示在这里</p>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-2">
                {historyExams.map((exam, idx) => (
                  <div key={exam.id} className="animate-fade-in-up" style={{ animationDelay: `${idx * 30}ms` }}>
                    <HistoryExamCard exam={exam} />
                  </div>
                ))}
              </div>
            )}
          </TabsContent>
        </Tabs>
      )}

      {/* Loading skeletons for history list */}
      {examsQuery.isLoading && (
        <div className="space-y-2 mt-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <HistoryCardSkeleton key={i} />
          ))}
        </div>
      )}
    </div>
  )
}

