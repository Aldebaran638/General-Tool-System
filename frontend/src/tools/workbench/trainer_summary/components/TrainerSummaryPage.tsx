import { Suspense, useState, useMemo } from "react"
import { useSuspenseQuery } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import {
  GraduationCap,
  Search,
  Calendar,
  Users,
  BookOpen,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { getTrainerSummary, type TrainerGroup } from "../api"

// ─── Date filter utilities (shared with system dashboard) ───────────────────

type DateRange =
  | "last7"
  | "last30"
  | "last90"
  | "thisYear"
  | "all"
  | "custom"

function formatDateInput(d: Date): string {
  const pad = (n: number) => String(n).padStart(2, "0")
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

function getDateRange(range: DateRange): { start?: string; end?: string } {
  const now = new Date()
  const end = formatDateInput(now)
  if (range === "all") return {}
  if (range === "thisYear") {
    return { start: `${now.getFullYear()}-01-01`, end }
  }
  const days =
    range === "last7" ? 7 : range === "last30" ? 30 : range === "last90" ? 90 : 0
  if (days > 0) {
    const startDate = new Date(now)
    startDate.setDate(startDate.getDate() - days)
    return { start: formatDateInput(startDate), end }
  }
  return {}
}

function DateRangeFilter({
  value,
  onChange,
}: {
  value: { range: DateRange; customStart: string; customEnd: string }
  onChange: (v: { range: DateRange; customStart: string; customEnd: string }) => void
}) {
  const { range, customStart, customEnd } = value

  const shortcuts: { key: DateRange; label: string }[] = [
    { key: "last7", label: "近7天" },
    { key: "last30", label: "近30天" },
    { key: "last90", label: "近90天" },
    { key: "thisYear", label: "本年度" },
    { key: "all", label: "全部" },
  ]

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center gap-2">
        <Calendar className="h-4 w-4 text-muted-foreground" />
        <span className="text-sm font-medium">时间范围</span>
      </div>
      <div className="flex flex-wrap gap-2">
        {shortcuts.map((s) => (
          <Button
            key={s.key}
            variant={range === s.key ? "default" : "outline"}
            size="sm"
            onClick={() =>
              onChange({ range: s.key, customStart, customEnd })
            }
          >
            {s.label}
          </Button>
        ))}
        <Button
          variant={range === "custom" ? "default" : "outline"}
          size="sm"
          onClick={() =>
            onChange({ range: "custom", customStart, customEnd })
          }
        >
          自定义
        </Button>
      </div>
      {range === "custom" && (
        <div className="grid grid-cols-2 gap-3">
          <div className="grid gap-1.5">
            <Label className="text-xs">开始日期</Label>
            <Input
              type="date"
              value={customStart}
              onChange={(e) =>
                onChange({
                  range,
                  customStart: e.target.value,
                  customEnd,
                })
              }
            />
          </div>
          <div className="grid gap-1.5">
            <Label className="text-xs">结束日期</Label>
            <Input
              type="date"
              value={customEnd}
              onChange={(e) =>
                onChange({
                  range,
                  customStart,
                  customEnd: e.target.value,
                })
              }
            />
          </div>
        </div>
      )}
    </div>
  )
}

// ─── Helpers ────────────────────────────────────────────────────────────────

function formatTrainerName(name: string): string {
  if (!name) return "未知讲师"
  // If it looks like a UUID (with or without hyphens), fallback
  if (
    /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(name) ||
    /^[0-9a-f]{32}$/i.test(name)
  ) {
    return "未知讲师"
  }
  return name
}

function formatDateTime(isoString: string): string {
  const date = new Date(isoString)
  return date.toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  })
}

// ─── Skeleton Components ────────────────────────────────────────────────────

