/**
 * Exam Participation Page — for regular users to view and take exams
 */

import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import {
  FileText,
  Clock,
  Calendar,
  CheckCircle2,
  ArrowRight,
  BookOpen,
  Trophy,
  AlertCircle,
  Timer,
  XCircle,
  RotateCcw,
  Lock,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"

import {
  fetchMyExams,
  type MyExam,
  type MyExamsResponse,
} from "../api"

function formatDate(s: string): string {
  return new Date(s).toLocaleString("zh-CN", { hour12: false })
}

function ExamStatusBadge({ exam }: { exam: MyExam }) {
  const now = new Date()
  const start = new Date(exam.start_at)
  const end = new Date(exam.end_at)

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
        未完成
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

function ExamCard({
  exam,
  onStart,
}: {
  exam: MyExam
  onStart: (examId: string) => void
}) {
  const now = new Date()
  const start = new Date(exam.start_at)
  const end = new Date(exam.end_at)
  const canStart = now >= start && now <= end

  // Calculate time remaining or until start
  const getTimeInfo = () => {
    if (now < start) {
      const days = Math.ceil((start.getTime() - now.getTime()) / (1000 * 60 * 60 * 24))
      if (days > 0) return `${days} 天后开始`
      const hours = Math.ceil((start.getTime() - now.getTime()) / (1000 * 60 * 60))
      return `${hours} 小时后开始`
    }
    if (now > end) return null
    const hoursLeft = Math.floor((end.getTime() - now.getTime()) / (1000 * 60 * 60))
    if (hoursLeft > 24) return `${Math.floor(hoursLeft / 24)} 天剩余`
    return `${hoursLeft} 小时剩余`
  }

  const timeInfo = getTimeInfo()

  return (
    <Card className="group relative overflow-hidden transition-all duration-300 hover:shadow-xl hover:-translate-y-1">
      {/* Status indicator bar */}
      <div
        className={`absolute top-0 left-0 right-0 h-1 ${
          canStart
            ? "bg-gradient-to-r from-success to-primary"
            : now < start
            ? "bg-gradient-to-r from-info to-primary"
            : "bg-gradient-to-r from-muted to-muted-foreground/30"
        }`}
      />

      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <div
                className={`rounded-lg p-1.5 ${
                  canStart
                    ? "bg-success/10 text-success"
                    : now < start
                    ? "bg-info/10 text-info"
                    : "bg-muted text-muted-foreground"
                }`}
              >
                <BookOpen className="h-4 w-4" />
              </div>
              <ExamStatusBadge exam={exam} />
            </div>
            <CardTitle className="text-lg font-semibold line-clamp-1 mt-2">
              {exam.name}
            </CardTitle>
            {exam.description && (
              <CardDescription className="mt-1 line-clamp-2">
                {exam.description}
              </CardDescription>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-0">
        <div className="space-y-3 mb-4">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Calendar className="h-4 w-4 flex-shrink-0" />
            <span className="truncate">开始：{formatDate(exam.start_at)}</span>
          </div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Calendar className="h-4 w-4 flex-shrink-0" />
            <span className="truncate">结束：{formatDate(exam.end_at)}</span>
          </div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Clock className="h-4 w-4 flex-shrink-0" />
            <span>时长：{exam.duration_minutes} 分钟</span>
          </div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Trophy className="h-4 w-4 flex-shrink-0" />
            <span>及格分：{exam.pass_score} 分</span>
          </div>
          {/* Attempt stats */}
          {exam.attempt_count > 0 && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <RotateCcw className="h-4 w-4 flex-shrink-0" />
              <span>
                已考 {exam.attempt_count} 次
                {exam.best_score !== null && ` · 最高 ${exam.best_score} 分`}
              </span>
            </div>
          )}
          {exam.last_score !== null && (
            <div className="flex items-center gap-2 text-sm">
              {exam.passed ? (
                <CheckCircle2 className="h-4 w-4 flex-shrink-0 text-emerald-500" />
              ) : (
                <XCircle className="h-4 w-4 flex-shrink-0 text-red-500" />
              )}
              <span className={exam.passed ? "text-emerald-600" : "text-red-600"}>
                上次成绩：{exam.last_score} 分 {exam.passed ? "(通过)" : "(未通过)"}
              </span>
            </div>
          )}
        </div>

        {timeInfo && canStart && (
          <div className="mb-4 flex items-center gap-2 rounded-lg bg-success/10 px-3 py-2 text-sm text-success">
            <AlertCircle className="h-4 w-4" />
            <span>{timeInfo}</span>
          </div>
        )}

        <Button
          onClick={() => onStart(exam.id)}
          disabled={!canStart || !exam.can_attempt}
          className={`w-full transition-all duration-200 ${
            canStart && exam.can_attempt
              ? "bg-gradient-to-r from-primary to-success shadow-md hover:shadow-lg"
              : ""
          }`}
          variant={canStart && exam.can_attempt ? "default" : "outline"}
        >
          {!exam.can_attempt ? (
            <>
              <Lock className="mr-2 h-4 w-4" />
              已达考试次数上限
            </>
          ) : exam.passed ? (
            <>
              <RotateCcw className="mr-2 h-4 w-4" />
              重新考试
            </>
          ) : exam.attempt_count > 0 ? (
            <>
              <RotateCcw className="mr-2 h-4 w-4" />
              再次考试
              <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-0.5" />
            </>
          ) : canStart ? (
            <>
              开始考试
              <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-0.5" />
            </>
          ) : now < start ? (
            <>
              <Timer className="mr-2 h-4 w-4" />
              考试尚未开始
            </>
          ) : (
            "考试已结束"
          )}
        </Button>
      </CardContent>
    </Card>
  )
}

function ExamCardSkeleton() {
  return (
    <Card className="overflow-hidden">
      <div className="h-1 bg-gray-200 dark:bg-gray-700" />
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <Skeleton className="h-7 w-7 rounded-lg" />
              <Skeleton className="h-5 w-16" />
            </div>
            <Skeleton className="h-6 w-3/4" />
            <Skeleton className="h-4 w-full mt-2" />
          </div>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="space-y-3 mb-4">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-2/3" />
          <Skeleton className="h-4 w-1/2" />
        </div>
        <Skeleton className="h-10 w-full" />
      </CardContent>
    </Card>
  )
}

export function ExamParticipationPage() {
  const navigate = useNavigate()
  const [page, setPage] = useState(1)

  const examsQuery = useQuery<MyExamsResponse>({
    queryKey: ["my-exams", page],
    queryFn: () => fetchMyExams(page),
  })

  const exams = examsQuery.data?.data ?? []
  const total = examsQuery.data?.count ?? 0
  const pageSize = 20
  const totalPages = Math.max(1, Math.ceil(total / pageSize))

  const handleStartExam = (examId: string) => {
    navigate({ to: `/my-exams/$examId`, params: { examId } })
  }

  return (
    <div className="flex flex-col gap-6">
      {/* Page header */}
      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-primary/10 p-2.5">
            <FileText className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">我的考试</h1>
            <p className="text-muted-foreground">
              查看和参与分配给您的考试
            </p>
          </div>
        </div>
      </div>

      {/* Loading state */}
      {examsQuery.isLoading && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <ExamCardSkeleton key={i} />
          ))}
        </div>
      )}

      {/* Error state */}
      {examsQuery.isError && (
        <Card className="border-destructive">
          <CardContent className="flex flex-col items-center justify-center py-16">
            <div className="rounded-full bg-destructive/10 p-4 mb-4">
              <AlertCircle className="h-12 w-12 text-destructive" />
            </div>
            <h3 className="text-lg font-semibold mb-1">加载失败</h3>
            <p className="text-muted-foreground text-center max-w-sm">
              {examsQuery.error?.message || "无法加载考试列表，请稍后重试"}
            </p>
            <Button
              variant="outline"
              onClick={() => examsQuery.refetch()}
              className="mt-4"
            >
              重试
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Empty state */}
      {!examsQuery.isLoading && exams.length === 0 && (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-20">
            <div className="relative mb-6">
              <div className="rounded-full bg-primary/10 p-5">
                <BookOpen className="h-14 w-14 text-primary" />
              </div>
              <div className="absolute -bottom-1 -right-1 rounded-full bg-success p-1.5">
                <CheckCircle2 className="h-4 w-4 text-white" />
              </div>
            </div>
            <h3 className="text-lg font-semibold mb-2">暂无考试</h3>
            <p className="text-muted-foreground text-center max-w-sm leading-relaxed">
              您还没有被分配任何考试，请联系管理员或等待考试发布后刷新页面
            </p>
          </CardContent>
        </Card>
      )}

      {/* Exam cards grid */}
      {!examsQuery.isLoading && exams.length > 0 && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {exams.map((exam, index) => (
            <div
              key={exam.id}
              className="animate-fade-in-up"
              style={{ animationDelay: `${index * 60}ms` }}
            >
              <ExamCard
                exam={exam}
                onStart={handleStartExam}
              />
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between rounded-lg border bg-card px-4 py-3">
          <span className="text-sm text-muted-foreground">
            共 {total} 场考试
          </span>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={page <= 1}
              onClick={() => setPage(page - 1)}
            >
              上一页
            </Button>
            <span className="text-sm text-muted-foreground px-2">
              {page} / {totalPages}
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
        </div>
      )}
    </div>
  )
}
