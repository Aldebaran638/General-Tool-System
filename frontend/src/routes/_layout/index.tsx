import { Suspense } from "react"
import { useNavigate, Link } from "@tanstack/react-router"
import { createFileRoute } from "@tanstack/react-router"
import { useSuspenseQuery } from "@tanstack/react-query"
import {
  CalendarDays,
  ClipboardList,
  BookOpen,
  Users,
  TrendingUp,
  ArrowRight,
  FileText,
  BarChart3,
  GraduationCap,
  UserCog,
  RefreshCw,
} from "lucide-react"

import useAuth from "@/hooks/useAuth"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { listExams } from "@/tools/exam/exam_management/api"
import { getSystemDashboardStats } from "@/tools/workbench/system_dashboard/api"

export const Route = createFileRoute("/_layout/")({
  component: Dashboard,
  head: () => ({
    meta: [
      {
        title: "Dashboard - 通用工具系统",
      },
    ],
  }),
})

function formatToday(): string {
  const now = new Date()
  const weekdays = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"]
  const pad = (n: number) => String(n).padStart(2, "0")
  return `${now.getFullYear()}年${pad(now.getMonth() + 1)}月${pad(now.getDate())}日 ${weekdays[now.getDay()]}`
}

function fmtTimeShort(s: string | null): string {
  if (!s) return "—"
  const d = new Date(s)
  const pad = (n: number) => String(n).padStart(2, "0")
  return `${pad(d.getMonth() + 1)}/${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

function ExamStatusBadge({ status, startAt, endAt }: { status: string; startAt: string; endAt: string }) {
  const now = new Date()
  const start = new Date(startAt)
  const end = new Date(endAt)

  if (status === "DRAFT") return <Badge variant="secondary">未发布</Badge>
  if (status === "ARCHIVED")
    return (
      <Badge variant="outline" className="text-muted-foreground">
        已归档
      </Badge>
    )
  if (now < start) return <Badge variant="info">未开始</Badge>
  if (now > end) return <Badge variant="warning">已结束</Badge>
  return <Badge variant="success">进行中</Badge>
}

// ─── Skeletons ─────────────────────────────────────────────────────────────

function PendingStats() {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <Card key={i} className="border-none shadow-sm">
          <CardContent className="p-5">
            <div className="flex items-center justify-between">
              <div className="flex flex-col gap-2">
                <Skeleton className="h-4 w-16" />
                <Skeleton className="h-8 w-12" />
              </div>
              <Skeleton className="h-10 w-10 rounded-xl" />
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}

function PendingRecentExams() {
  return (
    <Card className="border-none shadow-sm">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <Skeleton className="h-5 w-20" />
          <Skeleton className="h-8 w-20" />
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="flex flex-col gap-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <div
              key={i}
              className="flex items-center justify-between rounded-lg border px-4 py-3"
            >
              <div className="flex items-center gap-3 min-w-0">
                <Skeleton className="h-8 w-8 rounded-lg shrink-0" />
                <div className="min-w-0 flex flex-col gap-1.5">
                  <Skeleton className="h-4 w-32" />
                  <Skeleton className="h-3 w-24" />
                </div>
              </div>
              <Skeleton className="h-5 w-14 rounded-full shrink-0" />
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

// ─── Data Components ───────────────────────────────────────────────────────

function StatsContent() {
  const { data: stats } = useSuspenseQuery({
    queryKey: ["dashboardStats"],
    queryFn: () => getSystemDashboardStats({}),
  })

  const statCards = [
    {
      label: "考试场次",
      value: stats?.exam_count ?? 0,
      icon: ClipboardList,
      color: "text-blue-600",
      bg: "bg-blue-50 dark:bg-blue-950/30",
    },
    {
      label: "试题数量",
      value: stats?.question_count ?? 0,
      icon: BookOpen,
      color: "text-emerald-600",
      bg: "bg-emerald-50 dark:bg-emerald-950/30",
    },
    {
      label: "参与人次",
      value: stats?.total_participation ?? 0,
      icon: Users,
      color: "text-violet-600",
      bg: "bg-violet-50 dark:bg-violet-950/30",
    },
    {
      label: "及格率",
      value: stats?.overall_pass_rate ?? 0,
      suffix: "%",
      icon: TrendingUp,
      color: "text-amber-600",
      bg: "bg-amber-50 dark:bg-amber-950/30",
    },
  ]

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {statCards.map((card) => (
        <Card key={card.label} className="border-none shadow-sm">
          <CardContent className="p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">{card.label}</p>
                <p className="text-2xl font-bold mt-1">
                  {card.value.toLocaleString()}
                  {card.suffix}
                </p>
              </div>
              <div className={`rounded-xl p-3 ${card.bg}`}>
                <card.icon className={`h-5 w-5 ${card.color}`} />
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}

function RecentExamsContent() {
  const navigate = useNavigate()
  const { data: examsData } = useSuspenseQuery({
    queryKey: ["recentExams"],
    queryFn: () => listExams({ page: 1, limit: 5 }),
  })

  const recentExams = examsData?.data ?? []

  return (
    <Card className="border-none shadow-sm">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">最近考试</CardTitle>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate({ to: "/exams" })}
          >
            查看全部
            <ArrowRight className="ml-1 h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        {recentExams.length === 0 ? (
          <div className="flex flex-col items-center gap-3 py-8 text-muted-foreground">
            <div className="rounded-full bg-muted p-4">
              <FileText className="h-6 w-6" />
            </div>
            <p className="text-sm">暂无考试</p>
          </div>
        ) : (
          <div className="flex flex-col gap-2">
            {recentExams.map((exam) => (
              <div
                key={exam.id}
                className="flex items-center justify-between rounded-lg border px-4 py-3 transition-colors hover:bg-muted/50"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <div className="rounded-lg bg-primary/10 p-2 shrink-0">
                    <ClipboardList className="h-4 w-4 text-primary" />
                  </div>
                  <div className="min-w-0">
                    <Link
                      to="/exams/$examId"
                      params={{ examId: exam.id }}
                      className="text-sm font-medium hover:text-primary hover:underline truncate block"
                    >
                      {exam.name}
                    </Link>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      {fmtTimeShort(exam.start_at)} ~ {fmtTimeShort(exam.end_at)}
                    </p>
                  </div>
                </div>
                <div className="shrink-0 ml-2">
                  <ExamStatusBadge
                    status={exam.status}
                    startAt={exam.start_at}
                    endAt={exam.end_at}
                  />
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

// ─── Main Dashboard ────────────────────────────────────────────────────────

const QUICK_LINKS = [
  {
    label: "考试管理",
    description: "创建和管理考试",
    icon: ClipboardList,
    href: "/exams",
    color: "bg-blue-50 text-blue-600 dark:bg-blue-950/30 dark:text-blue-400",
    adminOnly: true,
  },
  {
    label: "试题库",
    description: "管理题库和分类",
    icon: BookOpen,
    href: "/question-bank",
    color: "bg-emerald-50 text-emerald-600 dark:bg-emerald-950/30 dark:text-emerald-400",
    adminOnly: false,
  },
  {
    label: "系统总览",
    description: "数据统计与分析",
    icon: BarChart3,
    href: "/system-dashboard",
    color: "bg-violet-50 text-violet-600 dark:bg-violet-950/30 dark:text-violet-400",
    adminOnly: true,
  },
  {
    label: "培训讲师",
    description: "讲师授课汇总",
    icon: GraduationCap,
    href: "/trainer-summary",
    color: "bg-amber-50 text-amber-600 dark:bg-amber-950/30 dark:text-amber-400",
    adminOnly: true,
  },
  {
    label: "用户管理",
    description: "管理系统用户",
    icon: UserCog,
    href: "/admin",
    color: "bg-rose-50 text-rose-600 dark:bg-rose-950/30 dark:text-rose-400",
    adminOnly: true,
  },
  {
    label: "数据同步",
    description: "同步企业微信数据",
    icon: RefreshCw,
    href: "/wecom-member-sync",
    color: "bg-cyan-50 text-cyan-600 dark:bg-cyan-950/30 dark:text-cyan-400",
    adminOnly: true,
  },
]

function Dashboard() {
  const { user: currentUser } = useAuth()
  const navigate = useNavigate()
  const isAdmin = currentUser?.is_superuser ?? false

  const visibleLinks = QUICK_LINKS.filter((link) => !link.adminOnly || isAdmin)

  return (
    <div className="flex flex-col gap-6">
      {/* Welcome banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-teal-600 via-teal-700 to-emerald-800 dark:from-teal-800 dark:via-teal-900 dark:to-emerald-950 px-6 py-8 md:px-10 md:py-10">
        {/* Decorative elements */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute -top-20 -right-20 h-60 w-60 rounded-full bg-white/10 blur-3xl" />
          <div className="absolute -bottom-20 -left-20 h-60 w-60 rounded-full bg-emerald-400/15 blur-3xl" />
          <div className="absolute top-1/2 right-1/4 h-40 w-40 rounded-full bg-white/5 blur-2xl" />
        </div>

        <div className="relative z-10 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-xl md:text-2xl font-bold text-white">
              欢迎回来，{currentUser?.full_name || currentUser?.email || "用户"}
            </h1>
            <p className="text-teal-100 text-sm mt-1">
              课程培训及考核管理平台
            </p>
          </div>
          <div className="flex items-center gap-2 text-teal-100 bg-white/10 backdrop-blur-sm rounded-lg px-4 py-2 border border-white/10">
            <CalendarDays className="h-4 w-4" />
            <span className="text-sm font-medium">{formatToday()}</span>
          </div>
        </div>
      </div>

      {/* Stat cards */}
      <Suspense fallback={<PendingStats />}>
        <StatsContent />
      </Suspense>

      {/* Quick links */}
      <div>
        <h2 className="text-lg font-semibold mb-3">快捷入口</h2>
        <div className="grid gap-3 grid-cols-[repeat(auto-fill,minmax(140px,1fr))]">
          {visibleLinks.map((link) => (
            <button
              key={link.label}
              onClick={() => navigate({ to: link.href })}
              className="flex flex-col items-center justify-center gap-2 rounded-xl border bg-card p-4 text-center transition-all hover:shadow-md hover:border-primary/30 hover:-translate-y-0.5"
            >
              <div className={`rounded-xl p-3 ${link.color}`}>
                <link.icon className="h-5 w-5" />
              </div>
              <div className="w-full">
                <p className="text-sm font-medium">{link.label}</p>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {link.description}
                </p>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Recent exams */}
      <Suspense fallback={<PendingRecentExams />}>
        <RecentExamsContent />
      </Suspense>
    </div>
  )
}