function PendingTrainerCard() {
  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center gap-3">
          <Skeleton className="h-9 w-9 rounded-lg" />
          <div className="flex-1">
            <Skeleton className="h-5 w-32 mb-2" />
            <div className="flex items-center gap-3">
              <Skeleton className="h-4 w-20" />
              <Skeleton className="h-4 w-20" />
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="rounded-md border overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow className="bg-muted/50">
                <TableHead>课程名称</TableHead>
                <TableHead>中心</TableHead>
                <TableHead>考试时间</TableHead>
                <TableHead className="text-right">培训人数</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {Array.from({ length: 3 }).map((_, i) => (
                <TableRow key={i}>
                  <TableCell><Skeleton className="h-4 w-32" /></TableCell>
                  <TableCell><Skeleton className="h-4 w-20" /></TableCell>
                  <TableCell><Skeleton className="h-4 w-28" /></TableCell>
                  <TableCell className="text-right"><Skeleton className="h-4 w-8 ml-auto" /></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  )
}

function PendingTrainerSummary() {
  return (
    <div className="flex flex-col gap-4">
      {Array.from({ length: 2 }).map((_, i) => (
        <PendingTrainerCard key={i} />
      ))}
    </div>
  )
}

// ─── Trainer Card ───────────────────────────────────────────────────────────

function TrainerCard({ group }: { group: TrainerGroup }) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-primary/10 p-2">
              <GraduationCap className="h-5 w-5 text-primary" />
            </div>
            <div>
              <CardTitle className="text-base">{formatTrainerName(group.trainer_name)}</CardTitle>
              <div className="flex items-center gap-3 text-sm text-muted-foreground mt-1">
                <span className="flex items-center gap-1">
                  <BookOpen className="h-3.5 w-3.5" />
                  授课 {group.exam_count} 次
                </span>
                <span className="flex items-center gap-1">
                  <Users className="h-3.5 w-3.5" />
                  培训 {group.total_participants} 人
                </span>
              </div>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="rounded-md border overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow className="bg-muted/50">
                <TableHead>课程名称</TableHead>
                <TableHead>中心</TableHead>
                <TableHead>考试时间</TableHead>
                <TableHead className="text-right">培训人数</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {group.exams.map((exam) => (
                <TableRow
                  key={exam.exam_id}
                  className="hover:bg-muted/30 transition-colors"
                >
                  <TableCell>
                    <Link
                      to="/exams/$examId"
                      params={{ examId: exam.exam_id }}
                      className="text-primary hover:underline font-medium"
                    >
                      {exam.exam_name}
                    </Link>
                  </TableCell>
                  <TableCell>{exam.center ?? "—"}</TableCell>
                  <TableCell className="text-sm whitespace-nowrap">
                    {formatDateTime(exam.start_at)}
                  </TableCell>
                  <TableCell className="text-right">
                    {exam.participant_count}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  )
}

// ─── Main Content ───────────────────────────────────────────────────────────

function TrainerSummaryContent({
  queryParams,
}: {
  queryParams: { q?: string; start_date?: string; end_date?: string }
}) {
  const summaryQuery = useSuspenseQuery({
    queryKey: ["trainerSummary", queryParams],
    queryFn: () => getTrainerSummary(queryParams),
  })

  const groups = summaryQuery.data?.data ?? []

  return (
    <>
      {/* Trainer groups */}
      {groups.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground border rounded-lg">
          <GraduationCap className="h-12 w-12 mx-auto mb-3 text-muted-foreground/50" />
          <p>暂无培训讲师数据</p>
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          {groups.map((group) => (
            <TrainerCard key={group.trainer_id} group={group} />
          ))}
        </div>
      )}
    </>
  )
}

// ─── Main Page ──────────────────────────────────────────────────────────────

export function TrainerSummaryPage() {
  const [searchQuery, setSearchQuery] = useState("")
  const [dateFilter, setDateFilter] = useState<{
    range: DateRange
    customStart: string
    customEnd: string
  }>({
    range: "all",
    customStart: "",
    customEnd: "",
  })

  const queryParams = useMemo(() => {
    const params: { q?: string; start_date?: string; end_date?: string } = {}
    if (searchQuery.trim()) params.q = searchQuery.trim()
    if (dateFilter.range === "custom") {
      if (dateFilter.customStart) params.start_date = dateFilter.customStart
      if (dateFilter.customEnd) params.end_date = dateFilter.customEnd
    } else {
      const range = getDateRange(dateFilter.range)
      if (range.start) params.start_date = range.start
      if (range.end) params.end_date = range.end
    }
    return params
  }, [searchQuery, dateFilter])

  return (
    <div className="flex flex-col gap-6">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">培训讲师汇总</h1>
        <p className="text-muted-foreground">
          讲师授课数据统计
        </p>
      </div>

      {/* Filters */}
      <div className="flex flex-col gap-4">
        {/* Search */}
        <div className="relative max-w-md">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="搜索讲师姓名或课程名称..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>

        {/* Date filter */}
        <DateRangeFilter value={dateFilter} onChange={setDateFilter} />
      </div>

      <Suspense fallback={<PendingTrainerSummary />}>
        <TrainerSummaryContent queryParams={queryParams} />
      </Suspense>
    </div>
  )
}
