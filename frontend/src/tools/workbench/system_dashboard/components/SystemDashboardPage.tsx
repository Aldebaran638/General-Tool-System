import { useQuery } from "@tanstack/react-query"
import { Loader2, Smartphone, Monitor, HelpCircle } from "lucide-react"

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { getSystemDashboardStats } from "../api"

const TYPE_LABELS: Record<string, string> = {
  SINGLE_CHOICE: "单选题",
  MULTIPLE_CHOICE: "多选题",
  TRUE_FALSE: "判断题",
}

const DIFFICULTY_LABELS: Record<string, string> = {
  EASY: "简单",
  MEDIUM: "中等",
  HARD: "困难",
}

const DIFFICULTY_COLORS: Record<string, string> = {
  EASY: "#22c55e",
  MEDIUM: "#f59e0b",
  HARD: "#ef4444",
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

export function SystemDashboardPage() {
  const statsQuery = useQuery({
    queryKey: ["systemDashboardStats"],
    queryFn: getSystemDashboardStats,
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
  const deviceTotal = stats.device_type_distribution.reduce((sum, d) => sum + d.count, 0)
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

  // Calculate pie chart segments for difficulty distribution
  const difficultyTotal = stats.difficulty_distribution.reduce((sum, d) => sum + d.count, 0)
  let difficultyAccumulated = 0
  const difficultySegments = stats.difficulty_distribution.map((d) => {
    const start = difficultyAccumulated
    const percentage = difficultyTotal > 0 ? d.count / difficultyTotal : 0
    difficultyAccumulated += percentage
    return {
      ...d,
      start,
      end: difficultyAccumulated,
      percentage: Math.round(percentage * 100),
    }
  })

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">系统总览</h1>
        <p className="text-muted-foreground">考试系统累计数据统计</p>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card className="flex flex-col">
          <CardHeader className="pb-2 flex-1">
            <CardDescription className="text-xs sm:text-sm leading-tight">考试场数</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl sm:text-3xl font-bold">{stats.exam_count}</div>
          </CardContent>
        </Card>
        <Card className="flex flex-col">
          <CardHeader className="pb-2 flex-1">
            <CardDescription className="text-xs sm:text-sm leading-tight">总参与人次</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl sm:text-3xl font-bold">
              {stats.total_participation}
            </div>
          </CardContent>
        </Card>
        <Card className="flex flex-col">
          <CardHeader className="pb-2 flex-1">
            <CardDescription className="text-xs sm:text-sm leading-tight">及格率</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl sm:text-3xl font-bold text-green-600">
              {stats.overall_pass_rate}%
            </div>
          </CardContent>
        </Card>
        <Card className="flex flex-col">
          <CardHeader className="pb-2 flex-1">
            <CardDescription className="text-xs sm:text-sm leading-tight">题目总数</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl sm:text-3xl font-bold">{stats.question_count}</div>
          </CardContent>
        </Card>
        <Card className="flex flex-col">
          <CardHeader className="pb-2 flex-1">
            <CardDescription className="text-xs sm:text-sm leading-tight">试卷总数</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl sm:text-3xl font-bold">{stats.paper_count}</div>
          </CardContent>
        </Card>
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Device type distribution pie chart */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">考试终端分布</CardTitle>
          </CardHeader>
          <CardContent>
            {deviceSegments.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">暂无数据</div>
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
                    <div key={s.device_type} className="flex items-center gap-1.5 text-sm">
                      <div
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: DEVICE_COLORS[s.device_type] || "#9ca3af" }}
                      />
                      {DEVICE_ICONS[s.device_type] || <HelpCircle className="h-4 w-4" />}
                      <span>{s.device_type === "UNKNOWN" ? "未知" : s.device_type === "MOBILE" ? "手机" : s.device_type === "PC" ? "电脑" : "平板"}</span>
                      <span className="text-muted-foreground">{s.percentage}%</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Difficulty distribution pie chart */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">题库难易度占比</CardTitle>
          </CardHeader>
          <CardContent>
            {difficultySegments.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">暂无数据</div>
            ) : (
              <div className="flex flex-col items-center gap-4">
                <div className="relative w-40 h-40">
                  <div
                    className="w-full h-full rounded-full"
                    style={{
                      background: `conic-gradient(${difficultySegments
                        .map(
                          (s) =>
                            `${DIFFICULTY_COLORS[s.difficulty] || "#9ca3af"} ${s.start * 360}deg ${s.end * 360}deg`,
                        )
                        .join(", ")})`,
                    }}
                  />
                  <div className="absolute inset-0 m-auto w-20 h-20 bg-card rounded-full" />
                </div>
                <div className="flex flex-wrap gap-3 justify-center">
                  {difficultySegments.map((s) => (
                    <div key={s.difficulty} className="flex items-center gap-1.5 text-sm">
                      <div
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: DIFFICULTY_COLORS[s.difficulty] || "#9ca3af" }}
                      />
                      <span>{DIFFICULTY_LABELS[s.difficulty] || s.difficulty}</span>
                      <span className="text-muted-foreground">{s.percentage}%</span>
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
