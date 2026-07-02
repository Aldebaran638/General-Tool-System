import { useState, useMemo } from "react"
import { useQuery } from "@tanstack/react-query"
import { Loader2, Smartphone, Monitor, HelpCircle, Calendar } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { getSystemDashboardStats } from "../api"

const TYPE_LABELS: Record<string, string> = {
  SINGLE_CHOICE: "单选题",
  MULTIPLE_CHOICE: "多选题",
  TRUE_FALSE: "判断题",
}

const DEVICE_ICONS: Record<string, React.ReactNode> = {
  MOBILE: <Smartphone className="h-4 w-4" />,
  PC: <Monitor className="h-4 w-4" />,
  TABLET: <Smartphone className="h-4 w-4" />,
  UNKNOWN: <HelpCircle className="h-4 w-4" />,
}

const DEVICE_COLORS: Record<string, string> = {
  MOBILE: "#3b82f6",
  PC: "#10b981",
  TABLET: "#f59e0b",
  UNKNOWN: "#9ca3af",
}

const DEVICE_LABELS: Record<string, string> = {
  MOBILE: "手机",
  PC: "电脑",
  TABLET: "平板",
  UNKNOWN: "未知",
}

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

export function SystemDashboardPage() {
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
    if (dateFilter.range === "custom") {
      return {
        start_date: dateFilter.customStart || undefined,
        end_date: dateFilter.customEnd || undefined,
      }
    }
    const range = getDateRange(dateFilter.range)
    return {
      start_date: range.start,
      end_date: range.end,
    }
  }, [dateFilter])

  const statsQuery = useQuery({
    queryKey: ["systemDashboardStats", queryParams],
    queryFn: () => getSystemDashboardStats(queryParams),
  })

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
      <div className="text-center py-12 text-muted-foreground">暂无数据</div>
    )
  }

  const maxCount = Math.max(
    ...stats.question_type_distribution.map((d) => d.count),
    1,
  )

  // Calculate pie chart segments for device distribution
  const deviceTotal = stats.device_type_distribution.reduce(
    (sum, d) => sum + d.count,
    0,
  )
  let deviceAccumulated = 0
  const deviceSegments = stats.device_type_distribution.map((d) => {
    const start = deviceAccumulated
    const percentage = deviceTotal > 0 ? d.count / deviceTotal : 0
    deviceAccumulated += percentage
    return {
      ...d,
      start,
      end: deviceAccumulated,
      percentage: Math.round(percentage * 100),
    }
  })

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">系统总览</h1>
        <p className="text-muted-foreground">考试系统累计数据统计</p>
      </div>

      {/* Date filter */}
      <Card>
        <CardContent className="pt-6">
          <DateRangeFilter value={dateFilter} onChange={setDateFilter} />
        </CardContent>
      </Card>

      {/* Summary cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card className="flex flex-col">
          <CardHeader className="pb-2 flex-1">
            <CardDescription className="text-xs sm:text-sm leading-tight">
              考试场数
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl sm:text-3xl font-bold">
              {stats.exam_count}
            </div>
          </CardContent>
        </Card>
        <Card className="flex flex-col">
          <CardHeader className="pb-2 flex-1">
            <CardDescription className="text-xs sm:text-sm leading-tight">
              总参与人次
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl sm:text-3xl font-bold">
              {stats.total_participation}
            </div>
          </CardContent>
        </Card>
        <Card className="flex flex-col">
          <CardHeader className="pb-2 flex-1">
            <CardDescription className="text-xs sm:text-sm leading-tight">
              及格率
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl sm:text-3xl font-bold text-green-600">
              {stats.overall_pass_rate}%
            </div>
          </CardContent>
        </Card>
        <Card className="flex flex-col">
          <CardHeader className="pb-2 flex-1">
            <CardDescription className="text-xs sm:text-sm leading-tight">
              题目总数
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl sm:text-3xl font-bold">
              {stats.question_count}
            </div>
          </CardContent>
        </Card>
        <Card className="flex flex-col">
          <CardHeader className="pb-2 flex-1">
            <CardDescription className="text-xs sm:text-sm leading-tight">
              试卷总数
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl sm:text-3xl font-bold">
              {stats.paper_count}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts row — 2 columns after removing difficulty chart */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Device type distribution pie chart */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">考试终端分布</CardTitle>
          </CardHeader>
          <CardContent>
            {deviceSegments.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                暂无数据
              </div>
            ) : (
              <div className="flex flex-col items-center gap-4">
                <div className="relative w-40 h-40">
                  <div
                    className="w-full h-full rounded-full"
                    style={{
                      background: `conic-gradient(${deviceSegments
                        .map(
                          (s) =>
                            `${DEVICE_COLORS[s.device_type] || "#9ca3af"} ${s.start * 360}deg ${s.end * 360}deg`,
                        )
                        .join(", ")})`,
                    }}
                  />
                  <div className="absolute inset-0 m-auto w-20 h-20 bg-card rounded-full" />
                </div>
                <div className="flex flex-wrap gap-3 justify-center">
                  {deviceSegments.map((s) => (
                    <div
                      key={s.device_type}
                      className="flex items-center gap-1.5 text-sm"
                    >
                      <div
                        className="w-3 h-3 rounded-full"
                        style={{
                          backgroundColor:
                            DEVICE_COLORS[s.device_type] || "#9ca3af",
                        }}
                      />
                      {DEVICE_ICONS[s.device_type] || (
                        <HelpCircle className="h-4 w-4" />
                      )}
                      <span>
                        {DEVICE_LABELS[s.device_type] || s.device_type}
                      </span>
                      <span className="text-muted-foreground">
                        {s.percentage}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Question type distribution bar chart */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">题库题型分布</CardTitle>
          </CardHeader>
          <CardContent>
            {stats.question_type_distribution.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                暂无题目数据
              </div>
            ) : (
              <div className="flex items-end gap-4 h-48">
                {stats.question_type_distribution.map((item) => (
                  <div
                    key={item.question_type}
                    className="flex flex-col items-center gap-2 flex-1"
                  >
                    <div className="text-sm font-medium">{item.count}</div>
                    <div
                      className="w-full bg-primary rounded-t-md transition-all"
                      style={{
                        height: `${(item.count / maxCount) * 120}px`,
                        minHeight: "4px",
                      }}
                    />
                    <div className="text-xs text-muted-foreground text-center">
                      {TYPE_LABELS[item.question_type] || item.question_type}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
